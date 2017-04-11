
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
    versioned_name = os.path.join(dirname, basename)
    if not os.path.exists(versioned_name):
        return versioned_name
        
    # Get a free version suffix.
    name, extension = os.path.splitext(basename)
    counter = 0
    while True:
        if not at_end:
            versioned_name = os.path.join(dirname, '{}_{}{}'.format(name, counter, extension))
        else:
            versioned_name = os.path.join(dirname, '{}_{}'.format(basename, counter))

        if not os.path.exists(versioned_name):
            break

        counter += 1
    
    return versioned_name

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

def complete_path(path):
    '''
    Completes the given path.
    
    Parameters:
        - path
            The path to complete.
            
    Returns:
        A list containing paths (not ending in path separators).
    '''
    path = path.strip()

    # Complete drive letters
    if len(path) == 1:
        path += ':'
        if os.path.isdir(path):
            return [path]
        else:
            return None
    elif len(path) == 2 and path[1] == ':':
        if os.path.isdir(path):
            return [path]
        else:
            return None

    # After this point try to complete where the basename is valid, but the tail isn't.

    head, tail = valid_split(path)

    # If there is no valid head, then we can't do anything.
    if head == '':
        return None

    # If there is no tail, then return the head. This handles "c:/path /" and "c:/path/ /"
    if tail == '':
        return [head]

    # Convert to lower case for case insensitivity.
    tail = tail.lower()

    # Get a list of the names in the directory.
    possibilities = (name.lower() for name in os.listdir(head))
    
    # Filter to the ones that the current tail is a prefix to, and convert to full paths.
    possibilities = (os.path.join(head, name) for name in possibilities if name.startswith(tail))
    
    return list(possibilities)
