'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

Tree based file system browser widget for browsing the file tree from a movable root.
'''

# pylint: disable=C0103

import os
import re
import datetime
import shutil
import string
import subprocess
from pathlib import Path

import ntfsutils.junction

from qtpy.QtCore import (
    Signal,
    Qt,
    QDir,
    QUrl,
    QMimeData,
    QSortFilterProxyModel,
    QEvent,
)

from qtpy.QtWidgets import (
    QFrame,
    QApplication,
    QAction,
    QHBoxLayout,
    QVBoxLayout,
    QFileSystemModel,
    QTreeView,
    QToolBar,
    QMessageBox,
    QMenu,
)

from . import path_utils
from . import regex_tools
from .json_file_icon_provider import JSONFileIconProvider
from .path_edit import PathEdit

class ChDir:
    '''
    Context manager for changing the current working directory and restoring it.
    '''
    def __init__(self, path):
        self.path = path
        self.previous_path = None
        
    def __enter__(self):
        self.previous_path = os.getcwd()
        os.chdir(self.path)
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.previous_path)

class FileSystemProxyModel(QSortFilterProxyModel):
    '''
    Sorts the source QFileSystemModel.
    '''
    def __init__(self):
        super(FileSystemProxyModel, self).__init__()

        self.setDynamicSortFilter(True)

        self._regex_filters = None

    def set_regex_filters(self, filters):
        '''
        Sets the model to filter out files.

        filters:
            A FastListMatcher that matches the file paths to hide. None to disable.
        '''
        self._regex_filters = filters

        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        '''
        Applies the filtering.
        '''
        model = self.sourceModel()

        # Get the row info.
        index = model.index(source_row, 0, source_parent)
        path = model.filePath(index)

        # Filter out junctions as QFileSystemModel does not work well with them.
        if ntfsutils.junction.isjunction(path):
            return False

        # Apply regex filtering.
        if self._regex_filters is not None:
            return not self._regex_filters.fullmatch(path)

        return True

    def isDir(self, index):
        '''
        Pass through to QFileSystemModel
        '''
        return self.sourceModel().isDir(self.mapToSource(index))

    def path_index(self, path):
        '''
        Pass through to QFileSystemModel
        '''
        return self.mapFromSource(self.sourceModel().index(path))

    def filePath(self, index):
        '''
        Pass through to QFileSystemModel
        '''
        return self.sourceModel().filePath(self.mapToSource(index))

    def remove(self, index):
        '''
        Pass through to QFileSystemModel
        '''
        return self.sourceModel().remove(self.mapToSource(index))

    def fileName(self, index):
        '''
        Pass through to QFileSystemModel
        '''
        return self.sourceModel().fileName(self.mapToSource(index))

    def lessThan(self, left, right):
        '''
        Sorts directories before files, then sorts lexicographically.
        '''
        model = self.sourceModel()

        # Sort directories above files, regardless of sort order.
        if model.isDir(left):
            if not model.isDir(right):
                return True if self.sortOrder() == Qt.AscendingOrder else False
        elif model.isDir(right):
            return False if self.sortOrder() == Qt.AscendingOrder else True

        # Sort items of the same type (file or directory) lexicographically.
        if model.filePath(left).lower() < model.filePath(right).lower():
            return True
        else:
            return False

class SubprocessAction(QAction):
    '''
    An action that executes a command when triggered.
    '''
    def __init__(self, *args, **kwargs):
        super(SubprocessAction, self).__init__(*args, **kwargs)

        self.command = None

        self.triggered.connect(self.execute)

    def execute(self):
        '''
        Executes the actions command.
        '''
        subprocess.Popen(self.command, shell=True)

class RootWidget(QFrame):
    '''
    This widget provides a view of a project root.
    '''
    close_request = Signal()
    open_request = Signal(str)

    def __init__(self, settings, path=None):
        super(RootWidget, self).__init__()

        # --- setup the file system model ---
        model = QFileSystemModel()
        model.setRootPath('This PC')
        model.setReadOnly(False)
        model.setIconProvider(
            JSONFileIconProvider('file_view_icons.json')
        )
        model.setFilter(
            QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Hidden
        )

        self._model = FileSystemProxyModel()
        self._model.setSourceModel(model)

        # --- setup the tree view ---
        self._view = QTreeView()
        self._view.setModel(self._model)
        self._view.setSelectionMode(QTreeView.ExtendedSelection)
        self._view.activated.connect(self._handle_activated_index)
        self._view.setSortingEnabled(True)
        self._view.setHeaderHidden(True)
        self._view.setExpandsOnDoubleClick(False)
        self._view.sortByColumn(0, Qt.AscendingOrder)

        # Setup drag and drop.
        self._view.setDragDropMode(QTreeView.DragDrop)
        self._view.setDefaultDropAction(Qt.MoveAction)

        # Setup the columns that show.
        self._view.hideColumn(1)
        self._view.hideColumn(2)
        self._view.hideColumn(3)

        # Note that the double click trigger cannot be in this list, otherwise it flashes in edit
        # mode before opening the file
        self._view.setEditTriggers(
            QTreeView.SelectedClicked | QTreeView.EditKeyPressed)

        # setup the context menu
        self._view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._view.customContextMenuRequested.connect(self._context_menu)

        # Unselect items on collapse.
        self._view.collapsed.connect(self._view.clearSelection)

        # --- setup the current root path label ---
        self._root_edit = PathEdit()
        self._root_edit.new_path.connect(self._set_root_path)

        # --- setup the tool bar ---
        tool_bar = QToolBar()

        new_file_action = QAction('New File', self)
        tool_bar.addAction(new_file_action)
        tool_bar.widgetForAction(new_file_action).setObjectName('new_file')
        new_file_action.triggered.connect(self._create_file)

        new_directory_action = QAction('New Directory', self)
        tool_bar.addAction(new_directory_action)
        tool_bar.widgetForAction(new_directory_action).setObjectName('new_directory')
        new_directory_action.triggered.connect(self._create_directory)

        close_action = QAction('Close', self)
        tool_bar.addAction(close_action)
        self._close_widget = tool_bar.widgetForAction(close_action)
        self._close_widget.setObjectName('close_root')
        close_action.triggered.connect(self.close_request.emit)

        # --- setup the layout ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        path_layout.addWidget(self._root_edit)
        path_layout.addWidget(tool_bar)
        main_layout.addLayout(path_layout)

        main_layout.addWidget(self._view)

        self.setLayout(main_layout)

        if path is not None:
            self._set_root_path(path)
            self._root_edit.update(path)

        self._settings = None
        self.update_settings(settings)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = QApplication.keyboardModifiers()

        if key == Qt.Key_Delete:
            if modifiers == Qt.ShiftModifier:
                self._delete_selected()
            elif modifiers == Qt.NoModifier:
                self._trash_selected()
        # TODO:
        # elif key == Qt.Key_X:
            # if modifiers == Qt.ControlModifier:
                # self._cut()
        elif key == Qt.Key_C:
            if modifiers == Qt.ControlModifier:
                self._copy()
        elif key == Qt.Key_V:
            if modifiers == Qt.ControlModifier:
                self._paste()

    def _context_menu(self, point):
        '''
        Opens a context menu generated from the user settings.
        '''
        menu_item_settings = self._settings['context_menu']

        # Don't do anything if there are no defined menu items.
        if len(menu_item_settings) == 0:
            return

        # Get all the selected file paths.
        selected_items = [self._model.filePath(index) for index in self._view.selectedIndexes()]

        # Get the current directory the user is in.
        current_directory = self.current_directory()

        # Create the menu.
        menu = QMenu(self)
        for menu_item_setting in menu_item_settings:
            command = menu_item_setting['command']

            # Get the highest field number in the command string, as well as a set of field names.
            field_names = set()
            highest_field_number = None
            for parse_record in string.Formatter().parse(command):
                field_name = parse_record[1]
                if field_name is None:
                    continue

                field_names.add(field_name)

                try:
                    field_number = int(field_name)
                except ValueError:
                    pass
                else:
                    if highest_field_number is None or field_number > highest_field_number:
                        highest_field_number = field_number

            # If field numbers were used, then the menu item will be disabled if the number of
            # selected items does not equal the highest field number + 1.
            enabled = True
            if highest_field_number is not None and len(selected_items) != highest_field_number + 1:
                enabled = False

            # Disable the menu item if the command uses {selected}, but there is nothing selected.
            if enabled and 'selected' in field_names and len(selected_items) == 0:
                enabled = False

            # Disable the menu item if the command uses {current_directory}, but there is no
            # current directory.
            if enabled and 'current_directory' in field_names and current_directory is None:
                enabled = False

            # Disable the menu item if any of the selected items don't match at least one of the
            # given regex patterns. Note that if this is specified at least one item must be
            # selected.
            if enabled and 'require' in menu_item_setting:
                require_filters = regex_tools.FastListMatcher(menu_item_setting['require'])

                if not selected_items:
                    enabled = False
                else:
                    for path in selected_items:
                        if not require_filters.fullmatch(path):
                            enabled = False
                            break

            # Disable the menu item if any of the selected items matches any of the given regex
            # patterns
            if enabled and 'exclude' in menu_item_setting:
                exclude_filters = regex_tools.FastListMatcher(menu_item_setting['exclude'])

                for path in selected_items:
                    if exclude_filters.fullmatch(path):
                        enabled = False
                        break

            if not enabled:
                # Only create a menu item if it is not hidden.
                if menu_item_setting.get('show_if_disabled', False):
                    action = SubprocessAction(menu_item_setting['label'], self)
                    action.setEnabled(False)
                    menu.addAction(action)

                # No need to setup the action command if it is disabled.
                continue

            action = SubprocessAction(menu_item_setting['label'], self)
            menu.addAction(action)

            # Set the menu item command. The item will be disabled if there is a field in the
            # command string that is not supported.
            escaped_items = ['"{}"'.format(item) for item in selected_items]
            selected = ' '.join(escaped_items)
            current_directory = '"{}"'.format(current_directory)
            try:
                command = menu_item_setting['command'].format(
                    *escaped_items,
                    selected=selected,
                    current_directory=current_directory)
            except KeyError:
                action.setEnabled(False)
            else:
                action.command = command

        # Show the menu if it has entries.
        if len(menu.actions()) != 0:
            menu.popup(self._view.mapToGlobal(point))

    def update_settings(self, new_settings):
        '''
        Updates the settings.
        '''
        self._settings = new_settings

        # Setup file hiding regex filters.
        regex_filters = new_settings.get('regex_filters', [])
        if regex_filters == []:
            regex_filters = None
        else:
            regex_filters = regex_tools.FastListMatcher(new_settings['regex_filters'])
        self._root_edit.set_regex_filters(regex_filters)
        self._model.set_regex_filters(regex_filters)

    def _copy(self):
        '''
        Copies all of the selected items to the clipboard.
        '''
        # Copy the urls of the selected files to the clipboard.
        filePath = self._model.filePath
        urls = [QUrl.fromLocalFile(filePath(index)) for index in self._view.selectedIndexes()]

        mime_data = QMimeData()
        mime_data.setUrls(urls)

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)

    def _paste(self):
        '''
        Handles paste events.
        '''
        # Get the clipboard contents.
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        destination_directory = self.current_directory()

        if mime_data.hasUrls():
            # If the clipboard contains urls, copy from the sources.
            paths = [url.toLocalFile() for url in mime_data.urls() if url.isLocalFile()]

            for path in paths:
                source_directory = os.path.dirname(path)

                basename = os.path.basename(path)

                if os.path.isdir(path):
                    destination = path_utils.versioned_name(
                        destination_directory, basename, at_end=True)
                    shutil.copytree(path, destination)
                elif os.path.isfile(path):
                    destination = path_utils.versioned_name(destination_directory, basename)
                    shutil.copy2(path, destination)
        elif mime_data.hasText():
            # If the clipboard contains text, paste it to the root edit.
            self._root_edit.paste()
        # TODO:
        # elif mime_data.hasImage():
            # create image file with contents

    def current_item_directory(self):
        '''
        Returns the directory containing the currently selected item.
        '''
        current_index = self._view.currentIndex()

        if not current_index.isValid():
            return None

        active_path = self._model.filePath(current_index)

        return os.path.dirname(active_path)

    def current_directory(self):
        '''
        Returns the directory containing the currently selected item, or the item if it is a
        directory.
        '''
        current_index = self._view.currentIndex()

        if not current_index.isValid():
            return None

        active_path = self._model.filePath(current_index)

        if os.path.isdir(active_path):
            directory = active_path
        else:
            directory = os.path.dirname(active_path)

        return directory

    def _create_file(self):
        '''
        Creates a new file in the same directory as the current item, and has the user edit its
        name.
        '''
        directory = self.current_directory()

        # Get a free file name
        new_file_path = path_utils.versioned_name(directory, 'new_file')

        # Create the new file.
        open(new_file_path, 'a').close()

        # Have the user edit the file name.
        index = self._model.path_index(new_file_path)
        self._view.scrollTo(index)
        self._view.edit(index)

    def _create_directory(self):
        '''
        Creates a directory in the same directory as the current item, and has the user edit its
        name.
        '''
        directory = self.current_directory()

        # Get a free directory name
        new_directory_path = path_utils.versioned_name(directory, 'new_directory', at_end=True)

        # Create the new file.
        os.mkdir(new_directory_path)

        # Have the user edit the file name.
        index = self._model.path_index(new_directory_path)
        self._view.scrollTo(index)
        self._view.edit(index)

    def _delete_selected(self):
        '''
        Deletes all of the currently selected items.
        '''
        selected_indexes = self._view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        selection = QMessageBox.warning(
            self,
            'Delete',
            'Permanently delete selected items?',
            (QMessageBox.Yes | QMessageBox.No))

        if selection != QMessageBox.Yes:
            return

        for index in selected_indexes:
            self._model.remove(index)

    def _trash_selected(self):
        '''
        Moves all of the currently selected items to the trash directory.
        '''
        trash_directory = self._settings['trash_directory']

        if not os.path.isdir(trash_directory):
            os.makedirs(trash_directory)

        for index in self._view.selectedIndexes():
            path = self._model.filePath(index)

            item_name = os.path.basename(path)
            filesystem_frendly_date = str(datetime.datetime.now()).replace(':', ';')
            deleted_item_name = '{}@{}'.format(item_name, filesystem_frendly_date)

            deleted_item_path = path_utils.versioned_name(
                trash_directory, deleted_item_name, at_end=True)

            shutil.move(self._model.filePath(index), deleted_item_path)

            self._model.remove(index)

    def _handle_activated_index(self, index):
        '''
        This slot handles the activation of items in the view. If the activated item is a directory,
        then the view will change to that directory. If ctrl is held, then the directory will open in
        a new root. If the item is a file, the item will be opened.
        '''
        if self._model.isDir(index):
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                # Send a request for opening a new root.
                self.open_request.emit(self._model.filePath(index))
                return

            # Change the root directory.
            self._move_root_index(index)
            path = self._model.filePath(self._view.rootIndex())
            self._root_edit.update(path)
        else:
            self._open_index(index)

    def _open_index(self, index):
        '''
        Opens the file with the associated model index.
        '''
        path = self._model.filePath(index)

        for pattern, command in self._settings['open_with']:
            if re.fullmatch(pattern, path):
                expanded_command = command.format(path='"{}"'.format(path))
                subprocess.Popen(expanded_command, shell=True)
                break
        else:
            # Open the file with the OS settings.
            try:
                with ChDir(Path(path).parent):
                    os.startfile(path)
            except:
                # Prevent application crash if windows errors out.
                QMessageBox.critical(
                    self,
                    'Error',
                    'Unable to open file. Check windows file association settings.'
                )

    def _set_root_path(self, path):
        '''
        Changes the root to view the given path.
        '''
        self._move_root_index(self._model.path_index(path))

    def _move_root_index(self, index):
        '''
        Moves the root to view the given index.
        '''
        self._view.setRootIndex(index)
        self._view.setCurrentIndex(index)
        self._view.collapseAll()

    def set_close_disabled(self, disabled):
        '''
        Sets whether close button is disabled.
        '''
        self._close_widget.setDisabled(disabled)

    def path(self):
        '''
        Gets the path of the root.
        '''
        return self._model.filePath(self._view.rootIndex())
