'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

This module extends the json module.
'''

import re
import json
import itertools

_COMMENT_REGEX = re.compile(r'//.*$', flags=re.MULTILINE)

class JSONSyntaxError(Exception):
    '''
    Extends JSONDecodeError to add context function for display to the user.
    '''
    def __init__(self, error):
        super().__init__()

        self.msg = error.msg
        self.doc = error.doc
        self.pos = error.pos
        self.lineno = error.lineno
        self.colno = error.colno

    def context(self, pre_context=5, post_context=5, column_indicator=True, line_numbers=True):
        doc_lines = self.doc.splitlines()

        first_line_number = max(self.lineno - pre_context - 1, 0)
        lines = doc_lines[first_line_number:self.lineno + post_context]

        if line_numbers:
            last_number_width = len(str(self.lineno + post_context))

            lines = [
                f'{str(number).ljust(last_number_width)}| {line}'
                for number, line in zip(itertools.count(first_line_number + 1), lines)
            ]

        if column_indicator:
            lines.insert(
                self.lineno - first_line_number,
                '-' * (self.colno - 1 + last_number_width + 2) + '^'
            )

        return '\n'.join(lines)

def loads(json_text):
    '''
    Parses the JSON data in the given string.

    Extends json.loads() to:
        - Support line comments of the form "//"
        - Better syntax errors
    '''
    # Note that during comment removal lines are not removed in order to preserve syntax error line
    # numbers aligning with the original file.

    # Remove line comments.
    json_text = _COMMENT_REGEX.sub('', json_text)

    # Parse the JSON.
    try:
        data = json.loads(json_text)
    except json.decoder.JSONDecodeError as error:
        raise JSONSyntaxError(error)

    return data

def load(file_):
    '''
    Parses JSON from the given file object.

    See loads() for extensions to JSON.
    '''
    json_text = file_.read()

    return loads(json_text)

def load_file(path):
    '''
    Loads the json file at the given path.

    See loads() for extensions to JSON.
    '''
    # Load the file.
    with open(path) as json_file:
        return load(json_file)
