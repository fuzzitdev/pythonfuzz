import argparse
import warnings
from pythonfuzz import fuzzer

warnings.filterwarnings('ignore')


class PythonFuzz(object):
    def __init__(self, func):
        self.function = func

    def __call__(self, *args, **kwargs):
        parser = argparse.ArgumentParser(description='Coverage-guided fuzzer for python packages')
        parser.add_argument('dirs', type=str, nargs='*',
                            help="one or more directories/files to use as seed corpus. the first directory will be used to save the generated test-cases")
        parser.add_argument('--exact-artifact-path', type=str, help='set exact artifact path for crashes/ooms')
        parser.add_argument('--regression',
                            type=bool,
                            default=False,
                            help='run the fuzzer through set of files for regression or reproduction')
        parser.add_argument('--rss-limit-mb', type=int, default=2048, help='Memory usage in MB')
        parser.add_argument('--max-input-size', type=int, default=4096, help='Max input size in bytes')
        parser.add_argument('--timeout', type=int, default=30,
                            help='If input takes longer then this timeout the process is treated as failure case')
        args = parser.parse_args()
        f = fuzzer.Fuzzer(self.function, args.dirs, args.exact_artifact_path,
                          args.rss_limit_mb, args.timeout, args.regression, args.max_input_size)
        f.start()


def main():
    parser = argparse.ArgumentParser(description='Coverage-guided fuzzer for python packages')
    parser.add_argument('target', type=str, help='path to fuzz target')
    parser.add_argument('dirs', type=str, nargs='*',
                        help="one or more directories/files to use as seed corpus. the first directory will be used to save the generated test-cases")
    parser.add_argument('--exact-artifact-path', type=str, help='set exact artifact path for crashes/ooms')
    parser.add_argument('--regression',
                        type=bool,
                        default=False,
                        help='run the fuzzer through set of files for regression or reproduction')
    parser.add_argument('--rss-limit-mb', type=int, default=2048, help='Memory usage in MB')
    parser.add_argument('--timeout', type=int, default=120,
                        help='If input takes longer then this timeout the process is treated as failure case')
    args = parser.parse_args()
    f = fuzzer.Fuzzer(args.target, args.dirs, args.exact_artifact_path,
                      args.rss_limit_mb, args.timeout, args.regression)
    f.start()

#
# if __name__ == '__main__':
#     main()
