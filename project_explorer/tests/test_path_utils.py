
from unittest import TestCase

import project_explorer.path_utils as path_utils

class Test_normalize_path(TestCase):
    def test_normpath(self):
        cases = (
            ('c:/foo'       , 'c:/foo'),
            ('c:/foo/'      , 'c:/foo'),
            ('c:/foo/./goo' , 'c:/foo/goo'),
            ('c:/foo/../goo', 'c:/goo'),
            ('c:/foo//goo'  , 'c:/foo/goo'),
        )
        
        for input, expected_output in cases:
            output = path_utils.normalize_path(input, separator='/')
            self.assertEqual(output, expected_output)
    
    def test_case(self):
        cases = (
            ('c:/foo'),
            ('c:/Foo'),
            ('C:/foo'),
        )
        
        for input in cases:
            expected_output = input.lower()
            output = path_utils.normalize_path(input, separator='/')
            self.assertEqual(output, expected_output)
    
    def test_separator(self):
        inputs = (
            (r'c:/foo/goo'),
            (r'c:\foo\goo'),
        )
        
        expected_output = 'c:/foo/goo'
        for input in inputs:
            output = path_utils.normalize_path(input, separator='/')
            self.assertEqual(output, expected_output)     
            
        expected_output = r'c:\foo\goo'
        for input in inputs:
            output = path_utils.normalize_path(input, separator='\\')
            self.assertEqual(output, expected_output)
            