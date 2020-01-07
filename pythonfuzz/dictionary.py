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
                    _dict.add(word.group(1))
        self._dict = list(_dict)

    def get_word(self):
        if not self._dict:
            return None
        return random.choice(self._dict)
