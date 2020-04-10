__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from pprint import pprint
import ybe
import yaml


with open("../ybe/data/example_database.ybe", "r") as stream:
    # gen = linter.run(stream, conf)
    try:
        d = list(yaml.safe_load_all(stream))
    except yaml.parser.ParserError as error:
        print(error)
# errors = list(gen)
# pprint(errors)
# if errors:
    # raise ImproperlyConfigured

# with open("../ybe/data/example_database.ybe", "r") as stream:
#     d = list(yaml.safe_load_all(stream))
# pprint(d)
