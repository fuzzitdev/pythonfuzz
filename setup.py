import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="pythonfuzz",
    version="1.0.1",
    author="fuzzit.dev",
    author_email="support@fuzzit.dev",
    description="coverage-guided fuzz testing for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fuzzitdev/pythonfuzz",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing"
    ],
    python_requires='>=3.5.3',
    packages=setuptools.find_packages('.', exclude=("examples",))
)
