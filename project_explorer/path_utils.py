
import os

def valid_split(path):
    '''
    Splits the given path into a valid head, and the basename immediately following it.  The
    remainder of the path after that basename is not returned.
    '''
    head = path
    basename = ''

    while True:
        head, basename = os.path.split(head)

        # Check if a valid head has been found.
        if os.path.isdir(head):
            break

        # Handle no valid head case.
        if head == '':
            break

    return head.strip(), basename.strip()

def normalize_path(path, separator='/'):
    '''
    Normalizes a path.

    Paths are normalized using os.path.normpath(), os.path.normcase(), and by replacing the path
    separator.
    
    Parameters:
        - path
            The path to normalize.
            
        - separator
            The path separator to normalize to. This should be / or \.
            
    Returns:
        The normalized path.
    '''
    if separator == '/':
        return os.path.normcase(os.path.normpath(path)).replace('\\', '/')
    elif separator == '\\':
        return os.path.normcase(os.path.normpath(path)).replace('/', '\\') 
    else:
        raise Exception('Invalid path separator.')

def complete_path(path, separator='/'):
    '''
    Completes the given path.
    
    Parameters:
        - path
            The path to complete.
            
        - separator
            The path separator to normalize to. This should be / or \.
            
    Returns:
        - None if there are no available completions (the path is invalid).
        - A list containing paths (not ending in path separators) if there are available 
        completions. The paths will be normalized using normalize_path().
    '''
    path = path.strip()

    # Complete drive letters
    if len(path) == 1:
        path += ':'
        if os.path.isdir(path):
            return [normalize_path(path, separator)]
        else:
            return None
    elif len(path) == 2 and path[1] == ':':
        if os.path.isdir(path):
            return [normalize_path(path, separator)]
        else:
            return None

    # After this point try to tab complete where the basename is valid, but the tail isn't.

    head, tail = valid_split(path)

    # If there is no valid head, then we can't do anything.
    if head == '':
        return None

    # If there is no tail, then change to the head. This handles "c:/path /" and "c:/path/ /"
    if tail == '':
        return [normalize_path(head, separator)]

    # Convert to lower case for case insensitivity.
    tail = tail.lower()

    # Get the list of directory names that start with the tail.
    possibilities = [name.lower() for name in os.listdir(head)]
    possibilities = [
        name
        for name in possibilities
        if name.startswith(tail) and os.path.isdir(os.path.join(head, name))
    ]

    if len(possibilities) == 0:
        return None
    elif len(possibilities) == 1:
        path = separator.join([head, possibilities[0]])
        return [normalize_path(path, separator)]
    else:
        return [
            normalize_path(separator.join([head, possibility]), separator)
            for possibility in possibilities
        ]
