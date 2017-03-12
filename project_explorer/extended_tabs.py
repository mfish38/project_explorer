'''
This module contains an implementation of tabs that is more flexible than QTabWidget.
'''

from PySide.QtCore import Qt, QSize
from PySide.QtGui import QTabBar, QFrame, QStackedWidget, QToolBar, QBoxLayout

class _NoMinimumWidthTabBar(QTabBar):
    '''
    Extends QTabBar to have no minimum width.
    
    QTabBar's default minimumSizeHint() is larger than the size of one tab. This means that if there
    is only one tab, then a QTabBar placed in a layout that has widgets to the right of it will have
    an empty gap between the between the tab and the widgets. This class solves this issue by
    setting the minimumSizeHint() width (or height in the case of vertical tabs) to 0.
    '''
    def __init__(self):
        super(_NoMinimumWidthTabBar, self).__init__()

    def minimumSizeHint(self):
        hint = super(_NoMinimumWidthTabBar, self).minimumSizeHint()
        
        if self.shape() in {
                QTabBar.RoundedNorth,
                QTabBar.RoundedSouth,
                QTabBar.TriangularNorth,
                QTabBar.TriangularSouth}:
            return QSize(0, hint.height())
        else:
            return QSize(hint.width(), 0)

class ExtendedTabBar(QFrame):
    '''
    A tab bar that has QToolBars to the left, right, and floating at the end of the tabs.
    
    Note that although this class inherits from QFrame, __getattr__() trickery is used to "inherit"
    the attributes of an internal object that inherits from QTabBar. This is done because it allows
    the actual tab bar object to be placed in a layout with other widgets, while allowing this class
    to be treated as the tab bar itself.
    '''
    RoundedNorth = QTabBar.RoundedNorth
    RoundedSouth = QTabBar.RoundedSouth
    RoundedWest = QTabBar.RoundedWest
    RoundedEast = QTabBar.RoundedEast
    TriangularNorth = QTabBar.TriangularNorth
    TriangularSouth = QTabBar.TriangularSouth   
    TriangularWest = QTabBar.TriangularWest
    TriangularEast = QTabBar.TriangularEast
    
    def __init__(self):
        super(ExtendedTabBar, self).__init__()
        
        self._tab_bar = _NoMinimumWidthTabBar()

        self._left_toolbar = QToolBar()
        self._floating_toolbar = QToolBar()
        self._right_toolbar = QToolBar()

        # Setup the layout.
        self._main_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._main_layout.addWidget(self._left_toolbar)
        self._main_layout.addWidget(self._tab_bar)
        self._main_layout.addWidget(self._floating_toolbar)
        self._main_layout.addStretch()
        self._main_layout.addWidget(self._right_toolbar)
        
        self.setLayout(self._main_layout)
    
    def __getattr__(self, name):
        '''
        Return the internal tab bar object's attributes if this class does not have the given
        attribute.
        '''
        try:
            return self.__dict__[name]
        except:
            return getattr(self._tab_bar, name)
    
    def minimumSizeHint(self):
        margins = self._main_layout.contentsMargins()
        minimum_size_hint = self._tab_bar.minimumSizeHint()
        
        # Add on any margins to the minimum size hint. The widget from getting sized so that the tab 
        # tops are not cut off.
        if self.shape() in {
                QTabBar.RoundedNorth,
                QTabBar.RoundedSouth,
                QTabBar.TriangularNorth,
                QTabBar.TriangularSouth}:
            return minimum_size_hint + QSize(0, margins.top() + margins.bottom())
        else:
            return minimum_size_hint + QSize(margins.left() + margins.right(), 0)
    
    def setShape(self, shape):
        '''
        Sets the tab shapes.
        
        shape
            One of:
                ExtendedTabBar.RoundedNorth
                ExtendedTabBar.RoundedSouth
                ExtendedTabBar.RoundedWest
                ExtendedTabBar.RoundedEast
                ExtendedTabBar.TriangularNorth
                ExtendedTabBar.TriangularSouth
                ExtendedTabBar.TriangularWest
                ExtendedTabBar.TriangularEast
        '''
        self._tab_bar.setShape(shape)
        
        if shape in {
                QTabBar.RoundedNorth,
                QTabBar.RoundedSouth,
                QTabBar.TriangularNorth,
                QTabBar.TriangularSouth}:
            direction = QBoxLayout.LeftToRight
            orientation = Qt.Horizontal
        else:
            direction = QBoxLayout.TopToBottom
            orientation = Qt.Vertical
            
        self._main_layout.setDirection(direction)
        self._left_toolbar.setOrientation(orientation)
        self._floating_toolbar.setOrientation(orientation)
        self._right_toolbar.setOrientation(orientation)
    
    @property
    def left_toolbar(self):
        '''
        Returns the QToolBar to the left (top) of the tabs.
        '''
        return self._left_toolbar
        
    @property
    def floating_toolbar(self):
        '''
        Returns the QToolBar floating to the right (bottom) of the tabs.
        '''
        return self._floating_toolbar
        
    @property
    def right_toolbar(self):
        '''
        Returns the QToolBar to the right (bottom) of the tabs.
        '''
        return self._right_toolbar
        
class ExtendedTabWidget(QFrame):
    '''
    Like QTabWidget, except the tab bar is located elsewhere. Intended for use with ExtendedTabBar.
    '''
    def __init__(self):
        super(ExtendedTabWidget, self).__init__()
        
        self._tab_bar = None
        self._stack = QStackedWidget()
        
        self._main_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addWidget(self._stack)
        self.setLayout(self._main_layout)
    
    def setCurrentIndex(self, index):
        '''
        Sets the current tab to the specified index.
        '''
        self._stack.setCurrentIndex(index)
    
    def setTabBar(self, tab_bar):
        '''
        Sets the tab bar that will be used to switch between tabs.
        
        tab_bar
            The tab bar to set as the controller of this widget.
        '''
        if self._tab_bar is not None:
            raise Exception('Tab bar already set.')
        
        # Connect the new tab bar.
        self._tab_bar = tab_bar
        tab_bar.currentChanged.connect(self.setCurrentIndex)
        tab_bar.tabCloseRequested.connect(self.closeTab)
    
    def closeTab(self, index):
        '''
        Closes a tab, removing from this widget, the tab bar, and deleting its widget.
        
        index
            Index of the tab to be closed.
        '''
        self._tab_bar.removeTab(index)
        
        widget = self._stack.widget(index)
        self._stack.removeWidget(widget)
        
        widget.deleteLater()
    
    def addTab(self, widget, label):
        '''
        Adds a tab.
        
        widget
            The widget for the tab contents.
        
        label
            The name of the tab to show in the tab bar.
        
        Returns the index of the added tab.
        '''
        index = self._tab_bar.addTab(label)
        self._stack.insertWidget(index, widget)
        
        return index
