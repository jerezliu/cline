from setuptools import setup, find_packages

setup(
    name="cline",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "requests",
        "beautifulsoup4",
    ],
    author="Cline",
    author_email="[no-reply@cline.bot](mailto:no-reply@cline.bot)",
    description="A Python library for building AI agents.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cline-labs/cline",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
