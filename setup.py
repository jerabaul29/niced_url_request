import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="niced_url_request",
    version="0.1",
    author="Jean Rabault",
    author_email="jean.rblt@gmail.com",
    description="a simple class wrapper to nice URL requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jerabaul29/niced_url_request",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "raise_assert>=0.2"
    ]
    python_requires='>=3.5',
)
