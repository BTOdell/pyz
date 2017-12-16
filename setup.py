from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name="pyz",
    version="0.1.0",
    description="Package all source code and dependencies into a single Python zip application.",
    long_description=readme(),
    author="Bradley Odell",
    author_email="btodell@hotmail.com",
    url="https://github.com/BTOdell/pyz",
    download_url="https://github.com/BTOdell/pyz/archive/0.1.0.tar.gz",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Build Tools"
    ],
    license="GPLv3",
    keywords=["pyz", "zip", "app", "zipapp", "bundle", "dependencies", "library"]
)
