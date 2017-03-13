'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

A project based file explorer.
'''

import os
import sys
import shutil
import datetime
import glob
import itertools
import ctypes

from PySide.QtCore import Signal, QModelIndex, Qt, QDir, QEvent
from PySide.QtGui import (
    QLineEdit,
    QSortFilterProxyModel,
    QItemDelegate,
    QFrame,
    QApplication,
    QAction,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QFileSystemModel,
    QTreeView,
    QToolBar,
)

from extended_tabs import ExtendedTabBar, ExtendedTabWidget
from json_file_icon_provider import JSONFileIconProvider

TRASH_DIRECTORY = '.trash'

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

class SortedFileSystemProxyModel(QSortFilterProxyModel):
    '''
    Sorts the source QFileSystemModel.
    '''
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
        self.sourceModel().remove(self.mapToSource(index))
    
    def lessThan(self, left, right):
        '''
        Sorts directories before files, then sorts lexicographically.
        '''
        model = self.sourceModel()
        
        # Sort directories above files, regardless of sort order.
        if model.isDir(left) and not model.isDir(right):
            return True if self.sortOrder() == Qt.AscendingOrder else False
        elif not model.isDir(left) and model.isDir(right):
            return False if self.sortOrder() == Qt.AscendingOrder else True
        
        # Sort items of the same type (file or directory) lexicographically.
        if model.filePath(left).lower() < model.filePath(right).lower():
            return True
        else:
            return False

class _EditableItemDelegate(QItemDelegate):
    '''
    An item delegate that is editable, and emits a signal when editing is finished.
    '''
    edited = Signal(QModelIndex)
    
    def setModelData(self, editor, model, index):
        super(_EditableItemDelegate, self).setModelData(editor, model, index)
        self.edited.emit(index)
        
class RootWidget(QFrame):
    '''
    This widget provides a view of a project root.
    '''
    close_request = Signal()
    
    def __init__(self, path=None):
        super(RootWidget, self).__init__()
            
        # --- setup the file system model ---
        model = QFileSystemModel()
        model.setRootPath('This PC')
        model.setReadOnly(False)
        model.setIconProvider(JSONFileIconProvider('file_view_icons.json'))
        model.setFilter(
            QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Hidden)
        
        self._model = SortedFileSystemProxyModel()
        self._model.setSourceModel(model)
        
        # --- setup the tree view ---
        self._view = QTreeView()
        self._view.setModel(self._model)
        self._view.setSelectionMode(QTreeView.ExtendedSelection)
        self._view.activated.connect(self._handle_activated_index)
        self._view.setSortingEnabled(True)
        self._view.setHeaderHidden(True)
        self._view.sortByColumn(0, Qt.AscendingOrder)
        
        # Setup resorting the view when a filename is edited.
        self._file_item_delegate = _EditableItemDelegate()
        self._file_item_delegate.edited.connect(self._model.invalidate)
        self._view.setItemDelegate(self._file_item_delegate)
        
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
            
        # --- setup the current root path label ---
        self._root_edit = RootEdit(self._model, self._view)
        self._root_edit.new_root.connect(self._set_root_path)
        
        # --- setup the tool bar ---
        tool_bar = QToolBar()
        
        new_file_action = QAction('New File', self);
        tool_bar.addAction(new_file_action)
        tool_bar.widgetForAction(new_file_action).setObjectName('new_file')
        new_file_action.triggered.connect(self._create_file)
        
        new_directory_action = QAction('New Directory', self);
        tool_bar.addAction(new_directory_action)
        tool_bar.widgetForAction(new_directory_action).setObjectName('new_directory')
        new_directory_action.triggered.connect(self._create_directory)
        
        close_action = QAction('Close', self);
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
    
    def keyPressEvent(self, event):
        '''
        Handle short cuts key presses.
        '''
        if event.key() == Qt.Key_Delete:
            if QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                self._delete_selected()
            else:
                self._trash_selected()
    
    def current_item_directory(self):
        '''
        Returns the directory containing the currently selected item.
        '''
        active_path = self._model.filePath(self._view.currentIndex())
        
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
        directory = self.current_item_directory()
        
        # Get a free file name
        counter = 0
        new_file_path_base = os.path.join(directory, 'new_file_{}')
        while True:
            new_file_path = new_file_path_base.format(counter)
            
            if not os.path.isfile(new_file_path):
                break
                
            counter += 1
        
        # Create the new file.
        open(new_file_path, 'a').close()
        
        # Have the user edit the file name.
        self._view.edit(self._model.path_index(new_file_path))
    
    def _create_directory(self):
        '''
        Creates a directory in the same directory as the current item, and has the user edit its
        name.
        '''
        directory = self.current_item_directory()
        
        # Get a free directory name
        counter = 0
        new_directory_path_base = os.path.join(directory, 'new_directory_{}')
        while True:
            new_directory_path = new_directory_path_base.format(counter)
            
            if not os.path.isdir(new_directory_path):
                break
                
            counter += 1
        
        # Create the new file.
        os.mkdir(new_directory_path)
        
        # Have the user edit the file name.
        self._view.edit(self._model.path_index(new_directory_path))
    
    def _delete_selected(self):
        '''
        Deletes all of the currently selected items.
        '''
        for index in self._view.selectedIndexes():
            self._model.remove(index)
    
    def _trash_selected(self):
        '''
        Moves all of the currently selected items to the trash directory.
        '''
        if not os.path.isdir(TRASH_DIRECTORY):
            os.makedirs(TRASH_DIRECTORY)
    
        for index in self._view.selectedIndexes():
            item_name = os.path.basename(self._model.filePath(index))
            filesystem_frendly_date = str(datetime.datetime.now()).replace(':', ';')
            deleted_item_name = '{}@{}'.format(item_name, filesystem_frendly_date)
            shutil.move(
                self._model.filePath(index), os.path.join(TRASH_DIRECTORY, deleted_item_name))

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

class Project(QFrame):
    '''
    This widget displays all of the roots for a project in a vertical splitter.
    '''
    def __init__(self):
        super(Project, self).__init__()

        # --- setup the splitter ---
        self._splitter = QSplitter()
        self._splitter.setOrientation(Qt.Vertical)

        self.add_root()
        self._set_closeing_disabled(True)
        
        # --- setup the add button ---
        tool_bar = QToolBar()
        
        add_root_action = QAction('Add Root', self);
        tool_bar.addAction(add_root_action)
        tool_bar.widgetForAction(add_root_action).setObjectName('add_root')
        add_root_action.triggered.connect(self.add_root)
        
        open_trash_action = QAction('Open Trash', self);
        tool_bar.addAction(open_trash_action)
        tool_bar.widgetForAction(open_trash_action).setObjectName('open_trash')
        open_trash_action.triggered.connect(self.open_trash)
        
        # --- setup the layout ---
        main_layout = QVBoxLayout()
        
        main_layout.addWidget(self._splitter)
        main_layout.addWidget(tool_bar)
        self.setLayout(main_layout)
        
    def _set_closeing_disabled(self, disabled):
        '''
        Sets whether the close buttons of all the project roots are disabled.
        '''
        child_count = self._splitter.count()
        for index in xrange(child_count):
            child = self._splitter.widget(index)

            child.set_close_disabled(disabled)
            
    def add_root(self, path=None):
        '''
        Adds a new root to the project.
        '''
        root_widget = RootWidget(path)
        root_widget.close_request.connect(self.handle_close_request)
        
        self._splitter.addWidget(root_widget)
        
        child_count = self._splitter.count()
        if child_count == 2:
            self._set_closeing_disabled(False)
    
    def open_trash(self):
        '''
        Opens a new project root that views the trash directory.
        '''
        if not os.path.isdir(TRASH_DIRECTORY):
            os.makedirs(TRASH_DIRECTORY)

        self.add_root(path=TRASH_DIRECTORY)

    def handle_close_request(self):
        '''
        Slot that handles removing project roots when their close button is clicked.
        '''
        child_count = self._splitter.count()
        if child_count == 2:
            self._set_closeing_disabled(True)
        
        self.sender().deleteLater()

class ProjectTabBar(ExtendedTabBar):
    '''
    Tab bar for switching between different open projects, as well as opening new ones.
    '''
    new_tab_requested = Signal()
    
    def __init__(self):
        super(ProjectTabBar, self).__init__()
        
        new_tab_action = QAction('New tab', self);
        self.floating_toolbar.addAction(new_tab_action)
        self.floating_toolbar.widgetForAction(new_tab_action).setObjectName('new_tab')
        new_tab_action.triggered.connect(self.new_tab_requested.emit)
    
class ProjectExplorer(QFrame):
    '''
    A project explorer with tabs.
    
    Tab contents show different projects as different project tabs are selected.
    '''
    def __init__(self):
        super(ProjectExplorer, self).__init__()
        
        self.setWindowTitle('ProjectExplorer')
        
        self._tab_widget = ExtendedTabWidget()
        self._tab_bar = ProjectTabBar()
        self._tab_bar.setShape(ProjectTabBar.RoundedEast)
        self._tab_bar.setTabsClosable(True)
        self._tab_bar.setMovable(True)
        self._tab_bar.setUsesScrollButtons(True)
        self._tab_bar.setDrawBase(False)
        self._tab_bar.new_tab_requested.connect(self._new_project)
        self._tab_widget.setTabBar(self._tab_bar)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(self._tab_widget)
        main_layout.addWidget(self._tab_bar)
        self.setLayout(main_layout)
        
        self._new_project()
        
    def _new_project(self):
        '''
        Creates a new project.
        '''
        # Get a unique project name.
        open_projects = {self._tab_bar.tabText(index) for index in xrange(self._tab_bar.count())}
        project_name_format = 'project_{}'
        project_count = 0
        while True:
            project_name = project_name_format.format(project_count)
            
            if project_name not in open_projects:
                break
            
            project_count += 1
    
        index = self._tab_widget.addTab(Project(), project_name)
        self._tab_bar.setCurrentIndex(index)
        
def main():
    # Set the AppUserModelID so that the window is not grouped with other python programs in the
    # taskbar.
    AppUserModelID = u'ProjectExplorer.ProjectExplorer'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(AppUserModelID)

    application = QApplication(sys.argv)
    
    # Load and apply the theme.
    with open('theme.css') as theme:
        style_sheet = theme.read()
    application.setStyleSheet(style_sheet)
    
    # Create and show the main window.
    main_window = ProjectExplorer()
    main_window.resize(500, 1000)
    main_window.show()
    
    # Enter the event loop.
    application.exec_()

if __name__ == '__main__':
    main()
