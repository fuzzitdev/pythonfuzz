#!/usr/bin/env python
"""
Run all the examples and collect the timings and results.

SUT:    Invocation
Area:   Examples run
Class:  Functional
Type:   System test
"""

import argparse
import os.path
import re
import subprocess
import sys
import time

here = os.path.dirname(__file__)


class Result(object):
    """
    Use the output from the tool to collect the information about its execution.

    Very sensitive to the format of the output as to whether it collects information or not.
    """
    coverage_re = re.compile('cov: (\d+)')
    corpus_re = re.compile('corp: (\d+)')
    speed_re = re.compile('exec/s: (\d+)')
    memory_re = re.compile('rss: (\d+\.\d+)')
    count_re = re.compile('^#(\d+)')
    count2_re = re.compile('^did (\d+) runs, stopping now')
    exception_re = re.compile('^Exception: (.*)')
    failfile_re = re.compile('^sample written to (.*)')

    def __init__(self):
        self.coverage = None
        self.corpus = None
        self.speed = None
        self.memory = None
        self.count = None
        self.time_start = None
        self.time_end = None
        self.fail_file = None
        self.exception = None
        self.lines = []
        self.rc = None

    def record_start(self):
        self.time_start = time.time()

    def record_end(self):
        self.time_end = time.time()

    @property
    def time_duration(self):
        """
        Number of seconds the execution took, or None if not known
        """
        if self.time_start and self.time_end:
            return self.time_end - self.time_start
        if self.time_start:
            return time.time() - self.time_start

        return None

    def process_output(self, line):
        match = self.coverage_re.search(line)
        if match:
            self.coverage = int(match.group(1))

        match = self.corpus_re.search(line)
        if match:
            self.corpus = int(match.group(1))

        match = self.speed_re.search(line)
        if match:
            self.speed = int(match.group(1))

        match = self.memory_re.search(line)
        if match:
            self.memory = float(match.group(1))

        match = self.count_re.search(line) or self.count2_re.search(line)
        if match:
            self.count = int(match.group(1))

        match = self.exception_re.search(line)
        if match:
            self.exception = match.group(1)

        match = self.failfile_re.search(line)
        if match:
            self.fail_file = match.group(1)

        self.lines.append(line)

    def show(self, show_lines=False, indent=''):
        """
        Show the status of this result.
        """
        print("{}Executions       : {}".format(indent, self.count))
        print("{}Corpus           : {}".format(indent, self.corpus))
        print("{}Coverage         : {}".format(indent, self.coverage))
        print("{}Final speed      : {}/s".format(indent, self.speed))
        if self.memory:
            print("{}Memory           : {:.2f} MB".format(indent, self.memory))
        print("{}Runtime          : {:.2f} s".format(indent, self.time_duration))
        if self.time_duration and self.count:
            print("{}Overall speed    : {:.2f}/s".format(indent, self.count / self.time_duration))
        print("{}Return code      : {}".format(indent, self.rc))
        if self.exception:
            print("{}Exception        : {}".format(indent, self.exception))
        if self.fail_file:
            print("{}Failed filename  : {}".format(indent, self.fail_file))

        if show_lines or self.rc:
            print("{}Lines:".format(indent))
            for line in self.lines:
                print("{}  {}".format(indent, line.strip('\n')))


class Example(object):

    def __init__(self, name, path, script):
        self.name = name
        self.path = path
        self.script = script

    def run(self, python='python', runs=100, log='/dev/null'):
        """
        Run the example script, capturing the output and maybe processing it.
        """
        cmd = [python, self.script, '--runs', str(runs)]

        result = Result()
        with open(log, 'w') as log_fh:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            result.record_start()
            for line in proc.stdout:
                line = line.decode('utf-8', 'replace')
                result.process_output(line)
            result.record_end()

            proc.wait()
            result.rc = proc.returncode

        return result


def find_examples():
    examples = []
    print("Looking in {} for examples".format(here))
    for obj in os.listdir(here):
        path = os.path.join(here, obj)
        if os.path.isdir(path):
            # At a later date we might actually provide multiple fuzz's per example.
            fuzz = os.path.join(path, 'fuzz.py')
            if os.path.isfile(fuzz):
                examples.append(Example(obj, path, fuzz))

    return examples


def main():
    parser = argparse.ArgumentParser(description='Exercise the example code')
    parser.add_argument('--runs', type=int, default=1000, help='Number of individual test runs.')
    parser.add_argument('--keep', action='store_true', help='Keep the crash/timeout files')

    args = parser.parse_args()

    # We remember whether the example itself failed (not the underlying module being fuzz'd)
    # so that we can fail this run.
    any_failed = False
    for example in find_examples():
        print("Example: {}".format(example.name))
        result = example.run(python=sys.executable, runs=args.runs)
        result.show(indent='  ')
        if not args.keep:
            if result.fail_file:
                os.remove(result.fail_file)
        if result.rc != 0:
            any_failed = True

    sys.exit(1 if any_failed else 0)


if __name__ == '__main__':
    main()
