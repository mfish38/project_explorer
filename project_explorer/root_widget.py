'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

Tree based file system browser widget for browsing the file tree from a movable root.
'''

import os
import datetime
import shutil
import itertools
import subprocess
import string

from PySide.QtCore import (
    Signal,
    Qt,
    QDir,
    QEvent,
    QUrl,
    QMimeData,
    QObject,
)

from PySide.QtGui import (
    QLineEdit,
    QSortFilterProxyModel,
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

from json_file_icon_provider import JSONFileIconProvider

def _valid_split(path):
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

def _remove_invalid_basenames(path):
    '''
    If the path is not valid, then apply dirname() until it is, or only an empty string is left.
    Does nothing to valid paths.
    '''
    while True:
        # Handle no valid path case.
        if path == '':
            break

        # Check if a valid path has been found.
        if os.path.isdir(path):
            break

        path = os.path.dirname(path).strip()

    return path

class RootEdit(QLineEdit):
    '''
    This widget displays the current path of a root, and allows the user to edit it.
    '''
    new_root = Signal(str)

    def __init__(self, model, view, parent=None):
        super(RootEdit, self).__init__(parent)

        self._model = model
        self._view = view

        self._tab_suggestions = None

        self.textEdited.connect(self._handle_edit)

    def _tab_complete(self):
        '''
        Implements tab completion.
        '''
        path = self.text().strip()

        # Tab complete drive letters
        if len(path) == 1:
            # If the drive letter is valid, then autocomplete it.
            path = '{}:{}'.format(path, os.sep)

            if os.path.isdir(path):
                self.setText(path)
                self.new_root.emit(path)

            return
        elif len(path) == 2 and path[1] == ':' and os.path.isdir(path):
            # Add a path separator if tab pressed on a valid drive letter.
            path += os.sep

            self.setText(path)
            self.new_root.emit(path)

            return

        # After this point try to tab complete where the basename is valid, but the tail isn't.

        head, tail = _valid_split(path)

        # If there is no valid head, then we can't do anything.
        if head == '':
            return

        # If there is no tail, then change to the head. This handles "c:/path /" and "c:/path/ /"
        if tail == '':
            head = os.path.normcase(os.path.normpath(head))
            head += os.sep
            self.setText(head)
            self.new_root.emit(head)
            return

        # convert to lower case for case insensitivity.
        tail = tail.lower()

        if self._tab_suggestions is None:
            possiblities = [name.lower() for name in os.listdir(head)]
            possiblities = [
                name
                for name in possiblities
                if name.startswith(tail) and os.path.isdir(os.path.join(head, name))]

            if len(possiblities) == 0:
                # If there are no possibilities, then do nothing.
                return
            elif len(possiblities) == 1:
                # If there is only one possibility then complete using it.
                completed_path = os.path.join(head, possiblities[0])
                completed_path = os.path.normcase(os.path.normpath(completed_path))
                completed_path += os.sep
                self.setText(completed_path)
                self.new_root.emit(completed_path)
                return

            # Create a loop of suggestions.
            self._tab_suggestions = itertools.cycle(possiblities)

            # Advance the suggestions by one if the current tail is the first suggestion.
            if tail == possiblities[0]:
                next(self._tab_suggestions)

        # Cycle through the possibilities.
        try:
            self.setText(os.path.join(head, next(self._tab_suggestions)))
        except StopIteration:
            # There were no suggestions
            pass

    def _handle_edit(self, text):
        '''
        This handles user edits, and if the input path is valid, changes the root to it.
        '''
        text = text.strip()

        # If the text is blank, then go to 'This PC'
        if text == '':
            self.new_root.emit('This PC')
            return

        # Throw out invalid basenames.
        text = _remove_invalid_basenames(text)

        # If there is no valid basename, go to 'This PC'
        if text == '':
            self.new_root.emit('This PC')
            return

        # Do nothing if the path is already the current root
        normalized_current_root = os.path.normcase(
            os.path.normpath(self._model.filePath(self._view.rootIndex())))
        normalized_text = os.path.normcase(os.path.normpath(text))
        if normalized_text == normalized_current_root:
            return

        # Handle ambiguous paths (paths that are a prefix to another path).
        if not text.endswith(('/', '\\')):
            basename = os.path.basename(text)
            ambiguous_path = any(
                (path.startswith(basename)
                 for path in os.listdir(os.path.dirname(text))
                 if path != basename))

            if ambiguous_path:
                # If the path is a folder in the current root, then don't do anything if the path is
                # ambiguous.
                if normalized_current_root == os.path.dirname(normalized_text):
                    return

                # If the current root and the new path are in the same directory, and the path is
                # ambiguous, then go to the directory containing them both.
                # print normalized_current_root
                # print text
                if os.path.dirname(normalized_current_root) == os.path.dirname(normalized_text):
                    text = os.path.dirname(text)

        # Normalize the path
        text = os.path.normcase(os.path.normpath(text))

        # Add a separator at the end if the path is not just a drive letter and the path does not
        # already end in a separator.
        if os.path.splitdrive(text)[1] != '' and not text.endswith(os.sep):
            text += os.sep

        self.setText(text)
        self.new_root.emit(text)

    def update(self):
        '''
        Updates the root edit to show the current path.
        '''
        path = self._model.filePath(self._view.rootIndex())

        if path != '':
            path = os.path.normcase(os.path.normpath(path))
            if not path.endswith(os.sep):
                path += os.sep

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

        return super(RootEdit, self).event(event)

class FileSystemProxyModel(QSortFilterProxyModel):
    '''
    Sorts the source QFileSystemModel.
    '''
    def __init__(self):
        super(FileSystemProxyModel, self).__init__()

        self.rowsInserted.connect(self.invalidate)
        self.dataChanged.connect(self.invalidate)

        self._filter_extensions = set()

    def filter_extensions(self, extensions):
        '''
        Sets the model to filter out files with the given extension.

        extensions:
            A list of extensions to filter out. Empty list to stop filtering.
        '''
        self._filter_extensions = set(extensions)

        self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()

        index = model.index(source_row, 0, source_parent)

        if model.isDir(index):
            return True

        extension = os.path.splitext(model.filePath(index))[1]

        return extension not in self._filter_extensions

    def setData(self, index, value, role):
        '''
        Modify a file system item name.
        '''
        # Fix issue where setting a name to the same name in a different case causes an error. This
        # issue is caused by a Qt bug (https://bugreports.qt.io/browse/QTBUG-3570).
        if role == Qt.EditRole and self.fileName(index).lower() == value.lower():
            try:
                source = self.filePath(index)
                os.rename(source, os.path.join(os.path.dirname(source), value))
            except:
                return False
            else:
                self.dataChanged.emit(index, index)
                return True
        else:
            return self.sourceModel().setData(self.mapToSource(index), value, role)

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

    def fileName(self, index):
        '''
        Pass through to QFileSystemModel
        '''
        return self.sourceModel().fileName(self.mapToSource(index))

    def remove(self, index):
        '''
        Pass through to QFileSystemModel
        '''
        self.sourceModel().remove(self.mapToSource(index))

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
        # Prevent CMD window from flashing on screen.
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        subprocess.Popen(self.command, startupinfo=startupinfo)
        
class RootWidget(QFrame):
    '''
    This widget provides a view of a project root.
    '''
    close_request = Signal()

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
            QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Hidden)

        self._model = FileSystemProxyModel()
        self._model.setSourceModel(model)

        # --- setup the tree view ---
        self._view = QTreeView()
        self._view.setModel(self._model)
        self._view.setSelectionMode(QTreeView.ExtendedSelection)
        self._view.activated.connect(self._handle_activated_index)
        self._view.setSortingEnabled(True)
        self._view.setHeaderHidden(True)
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
        
        # --- setup the current root path label ---
        self._root_edit = RootEdit(self._model, self._view)
        self._root_edit.new_root.connect(self._set_root_path)

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

        path_layout = QHBoxLayout()
        path_layout.addWidget(self._root_edit)
        path_layout.addWidget(tool_bar)
        main_layout.addLayout(path_layout)

        main_layout.addWidget(self._view)

        self.setLayout(main_layout)

        if path is not None:
            self._set_root_path(path)
            self._root_edit.update()

        self._settings = None
        self.update_settings(settings)

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
            
            # Check if the menu item should be disabled.
            enabled = True
            if (
                    highest_field_number is not None
                    and len(selected_items) != highest_field_number + 1
                ):
                # If field numbers were used, then the menu item will be disabled if the number of
                # selected items does not equal the highest field number + 1.
                enabled = False
            elif 'selected' in field_names and len(selected_items) == 0:
                # Disable the menu item if the command uses {selected}, but there is nothing
                # selected.
                enabled = False
            elif 'current_directory' in field_names and current_directory is None:
                # Disable the menu item if the command uses {current_directory}, but there is no
                # current directory.
                enabled = False
            else:
                # Disable the menu item if an extensions list is specified, and one of the selected
                # items is not a file with an extension in the list.
                try:
                    extensions = menu_item_setting['extensions']
                except KeyError:
                    pass
                else:
                    extensions = set(extensions)
                    
                    for path in selected_items:
                        if not os.path.isfile(path) or os.path.splitext(path)[1] not in extensions:
                            enabled = False
                            break
            
            if not enabled:
                # On create a menu item if it is not specified to hide the item.
                if not menu_item_setting.get('hide_if_disabled', False):
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
            try:
                command = menu_item_setting['command'].format(
                    *escaped_items,
                    selected=selected,
                    current_directory=current_directory)
            except KeyError:
                action.setEnabled(False)
            else:
                action.command = command
        
        # Show the menu.
        menu.popup(self._view.mapToGlobal(point))

    def update_settings(self, new_settings):
        '''
        Updates the settings.
        '''
        self._settings = new_settings

        self._model.filter_extensions(new_settings['filter_extensions'])

    def keyPressEvent(self, event):
        '''
        Handle short cuts key presses.
        '''
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

    def _copy(self):
        '''
        Copies all of the selected items to the clipboard.
        '''
        filePath = self._model.filePath
        urls = [QUrl.fromLocalFile(filePath(index)) for index in self._view.selectedIndexes()]

        mime_data = QMimeData()
        mime_data.setUrls(urls)

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)

    def _paste(self):
        '''
        Pastes files/folders from the clipboard.
        '''
        clipboard = QApplication.clipboard()

        mime_data = clipboard.mimeData()

        destination_directory = self.current_directory()

        if mime_data.hasUrls():
            paths = [url.toLocalFile() for url in mime_data.urls() if url.isLocalFile()]

            for path in paths:
                source_directory = os.path.dirname(path)

                basename = os.path.basename(path)

                if os.path.isdir(path):
                    if source_directory == destination_directory:
                        # Get a free version suffix.
                        counter = 0
                        while True:
                            destination = os.path.join(
                                destination_directory, basename + '_{}'.format(counter))

                            if not os.path.isdir(destination):
                                break

                            counter += 1
                    else:
                        destination = os.path.join(destination_directory, basename)

                    shutil.copytree(path, destination)
                elif os.path.isfile(path):
                    if source_directory == destination_directory:
                        # Get a free version suffix.
                        name, extension = os.path.splitext(basename)
                        counter = 0
                        while True:
                            destination = os.path.join(
                                destination_directory, name + '_{}{}'.format(counter, extension))

                            if not os.path.isfile(destination):
                                break

                            counter += 1
                    else:
                        destination = os.path.join(destination_directory, basename)

                    shutil.copy2(path, destination)

        # TODO:
        # elif mime_data.hasText():
        # elif mime_data.hasImage():

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
        counter = 0
        while True:
            new_file_path = os.path.join(directory, 'new_file_{}'.format(counter))

            if not os.path.isfile(new_file_path):
                break

            counter += 1

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
        counter = 0
        while True:
            new_directory_path = os.path.join(directory, 'new_directory_{}'.format(counter))

            if not os.path.isdir(new_directory_path):
                break

            counter += 1

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

            if os.path.isdir(path):
                shutil.copytree(
                    self._model.filePath(index), os.path.join(trash_directory, deleted_item_name))
            elif os.path.isfile(path):
                shutil.copy2(
                    self._model.filePath(index), os.path.join(trash_directory, deleted_item_name))

            self._model.remove(index)

    def _handle_activated_index(self, index):
        '''
        This slot handles the activation of items in the view. If the activated item is a directory,
        then the view will change to that directory. Otherwise, the item will be opened.
        '''
        if self._model.isDir(index):
            self._move_root_index(index)
            self._root_edit.update()
        else:
            self._open_index(index)

    def _open_index(self, index):
        '''
        Opens the file with the associated model index.
        '''
        path = self._model.filePath(index)
        os.startfile(path)

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

    def move_root_up(self):
        '''
        Moves the root of the view up one level. Note that the previous root will be collapsed to
        prevent cluttering the view.
        '''
        initial_root_index = self._view.rootIndex()
        self._move_root_index(self._model.parent(initial_root_index))
        self._view.collapse(initial_root_index)
        self._root_edit.update()

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
