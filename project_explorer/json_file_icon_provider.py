'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

This module contains an icon provider for use with a QFileSystemModel, where the icons are specified
using a JSON settings file.

The format of the JSON file should be:

{
    "fonts_to_load" : [
        "<font path>"
    ],
    
    "types" : {
        "Computer" : ["<FontFamily>", "<icon text>"],
        "Desktop"  : "<icon path>",
        "Trashcan" : "<icon path>",
        "Network"  : "<icon path>",
        "Drive"    : "<icon path>",
        "Folder"   : "<icon path>",
        "File"     : "<icon path>"
    },
    
    "patterns" : {
        "*.txt" : ["<FontFamily>", "<icon text>"],
        "*.jpg" : "<icon path>",
        <etc...>
    },
    
    "file_default" : "<icon path>"
}

Note that null can be given for any path to not specify an icon. In all cases, either an icon path
can be given, or a font family and icon text. All font families must be system fonts, or in a font
loaded with "fonts_to_load".
'''

import os
import json
from fnmatch import fnmatch

from PySide.QtCore import QFileInfo
from PySide.QtGui import QFileIconProvider, QIcon, QFontDatabase, QFont

from font_icon import FontIcon

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
        
        # Get the font families to load.
        fonts_to_load = settings['fonts_to_load']
        
        # Load the fonts.
        for font_path in fonts_to_load:
            QFontDatabase.addApplicationFont(font_path)
        
        # Icon cache for load_icon().
        icons = {}
        
        def load_icon(icon_specifier):
            '''
            Loads (with caching) the icon specified by the given specifier.
            '''
            if isinstance(icon_specifier, basestring):
                icon_specifier = os.path.normcase(os.path.abspath(icon_specifier))
                
                if icon_specifier not in icons:
                    icon = QIcon(icon_specifier)
                    icons[icon_specifier] = icon
                else:
                    icon = icons[icon_specifier]
            elif isinstance(icon_specifier, list):
                icon_specifier = tuple(icon_specifier)
                
                if icon_specifier not in icons:
                    font_family, icon_text = icon_specifier
                    icon = FontIcon(QFont(font_family), icon_text)
                    icons[icon_specifier] = icon
                else:
                    icon = icons[icon_specifier]
            elif icon_specifier is None:
                if icon_specifier not in icons:
                    icon = QIcon()
                    icons[icon_specifier] = icon
                else:
                    icon = icons[icon_specifier]
            else:
                raise Exception('Unsuported icon specifier: {}.'.format(icon_specifier))
             
            return icon
        
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
        
        self._type_icons = {}
        for type_name, icon_specifier in settings['types'].iteritems():
            self._type_icons[type_map[type_name]] = load_icon(icon_specifier)        
            
        self._pattern_icons = {}
        for pattern, icon_specifier in settings['patterns'].iteritems():
            self._pattern_icons[pattern] = load_icon(icon_specifier)
        
        self._file_default_icon = load_icon(settings['file_default'])
    
    def icon(self, type_or_info):
        '''
        Returns the icon to use for the given file info or type.
        
        type_or_info
            Either a QFileIconProvider type enumeration, or a QFileInfo object.
        '''
        if isinstance(type_or_info, QFileInfo):
            # called icon(info)           
            if type_or_info.isFile():
                for pattern, icon in self._pattern_icons.iteritems():
                    if fnmatch(type_or_info.fileName(), pattern):
                        return icon
                    
                return self._file_default_icon

            return QIcon()
        else:
            # called icon(type)
            return self._type_icons.get(type_or_info, QIcon())
            