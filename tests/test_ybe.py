#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from importlib import resources

from ybe import read_ybe_string, write_ybe_string


class TestYbe(unittest.TestCase):

    def test_roundtrip_ybe_conversion(self):
        true_ybe_string = resources.read_text('ybe.data', 'example_database.ybe')
        roundtrip_converted = write_ybe_string(read_ybe_string(true_ybe_string), minimal=True)
        assert(true_ybe_string == roundtrip_converted)


if __name__ == '__main__':
    unittest.main()
