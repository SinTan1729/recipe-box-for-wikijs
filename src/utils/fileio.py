import os


def ensure_directory_exists(path, expand_user=True, file=False) -> str:
    """Create a directory if it doesn't exists.

    Expanding '~' to the user's home directory on POSIX systems.
    """
    if expand_user:
        path = os.path.expanduser(path)

    if file:
        directory = os.path.dirname(path)
    else:
        directory = path

    if not os.path.exists(directory) and directory:
        try:
            os.makedirs(directory)
        except OSError:
            # A parallel process created the directory after the existence check.
            pass

    return path


def valid_filename(directory, filename=None) -> str:
    """Return a valid "new" filename in a directory, given a filename/directory=path to test.

    Deal with duplicate filenames.
    """

    def test_filename(filename, count):
        """Filename to test for existence."""
        fn, ext = os.path.splitext(filename)
        return fn + "({})".format(count) + ext

    return_path = filename is None

    # Directory is a path.
    if filename is None:
        filename = os.path.basename(directory)
        directory = os.path.dirname(directory)

    # Allow for directories.
    ensure_directory_exists(directory)
    items = os.listdir(directory)

    if filename in items:
        answer = input("File already exists. Do you want to overwrite? [y/N]: ").strip().lower()
        if answer != "y":
            exit(2)

    if return_path:
        return os.path.join(directory, filename)
    return filename
