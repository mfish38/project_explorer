
import os
import shutil
import tempfile
from unittest import TestCase

import project_explorer.path_utils as path_utils

class TestVersionedName(TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.directory)
    
    def test_versioning(self):
        '''
        Tests that versions are added and incremented to make unique names.
        '''
        # Test that no version is added if the path doesn't exist.
        output = path_utils.versioned_name(self.directory, 'foo')
        expected_output = os.path.join(self.directory, 'foo')
        self.assertEqual(output, expected_output)
        
        # Test that a file causes the version to increment.
        with open(expected_output, 'w'):
            pass
        output = path_utils.versioned_name(self.directory, 'foo')
        expected_output = os.path.join(self.directory, 'foo_0')
        self.assertEqual(output, expected_output)

        # Test that a directory causes the version to increment.
        os.mkdir(os.path.join(self.directory, 'foo_0'))
        output = path_utils.versioned_name(self.directory, 'foo')
        expected_output = os.path.join(self.directory, 'foo_1')
        self.assertEqual(output, expected_output)
    
    def test_extensions(self):
        '''
        Test that the version number is added before file extensions.
        '''
        # Test version added before file extensions.
        with open(os.path.join(self.directory, 'foo.txt'), 'w'):
            pass
        output = path_utils.versioned_name(self.directory, 'foo.txt')
        expected_output = os.path.join(self.directory, 'foo_0.txt')
        self.assertEqual(output, expected_output)
        
        # Test version added before extension of files starting with "."
        with open(os.path.join(self.directory, '.foo.txt'), 'w'):
            pass
        output = path_utils.versioned_name(self.directory, '.foo.txt')
        expected_output = os.path.join(self.directory, '.foo_0.txt')
        self.assertEqual(output, expected_output)
        
        # Test version added at end of name of files starting with . if there is no extension.
        with open(os.path.join(self.directory, '.foo'), 'w'):
            pass
        output = path_utils.versioned_name(self.directory, '.foo')
        expected_output = os.path.join(self.directory, '.foo_0')
        self.assertEqual(output, expected_output)
    
    def test_at_end(self):
        '''
        Test that versions added at the very end of the name (regardless of the existence of an 
        extension) if the at_end option is specified.
        '''
        with open(os.path.join(self.directory, 'foo.txt'), 'w'):
            pass
        output = path_utils.versioned_name(self.directory, 'foo.txt', at_end=True)
        expected_output = os.path.join(self.directory, 'foo.txt_0')
        self.assertEqual(output, expected_output)
        
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
        test_path = path_utils.versioned_name('', 'foo')
        
        output = path_utils.valid_split(test_path)
        expected_output = ('', test_path)
        
        self.assertEqual(output, expected_output)
        
    def test_invalid_basename(self):
        '''
        Tests the behavior where the basename is invalid.
        '''
        dirname = os.path.dirname(__file__)
        test_path = path_utils.versioned_name(dirname, 'foo')
        
        output = path_utils.valid_split(test_path)
        expected_output = (dirname, os.path.basename(test_path))
        
        self.assertEqual(output, expected_output)
        
    def test_invalid_multiple_basenames(self):
        '''
        Tests the behavior where multiple components at the end of the path are invalid.
        '''
        dirname = os.path.dirname(__file__)
        dirname2 = path_utils.versioned_name(dirname, 'foo')
        test_path = path_utils.versioned_name(dirname2, 'goo')
        
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
         
class TestCompletePath(TestCase):
    def test_drive_letters(self):
        '''
        Tests drive letter completions.
        '''
        valid_drive_letter = 'C'
    
        invalid_drive_letter = None
        for drive_letter in (chr(x) for x in xrange(65, 91)):
            if not os.path.isdir(drive_letter + ':'):
                invalid_drive_letter = drive_letter
                break
        
        if invalid_drive_letter is None:
            self.fail('Could not find an invalid drive letter for testing purposes.')
        
        # Test a valid drive letter without a colon.
        output = path_utils.complete_path(valid_drive_letter)
        expected_output = [valid_drive_letter + ':']
        self.assertEqual(output, expected_output)
        
        # Test a valid drive letter with a colon.
        output = path_utils.complete_path(valid_drive_letter + ':')
        expected_output = [valid_drive_letter + ':']
        self.assertEqual(output, expected_output)
        
        # Test an invalid drive letter without a colon.
        output = path_utils.complete_path(invalid_drive_letter)
        expected_output = []
        self.assertEqual(output, expected_output)
        
        # Test an invalid drive letter with a colon.
        output = path_utils.complete_path(invalid_drive_letter + ':')
        expected_output = []
        self.assertEqual(output, expected_output)
       
    def test_completions(self):
        '''
        Test path completions.
        '''
        # Test 100% invalid path
        test_path = path_utils.versioned_name('', 'foo')
        output = path_utils.complete_path(test_path)
        expected_output = []
        self.assertEqual(output, expected_output)
        
        # Test an invalid path ending in a separator
        test_path = path_utils.versioned_name('', 'foo/')
        output = path_utils.complete_path(test_path)
        expected_output = []
        self.assertEqual(output, expected_output)
        
        test_directory = tempfile.mkdtemp()
        
        # Test valid unambiguous path
        test_path = os.path.join(test_directory, 'unambiguous_dir')
        os.mkdir(test_path)
        output = path_utils.complete_path(test_path)
        expected_output = [test_path]
        self.assertEqual(output, expected_output)        
        
        # Test valid unambiguous path ending in a separator
        test_path = os.path.join(test_directory, 'unambiguous_dir/')
        output = path_utils.complete_path(test_path)
        expected_output = [test_path]
        self.assertEqual(output, expected_output)
        
        # Test valid ambiguous path
        ambiguous_test_path_1 = os.path.join(test_directory, 'ambiguous_dir')
        os.mkdir(ambiguous_test_path_1)
        ambiguous_test_path_2 = os.path.join(test_directory, 'ambiguous_dir1')
        os.mkdir(ambiguous_test_path_2)
        output = path_utils.complete_path(ambiguous_test_path_1)
        expected_output = [ambiguous_test_path_1, ambiguous_test_path_2]
        self.assertEqual(set(output), set(expected_output))        
        
        # Test valid ambiguous path ending in a separator
        test_path_1 = os.path.join(test_directory, 'ambiguous_dir/')
        output = path_utils.complete_path(test_path_1)
        expected_output = [test_path_1]
        self.assertEqual(output, expected_output)
        
        # Test partially invalid path with no possible completions.
        test_path = os.path.join(test_directory, 'foo/goo/moo')
        output = path_utils.complete_path(test_path)
        expected_output = []
        self.assertEqual(output, expected_output)        
        
        # Test partially invalid path with possible completions.
        test_path = os.path.join(test_directory, 'ambig')
        output = path_utils.complete_path(test_path)
        expected_output = [ambiguous_test_path_1, ambiguous_test_path_2]
        self.assertEqual(set(output), set(expected_output))           
        
        # Test partially invalid path ending with a separator.
        test_path = os.path.join(test_directory, 'ambig/')
        output = path_utils.complete_path(test_path)
        expected_output = [ambiguous_test_path_1, ambiguous_test_path_2]
        self.assertEqual(set(output), set(expected_output))      
        
        shutil.rmtree(test_directory)
        