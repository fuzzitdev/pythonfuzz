"""
Test the fuzzing terminates when no faults found, at a run limit.

SUT:    Fuzzer
Area:   Non-fault operation
Class:  Functional
Type:   Integration test
"""

import unittest

try:
    from unittest.mock import patch
except ImportError:
    # Python 2 backport of mock
    from mock import patch

import pythonfuzz.fuzzer


class TestFindCrash(unittest.TestCase):
    def test_find_crash(self):
        """
        Tests that when no Exception occurs in the fuzz function, we exit without error.

        Detects the exception implicitly by the fact that a logger call was made with
        particular text.
        """
        def fuzz(buf):
            return True

        with patch('logging.Logger.info') as mock:
            pythonfuzz.fuzzer.Fuzzer(fuzz, runs=100).start()
            mock.assert_called_with('did %d runs, stopping now.', 100)
