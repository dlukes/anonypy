#!/usr/bin/env python3


"""Anonymize wav files according to codes in trs transcript.

"""


import sys
import argparse
import io

import re


class Anonymizer:
    """An anonymizing session.

    """


    def __init__(self, enc):
        """enc is the encoding assumed for the input trs files.

        """
        self.encoding = enc

    def anonymize(self, wav_file, trs_file):
        pass

    def anon_timespans(self, trs_file):
        """Extract pairs of Sync time attrs corresponding to anonymized spans.

        An anonymized entry is such that its text contains only NP, NN, NJ, NM
        or NO.
        """
        anon = []
        with io.open(trs_file, encoding = self.encoding) as fh:
            lines = fh.read().splitlines()
            for i, line in enumerate(lines):
                print(line.strip())
                if re.match("^N[PNJMO]$", line.strip()):
                    start = float(re.search("([\d\.]+)", lines[i-1]).group(1))
                    end = float(re.search("([\d\.]+)", lines[i+1]).group(1))
                    anon.append({"start": start,
                                 "text": line,
                                 "end": end})
        return anon


def process_command_line(argv):

    """Return args list. `argv` is a list of arguments, or `None` for
    ``sys.argv[1:]``.

    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description="""Identify overlong segments in eaf
                                 transcript file.""")

    # define options here:
    parser.add_argument("-o", "--output", help="specify file to write output to")
    parser.add_argument("-m", "--max-tokens-per-seg", type=int, default=25,
                        help="""specify maximum allowed number of tokens per
                        segment""")
    parser.add_argument("-f", "--format", help="""specify type of output;
                        defaults to eaf""", choices=["eaf", "numbered-log",
                                                     "timestamped-log"])
    parser.add_argument("input_file", nargs="+")
    parser.add_argument("-q", "--quiet", action="store_true", help="""suppress
                        logging messages""")
    parser.add_argument("-y", "--yes", action="store_true", help="""assume yes
                        to all required user interaction (WARNING: use with
                        caution)""")

    args = parser.parse_args(argv)

    # check number of arguments, verify values, etc.:
    if args:
        parser.error('program takes no command-line arguments; '
                     '"%s" ignored.' % (args,))

    # further process settings & args if necessary

    return args


def main(argv=None):
    args = process_command_line(argv)
    # application code here, like:
    # run(settings, args)
    return 0        # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
