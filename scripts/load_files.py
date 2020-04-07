__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pprint import pprint

import ybe
import yaml

questions = [
    {'question': 'Hoe lief is Robbert?',
     'type': 'multiple_choice',
     'answers': ['Aardig', 'Lief', 'Superlief'],
     'correct_answer': 2
     },

    {'question': 'Wat zou je meer willen zien bij Robbert?',
     'type': 'open',
     'length': '1/2 page'
     }
]

# print(yaml.dump_all(questions, default_flow_style=False))

with open("../ybe/data/example_database.yaml", "r") as stream:
    d = list(yaml.safe_load_all(stream))
pprint(d)
exit()


pprint(list(yaml.load_all('''
type: multiple_choice
data:
    question: Hoe lief is Robbert?
    answers:
        - answer:
            text: Aardig
            correct: True
            points: 1
        - answer:
            text: Lief
        - answer:
            text: Superlief
---
data:
    question: Hoe lief is Robbert?
    answers:
        - answer: Aardig
          correct: True
          points: 1
        - answer: Lief
        - answer Superlief
---
data:
    question: Hoe lief is Robbert?
    answers:
        - "Aardig.":
            correct: True
            points: 1
        - Hij kan ook lief zijn.
        - Hij is soms super-duper lief.
''', Loader=yaml.SafeLoader)))

''
# with open("../ybe/data/example_database.yaml", "r") as stream:
#     d = list(yaml.safe_load_all(stream))

# d.append(d[-1])
# print(d)
#
