import os
import sys
import time
import psutil
import hashlib
import logging
import coverage
import multiprocessing as mp

from pythonfuzz import corpus

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger().setLevel(logging.DEBUG)

SAMPLING_WINDOW = 5 # IN SECONDS


def worker(target, child_conn):
    cov = coverage.Coverage(branch=True, cover_pylib=True)
    cov.start()
    while True:
        buf = child_conn.recv()
        try:
            target(buf)
        except Exception as e:
            logging.exception(e)
            child_conn.send(e)
            break
        else:
            total_coverage = 0
            cov_data = cov.get_data()
            for filename in cov_data._arcs:
                total_coverage += len(cov_data._arcs[filename])
            child_conn.send(total_coverage)


class Fuzzer(object):
    def __init__(self,
                 target,
                 dirs=None,
                 exact_artifact_path=None,
                 rss_limit_mb=2048,
                 timeout=120,
                 regression=False,
                 max_input_size=4096):
        self._target = target
        self._dirs = [] if dirs is None else dirs
        self._exact_artifact_path = exact_artifact_path
        self._rss_limit_mb = rss_limit_mb
        self._timeout = timeout
        self._regression = regression
        self._corpus = corpus.Corpus(self._dirs, max_input_size)
        self._total_executions = 0
        self._executions_in_sample = 0
        self._last_sample_time = time.time()
        self._total_coverage = 0
        self._p = None

    def log_stats(self, log_type):
        rss = (psutil.Process(self._p.pid).memory_info().rss + psutil.Process(os.getpid()).memory_info().rss) / 1024 / 1024

        endTime = time.time()
        execs_per_second = int(self._executions_in_sample / (endTime - self._last_sample_time))
        self._last_sample_time = time.time()
        self._executions_in_sample = 0
        logging.info('#{} {}     cov: {} corp: {} exec/s: {} rss: {} MB'.format(
            self._total_executions, log_type, self._total_coverage, self._corpus.length, execs_per_second, rss))
        return rss

    def write_crash(self, buf):
        m = hashlib.sha256()
        m.update(buf)
        if self._exact_artifact_path:
            crash_path = self._exact_artifact_path
        else:
            crash_path = 'crash-' + m.hexdigest()
        with open(crash_path, 'wb') as f:
            f.write(buf)
        logging.info('crash was written to {}'.format(crash_path))
        if len(buf) < 200:
            logging.info('crash = {}'.format(buf.hex()))

    def start(self):
        logging.info("#0 READ units: {}".format(self._corpus.length))

        parent_conn, child_conn = mp.Pipe()
        self._p = mp.Process(target=worker, args=(self._target, child_conn))
        self._p.start()

        while True:
            buf = self._corpus.generate_input()
            parent_conn.send(buf)
            if not parent_conn.poll(self._timeout):
                self._p.kill()
                logging.info("=================================================================")
                logging.info("timeout reached. testcase took: {}".format(self._timeout))
                break

            total_coverage = parent_conn.recv()
            if type(total_coverage) != int:
                self.write_crash(buf)
                break

            self._total_executions += 1
            self._executions_in_sample += 1
            rss = 0
            if total_coverage > self._total_coverage:
                rss = self.log_stats("NEW")
                self._total_coverage = total_coverage
                self._corpus.put(buf)
            else:
                if (time.time() - self._last_sample_time) > SAMPLING_WINDOW:
                    rss = self.log_stats('PULSE')

            if rss > self._rss_limit_mb:
                logging.info('MEMORY OOM: exceeded {} MB. Killing worker'.format(self._rss_limit_mb))
                self.write_crash(buf)
                self._p.kill()
                break

        self._p.join()
