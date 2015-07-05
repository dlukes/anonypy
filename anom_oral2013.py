#!/usr/bin/env python3


import os
import sys
import argparse
# import multiprocessing as mp

sys.path.append("/cnk/users/home/lukes/.local/lib/python3.4/site-packages")

import re
import numpy as np
from lxml import etree
import scipy.io.wavfile as scwav


def doc_generator(vert_file):
    """Yield input vertical one doc (as parsed XML) at a time.

    """
    with open(vert_file) as fh:
        doc = ""
        for line in fh:
            doc += line
            if line.startswith("</doc"):
                yield etree.fromstring(doc)
                doc = ""


def anonymize(doc_root, wav_dir, sin_freq = 440):
    """Anonymize recording corresponding to doc id.

    """
    def is_anom_seg(seg):
        return re.match("^N[PNJMO]$", seg.text.strip())

    def time2samples(time_attrib, rate):
        time = float(time_attrib)
        return int(time * rate)

    def equiv_sine_peak(num_array):
        rms = np.sqrt(np.mean(np.square(num_array.astype(int))))
        return rms*np.sqrt(2)

    def gen_sin(length, freq, fs):
        step = freq / fs * 2 * np.pi
        x = np.arange(0, length, dtype = float) * step
        return np.sin(x)

    id = doc_root.attrib["id"]
    wav_file = os.path.join(wav_dir, id + ".wav")
    fs, samples = scwav.read(wav_file)
    for seg in doc_root.xpath("//seg"):
        if is_anom_seg(seg):
            start = time2samples(seg.attrib["start"], fs)
            end = time2samples(seg.attrib["end"], fs)
            peak = equiv_sine_peak(samples[start:end+1])
            sin = gen_sin(end + 1 - start, sin_freq, fs) * peak
            samples[start:end+1] = sin.astype(np.int16)
    return fs, samples


def process(doc, args):
    id = doc.attrib["id"]
    out_file = os.path.join(args.output_dir, id + ".wav")
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
    parser = argparse.ArgumentParser(description = """
Anonymize spoken corpus recordings in WAV format based on
timestamps in corpus vertical.
""")
    parser.add_argument("vertical", help = """
a spoken corpus with timestamps for each segment, in vertical format 
""")
    parser.add_argument("-i", "--input-dir", help = """
path to directory containing input WAV files
""", required = True)
    parser.add_argument("-o", "--output-dir", help = """
path to directory where output WAV files will be saved
""", required = True)
    parser.add_argument("-f", "--freq", help = """
frequency of sine wave (in Hz) to replace anonymized segments; default
is 440 Hz
""", type = int, default = 440)
    return parser.parse_args(argv)


def main(argv = None):
    args = parse_invocation(argv)
    results = []
    for doc in doc_generator(args.vertical):
        results.append(process(doc, args))
    # pool = mp.Pool(4)
    # results = [pool.apply_async(process, args = (doc,))
    #            for doc in doc_generator(args.vertical)]
    # results = [result.get() for result in results]
    if any(results):
        sys.stderr.write("There were some errors.\n")
        return 1
    else:
        return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
