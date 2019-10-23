import io
import zipfile
# from html.parser import HTMLParser
from pythonfuzz.main import PythonFuzz


@PythonFuzz
def fuzz(buf):
    # try:
    #     string = buf.decode("utf-8")
    #     parser = HTMLParser()
    #     parser.feed(string)
    # except UnicodeDecodeError:
    #     pass
    f = io.BytesIO(buf)
    try:
        z = zipfile.ZipFile(f)
        z.testzip()
    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        pass


if __name__ == '__main__':
    fuzz()
