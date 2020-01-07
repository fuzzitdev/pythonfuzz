import os
import math
import numpy
import random
import struct
import hashlib

from . import dictionary


INTERESTING8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
INTERESTING16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
INTERESTING32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]


# A list of all the mutator clases we have available
mutator_classes = []


def register_mutator(cls):
    mutator_classes.append(cls)
    return cls


class Mutator(object):
    """
    Base class for all mutators.

    All mutators are based on this class, and must provide a `mutate` method, which performs
    some form of mutation on the input resource. Subclasses can be created which share some
    properties with others.

    Each mutator has a number of properties which can be used to select whether the mutator
    is of interest to the user or not.

        `name` - describes the mutator
        `types` - provides a set of named types of mutations that the class performs.
                  these types can be used to filter out uninteresting mutations.
    """
    name = None
    types = set([])

    def __init__(self, corpus):
        self.corpus = corpus

    @staticmethod
    def _rand(n):
        if n == 1 or n == 0:
            return 0
        return random.randint(0, n-1)

    @staticmethod
    def _choose_len(n):
        x = Corpus._rand(100)
        if x < 90:
            return Corpus._rand(min(8, n)) + 1
        elif x < 99:
            return Corpus._rand(min(32, n)) + 1
        else:
            return Corpus._rand(n) + 1

    @staticmethod
    def copy(src, dst, start_source, start_dst, end_source=None, end_dst=None):
        end_source = len(src) if end_source is None else end_source
        end_dst = len(dst) if end_dst is None else end_dst
        byte_to_copy = min(end_source-start_source, end_dst-start_dst)
        src[start_source:start_source+byte_to_copy] = dst[start_dst:start_dst+byte_to_copy]

    def mutate(self, res):
        """
        Function to mutate a given resource into another one.

        @return: new resource, or None if this mutator is not appropriate.
        """
        raise NotImplementedError('mutate not implemented in {}'.format(self.__class__.__name__))


@register_mutator
class MutatorRemoveRange(Mutator):
    name = 'Remove a range of bytes'
    types = set(['byte'])

    def mutate(self, res):
        if len(res) < 2:
            # Originally this checked the size of the corpus; we merely check whether the
            # resource is long. If not, we give up.
            return None

        pos0 = self._rand(len(res))
        pos1 = pos0 + self._choose_len(len(res) - pos0)
        self.copy(res, res, pos1, pos0)
        return res[:len(res) - (pos1-pos0)]


@register_mutator
class MutatorInsertBytes(Mutator):
    name = 'Insert a range of random bytes'
    types = set(['byte'])

    def mutate(self, res):
        pos = self._rand(len(res) + 1)
        n = self._choose_len(10)
        for k in range(n):
            res.append(0)
        self.copy(res, res, pos, pos+n)
        for k in range(n):
            res[pos+k] = self._rand(256)
        return res


@register_mutator
class MutatorDuplicateBytes(Mutator):
    name = 'Duplicate a range of bytes'
    types = set(['byte'])

    def mutate(self, res):
        if len(res) <= 1:
            return None
        src = self._rand(len(res))
        dst = self._rand(len(res))
        while src == dst:
            dst = self._rand(len(res))
        n = self._choose_len(len(res) - src)
        tmp = bytearray(n)
        self.copy(res, tmp, src, 0)
        for k in range(n):
            res.append(0)
        self.copy(res, res, dst, dst+n)
        for k in range(n):
            res[dst+k] = tmp[k]
        return res


@register_mutator
class MutatorCopyBytes(Mutator):
    name = 'Copy a range of bytes'
    types = set(['byte'])

    def mutate(self, res):
        if len(res) <= 1:
            return None
        src = self._rand(len(res))
        dst = self._rand(len(res))
        while src == dst:
            dst = self._rand(len(res))
        n = self._choose_len(len(res) - src)
        self.copy(res, res, src, dst, src+n)
        return res


@register_mutator
class MutatorBitFlip(Mutator):
    name = 'Bit flip'
    types = set(['bit'])

    def mutate(self, res):
        if len(res) == 0:
            return None
        pos = self._rand(len(res))
        res[pos] ^= 1 << self._rand(8)
        return res


@register_mutator
class MutatorRandomiseByte(Mutator):
    name = 'Set a byte to a random value.'
    types = set(['byte'])

    def mutate(self, res):
        if len(res) == 0:
            return None
        pos = self._rand(len(res))
        res[pos] ^= self._rand(255) + 1
        return res


