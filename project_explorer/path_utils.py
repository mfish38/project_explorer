'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

Utilities for working with paths.
'''

import os

def versioned_name(dirname, basename, at_end=False):
    '''
    Creates a versioned name for use in the given directory.

    If the name already exists in the directory, a version number as added and incremented until an
    unused name is found. If the name does not exist, no version will be added.

    Parameters:
        - dirname
            The directory that the name will be in.

        - basename
            The intended name.

        - at_end
            If true, the version will be added at the end of the name instead of before any
            extension. This is for use with names that are intended to be for directories.

    Returns:
        The full path of the file name to use. Any version numbers will be added as an underscore
        followed by a number at the end of the path (immediately before the extension if there is
        one).
    '''
    generated_name = os.path.join(dirname, basename)
    if not os.path.exists(generated_name):
        return generated_name

    # Get a free version suffix.
    name, extension = os.path.splitext(basename)
    counter = 0
    while True:
        if not at_end:
            generated_name = os.path.join(dirname, '{}_{}{}'.format(name, counter, extension))
        else:
            generated_name = os.path.join(dirname, '{}_{}'.format(basename, counter))

        if not os.path.exists(generated_name):
            break

        counter += 1

    return generated_name

def isdir(path, ignore=None):
    '''
    Same as os.path.isdir, except returns false if the path is in the ignore set.

    Parameters:
        path
            The path to check.

        ignore
            A regex_tools.FastListMatcher object of paths to ignore. These paths will be treated as
            if they don't exist.
    '''
    if ignore is not None and ignore.fullmatch(path):
        return False

    return os.path.isdir(path)

def listdir(path, ignore=None):
    '''
    Same as os.listdir, except paths in the ignore set are filtered out.

    Parameters:
        path
            The directory to list

        ignore
            A regex_tools.FastListMatcher object of paths to ignore. These paths will be treated as
            if they don't exist.
    '''
    paths = os.listdir(path)

    if ignore is not None:
        paths = [item for item in paths if not ignore.fullmatch(item)]

    return paths

def valid_split(path, ignore=None):
    '''
    Splits the given path into a head and basename like os.path.split(), except that if the head is
    not a valid path, then head is repeatedly split into a new head and basename until it is.

    Parameters:
        path
            The path to split

        ignore
            A regex_tools.FastListMatcher object of paths to ignore. These paths will be treated as
            if they don't exist.

    Returns:
        (head, tail)
            - head
                The valid head. This will be an empty string if there is none.

            - tail
                The basename.
    '''
    head = path
    basename = ''

    while True:
        head, basename = os.path.split(head)

        # Handle no valid head case.
        if head == '':
            break

        # Check if a valid head has been found.
        if isdir(head + os.sep, ignore=ignore):
            break

    return head, basename

def normalize_path(path, separator='/'):
    '''
    Normalizes a path.

    Paths are normalized using os.path.normpath(), os.path.normcase(), and by replacing the path
    separator.

    Parameters:
        - path
            The path to normalize.

        - separator
            The path separator to normalize to. This should be / or \\.

    Returns:
        The normalized path.
    '''
    if separator == '/':
        return os.path.normcase(os.path.normpath(path)).replace('\\', '/')
    elif separator == '\\':
        return os.path.normcase(os.path.normpath(path)).replace('/', '\\')
    else:
        raise Exception('Invalid path separator.')

def complete_path(path, ignore=None):
    '''
    Completes the given path.

    If path is a single character that corresponds to a valid drive letter, then a colon is added
    and the path returned as the only possibility.

    If the path is a single character followed by a colon, then the path is returned unchanged as
    the only possibility.

    If the path ends in a / or \\, and is a valid directory path, then the path is returned
    unchanged as the only possibility.

    Otherwise, the path is split using valid_split() into a head and tail. Then a list of all paths
    in the head directory that are prefixed with the tail are returned as possible completions. This
    prefix check is done case insensitively.

    Parameters:
        - path
            The path to complete.

        - ignore
            A regex_tools.FastListMatcher object of paths to ignore. These paths will be treated as
            if they don't exist.

    Returns:
        A list containing paths (not ending in path separators).
    '''
    # Complete drive letters
    if len(path) == 1:
        path += ':'
        if isdir(path, ignore=ignore):
            return [path]
        else:
            return []
    elif len(path) == 2 and path[1] == ':':
        if isdir(path, ignore=ignore):
            return [path]
        else:
            return []
    elif path.endswith(('/', '\\')) and isdir(path, ignore=ignore):
        return [path]

    # After this point try to complete where the basename is valid, but the tail isn't.

    head, tail = valid_split(path, ignore=ignore)

    # If there is no valid head, then we can't do anything.
    if head == '':
        return []

    # Filter to the ones that the current tail is a prefix to, and convert to full paths.
    possibilities = [
        os.path.join(head, name)
        for name in listdir(head, ignore=ignore)
        if name.lower().startswith(tail.lower())
    ]

    return possibilities
