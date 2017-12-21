"""
Provides utility functions to build a Python zip application.
"""

import fnmatch
import os
import shutil
import zipfile


__MAIN_TEMPLATE = """
{0}
# Run main
from {1} import {2}
{2}()
""".lstrip()

__VERSION_CHECK_TEMPLATE = """
import sys
v = sys.version_info
if {0}:
    # Print error message
    sys.stderr.write("Python {{0}}.{{1}}.{{2}} is not supported.\\n".format(v.major, v.minor, v.micro))
    sys.stderr.write("Supported versions: {1}version{2}\\n")
    sys.exit(1)
""".lstrip()


def build(out_file_path, main_module_path, includes,
          include_directory=None,
          main_function=None,
          version_requirement=None,
          archive_source_base=None,
          unixify=None):
    """
    Builds a "standalone" Python application by bundling the source code
    and any virtual environment dependencies into an executable zip archive.

    :param out_file_path: The output file path of the Python zip application.
    :type out_file_path: str
    :param main_module_path: The path to the main module (relative to the include directory, without the .py extension).
    :type main_module_path: str
    :param includes: A list of include items to be added to the Python zip application.
    :type includes: list[Include]
    :param include_directory: The base directory to add include items from.
    :type include_directory: str|None
    :param main_function: The name of the main function to invoke.
    :type main_function: str|None
    :param version_requirement: The range of versions to check against the running interpreter version.
    :type version_requirement: VersionRequirement|None
    :param archive_source_base: The base directory in the zip application to include all source files.
    :type archive_source_base: str|None
    :param unixify: Additional information to output a unix-like application.
    :type unixify: Unixify|None
    :return: None
    """
    archive_source_base_path = "dist" if archive_source_base is None else archive_source_base

    def write_zip_app(file_path, mode='w'):
        # Note: Must use try-finally instead of 'with' context manager in order to maintain 2.6 compatibility.
        pyz = zipfile.ZipFile(file_path, mode, zipfile.ZIP_DEFLATED, False)
        try:
            def add_includes():
                # Add files to zip file
                for include in includes:
                    __add_include_path(pyz, archive_source_base_path, include)

            if include_directory is None:
                add_includes()
            else:
                # Change to include directory
                old_cwd = os.getcwd()
                os.chdir(include_directory)
                try:
                    add_includes()
                finally:
                    os.chdir(old_cwd)

            # Generate __main__.py for zip file
            pyz.writestr("__main__.py",
                         __generate_main(os.path.join(archive_source_base_path, main_module_path),
                                         main_function=main_function,
                                         version_requirement=version_requirement))
        finally:
            pyz.close()

    if unixify is None:
        # Write one zip application file
        write_zip_app(out_file_path)
    else:
        def write_unix(file_path, append_file_path=None):
            with open(file_path, "wb") as unix_app:
                # Write shebang
                unix_app.write("#!{0}\n".format(unixify.shebang).encode())
                # Optionally append another file
                if append_file_path is not None:
                    with open(append_file_path, "rb") as append_file:
                        shutil.copyfileobj(append_file, unix_app)

        unix_out_file_path = unixify.out_file_path
        if unix_out_file_path is None:
            # Write one unix zip application file
            write_unix(out_file_path)
            write_zip_app(out_file_path, mode='a')
        else:
            # Write non-unix zip application file
            write_zip_app(out_file_path)
            # Write unix zip application file
            write_unix(unix_out_file_path, append_file_path=out_file_path)


