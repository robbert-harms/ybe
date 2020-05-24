__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe import read_ybe_file, write_ybe_file
from importlib import resources


# read the provided example Ybe.
with resources.path('ybe.data', 'example_database.ybe') as path:
    ybe_exam = read_ybe_file(path)

# change to your preference
output_dir = '/tmp/ybe_to_ybe/'

# write the ybe file, ignoring all non-set options (minimal=True).
write_ybe_file(ybe_exam, output_dir + 'example_database.ybe', minimal=True)

# write the ybe file with all options
write_ybe_file(ybe_exam, output_dir + 'example_database_full.ybe', minimal=False)
