import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from pythonfuzz.main import PythonFuzz


@PythonFuzz
def fuzz(buf):
    try:
        string = buf.decode("utf-8")
        ET.fromstring(string)
    except (UnicodeDecodeError, ParseError):
        pass


if __name__ == '__main__':
    fuzz()
