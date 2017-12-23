# project_explorer
A simple file browser that uses project based concepts.

## Features
- Projects with multiple folder roots
- Configurable right click file/folder menus
    - JSON configurable
    - Context sensitive
    - Execute custom commands
- Fast directory traversal:
    - Case insensitive tab completion
    - Location will automatically change as paths are typed
    - Backspace at end of path for navigating up
- Themeable in Qt's CSS extended with SCSS

## Screenshots
![alt text](images/screenshot_1.png "Screenshot")

## Installation

Currently developed for Windows and requires Python 3.6.

Requires a Qt python library supported by [qtpy](https://github.com/spyder-ide/qtpy). Currently only PyQt5 is tested.

Install with pip:

```bash
pip install project_explorer
```

## Running

To create a Windows desktop shortcut, Right Click->New->Shortcut and set the location to:

```
pythonw.exe -m project_explorer.project_explorer
```

## Keyboard Shortcuts

| Action               | Keys                            |
| -------------------- | ------------------------------- |
| Autocomplete Path    | <kbd>Tab</kbd>                  |
| Copy File/Directory  | <kbd>Ctrl</kbd>+<kbd>C</kbd>    |
| Paste File/Directory | <kbd>Ctrl</kbd>+<kbd>V</kbd>    |
| Trash Selected       | <kbd>Del</kbd>                  |
| Delete Selected      | <kbd>Shift</kbd>+<kbd>Del</kbd> |
