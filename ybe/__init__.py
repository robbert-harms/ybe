__author__ = 'Robbert Harms'
__date__ = '2020-07-07'
__email__ = 'robbert@xkls.nl'
__license__ = "GPL v3"
__maintainer__ = "Robbert Harms"

import logging.config as logging_config

from ybe.configuration import get_logging_configuration_dict

try:
    logging_config.dictConfig(get_logging_configuration_dict())
except ValueError as e:
    print('Logging disabled, error message: {}'.format(e))

from ybe.__version__ import VERSION, VERSION_STATUS, __version__
from ybe.lib.ybe_writer import write_ybe_string, write_ybe_file
from ybe.lib.ybe_reader import read_ybe_string, read_ybe_file
from ybe.lib.qti_reader import read_qti_dir, read_qti_zip
from ybe.lib.qti_writer import write_qti_dir, write_qti_zip
from ybe.lib.utils import markdown_to_latex, html_to_latex
from ybe.lib.latex_writer import write_latex_file
