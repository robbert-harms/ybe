__author__ = 'Robbert Harms'
__date__ = '2020-07-07'
__email__ = 'robbert@xkls.nl'
__license__ = "GPL v3"
__maintainer__ = "Robbert Harms"

import logging
import logging.config as logging_config

from ybe.configuration import get_logging_configuration_dict

try:
    logging_config.dictConfig(get_logging_configuration_dict())
except ValueError as e:
    print('Logging disabled, error message: {}'.format(e))

from ybe.__version__ import VERSION, VERSION_STATUS, __version__


'''
#todo
- raise exception when a multiple choice question does not have an answer marked as 'correct'
- gui?
- query functions
- yaml reader and writer
- write down format descriptions
    - i.e. which kind of values are allows and which are not
- integrate yamllint as tester
'''
