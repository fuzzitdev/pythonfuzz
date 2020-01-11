"""
Test the mutators operate as desired.

SUT:    Corpus
Area:   Mutators
Class:  Functional
Type:   Unit test
"""

import unittest

try:
    from unittest.mock import patch
except ImportError:
    # Python 2 backport of mock
    from mock import patch

import pythonfuzz.corpus as corpus


class FakeCorpus(object):
    pass


class BaseTestMutators(unittest.TestCase):
    """
    Test that the mutators objects are doing what we want them to do.
    """
    # Subclasses should set this - 'mutator' will be created as part of setup.
    mutator_class = None

    def setUp(self):
        self.corpus = FakeCorpus()
        self.patch_rand = patch('pythonfuzz.corpus.Mutator._rand')
        self.mock_rand = self.patch_rand.start()
        self.mock_rand.side_effect = []
        # Update the side effects in your subclass

        self.addCleanup(self.patch_rand.stop)

        self.mutator = self.mutator_class(self.corpus)


class TestMutatorRemoveRange(BaseTestMutators):
    mutator_class = corpus.MutatorRemoveRange

    def test01_empty(self):
        # You cannot remove values from an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_remove_section(self):
        # Check that it removes a sensible range

        # Check that removing at the 2nd position, removing 4 characters leaves the right string.
        self.mock_rand.side_effect = [2, 0, 3]

        res = self.mutator.mutate(bytearray(b'1234567890'))
        self.assertEqual(res, bytearray(b'127890'))


class TestMutatorInsertBytes(BaseTestMutators):
    mutator_class = corpus.MutatorInsertBytes

    def test02_insert_bytes(self):
        # Check that it inserts sensibly

        # Check that inserting at the 2nd position, adding 4 characters gives us the right string
        self.mock_rand.side_effect = [2, 0, 3, 65, 66, 67, 68]

        res = self.mutator.mutate(bytearray(b'123456789'))
        self.assertEqual(res, bytearray(b'12ABCD3456789'))


class TestMutatorDuplicateBytes(BaseTestMutators):
    mutator_class = corpus.MutatorDuplicateBytes

    def test01_empty(self):
        # Cannot work with an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_duplicate_bytes(self):
        # Check that it duplicates

        # Duplicate from offset 2 to offset 5, length 2
        self.mock_rand.side_effect = [2, 5, 0, 1]

        res = self.mutator.mutate(bytearray(b'123456789'))
        self.assertEqual(res, bytearray(b'12345346789'))


class TestMutatorCopyBytes(BaseTestMutators):
    mutator_class = corpus.MutatorDuplicateBytes

    def test01_empty(self):
        # Cannot work with an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_duplicate_bytes(self):
        # Check that it duplicates

        # Duplicate from offset 2 to offset 5, length 2
        self.mock_rand.side_effect = [2, 5, 0, 1]

        res = self.mutator.mutate(bytearray(b'123456789'))
        self.assertEqual(res, bytearray(b'12345346789'))


class TestMutatorBitFlip(BaseTestMutators):
    mutator_class = corpus.MutatorBitFlip

    def test01_empty(self):
        # Cannot work with an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_flip_bit(self):
        # Check that it flips

        # At offset 4, flip bit 3
        self.mock_rand.side_effect = [4, 3]

        res = self.mutator.mutate(bytearray(b'123456789'))
        self.assertEqual(res, bytearray(b'1234=6789'))


class TestMutatorRandomiseByte(BaseTestMutators):
    mutator_class = corpus.MutatorRandomiseByte

    def test01_empty(self):
        # Cannot work with an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_randomise_byte(self):
        # Check that it changes a byte

        # At offset 4, EOR with 65+1
        self.mock_rand.side_effect = [4, 65]

        res = self.mutator.mutate(bytearray(b'123456789'))
        self.assertEqual(res, bytearray(b'1234w6789'))


class TestMutatorSwapBytes(BaseTestMutators):
    mutator_class = corpus.MutatorSwapBytes

    def test01_empty(self):
        # Cannot work with an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_swap_bytes(self):
        # Check that it swaps bytes

        # Swap bytes at 1 and 6
        self.mock_rand.side_effect = [1, 6]

        res = self.mutator.mutate(bytearray(b'123456789'))
        self.assertEqual(res, bytearray(b'173456289'))


class TestMutatorAddSubByte(BaseTestMutators):
    mutator_class = corpus.MutatorAddSubByte

    def test01_empty(self):
        # Cannot work with an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_add_bytes(self):
        # Check that it adds/subs
        # FIXME: Not yet implemented - uses a randomised bit for the add/sub
        pass

# FIXME: Also not implemented AddSubShort, AddSubLong, AddSubLongLong
# FIXME: Not yet implemented ReplaceByte, ReplaceShort, ReplaceLong


class TestMutatorReplaceDigit(BaseTestMutators):
    mutator_class = corpus.MutatorReplaceDigit

    def test01_empty(self):
        # Cannot work with an empty input
        res = self.mutator.mutate(bytearray(b''))
        self.assertIsNone(res)

    def test02_no_digits(self):
        # Cannot work with a string that has no digits
        res = self.mutator.mutate(bytearray(b'wibble'))
        self.assertIsNone(res)

    def test03_replace_digit(self):
        # Check that it replaces a digit
        self.mock_rand.side_effect = [0, 5]

        res = self.mutator.mutate(bytearray(b'there are 4 lights'))
        self.assertEqual(res, bytearray(b'there are 5 lights'))


# FIXME: Not yet implemented: Dictionary insert, Dictionary Append


if __name__ == '__main__':
    unittest.main()
