__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
from dataclasses import MISSING


def copy_ybe_resources(ybe_file, dirname):
    """Copy all the resource specified in the provided Ybe file object to the provided directory.

    Args:
        ybe_file (ybe.lib.ybe_contents.YbeFile): the Ybe file data to search for (external) resources.
        dirname (str): the directory to write the data to.
    """
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    for resource in ybe_file.get_resources():
        ybe_file.resource_context.copy_resource(resource, dirname)


def get_default_value(field):
    """Resolve the default value of a dataclass field.

    This first looks if ``default`` is defined, next it tries to call the function ``default_factory``, else it
    returns None.

    Args:
        field (dataclass.field): one field of a class with @dataclass decorator

    Returns:
        Any: the default field object.
    """
    if hasattr(field, 'default') and field.default is not MISSING:
        return field.default
    elif hasattr(field, 'default_factory') and field.default_factory is not MISSING:
        return field.default_factory()
    return None
