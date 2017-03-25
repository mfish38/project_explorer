'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

This module extends the json module.
'''

import re
import json

_COMMENT_REGEX = re.compile(r'//.*$', flags=re.MULTILINE)

def loads(json_text):
    '''
    Parses the JSON data in the given string.
    
    Extends json.loads() to:
        - Support comments.
    '''
    # Remove comments.
    json_text = _COMMENT_REGEX.sub('', json_text)
    
    # Parse the JSON.
    data = json.loads(json_text)
    
    return data

def load(file):
    '''
    Parses JSON from the given file object.
    
    Extends json.load() by using this module's loads() instead.
    '''
    json_text = file.read()
    
    return loads(json_text)
    
def load_file(path):
    '''
    Loads the json file at the given path.
    '''
    # Load the file.
    with open(path) as json_file:
        return load(json_file)
