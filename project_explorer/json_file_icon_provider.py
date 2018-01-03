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

    "filenames" : {
        "LICENSE" : "<icon path>",
        "README.md" : "<icon path>",
        <etc...>
    },

    "extensions" : {
        "txt" : "<icon path>",
        "jpg" : "<icon path>",
        <etc...>
    },

    "file_default" : "<icon path>"
}

Note that null can be given for any path to not specify an icon.

Comments of the // form are allowed.

Filenames settings override extension settings.
'''

import os

from qtpy.QtCore import QFileInfo
from qtpy.QtWidgets import QFileIconProvider
from qtpy.QtGui import QIcon

from . import extended_json

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

        settings = extended_json.load_file(path)

        # Icon cache for load_icon().
        icons = {}

        def load_icon(icon_specifier):
            '''
            Loads (with caching) the icon specified by the given specifier.
            '''
            if isinstance(icon_specifier, str):
                icon_specifier = os.path.normcase(os.path.abspath(icon_specifier))

                if icon_specifier not in icons:
                    icon = QIcon(icon_specifier)
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
        for type_name, icon_specifier in settings['types'].items():
            self._type_icons[type_map[type_name]] = load_icon(icon_specifier)

        self._filename_icons = {}
        for filename, icon_specifier in settings['filenames'].items():
            self._filename_icons[filename] = load_icon(icon_specifier)

        self._extension_icons = {}
        for extension, icon_specifier in settings['extensions'].items():
            self._extension_icons[extension] = load_icon(icon_specifier)

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
                try:
                    return self._filename_icons[type_or_info.fileName()]
                except KeyError:
                    pass

                try:
                    return self._extension_icons[type_or_info.suffix()]
                except KeyError:
                    pass

                return self._file_default_icon

            return QIcon()
        else:
            # called icon(type)
            return self._type_icons.get(type_or_info, QIcon())
