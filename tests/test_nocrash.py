import unittest
import zipfile
import io
from unittest.mock import patch

import pythonfuzz

class TestFindCrash(unittest.TestCase):
    def test_find_crash(self):
        def fuzz(buf):
            return True

        with patch('logging.Logger.info') as mock:
            pythonfuzz.fuzzer.Fuzzer(fuzz, runs=100).start()
            mock.assert_called_with('did %d runs, stopping now.', 100)
