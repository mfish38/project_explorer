
import os
from unittest import TestCase

import project_explorer.path_utils as path_utils

class TestValidSplit(TestCase):
    def test_valid_file_path(self):
        '''
        Tests behavior with a 100% valid path to a file.
        '''
        output = path_utils.valid_split(__file__)
        expected_output = os.path.split(__file__)
        
        self.assertEqual(output, expected_output)

    def test_valid_dir_path(self):
        '''
        Tests behavior with a 100% valid path to a directory.
        '''
        test_path = os.path.dirname(__file__)
        output = path_utils.valid_split(test_path)
        expected_output = os.path.split(test_path)
        
        self.assertEqual(output, expected_output)
    
    def test_invalid_path(self):
        '''
        Tests behavior with a 100% invalid path.
        '''
        test_path = path_utils.version_directory_name('', 'foo')
        
        output = path_utils.valid_split(test_path)
        expected_output = ('', test_path)
        
        self.assertEqual(output, expected_output)
        
    def test_invalid_basename(self):
        '''
        Tests the behavior where the basename is invalid.
        '''
        dirname = os.path.dirname(__file__)
        test_path = path_utils.version_directory_name(dirname, 'foo')
        
        output = path_utils.valid_split(test_path)
        expected_output = (dirname, os.path.basename(test_path))
        
        self.assertEqual(output, expected_output)
        
    def test_invalid_multiple_basenames(self):
        '''
        Tests the behavior where multiple components at the end of the path are invalid.
        '''
        dirname = os.path.dirname(__file__)
        dirname2 = path_utils.version_directory_name(dirname, 'foo')
        test_path = path_utils.version_directory_name(dirname2, 'goo')
        
        output = path_utils.valid_split(test_path)
        expected_output = (dirname, os.path.basename(dirname2))
        
        self.assertEqual(output, expected_output)

class TestNormalizePath(TestCase):
    def test_normpath(self):
        '''
        Tests that os.path.normpath() works as expected.
        '''
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
        '''
        Tests the case normalization.
        '''
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
        '''
        Tests the separator normalization.
        '''
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
        
        with self.assertRaises(Exception):
            path_utils.normalize_path('c:/foo/goo', separator='X')
            