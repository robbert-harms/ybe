"""Contains the runtime configuration of YBE.

This consists of two parts, functions to get the current runtime settings and configuration actions to update these
settings. To set a new configuration, create a new :py:class:`ConfigAction` and use this within a context environment
using :py:func:`config_context`. Example:

.. code-block:: python

    from ybe.configuration import YamlStringAction, config_context

    config = '''
        ...
    '''
    with ybe.config_context(YamlStringAction(config)):
        ...
"""
import os
from copy import deepcopy

import yaml
from contextlib import contextmanager
from pkg_resources import resource_stream

from ybe.__version__ import __version__

__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

""" The current configuration """
_config = {}


def get_config_option(option_name):
    """Get the current configuration option for the given option name.

    Args:
        option_name (list of str or str): the name of the option, or a path to the option.

    Returns:
        object: the raw configuration value defined for that option
    """
    if isinstance(option_name, str):
        return _config[option_name]
    else:
        config = _config
        for el in option_name[:-1]:
            config = config[el]
        return config[option_name[-1]]


def get_logging_configuration_dict():
    """Get the configuration dictionary for the logging.dictConfig().

    ybe uses a few special logging configuration options to log to the files and GUI's. These options are defined
    using a configuration dictionary that this function returns.

    Returns:
        dict: the configuration dict for use with dictConfig of the Python logging modules
    """
    return _config['logging']['info_dict']


def set_config_option(option_name, value):
    """Set the current configuration option for the given option name.

    This will overwrite the current configuration for that option with the given value. Be careful, this will change
    the global configuration value.

    Provided values should be objects and not YAML strings. For updating the configuration with YAML strings, please use
    the function :func:`load_from_yaml`.

    Args:
        option_name (list of str or str): the name of the option, or a path to the option.
        value : the object to set for that option

    Returns:
        object: the raw configuration value defined for that option
    """
    if isinstance(option_name, str):
        _config[option_name] = value
    else:
        config = _config
        for el in option_name[:-1]:
            config = config[el]
        config[option_name[-1]] = value


def get_config_dir():
    """Get the location of the components.

    Return:
        str: the path to the components
    """
    return os.path.join(os.path.expanduser("~"), '.ybe', __version__)


def _config_insert(keys, value):
    """Insert the given value in the given key.

    This will create all layers of the dictionary if needed.

    Args:
        keys (list of str): the position of the input value
        value : the value to put at the position of the key.
    """
    config = _config
    for key in keys[:-1]:
        if key not in config:
            config[key] = {}
        config = config[key]

    config[keys[-1]] = value


def ensure_exists(keys):
    """Ensure the given layer of keys exists.

    Args:
        keys (list of str): the positions to ensure exist
    """
    config = _config
    for key in keys:
        if key not in config:
            config[key] = {}
        config = config[key]


def load_builtin():
    """Load the config file from the skeleton in ybe/data/ybe.conf"""
    with resource_stream('ybe', 'data/ybe.conf') as f:
        load_from_yaml(f.read())


def load_user_home():
    """Load the config file from the user home directory"""
    config_file = os.path.join(get_config_dir(), 'ybe.conf')
    if os.path.isfile(config_file):
        with open(config_file) as f:
            load_from_yaml(f.read())
    else:
        raise IOError('Config file could not be loaded.')


def load_specific(file_name):
    """Can be called by the application to use the config from a specific file.

    This assumes that the given file contains YAML content, that is, we want to process it
    with the function load_from_yaml().

    Please note that the last configuration loaded overwrites the values of the previously loaded config files.

    Also, please note that this will change the global configuration, i.e. this is a persistent change. If you do not
    want a persistent state change, consider using :func:`~ybe.configuration.config_context` instead.

    Args:
        file_name (str): The name of the file to use.
    """
    with open(file_name) as f:
        load_from_yaml(f.read())


def load_from_yaml(yaml_str):
    """Can be called to use configuration options from a YAML string.

    This will update the current configuration with the new options.

    Please note that this will change the global configuration, i.e. this is a persistent change. If you do not
    want a persistent state change, consider using :func:`~ybe.configuration.config_context` instead.

    Args:
        yaml_str (str): The string containing the YAML config to parse.
    """
    config_dict = yaml.safe_load(yaml_str) or {}
    load_from_dict(config_dict)


