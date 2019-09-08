import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wArgsTools",
    version="0.0.1",
    author="Mo Hossny",
    author_email="mohossny@deakin.edu.au",
    description="Class factory for to callabls' args dynamically using ArgParser ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TBA",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
