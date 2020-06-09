import os
import sys
import time
import sys
import psutil
import hashlib
import logging
import functools
import multiprocessing as mp

from pythonfuzz import corpus, tracer

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger().setLevel(logging.DEBUG)

SAMPLING_WINDOW = 5 # IN SECONDS

try:
    lru_cache = functools.lru_cache
except:
    import functools32
    lru_cache = functools32.lru_cache


def worker(target, child_conn, close_fd_mask):
    # Silence the fuzzee's noise
    class DummyFile:
        """No-op to trash stdout away."""
        def write(self, x):
            pass
    logging.captureWarnings(True)
    logging.getLogger().setLevel(logging.CRITICAL)
    if close_fd_mask & 1:
        sys.stdout = DummyFile()
    if close_fd_mask & 2:
        sys.stderr = DummyFile()

    sys.settrace(tracer.trace)
    while True:
        buf = child_conn.recv_bytes()
        try:
            target(buf)
        except Exception as e:
            print("Exception: %r\n" % (e,))
            logging.exception(e)
            child_conn.send(e)
            break
        else:
            child_conn.send_bytes(b'%d' % tracer.get_coverage())


class Fuzzer(object):
    def __init__(self,
                 target,
                 dirs=None,
                 exact_artifact_path=None,
                 rss_limit_mb=2048,
                 timeout=120,
                 regression=False,
                 max_input_size=4096,
                 close_fd_mask=0,
                 runs=-1,
                 mutators_filter=None,
                 dict_path=None):
        self._target = target
        self._dirs = [] if dirs is None else dirs
        self._exact_artifact_path = exact_artifact_path
        self._rss_limit_mb = rss_limit_mb
        self._timeout = timeout
        self._regression = regression
        self._close_fd_mask = close_fd_mask
        self._corpus = corpus.Corpus(self._dirs, max_input_size, mutators_filter, dict_path)
        self._total_executions = 0
        self._executions_in_sample = 0
        self._last_sample_time = time.time()
        self._total_coverage = 0
        self._p = None
        self.runs = runs

    def help_mutators(self):
        print("Mutators currently available (and their types):")
        active_mutators = [mutator.__class__ for mutator in self._corpus.mutators]
        for mutator in corpus.mutator_classes:
            active = mutator in active_mutators
            indicator = '-' if not active else ' '
            print("  {}{:<60s} [{}]".format(indicator, mutator.name, ', '.join(sorted(mutator.types))))
        print("\nMutators prefixed by '-' are currently disabled.")

    def log_stats(self, log_type):
        rss = (psutil.Process(self._p.pid).memory_info().rss + psutil.Process(os.getpid()).memory_info().rss) / 1024 / 1024

        endTime = time.time()
        execs_per_second = int(self._executions_in_sample / (endTime - self._last_sample_time))
        self._last_sample_time = time.time()
        self._executions_in_sample = 0
        logging.info('#{} {}     cov: {} corp: {} exec/s: {} rss: {} MB'.format(
            self._total_executions, log_type, self._total_coverage, self._corpus.length, execs_per_second, rss))
        return rss

    def write_sample(self, buf, prefix='crash-'):
        m = hashlib.sha256()
        m.update(buf)
        if self._exact_artifact_path:
            crash_path = self._exact_artifact_path
        else:
            crash_path = prefix + m.hexdigest()
        logging.info('sample written to {}'.format(crash_path))
        if len(buf) < 200:
            try:
                logging.info('sample = {}'.format(buf.hex()))
            except AttributeError:
                logging.info('sample = {!r}'.format(buf))
        with open(crash_path, 'wb') as f:
            f.write(buf)

    def start(self):
        logging.info("#0 READ units: {}".format(self._corpus.length))

        parent_conn, child_conn = mp.Pipe()
        self._p = mp.Process(target=worker, args=(self._target, child_conn, self._close_fd_mask))
        self._p.start()

        while True:
            if self.runs != -1 and self._total_executions >= self.runs:
                self._p.terminate()
                logging.info('did %d runs, stopping now.', self.runs)
                break

            buf = self._corpus.generate_input()
            parent_conn.send_bytes(bytes(buf))
            if not parent_conn.poll(self._timeout):
                self._p.terminate()
                logging.info("=================================================================")
                logging.info("timeout reached. testcase took: {}".format(self._timeout))
                self.write_sample(buf, prefix='timeout-')
                break

            try:
                total_coverage = int(parent_conn.recv_bytes())
            except ValueError:
                self.write_sample(buf)
                break

            self._total_executions += 1
            self._executions_in_sample += 1
            rss = 0
            if total_coverage > self._total_coverage:
                self._total_coverage = total_coverage
                self._corpus.put(buf)
                rss = self.log_stats("NEW")
            else:
                if (time.time() - self._last_sample_time) > SAMPLING_WINDOW:
                    rss = self.log_stats('PULSE')

            if rss > self._rss_limit_mb:
                logging.info('MEMORY OOM: exceeded {} MB. Killing worker'.format(self._rss_limit_mb))
                self.write_sample(buf)
                self._p.kill()
                break

        self._p.join()
