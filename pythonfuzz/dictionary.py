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

    def __init__(self, dict_path=None):
        if not dict_path or not os.path.exists(dict_path):
            self._dict = list()
            return

        _dict = set()
        with open(dict_path) as f:
            for line in f:
                line = line.lstrip()
                if line.startswith('#'):
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
