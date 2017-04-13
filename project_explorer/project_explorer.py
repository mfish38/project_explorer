'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

A project based file explorer.
'''

import os
import sys
import json
import shutil
import ctypes

from PySide.QtCore import (
    Signal,
    Qt,
    QFileSystemWatcher,
    QTimer
)

from PySide.QtGui import (
    QFrame,
    QApplication,
    QAction,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QToolBar,
    QMessageBox,
    QFileDialog,
)

from extended_tabs import ExtendedTabBar, ExtendedTabWidget
import extended_json
from root_widget import RootWidget

SETTINGS_PATH = '.settings.json'
DEFAULT_SETTINGS_PATH = '.default_settings.json'

class Project(QFrame):
    '''
    This widget displays all of the roots for a project in a vertical splitter.
    '''
    name_changed = Signal()

    def __init__(self, name, settings):
        super(Project, self).__init__()

        self._name = name

        # --- setup the splitter ---
        self._splitter = QSplitter()
        self._splitter.setOrientation(Qt.Vertical)

        self._set_closeing_disabled(True)

        # --- setup the project buttons ---
        tool_bar = QToolBar()

        add_root_action = QAction('Add Root', self)
        tool_bar.addAction(add_root_action)
        tool_bar.widgetForAction(add_root_action).setObjectName('add_root')
        add_root_action.triggered.connect(self.add_root)

        open_trash_action = QAction('Open Trash', self)
        tool_bar.addAction(open_trash_action)
        tool_bar.widgetForAction(open_trash_action).setObjectName('open_trash')
        open_trash_action.triggered.connect(self.open_trash)

        save_action = QAction('Save Project', self)
        tool_bar.addAction(save_action)
        tool_bar.widgetForAction(save_action).setObjectName('save_project')
        save_action.triggered.connect(self.save)

        # --- setup the layout ---
        main_layout = QVBoxLayout()

        main_layout.addWidget(self._splitter)
        main_layout.addWidget(tool_bar)
        self.setLayout(main_layout)

        self._settings = None
        self.update_settings(settings)

    @property
    def name(self):
        return self._name

    def update_settings(self, new_settings):
        self._settings = new_settings

        roots = (self._splitter.widget(index) for index in xrange(self._splitter.count()))
        for root in roots:
            root.update_settings(new_settings)

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
        root_widget = RootWidget(self._settings, path)
        root_widget.close_request.connect(self.handle_close_request)

        self._splitter.addWidget(root_widget)

        child_count = self._splitter.count()
        if child_count == 2:
            self._set_closeing_disabled(False)

    def open_trash(self):
        '''
        Opens a new project root that views the trash directory.
        '''
        trash_directory = self._settings['trash_directory']

        if not os.path.isdir(trash_directory):
            os.makedirs(trash_directory)

        self.add_root(path=trash_directory)

    def handle_close_request(self):
        '''
        Slot that handles removing project roots when their close button is clicked.
        '''
        child_count = self._splitter.count()
        if child_count == 2:
            self._set_closeing_disabled(True)

        self.sender().deleteLater()

    def save(self):
        '''
        Prompts the user for project name and saves the current state of the project to a JSON file
        as follows:

            [[list of root paths], [list of root widget sizes]]
        '''
        projects_directory = self._settings['projects_directory']

        if not os.path.isdir(projects_directory):
            os.makedirs(projects_directory)

        path, filter = QFileDialog.getSaveFileName(
            self, 'Save Project', os.path.join(projects_directory, self._name))

        if path == '' and filter == '':
            return

        root_paths = [
            self._splitter.widget(index).path()
            for index in xrange(self._splitter.count())]

        spliter_sizes = self._splitter.sizes()

        state = [root_paths, spliter_sizes]

        with open(path, 'w') as save_file:
            json.dump(state, save_file)

        self._name = os.path.splitext(os.path.basename(path))[0]

        self.name_changed.emit()

    @classmethod
    def open(cls, path, settings):
        '''
        Instantiates a Project widget from the given saved project file, and returns it.
        '''
        with open(path, 'r') as save_file:
            state = json.load(save_file)

        root_paths, spliter_sizes = state

        name = os.path.splitext(os.path.basename(path))[0]

        project = cls(name, settings)

        for path in root_paths:
            project.add_root(path=path)

        project._splitter.setSizes(spliter_sizes)

        return project

class ProjectExplorer(QFrame):
    '''
    A project explorer with tabs.

    Tab contents show different projects as different project tabs are selected.
    '''
    def __init__(self):
        super(ProjectExplorer, self).__init__()

        self.setWindowTitle('ProjectExplorer')

        # --- Setup the tab bar ---
        self._tab_bar = ExtendedTabBar()

        self._tab_bar.setShape(ExtendedTabBar.RoundedEast)
        self._tab_bar.setTabsClosable(True)
        self._tab_bar.setMovable(True)
        self._tab_bar.setUsesScrollButtons(True)
        self._tab_bar.setDrawBase(False)

        open_project_action = QAction('Open Project', self)
        self._tab_bar.floating_toolbar.addAction(open_project_action)
        (
            self
            ._tab_bar
            .floating_toolbar
            .widgetForAction(open_project_action)
            .setObjectName('open_project')
        )
        open_project_action.triggered.connect(self._open_project)

        new_project_action = QAction('New Project', self)
        self._tab_bar.floating_toolbar.addAction(new_project_action)
        (
            self
            ._tab_bar
            .floating_toolbar
            .widgetForAction(new_project_action)
            .setObjectName('new_project')
        )
        new_project_action.triggered.connect(self._new_project)

        settings_action = QAction('Settings', self)
        self._tab_bar.right_toolbar.addAction(settings_action)
        self._tab_bar.right_toolbar.widgetForAction(settings_action).setObjectName('settings')
        settings_action.triggered.connect(self._open_settings)

        # --- Setup the tab widget ---
        self._tab_widget = ExtendedTabWidget()
        self._tab_widget.setTabBar(self._tab_bar)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self._tab_widget)
        main_layout.addWidget(self._tab_bar)
        self.setLayout(main_layout)

        self._settings_watcher = QFileSystemWatcher()
        self._settings_watcher.fileChanged.connect(self.load_settings)

        self._settings = None
        self._load_settings()

        # There needs to be a delay after the settings watcher triggers to allow external
        # applications to finish writing to disk.
        self._settings_load_delay = QTimer()
        self._settings_load_delay.setSingleShot(True)
        self._settings_load_delay.setInterval(200)
        self._settings_load_delay.timeout.connect(self._load_settings)

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

        project = Project(project_name, self._settings)
        project.name_changed.connect(self._handle_name_change)
        project.add_root()

        index = self._tab_widget.addTab(project, project_name)
        self._tab_bar.setCurrentIndex(index)

    def _open_project(self):
        '''
        Opens a saved project.
        '''
        projects_directory = self._settings['projects_directory']

        if not os.path.isdir(projects_directory):
            os.makedirs(projects_directory)

        path, filter = QFileDialog.getOpenFileName(
            self, 'Open Project', os.path.join(projects_directory))

        if path == '' and filter == '':
            return

        project = Project.open(path, self._settings)
        project.name_changed.connect(self._handle_name_change)
        index = self._tab_widget.addTab(project, project.name)
        self._tab_bar.setCurrentIndex(index)

    def _handle_name_change(self):
        '''
        Updates the tab text of projects that have been saved.
        '''
        project = self.sender()
        sender_index = self._tab_widget.indexOf(project)
        self._tab_bar.setTabText(sender_index, project.name)

    def _open_settings(self):
        '''
        Opens the settings file.
        '''
        os.startfile(SETTINGS_PATH)

    def _apply_theme_settings(self):
        '''
        Apply the theme specified in the settings.
        '''
        theme_path = self._settings['theme']
        try:
            with open(theme_path) as theme:
                style_sheet = theme.read()
        except IOError:
            QMessageBox.critical(
                self,
                'Invalid Setting',
                'Unable to load theme:\n"{}"'.format(theme_path))

            return

        self.setStyleSheet(style_sheet)

    def _load_settings(self):
        '''
        Since the settings file is modified by an external program, load_settings() must wait some
        delay to allow the file to be completely written. This function does the actually settings
        load.
        '''
        # Make sure the settings exist.
        if not os.path.isfile(SETTINGS_PATH):
            shutil.copy(DEFAULT_SETTINGS_PATH, SETTINGS_PATH)

        # Make sure the settings are being watched. Note that this needs to be outside of the
        # existence check above, otherwise the settings won't be watched if they already exist.
        if len(self._settings_watcher.files()) == 0:
            self._settings_watcher.addPath(SETTINGS_PATH)

        self._settings = extended_json.load_file(SETTINGS_PATH)

        self._apply_theme_settings()

        # Update the setting of all the open project widgets.
        projects = (self._tab_widget.widget(index) for index in xrange(self._tab_widget.count()))
        for project in projects:
            project.update_settings(self._settings)

    def load_settings(self):
        '''
        Loads the settings file.
        '''
        self._settings_load_delay.start()

def main():
    # The current working directory must be the package directory so that relative paths are
    # interpreted as relative to the installation.
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # Set the AppUserModelID so that the window is not grouped with other python programs in the
    # taskbar.
    AppUserModelID = u'ProjectExplorer.ProjectExplorer'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(AppUserModelID)

    application = QApplication(sys.argv)

    # Create and show the main window.
    main_window = ProjectExplorer()
    main_window.resize(500, 1000)
    main_window.show()

    # Enter the event loop.
    application.exec_()

if __name__ == '__main__':
    main()
