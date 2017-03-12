'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

This module contains an icon provider for use with a QFileSystemModel, where the icons are specified
using a JSON settings file.

The format of the JSON file should be:

{
    "types" : {
        "Computer" : "<icon path>",
        "Desktop"  : "<icon path>",
        "Trashcan" : "<icon path>",
        "Network"  : "<icon path>",
        "Drive"    : "<icon path>",
        "Folder"   : "<icon path>",
        "File"     : "<icon path>"
    },
    
    "extensions" : {
        "txt" : "<icon path>",
        "jpg" : "<icon path>",
        <etc...>
    },
    
    "file_default" : "<icon path>"
}

Note that null can be given for any path to not specify an icon.
'''

import os
import json

from PySide.QtCore import QFileInfo
from PySide.QtGui import QFileIconProvider, QIcon

class JSONFileIconProvider(QFileIconProvider):
    '''
    Provide icons to a QFileSystemModel based on a JSON file.
    '''
    def __init__(self, path):
        '''
        path
            The path to the JSON file containing the paths to the icons to use.
        '''
        super(JSONFileIconProvider, self).__init__()
        
        with open(path) as json_file:
            settings = json.load(json_file)
        
        # Map JSON keys to QFileIconProvider file types.
        type_map = {
            'Computer' : QFileIconProvider.Computer,
            'Desktop'  : QFileIconProvider.Desktop,
            'Trashcan' : QFileIconProvider.Trashcan,
            'Network'  : QFileIconProvider.Network,
            'Drive'    : QFileIconProvider.Drive,
            'Folder'   : QFileIconProvider.Folder,
            'File'     : QFileIconProvider.File
        }
        
        # Get the type settings, normalize the paths, and map the types.
        type_paths = {
            type_map[type_name] :
                os.path.normcase(os.path.abspath(path)) if path is not None else None
            for type_name, path in settings['types'].iteritems()}
        
        # Get the extension settings, normalize the extensions, and normalize the paths.
        extension_paths = {
            extension.lower() :
                os.path.normcase(os.path.abspath(path)) if path is not None else None
            for extension, path in settings['extensions'].iteritems()}
        
        # Get the default file icon path and normalize it.
        file_default_path = settings['file_default']
        file_default_path = os.path.normcase(os.path.abspath(file_default_path)) \
            if file_default_path is not None else None
        
        # Get the distinct set of icon paths.
        icon_paths = \
            set(type_paths.values()) | set(extension_paths.values()) | set([file_default_path])
        
        # Load all the icons.
        icons = {
            path : QIcon(path) if path is not None else QIcon()
            for path in icon_paths}
        
        self._type_icons = {
            type : icons[path]
            for type, path in type_paths.iteritems()}
            
        self._extension_icons = {
            extension : icons[path]
            for extension, path in extension_paths.iteritems()}
        
        self._file_default_icon = icons[file_default_path]
    
    def icon(self, type_or_info):
        '''
        Returns the icon to use for the given file info or type.
        
        type_or_info
            Either a QFileIconProvider type enumeration, or a QFileInfo object.
        '''
        if isinstance(type_or_info, QFileInfo):
            # called icon(info)           
            if type_or_info.isFile():
                return self._extension_icons.get(
                    type_or_info.completeSuffix().lower(),
                    self._file_default_icon)
            
            return QIcon()
        else:
            # called icon(type)
            return self._type_icons.get(type_or_info, QIcon())
            