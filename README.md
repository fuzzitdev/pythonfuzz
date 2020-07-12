fuzzit.dev was [acquired](https://about.gitlab.com/press/releases/2020-06-11-gitlab-acquires-peach-tech-and-fuzzit-to-expand-devsecops-offering.html) by GitLab and the new home for this repo is [here](https://gitlab.com/gitlab-org/security-products/analyzers/fuzzers/pythonfuzz)

# pythonfuzz: coverage-guided fuzz testing for python

PythonFuzz is coverage-guided [fuzzer](https://developer.mozilla.org/en-US/docs/Glossary/Fuzzing) for testing python packages.

Fuzzing for safe languages like python is a powerful strategy for finding bugs like unhandled exceptions, logic bugs,
security bugs that arise from both logic bugs and Denial-of-Service caused by hangs and excessive memory usage.

Fuzzing can be seen as a powerful and efficient strategy in real-world software in addition to classic unit-tests.

## Usage

### Fuzz Target

The first step is to implement the following function (also called a fuzz
target). Here is an example of a simple fuzz function for the built-in `html` module

```python
from html.parser import HTMLParser
from pythonfuzz.main import PythonFuzz


@PythonFuzz
def fuzz(buf):
    try:
        string = buf.decode("ascii")
        parser = HTMLParser()
        parser.feed(string)
    except UnicodeDecodeError:
        pass


if __name__ == '__main__':
    fuzz()
```

Features of the fuzz target:

* fuzz will call the fuzz target in an infinite loop with random data (according to the coverage guided algorithm) passed to `buf`( in a separate process).
* The function must catch and ignore any expected exceptions that arise when passing invalid input to the tested package.
* The fuzz target must call the test function/library with with the passed buffer or a transformation on the test buffer 
if the structure is different or from different type.
* Fuzz functions can also implement application level checks to catch application/logical bugs - For example: 
decode the buffer with the testable library, encode it again, and check that both results are equal. To communicate the results
the result/bug the function should throw an exception.
* pythonfuzz will report any unhandled exceptions as crashes as well as inputs that hit the memory limit specified to pythonfuzz
or hangs/they run more the the specified timeout limit per testcase.


### Running

The next step is to download pythonfuzz and then run your fuzzer

```bash
pip install pythonfuzz
python examples/htmlparser/fuzz.py

#394378 NEW     cov: 608 corp: 24 exec/s: 1119 rss: 10.73828125 MB
subclasses of ParserBase must override error()
Traceback (most recent call last):
  File "/Users/yevgenyp/fuzzitdev/pythonfuzz/pythonfuzz/fuzzer.py", line 21, in worker
    target(buf)
  File "examples/htmlparser/fuzz.py", line 12, in fuzz
    pass
  File "/usr/local/Cellar/python/3.7.4/Frameworks/Python.framework/Versions/3.7/lib/python3.7/html/parser.py", line 111, in feed
    self.goahead(0)
  File "/usr/local/Cellar/python/3.7.4/Frameworks/Python.framework/Versions/3.7/lib/python3.7/html/parser.py", line 179, in goahead
    k = self.parse_html_declaration(i)
  File "/usr/local/Cellar/python/3.7.4/Frameworks/Python.framework/Versions/3.7/lib/python3.7/html/parser.py", line 264, in parse_html_declaration
    return self.parse_marked_section(i)
  File "/usr/local/Cellar/python/3.7.4/Frameworks/Python.framework/Versions/3.7/lib/python3.7/_markupbase.py", line 159, in parse_marked_section
    self.error('unknown status keyword %r in marked section' % rawdata[i+3:j])
  File "/usr/local/Cellar/python/3.7.4/Frameworks/Python.framework/Versions/3.7/lib/python3.7/_markupbase.py", line 34, in error
    "subclasses of ParserBase must override error()")
NotImplementedError: subclasses of ParserBase must override error()
crash was written to crash-dbfa437e5956643645681fe6a3ac76997be0b29a7c7af82d88c8c390f379502d
crash = 3c215b63612121
```

This example quickly finds an an unhandled exception/flow in a few minutes.

### Corpus

PythonFuzz will generate and test various inputs in an infinite loop. `corpus` is optional directory and will be used to
save the generated testcases so later runs can be started from the same point and provided as seed corpus.

PythonFuzz can also start with an empty directory (i.e no seed corpus) though some valid test-cases in the seed corpus
may speed up the fuzzing substantially.  

PythonFuzz tries to mimic some of the arguments and output style from [libFuzzer](https://llvm.org/docs/LibFuzzer.html).

More fuzz targets examples (for real and popular libraries) are located under the examples directory and
bugs that were found using those targets are listed in the trophies section.

## Credits & Acknowledgments

PythonFuzz is a port of [fuzzitdev/jsfuzz](https://github.com/fuzzitdev/jsfuzz)

which is in turn heavily based on [go-fuzz](https://github.com/dvyukov/go-fuzz) originally developed by [Dmitry Vyukov's](https://twitter.com/dvyukov).
Which is in turn heavily based on [Michal Zalewski](https://twitter.com/lcamtuf) [AFL](http://lcamtuf.coredump.cx/afl/).

## Contributions

Contributions are welcome!:) There are still a lot of things to improve, and tests and features to add. We will slowly post those in the
issues section. Before doing any major contribution please open an issue so we can discuss and help guide the process before
any unnecessary work is done.


## Trophies

* [python built-in HTMLParser - unhandled exception](https://bugs.python.org/msg355287), [twice](https://bugs.launchpad.net/beautifulsoup/+bug/1883104)
* [CleverCSV - unhandled exceptions](https://github.com/alan-turing-institute/CleverCSV/issues/7)
* [beautifulsoup](https://bugs.launchpad.net/beautifulsoup/+bug/1883264)

**Feel free to add bugs that you found with pythonfuzz to this list via pull-request**
