"""
Basic reader for libfuzzer/AFL style dictionaries.

See documentation at:
    https://llvm.org/docs/LibFuzzer.html#dictionaries
    https://github.com/google/AFL/blob/master/dictionaries/README.dictionaries

For our use, we only support reading the content of the dictionary values.
"""

import codecs
import random
import re
import os

class Dictionary:
    line_re = re.compile('"(.+)"$')

    def __init__(self):
        self._dict = list()

    def load(self, dict_path):
        if os.path.isfile(dict_path):
            self.load_file(dict_path)
        else:
            self.load_directory(dict_path)

    def load_directory(self, dict_path):
        """
        Read a directory of files, which are loaded raw.
        """
        for bin_file in os.listdir(dict_path):
            filename = os.path.join(dict_path, bin_file)
            if os.path.isfile(filename):
                with open(filename, 'rb') as fh:
                    self._dict.append(fh.read())

    def load_file(self, dict_path):
        """
        Read a dictionary file containing tokens.
        """
        # Token names are discarded, as per the AFL documentation

        if not dict_path or not os.path.exists(dict_path):
            return

        _dict = set()
        with open(dict_path) as f:
            for line in f:
                line = line.lstrip()
                if not line or line.startswith('#'):
                    continue
                word = self.line_re.search(line)
                if word:
                    # Decode any escaped characters, giving us a bytes object
                    value = word.group(1)
                    (value, _) = codecs.escape_decode(value)
                    _dict.add(value)
        self._dict = list(_dict)

    def get_word(self):
        if not self._dict:
            return None
        return random.choice(self._dict)
