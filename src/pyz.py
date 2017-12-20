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


def build(out_file_path, working_directory, main_path, includes,
          unixify=None,
          main_function=None,
          version_requirement=None):
    """
    Builds a "standalone" Python application by bundling the source code
    and any virtual environment dependencies into an executable zip archive.

    :param out_file_path:
    :type out_file_path: str
    :param working_directory:
    :type working_directory: str
    :param main_path:
    :type main_path: str
    :param includes:
    :type includes: list[Include]
    :param unixify:
    :type unixify: str|None
    :param main_function: The name of the main function to invoke.
    :type main_function: str|None
    :param version_requirement: The range of versions to check against the running interpreter version.
    :type version_requirement: VersionRequirement|None
    :return: None
    """
    archive_base = "app"
    old_cwd = os.getcwd()
    os.chdir(working_directory)
    try:
        # Create zip file
        zip_file_path = os.path.join(old_cwd, out_file_path + ".pyz")
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED, False) as zip_app:
            # Add files to zip file
            for include in includes:
                __add_include_path(zip_app, archive_base, include)
            # Generate __main__.py for zip file
            zip_app.writestr("__main__.py", __generate_main(os.path.join(archive_base, main_path),
                                                            main_function=main_function,
                                                            version_requirement=version_requirement))
        # If 'unixify' is truthy, then make an executable version without an extension
        if unixify:
            unix_out_file_path = os.path.join(old_cwd, out_file_path)
            with open(unix_out_file_path, "wb") as unix_app:
                # Write shabang
                unix_app.write("#!/usr/bin/env {0}\n".format(unixify).encode())
                # Append the zip application
                with open(zip_file_path, "rb") as zip_app:
                    shutil.copyfileobj(zip_app, unix_app)
    finally:
        os.chdir(old_cwd)


def __generate_main(main_path, main_function=None, version_requirement=None):
    """
    Generates the __main__.py file content to bootstrap the Python zip application.

    :param main_path: The path to the main module.
    :type main_path: str
    :param main_function: The name of the main function to invoke.
    :type main_function: str|None
    :param version_requirement: The range of versions to check against the running interpreter version.
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
            maximum_version_check_template = "(v >= {0})" if version_requirement.exclusive_maximum else "(v > {0})"
            version_checks.append(maximum_version_check_template.format(str(version_requirement.maximum)))
        if len(version_checks) > 0:
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

    :param zip_file:
    :type zip_file: zipfile.ZipFile
    :param archive_path:
    :type archive_path: str
    :param include:
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


def __locate_site_packages_dir():
    """
    Searches the filesystem starting from the current working directory
    to find the virtual environment's "site-packages" directory.

    :return: str
    """
    pass


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
