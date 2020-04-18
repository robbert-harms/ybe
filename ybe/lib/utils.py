__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe.lib.ybe_parser import load_ybe_string
from ybe.lib.ybe_writer import write_ybe_string


def load(fname):
    """Load the data from the provided .ybe file and return an :class:`ybe.lib.ybe_contents.YbeFile` object.

    Args:
        fname (str): the filename of the .ybe file to load

    Returns:
        ybe.lib.ybe_contents.YbeFile: the contents of the .ybe file.

    Raises:
        ybe.lib.errors.YbeLoadingError: if the file could not be loaded due to syntax errors
    """
    with open(fname, "r") as f:
        return loads(f.read())


def loads(ybe_str):
    """Load the data from the provided Ybe formatted string and return an :class:`ybe.lib.ybe_contents.YbeFile` object.

    Args:
        ybe_str (str): an .ybe formatted string to load

    Returns:
        ybe.lib.ybe_contents.YbeFile: the contents of the .ybe file.

    Raises:
        ybe.lib.errors.YbeLoadingError: if the file could not be loaded due to syntax errors
    """
    return load_ybe_string(ybe_str)


def dumps(ybe_file, minimal=False):
    """Dump the provided ybe file as a .ybe formatted string.

    Args:
        ybe_file (ybe.lib.ybe_file.YbeFile): the ybe file contents to dump
        minimal (boolean): if set to True we only print the configured options.
            By default this flag is False, meaning we print all the available options, if needed with null placeholders.

    Returns:
        str: an .ybe formatted string
    """
    return write_ybe_string(ybe_file, minimal=minimal)


def dump(ybe_file, fname, minimal=False):
    """Dump the provided Ybe file to the indicated file.

    Args:
        ybe_file (ybe.lib.ybe_file.YbeFile): the ybe file contents to dump
        fname (str): the filename to dump to
        minimal (boolean): if set to True we only print the configured options.
            By default this flag is False, meaning we print all the available options, if needed with null placeholders.
    """
    with open(fname, 'w') as f:
        f.write(dumps(ybe_file, minimal=minimal))

