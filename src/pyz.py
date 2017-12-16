import fnmatch
import os
import shutil
import zipfile


__MAIN_TEMPLATE = """
import sys
import os
v = sys.version_info
if {0} or {1}:
    # Print error message
    sys.stderr.write("Python {{0}}.{{1}}.{{2}} is not supported.\\n".format(v.major, v.minor, v.micro))
    sys.stderr.write("Supported versions: {2}.{3} <= version {4} {5}.{6}\\n")
    sys.exit(1)
# Run main
from {7} import {8}
{8}()
""".lstrip()


def build(out_file_path, base, main, includes, unixify=None,
          min_version=(2, 7), max_version=(3, 0), exclusive_version=True):
    """
    Builds a "standalone" Python application by bundling the source code and any virtual environment dependencies.

    :param out_file_path:
    :param base:
    :param main:
    :param includes:
    :param unixify:
    :param min_version:
    :param max_version:
    :param exclusive_version:
    :return: None
    """
    archive_base = "app"
    old_cwd = os.getcwd()
    os.chdir(os.path.join(old_cwd, base))
    try:
        # Create zip file
        zip_file_path = os.path.join(old_cwd, out_file_path + ".pyz")
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED, False) as zip_app:
            # Add files to zip file
            for include in includes:
                __add_include_path(zip_app, include, archive_base)
            # Generate __main__.py for zip file
            zip_app.writestr("__main__.py", __generate_main(os.path.join(archive_base, main),
                                                            min_version=min_version, max_version=max_version,
                                                            exclusive_version=exclusive_version))
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


def __generate_main(path, main_function="main", min_version=(2, 7), max_version=(3, 0), exclusive_version=True):
    """

    :param path:
    :param main_function:
    :param min_version:
    :param max_version:
    :param exclusive_version:
    :return:
    """
    min_check = "(v < {0})".format(str(min_version))
    max_check = ("(v >= {0})" if exclusive_version else "(v > {0})").format(str(max_version))
    split = [str(package) for package in os.path.normpath(path).split(os.path.sep) if len(package) > 0]
    return __MAIN_TEMPLATE.format(min_check, max_check,
                                  min_version[0], min_version[1],
                                  "<" if exclusive_version else "<=",
                                  max_version[0], max_version[1],
                                  ".".join(split), main_function)


def __add_include_path(zip_file, include_path, archive_base):
    """

    :param zip_file:
    :param include_path:
    :param archive_base:
    :return:
    """
    if isinstance(include_path, tuple):
        source_path = include_path[0]
        destination_path = include_path[1]
    else:
        source_path = include_path
        destination_path = include_path
    if os.path.isfile(source_path):
        zip_file.write(source_path, os.path.join(archive_base, destination_path))
    else:
        if source_path != destination_path:
            raise ValueError("Source is a directory and cannot be mapped.")
        for info in os.walk(source_path):
            # Add files
            dirpath = info[0]
            filenames = info[2]
            for filename in fnmatch.filter(filenames, "*.py"):
                filepath = os.path.join(dirpath, filename)
                zip_file.write(filepath, os.path.join(archive_base, filepath))


def __locate_site_packages_dir():
    """
    Searches the filesystem starting from the current working directory
    to find the virtual environment's "site-packages" directory.

    :return: str
    """
    pass
