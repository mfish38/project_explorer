'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

A line edit for editing paths.
'''

import os
import itertools

from PySide.QtCore import (
    Signal,
    Qt,
    QEvent,
)

from PySide.QtGui import QLineEdit

import path_utils

_PATH_SEPARATOR = '/'

class PathEdit(QLineEdit):
    '''
    A line edit for editing paths.
    '''
    new_path = Signal(str)

    def __init__(self, parent=None):
        super(PathEdit, self).__init__(parent)

        self._tab_suggestions = None
        self._previous_text = None

        self.textEdited.connect(self._handle_edit)

    def _tab_complete(self):
        '''
        Implements tab completion.
        '''
        text = self.text()

        if self._tab_suggestions is None:
            possibilities = path_utils.complete_path(text)

            # Normalize the possibilities and filter to directories.
            possibilities = [
                path_utils.normalize_path(path, _PATH_SEPARATOR)
                for path in possibilities
                if os.path.isdir(path)]

            if len(possibilities) == 0:
                return
            elif len(possibilities) == 1:
                path = possibilities[0]
                if not path.endswith(_PATH_SEPARATOR):
                    path += _PATH_SEPARATOR
                self.setText(path)
                self.new_path.emit(path)
                return
            else:
                # Create a loop of suggestions.
                self._tab_suggestions = itertools.cycle(possibilities)

                # Advance the suggestions by one if the current text is the first suggestion.
                if text == possibilities[0]:
                    next(self._tab_suggestions)

        # Cycle through the possibilities.
        try:
            self.setText(next(self._tab_suggestions))
        except StopIteration:
            # There were no suggestions
            pass

    def setText(self, text):
        '''
        Set the text of the path edit.
        '''
        self._previous_text = text
        super(PathEdit, self).setText(text)

    def _handle_edit(self, text):
        '''
        This handles user edits, and if the input path is valid emits new_path.
        '''
        previous_text = self._previous_text

        if text == '':
            # If the text is blank, then go to 'This PC'
            self.new_path.emit('This PC')
            return
        elif (
            (
                previous_text is not None
                and text == previous_text[:-1]
                and previous_text.endswith(('/', '\\'))
            )
            or os.path.isfile(text)
        ):
            # If the path separator has been deleted, or the text is a file path, then go to the
            # dirname.

            path = os.path.dirname(text)
            if path == text:
                # The dirname did nothing so the text is a drive. Go to 'This PC'
                self.setText('')
                self.new_path.emit('This PC')
                return

            path = path_utils.normalize_path(path, _PATH_SEPARATOR)
            if not path.endswith(_PATH_SEPARATOR):
                path += _PATH_SEPARATOR
            self.setText(path)
            self.new_path.emit(path)
            return

        possibilities = path_utils.complete_path(text)

        # Normalize the possibilities and filter to directories.
        possibilities = [
            path_utils.normalize_path(path, _PATH_SEPARATOR)
            for path in possibilities
            if os.path.isdir(path)]

        if len(possibilities) == 0:
            # Do nothing if the path has no completions.
            return
        elif len(possibilities) > 1:
            # Do nothing if there is more than one completion.
            return

        possibility = possibilities[0]
        path = path_utils.normalize_path(text, _PATH_SEPARATOR)

        # Add a colon for drive letters.
        if len(path) == 1:
            path += ':'

        # Go to the path if it is its own completion.
        if path == possibility:
            if not path.endswith(_PATH_SEPARATOR):
                path += _PATH_SEPARATOR
            self.setText(path)
            self.new_path.emit(path)
            return

    def update(self, path):
        '''
        Updates the path edit to show a new path.
        '''
        if path != '':
            path = path_utils.normalize_path(path, _PATH_SEPARATOR)
            if not path.endswith(_PATH_SEPARATOR):
                path += _PATH_SEPARATOR

        self.setText(path)

    def event(self, event):
        '''
        Detects tab presses to trigger tab completion.
        '''
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                self._tab_complete()

                return True
            else:
                # The user has hit a key other than tab, so clear the tab suggestions.
                self._tab_suggestions = None

        return super(PathEdit, self).event(event)
