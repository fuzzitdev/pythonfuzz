import io
import zipfile
from pythonfuzz.main import PythonFuzz

try:
    allowed_exceptions = (zipfile.BadZipFile, zipfile.LargeZipFile)
except AttributeError:
    # In Python2, one of these had an inconsistent capitalisation
    allowed_exceptions = (zipfile.BadZipfile, zipfile.LargeZipFile)


@PythonFuzz
def fuzz(buf):
    f = io.BytesIO(buf)
    try:
        z = zipfile.ZipFile(f)
        z.testzip()
    except :
        pass


if __name__ == '__main__':
    fuzz()
