import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import sys

from pythonfuzz.main import PythonFuzz


@PythonFuzz
def fuzz(buf):
    try:
        # In Python 2, the ElementTree only consumes bytes, not unicode strings,
        # so we need to supply the correct format depending on the python version.
        if sys.version_info[0] == 2:
            string = bytes(buf)
        else:
            string = buf.decode("utf-8")
        ET.fromstring(string)
    except (UnicodeDecodeError, ParseError):
        pass


if __name__ == '__main__':
    fuzz()