def load_from_dict(config_dict):
    """Load configuration options from a given dictionary.

    Please note that this will change the global configuration, i.e. this is a persistent change. If you do not
    want a persistent state change, consider using :func:`~ybe.configuration.config_context` instead.

    Args:
        config_dict (dict): the dictionary from which to use the configurations
    """
    for key, value in config_dict.items():
        loader = get_section_loader(key)
        loader.load(value)


def update_write_config(config_file, update_dict):
    """Update a given configuration file with updated values.

    If the configuration file does not exist, a new one is created.

    Args:
        config_file (str): the location of the config file to update
        update_dict (dict): the items to update in the config file
    """
    if not os.path.exists(config_file):
        with open(config_file, 'a'):
            pass

    with open(config_file, 'r') as f:
        config_dict = yaml.safe_load(f.read()) or {}

    for key, value in update_dict.items():
        loader = get_section_loader(key)
        loader.update(config_dict, value)

    with open(config_file, 'w') as f:
        yaml.safe_dump(config_dict, f)


class ConfigSectionLoader:

    def load(self, value):
        """Load the given configuration value into the current configuration.

        Args:
            value: the value to use in the configuration
        """

    def update(self, config_dict, updates):
        """Update the given configuration dictionary with the values in the given updates dict.

        This enables automating updating a configuration file. Updates are written in place.

        Args:
            config_dict (dict): the current configuration dict
            updates (dict): the updated values to add to the given config dict.
        """


class LoggingLoader(ConfigSectionLoader):
    """Loader for the top level key logging. """

    def load(self, value):
        ensure_exists(['logging', 'info_dict'])
        if 'info_dict' in value:
            self._load_info_dict(value['info_dict'])

    def _load_info_dict(self, info_dict):
        for item in ['version', 'disable_existing_loggers', 'formatters', 'handlers', 'loggers', 'root']:
            if item in info_dict:
                _config_insert(['logging', 'info_dict', item], info_dict[item])


def get_section_loader(section):
    """Get the section loader to use for the given top level section.

    Args:
        section (str): the section key we want to get the loader for

    Returns:
        ConfigSectionLoader: the config section loader for this top level section of the configuration.
    """
    if section == 'logging':
        return LoggingLoader()

    raise ValueError('Could not find a suitable configuration loader for the section {}.'.format(section))


@contextmanager
def config_context(config_action):
    """Creates a temporary configuration context with the given config action.

    This will temporarily alter the given configuration keys to the given values. After the context is executed
    the configuration will revert to the original settings.

    Example usage:

    .. code-block:: python

        config = '''
            ...
        '''
        with ybe.config_context(ybe.configuration.YamlStringAction(config)):
            ...

    or, equivalently::

        config = '''
            ...
        '''
        with ybe.config_context(config):
            ...

    This loads the configuration from a YAML string and uses that configuration as the context.

    Args:
        config_action (ybe.configuration.ConfigAction or str): the configuration action to apply.
            If a string is given we will use it using the YamlStringAction config action.
    """
    if isinstance(config_action, str):
        config_action = YamlStringAction(config_action)

    config_action.apply()
    yield
    config_action.unapply()


class ConfigAction:

    def __init__(self):
        """Defines a configuration action for the use in a configuration context.

        This should define an apply and an unapply function that sets and unsets the given configuration options.

        The applying action needs to remember the state before applying the action.
        """

    def apply(self):
        """Apply the current action to the current runtime configuration."""

    def unapply(self):
        """Reset the current configuration to the previous state."""


class VoidConfigAction(ConfigAction):
    """Does nothing. Meant as a container to not have to check for None's everywhere."""

    def apply(self):
        pass

    def unapply(self):
        pass


class SimpleConfigAction(ConfigAction):

    def __init__(self):
        """Defines a default implementation of a configuration action.

        This simple config implements a default apply() method that saves the current state and a default
        unapply() that restores the previous state.

        It is easiest to implement _apply() for extra actions.
        """
        super().__init__()
        self._old_config = {}

    def apply(self):
        """Apply the current action to the current runtime configuration."""
        self._old_config = deepcopy(_config)
        self._apply()

    def unapply(self):
        """Reset the current configuration to the previous state."""
        global _config
        _config = self._old_config

    def _apply(self):
        """Implement this function add apply() logic after this class saves the current config."""


class YamlStringAction(SimpleConfigAction):

    def __init__(self, yaml_str):
        super().__init__()
        self._yaml_str = yaml_str

    def _apply(self):
        load_from_yaml(self._yaml_str)


"""Load the default configuration, and if possible, the users configuration."""
load_builtin()
try:
    load_user_home()
except IOError:
    pass