@register_mutator
class MutatorSwapBytes(Mutator):
    name = 'Swap 2 bytes'
    types = set(['byte'])

    def mutate(self, res):
        if len(res) <= 1:
            return None
        src = self._rand(len(res))
        dst = self._rand(len(res))
        while src == dst:
            dst = self._rand(len(res))
        res[src], res[dst] = res[dst], res[src]
        return res


@register_mutator
class MutatorAddSubByte(Mutator):
    name = 'Add/subtract from a byte'
    types = set(['byte'])

    def mutate(self, res):
        if len(res) == 0:
            return None
        pos = self._rand(len(res))
        v = self._rand(35) + 1
        if bool(random.getrandbits(1)):
            res[pos] = numpy.uint8(res[pos]) + numpy.uint8(v)
        else:
            res[pos] = numpy.uint8(res[pos]) - numpy.uint8(v)
        return res


@register_mutator
class MutatorAddSubShort(Mutator):
    name = 'Add/subtract from a uint16'
    types = set(['short'])

    def mutate(self, res):
        if len(res) < 2:
            return None
        pos = self._rand(len(res) - 1)
        v = numpy.uint16(self._rand(35) + 1)
        if bool(random.getrandbits(1)):
            v = numpy.uint16(0) - v
        if bool(random.getrandbits(1)):
            v = struct.pack('>H', v)
        else:
            v = struct.pack('<H', v)
        v = bytearray(v)
        res[pos] = numpy.uint8(res[pos] + v[0])
        res[pos+1] = numpy.uint8(res[pos] + v[1])
        return res


@register_mutator
class MutatorAddSubLong(Mutator):
    name = 'Add/subtract from a uint32'
    types = set(['long'])

    def mutate(self, res):
        if len(res) < 4:
            return None
        pos = self._rand(len(res) - 3)
        v = numpy.uint32(self._rand(35) + 1)
        if bool(random.getrandbits(1)):
            v = numpy.uint32(0) - v
        if bool(random.getrandbits(1)):
            v = struct.pack('>I', v)
        else:
            v = struct.pack('<I', v)
        v = bytearray(v)
        for k in range(4):
            res[pos+k] = numpy.uint8(res[pos+k] + v[k])
        return res


@register_mutator
class MutatorAddSubLongLong(Mutator):
    name = 'Add/subtract from a uint64'
    types = set(['longlong'])

    def mutate(self, res):
        if len(res) < 8:
            return None
        pos = self._rand(len(res) - 7)
        v = numpy.uint64(self._rand(35) + 1)
        if bool(random.getrandbits(1)):
            v = numpy.uint64(0) - v
        if bool(random.getrandbits(1)):
            v = struct.pack('>Q', v)
        else:
            v = struct.pack('<Q', v)
        v = bytearray(v)
        for k in range(8):
            res[pos+k] = numpy.uint8(res[pos+k] + v[k])
        return res


@register_mutator
class MutatorReplaceByte(Mutator):
    name = 'Replace a byte with an interesting value'
    types = set(['byte'])

    def mutate(self, res):
        if len(res) == 0:
            return None
        pos = self._rand(len(res))
        res[pos] = numpy.uint8(INTERESTING8[self._rand(len(INTERESTING8))])
        return res


@register_mutator
class MutatorReplaceShort(Mutator):
    name = 'Replace an uint16 with an interesting value'
    types = set(['short'])

    def mutate(self, res):
        if len(res) < 2:
            return None
        pos = self._rand(len(res) - 1)
        v = numpy.uint16(INTERESTING16[self._rand(len(INTERESTING16))])
        if bool(random.getrandbits(1)):
            v = struct.pack('>H', v)
        else:
            v = struct.pack('<H', v)
        v = bytearray(v)
        res[pos] = numpy.uint8(v[0])
        res[pos+1] = numpy.uint8(v[1])
        return res


@register_mutator
class MutatorReplaceLong(Mutator):
    name = 'Replace an uint32 with an interesting value'
    types = set(['long'])

    def mutate(self, res):
        if len(res) < 4:
            return None
        pos = self._rand(len(res) - 3)
        v = numpy.uint32(INTERESTING32[self._rand(len(INTERESTING32))])
        if bool(random.getrandbits(1)):
            v = struct.pack('>I', v)
        else:
            v = struct.pack('<I', v)
        v = bytearray(v)
        for k in range(4):
            res[pos+k] = numpy.uint8(v[k])
        return res


