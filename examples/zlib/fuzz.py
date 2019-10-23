import zlib
from pythonfuzz.main import PythonFuzz


@PythonFuzz
def fuzz(buf):
    try:
        zlib.decompress(buf)
    except zlib.error:
        pass


if __name__ == '__main__':
    fuzz()
