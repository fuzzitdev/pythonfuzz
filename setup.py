import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pythonfuzz",
    version="1.0.3",
    author="fuzzit.dev",
    author_email="support@fuzzit.dev",
    description="coverage-guided fuzz testing for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fuzzitdev/pythonfuzz",
    install_requires=[
        # WARNING: Keep these values in line with those in requirements.txt
        "psutil==5.6.6",
        "numpy==1.16.6; python_version < '3'",
        "numpy==1.17.3; python_version >= '3'",
        "functools32==3.2.3.post2; python_version < '3'",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing"
    ],
    python_requires='~=2.7, ~=3.5.3',
    packages=setuptools.find_packages('.', exclude=("examples",))
)
