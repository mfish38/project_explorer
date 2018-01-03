
import os
import sys
import ctypes

from qtpy.QtWidgets import QApplication

from .project_explorer import ProjectExplorer

def main():
    '''
    Runs the project explorer as a standalone program.
    '''
    # The current working directory must be the package directory so that relative paths are
    # interpreted as relative to the installation.
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # Set the AppUserModelID so that the window is not grouped with other python programs in the
    # taskbar.
    app_user_model_id = u'ProjectExplorer.ProjectExplorer'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_user_model_id)

    application = QApplication(sys.argv)

    # Create and show the main window.
    main_window = ProjectExplorer()
    main_window.resize(500, 1000)
    main_window.show()

    # Enter the event loop.
    application.exec_()

if __name__ == '__main__':
    main()
