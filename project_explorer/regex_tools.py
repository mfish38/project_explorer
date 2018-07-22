'''
Copyright (c) 2018 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

This module contains tools for use with regular expressions.
'''

import re

class FastListMatcher:
    '''
    This class enables faster matching using a large list of regular expressions, where it is not a
    requirement to know which expression matched.

    The implementation relies on the fact that most expressions operator operate on O(N) where N is
    the length of the string being matched. This means that for a list of M expressions, the worst
    case is O(N * M). This can be avoided by compiling the expressions into a single expression,
    reducing the complexity.
    '''
    def __init__(self, expressions, flags=0):
        '''
        # Parameters
        ## expressions
            List of expression strings.

        ## flags
            Flags for re.compile.
        '''
        expressions = [f'(?:{expression})' for expression in expressions]
        expression = f'(?:{"|".join(expressions)})'

        self._regex = re.compile(expression, flags=flags)

    def search(self, string):
        '''
        Find match anywhere in the string
        '''
        return self._regex.search(string)

    def match(self, string):
        '''
        Find match only at start of the string.
        '''
        return self._regex.match(string)

    def fullmatch(self, string):
        '''
        Check if the entire string is matches.
        '''
        return self._regex.fullmatch(string)