@register_mutator
class MutatorReplaceDigit(Mutator):
    name = 'Replace an ascii digit with another digit'
    types = set(['byte', 'ascii'])

    def mutate(self, res):
        digits = []
        for k in range(len(res)):
            if ord('0') <= res[k] <= ord('9'):
                digits.append(k)
        if len(digits) == 0:
            return None
        pos = self._rand(len(digits))
        was = res[digits[pos]]
        now = was
        while was == now:
            now = self._rand(10) + ord('0')
        res[digits[pos]] = now
        return res


@register_mutator
class MutatorDictionaryWordInsert(Mutator):
    name = 'Insert a word at a random position'
    types = set(['text', 'dictionary'])

    def mutate(self, res):
        word = self.corpus._dict.get_word()
        if not word:
            return None
        pos = self._rand(len(res) + 1)
        for _ in word:
            res.append(0)
        self.copy(res, res, pos, pos+len(word))
        for k in range(len(word)):
            res[pos+k] = ord(word[k])


class CorpusError(Exception):
    pass


class Corpus(object):

    def __init__(self, dirs=None, max_input_size=4096, mutators_filter=None, dict_path=None):
        self._inputs = []
        self._dict = dictionary.Dictionary()
        if dict_path:
            self._dict.load(dict_path)
        self._max_input_size = max_input_size
        self._dirs = dirs if dirs else []
        for i, path in enumerate(dirs):
            if i == 0 and not os.path.exists(path):
                os.mkdir(path)

            if os.path.isfile(path):
                self._add_file(path)
            else:
                for i in os.listdir(path):
                    fname = os.path.join(path, i)
                    if os.path.isfile(fname):
                        self._add_file(fname)
        self._seed_run_finished = not self._inputs
        self._seed_idx = 0
        self._save_corpus = dirs and os.path.isdir(dirs[0])

        # Work out what we'll filter
        filters = mutators_filter.split(' ')
        negative_filters = [f[1:] for f in filters if f and f[0] == '!']
        required_filters = [f for f in filters if f and f[0] != '!']

        def acceptable(cls):
            # No filters => everything's fine!
            if mutators_filter is None:
                return True

            # First check that the required mutator types are set
            for f in required_filters:
                if f not in cls.types:
                    return False
            # Now remove any that are not allowed
            for f in negative_filters:
                if f in cls.types:
                    return False

            return True

        # Construct an object for each mutator we can use
        self.mutators = [cls(self) for cls in mutator_classes if acceptable(cls)]
        if not self.mutators:
            raise CorpusError("No mutators are available")

    def __repr__(self):
        return "<{}(corpus of {}, %i mutators)>".format(self.__class__.__name__,
                                                        len(self._inputs),
                                                        len(self.mutators))

    def _add_file(self, path):
        with open(path, 'rb') as f:
            self._inputs.append(bytearray(f.read()))

    @property
    def length(self):
        return len(self._inputs)

    @staticmethod
    def _rand(n):
        if n == 1 or n == 0:
            return 0
        return random.randint(0, n-1)

    # Exp2 generates n with probability 1/2^(n+1).
    @staticmethod
    def _rand_exp():
        rand_bin = bin(random.randint(0, 2**32-1))[2:]
        rand_bin = '0'*(32 - len(rand_bin)) + rand_bin
        count = 0
        for i in rand_bin:
            if i == '0':
                count +=1
            else:
                break
        return count

    def put(self, buf):
        self._inputs.append(buf)
        if self._save_corpus:
            m = hashlib.sha256()
            m.update(buf)
            fname = os.path.join(self._dirs[0], m.hexdigest())
            with open(fname, 'wb') as f:
                f.write(buf)

    def generate_input(self):
        if not self._seed_run_finished:
            next_input = self._inputs[self._seed_idx]
            self._seed_idx += 1
            if self._seed_idx >= len(self._inputs):
                self._seed_run_finished = True
            return next_input

        if len(self._inputs) == 0:
            zero_test_case = bytearray(0)
            self.put(zero_test_case)
            return zero_test_case
        else:
            buf = self._inputs[self._rand(len(self._inputs))]
            return self.mutate(buf)

    def mutate(self, buf):
        res = buf[:]
        nm = self._rand_exp()
        for i in range(nm):

            # Select a mutator from those we can apply
            # We'll try up to 20 times, but if we don't find a
            # suitable mutator after that, we'll just give up.
            for n in range(20):
                x = self._rand(len(self.mutators))
                mutator = self.mutators[x]

                newres = mutator.mutate(res)
                if newres is not None:
                    break
            if newres is not None:
                res = newres

        if len(res) > self._max_input_size:
            res = res[:self._max_input_size]
        return res
