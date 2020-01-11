import unittest
import zipfile
import io

try:
    from unittest.mock import patch
except ImportError:
    # Python 2 backport of mock
    from mock import patch

import pythonfuzz.fuzzer


class TestFindCrash(unittest.TestCase):
    def test_find_crash(self):
        """
        Tests that when an Exception occurs in the fuzz function, we detect this.

        Requires that the Fuzzer's configuration causes it to stop when an exception
        is detected, and that the fuzzer will generate an invalid zip file.
        Detects the exception implicitly by the fact that a logger call was made.
        """
        def fuzz(buf):
            f = io.BytesIO(buf)
            z = zipfile.ZipFile(f)
            z.testzip()

        with patch('logging.Logger.info') as mock:
            pythonfuzz.fuzzer.Fuzzer(fuzz).start()
            self.assertTrue(mock.called_once)
