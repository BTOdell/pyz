pyz
===

Packages all source code and dependencies into a single Python zip application.
                                                                               

Summary
-------

Deploying a Python application any larger than a single file is
cumbersome - this library aims to solve that problem.

Python has been able to run code from within a zip file since version
2.6. Python 3.5 introduced a
**`zipapp <https://docs.python.org/3/library/zipapp.html>`__** module
which aims to simplify the process of creating a zip application.
However, **zipapp** isn’t a complete solution to the problem - it
doesn’t handle dependencies and it doesn’t include certain extra
features that this library provides.

This library allows you to bundle all of your Python code **AND** your
dependencies into a single Python zip application file.

Note: The dependency bundling feature is not implemented yet, but it is
in the works!

Features
--------

1. Bundle all Python source code with fine-grained control over included
   files.
2. Ability to “unixify” the output application by prepending a
   customizable
   `shebang <https://en.wikipedia.org/wiki/Shebang_(Unix)>`__.
3. Python interpreter version check - display a friendly notice instead
   of a Python exception if the user runs your application using an
   unsupported Python version.

Planned
-------

1. Automatically identify dependencies and package them accordingly.
