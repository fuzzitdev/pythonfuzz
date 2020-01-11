"""
Test the fuzzing terminates when a fault is found.

SUT:    Fuzzer
Area:   Fault finding
Class:  Functional
Type:   Integration test
"""

import io
import os
import unittest
import zipfile

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

            # Check that we created a crash file
            # (this is the hash of an empty string, because we know that the first call is with an empty string)
            self.assertTrue(os.path.exists('crash-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'))

            # Clean up after ourselves
            os.remove('crash-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
