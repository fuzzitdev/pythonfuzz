import unittest
import zipfile
import io
from unittest.mock import patch

import pythonfuzz

class TestFindCrash(unittest.TestCase):
    def test_find_crash(self):
        def fuzz(buf):
            f = io.BytesIO(buf)
            z = zipfile.ZipFile(f)
            z.testzip()

        with patch('logging.Logger.info') as mock:
            pythonfuzz.fuzzer.Fuzzer(fuzz).start()
            self.assertTrue(mock.called_once)