def __generate_main(main_path, main_function=None, version_requirement=None):
    """
    Generates the __main__.py file content to bootstrap the Python zip application.

    :param main_path: The path to the main module.
    :type main_path: str
    :param main_function: The name of the main function to invoke.
    :type main_function: str|None
    :param version_requirement: The range of versions to check
                                against the running interpreter version.
    :type version_requirement: VersionRequirement|None
    :return: The generated __main__.py file content.
    :rtype: str
    """
    # Determine main function name
    main_function_name = "main" if main_function is None else main_function
    # Generate version check Python code
    version_code = ""
    if version_requirement is not None:
        version_checks = []
        if version_requirement.minimum is None:
            minimum_version_str = ""
        else:
            minimum_version_str = "{0} <= ".format(".".join(map(str, version_requirement.minimum)))
            version_checks.append("(v < {0})".format(str(version_requirement.minimum)))
        if version_requirement.maximum is None:
            maximum_version_str = ""
        else:
            maximum_version_str = " {0} {1}".format("<" if version_requirement.exclusive_maximum else "<=",
                                                    ".".join(map(str, version_requirement.maximum)))
            maximum_version_check = "(v >= {0})" if version_requirement.exclusive_maximum else "(v > {0})"
            version_checks.append(maximum_version_check.format(str(version_requirement.maximum)))
        if version_checks:
            version_check = " or ".join(version_checks)
            version_code = __VERSION_CHECK_TEMPLATE.format(version_check, minimum_version_str, maximum_version_str)
    # Generate __main__.py file content
    split = [str(package) for package in os.path.normpath(main_path).split(os.path.sep) if len(package) > 0]
    return __MAIN_TEMPLATE.format(version_code,
                                  ".".join(split),
                                  main_function_name)


def __add_include_path(zip_file, archive_path, include):
    """
    Adds the given include item to the zip archive.

    :param zip_file: The zip file to add the include item to.
    :type zip_file: zipfile.ZipFile
    :param archive_path: The base path in the zip file to add the include item relative to.
    :type archive_path: str
    :param include: Specifies resource(s) to include in the zip file.
    :type include: Include
    """
    if os.path.isfile(include.source_path):
        zip_file.write(include.source_path, os.path.join(archive_path, include.destination_path))
    else:
        # Add Python file(s) to zip archive.
        if include.source_path != include.destination_path:
            raise ValueError("Source is a directory and cannot be mapped.")
        for info in os.walk(include.source_path):
            dirpath = info[0]
            filenames = info[2]
            for filename in fnmatch.filter(filenames, include.glob):
                filepath = os.path.join(dirpath, filename)
                zip_file.write(filepath, os.path.join(archive_path, filepath))


class Include(object):
    """
    Represents a resource (file, directory, etc) to be included in the Python zip application.
    """

    def __init__(self, source_path, destination_path=None, glob=None):
        """
        Creates a new metadata item for including resources in a Python zip application.

        :param source_path: The source path of the resource to include.
        :type source_path: str
        :param destination_path: The destination (archive) path of the included resource.
        :type destination_path: str|None
        :param glob: A glob to filter individual files to be included.
        :type glob: str|None
        """
        super(Include, self).__init__()
        self.source_path = source_path
        self.destination_path = source_path if destination_path is None else destination_path
        self.glob = "*.py" if glob is None else glob


class VersionRequirement(object):
    """
    Represents a range of versions to check against an interpreter version.
    """

    def __init__(self, minimum=None, maximum=None, exclusive_maximum=True):
        """
        Creates a version requirement range.

        :param minimum: The minimum required version.
        :type minimum: tuple[int, int, int]
        :param maximum: The maximum required version.
        :type maximum: tuple[int, int, int]
        :param exclusive_maximum: Whether the maximum version is exclusive.
        :type exclusive_maximum: bool
        """
        super(VersionRequirement, self).__init__()
        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum


class Unixify(object):
    """
    Provides information to output a unix-like executable.
    """

    def __init__(self, out_file_path=None, shebang=None):
        """
        Creates a specification for building a unix-like executable.

        :param out_file_path: The output file path of a second executable.
                              If None, then the main output file path is used
                              for the unix-like executable and only one file is generated.
        :type out_file_path: str|None
        :param shebang: The shebang string to insert at the start of the zip file to enable unix-like behavior.
                        This string should not include the shebang (#!) itself or a newline at the end.
                        Default: /usr/bin/env python
        :type shebang: str|None
        """
        super(Unixify, self).__init__()
        self.out_file_path = out_file_path
        self.shebang = "/usr/bin/env python" if shebang is None else shebang
