#!/cnk/users/home/lukes/.linuxbrew/bin/python3

import os
import sys
import argparse
# import multiprocessing as mp

sys.path.append("/cnk/users/home/lukes/.local/lib/python3.4/site-packages")

import re
import numpy as np
from lxml import etree
import scipy.io.wavfile as scwav


class Transcript():
    """A wrapper offering a shared interface to vertical and trs transcripts.

    """
    def __init__(self, doc_root, trs=False, id=None):
        self.root = doc_root
        self.trs = trs
        if id is None:
            self.id = self.root.attrib["id"]
        else:
            self.id = id

    def segs(self):
        if self.trs:
            return self.root.xpath("//text()")
        else:
            return self.root.xpath("//seg")

    def is_anom_seg(self, seg):
        text = seg.strip() if self.trs else seg.text.strip()
        return re.match("^N[PNJMO]$", text)

    def seg_start(self, seg):
        if self.trs:
            p = seg.getparent()
            # get @time of <Sync> or @startTime of <Turn> if the parent is a
            # <Turn> (shouldn't be, but who knows)
            return p.get("time", p.get("startTime"))
        else:
            return seg.attrib["start"]

    def seg_end(self, seg):
        if self.trs:
            # get next <Sync> or failing that, enclosing <Turn>
            n = seg.getparent().getnext()
            if n is None:
                n = seg.getparent().getparent()
            # get @time of next <Sync> or @endTime of enclosing <Turn>
            return n.get("time", n.get("endTime"))
        else:
            return seg.attrib["end"]


def doc_generator(input, trs=False):
    """Yield input vertical or trs one doc (as parsed XML) at a time.

    """
    with open(input) as fh:
        if trs:
            root = etree.parse(input).getroot()
            id, _ = os.path.splitext(os.path.basename(input))
            yield Transcript(root, trs, id)
        else:
            doc = ""
            for line in fh:
                doc += line
                if line.startswith("</doc"):
                    yield Transcript(etree.fromstring(doc))
                    doc = ""


def anonymize(doc, wav_dir, sin_freq=440):
    """Anonymize recording corresponding to doc id.

    """
    def time2samples(time_attrib, rate):
        time = float(time_attrib)
        return int(time * rate)

    def equiv_sine_peak(num_array):
        rms = np.sqrt(np.mean(np.square(num_array.astype(int))))
        return rms * np.sqrt(2)

    def gen_sin(length, freq, fs):
        step = freq / fs * 2 * np.pi
        x = np.arange(0, length, dtype=float) * step
        return np.sin(x)

    wav_file = os.path.join(wav_dir, doc.id + ".wav")
    fs, samples = scwav.read(wav_file)
    dtype = samples.dtype
    channels = samples.shape[1]
    if channels > 1:
        sys.stderr.write(
            "{} is not mono ({} channels).\n".format(wav_file, channels))
    for seg in doc.segs():
        if doc.is_anom_seg(seg):
            start = time2samples(doc.seg_start(seg), fs)
            end = min(time2samples(doc.seg_end(seg), fs),
                      len(samples) - 1)
            peak = equiv_sine_peak(samples[start:end + 1])
            sin = gen_sin(end + 1 - start, sin_freq, fs) * peak
            sin = sin.astype(dtype)
            for i in range(channels):
                samples[start:end + 1, i] = sin
    return fs, samples


def process(doc, args):
    out_file = os.path.join(args.output_dir, doc.id + ".wav")
    if not os.path.isfile(out_file):
        fs, samples = anonymize(doc, args.input_dir, args.freq)
        scwav.write(out_file, fs, samples)
        sys.stderr.write("Saved {}.\n".format(out_file))
        return 0
    else:
        sys.stderr.write("Target file {} already exists in output "
                         "directory {}. Please remove it or specify a "
                         "different output dir.\n".format(
                             os.path.basename(out_file),
                             os.path.dirname(out_file)))
        sys.stderr.flush()
        return 1


def parse_invocation(argv):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description="""
Anonymize spoken corpus recordings in WAV format based on
timestamps in corpus vertical.
""")
    parser.add_argument("input", help="""
a spoken corpus with timestamps for each segment, in vertical format;
alternatively, a .trs file (see option --trs)
""")
    parser.add_argument("-i", "--input-dir", help="""
path to directory containing input WAV files
""", required=True)
    parser.add_argument("-o", "--output-dir", help="""
path to directory where output WAV files will be saved
""", required=True)
    parser.add_argument("-f", "--freq", help="""
frequency of sine wave (in Hz) to replace anonymized segments; default
is 440 Hz
""", type=int, default=440)
    parser.add_argument("-t", "--trs", action="store_true", help="""
consider input to be .trs instead of vertical
""")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_invocation(argv)
    results = []
    for doc in doc_generator(args.input, args.trs):
        results.append(process(doc, args))
    # pool = mp.Pool(4)
    # results = [pool.apply_async(process, args = (doc,))
    #            for doc in doc_generator(args.vertical)]
    # results = [result.get() for result in results]
    if any(results):
        sys.stderr.write("WARNING: Some already existing files were not"
                         " overwritten.\n")
        return 0
    else:
        return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
