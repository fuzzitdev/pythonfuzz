import os
import math
import numpy
import random
import struct
import hashlib


INTERESTING8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
INTERESTING16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
INTERESTING32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]


class Corpus(object):
    def __init__(self, dirs=None, max_input_size=4096):
        self._inputs = []
        self._max_input_size = max_input_size
        self._dirs = [] if dirs is None else dirs
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
        self._seed_run_finished = True if len(self._inputs) == 0 else False
        self._seed_idx = 0
        self._save_corpus = True if len(dirs) > 0 and os.path.isdir(dirs[0]) else False

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
            # Remove a range of bytes.
            x = self._rand(15)
            if x == 0:
                if len(self._inputs) <= 1:
                    i -= 1
                    continue
                pos0 = self._rand(len(res))
                pos1 = pos0 + self._choose_len(len(res) - pos0)
                self.copy(res, res, pos1, pos0)
                res = res[:len(res) - (pos1-pos0)]
            elif x == 1:
                # Insert a range of random bytes.
                pos = self._rand(len(res) + 1)
                n = self._choose_len(10)
                for k in range(n):
                    res.append(0)
                self.copy(res, res, pos, pos+n)
                for k in range(n):
                    res[pos+k] = self._rand(256)
            elif x == 2:
                # Duplicate a range of bytes.
                if len(res) <= 1:
                    i -= 1
                    continue
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
            elif x == 3:
                # Copy a range of bytes.
                if len(res) <= 1:
                    i -= 1
                    continue
                src = self._rand(len(res))
                dst = self._rand(len(res))
                while src == dst:
                    dst = self._rand(len(res))
                n = self._choose_len(len(res) - src)
                self.copy(res, res, src, dst, src+n)
            elif x == 4:
                # Bit flip. Spooky!
                if len(res) == 0:
                    i -= 1
                    continue
                pos = self._rand(len(res))
                res[pos] ^= 1 << self._rand(8)
            elif x == 5:
                # Set a byte to a random value.
                if len(res) == 0:
                    i -= 1
                    continue
                pos = self._rand(len(res))
                res[pos] ^= self._rand(255) + 1
            elif x == 6:
                # Swap 2 bytes.
                if len(res) <= 1:
                    i -= 1
                    continue
                src = self._rand(len(res))
                dst = self._rand(len(res))
                while src == dst:
                    dst = self._rand(len(res))
                res[src], res[dst] = res[dst], res[src]
            elif x == 7:
                # Add/subtract from a byte.
                if len(res) == 0:
                    i -= 1
                    continue
                pos = self._rand(len(res))
                v = self._rand(35) + 1
                if bool(random.getrandbits(1)):
                    res[pos] = numpy.uint8(res[pos]) + numpy.uint8(v)
                else:
                    res[pos] = numpy.uint8(res[pos]) - numpy.uint8(v)
            elif x == 8:
                # Add/subtract from a uint16.
                if len(res) < 2:
                    i -= 1
                    continue
                pos = self._rand(len(res) - 1)
                v = numpy.uint16(self._rand(35) + 1)
                if bool(random.getrandbits(1)):
                    v = numpy.uint16(0) - v
                if bool(random.getrandbits(1)):
                    v = struct.pack('>H', v)
                else:
                    v = struct.pack('<H', v)
                res[pos] = numpy.uint8(res[pos] + v[0])
                res[pos+1] = numpy.uint8(res[pos] + v[1])
            elif x == 9:
                # Add/subtract from a uint32.
                if len(res) < 4:
                    i -= 1
                    continue
                pos = self._rand(len(res) - 3)
                v = numpy.uint32(self._rand(35) + 1)
                if bool(random.getrandbits(1)):
                    v = numpy.uint32(0) - v
                if bool(random.getrandbits(1)):
                    v = struct.pack('>I', v)
                else:
                    v = struct.pack('<I', v)
                for k in range(4):
                    res[pos+k] = numpy.uint8(res[pos+k] + v[k])
            elif x == 10:
                # Add/subtract from a uint64.
                if len(res) < 8:
                    i -= 1
                    continue
                pos = self._rand(len(res) - 7)
                v = numpy.uint64(self._rand(35) + 1)
                if bool(random.getrandbits(1)):
                    v = numpy.uint64(0) - v
                if bool(random.getrandbits(1)):
                    v = struct.pack('>Q', v)
                else:
                    v = struct.pack('<Q', v)
                for k in range(8):
                    res[pos+k] = numpy.uint8(res[pos+k] + v[k])
            elif x == 11:
                # Replace a byte with an interesting value.
                if len(res) == 0:
                    i -= 1
                    continue
                pos = self._rand(len(res))
                res[pos] = numpy.uint8(INTERESTING8[self._rand(len(INTERESTING8))])
            elif x == 12:
                # Replace an uint16 with an interesting value.
                if len(res) < 2:
                    i -= 1
                    continue
                pos = self._rand(len(res) - 1)
                v = numpy.uint16(INTERESTING16[self._rand(len(INTERESTING16))])
                if bool(random.getrandbits(1)):
                    v = struct.pack('>H', v)
                else:
                    v = struct.pack('<H', v)
                res[pos] = numpy.uint8(v[0])
                res[pos+1] = numpy.uint8(v[1])
            elif x == 13:
                # Replace an uint32 with an interesting value.
                if len(res) < 4:
                    i -= 1
                    continue
                pos = self._rand(len(res) - 3)
                v = numpy.uint32(INTERESTING32[self._rand(len(INTERESTING32))])
                if bool(random.getrandbits(1)):
                    v = struct.pack('>I', v)
                else:
                    v = struct.pack('<I', v)
                for k in range(4):
                    res[pos+k] = numpy.uint8(v[k])
            elif x == 14:
                # Replace an ascii digit with another digit.
                digits = []
                for k in range(len(res)):
                    if ord('0') <= res[k] <= ord('9'):
                        digits.append(k)
                if len(digits) == 0:
                    i -= 1
                    continue
                pos = self._rand(len(digits))
                was = res[digits[pos]]
                now = was
                while was == now:
                    now = self._rand(10) + ord('0')
                res[digits[pos]] = now

        if len(res) > self._max_input_size:
            res = res[:self._max_input_size]
        return res
