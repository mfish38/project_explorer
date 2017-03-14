'''
Copyright (c) 2017 Mark Fisher
Licensed under the MIT License, see LICENSE in the project root for full license.

This module implements icons drawn from fonts.
'''

import sys

from PySide.QtCore import Qt, QRect, QPoint
from PySide.QtGui import QIconEngine, QIcon, QFont, QImage, qRgba, QPixmap, QPainter

class _FontIconEngine(QIconEngine):
    '''
    Icon engine for rendering icon fonts.
    '''
    def __init__(self, font, text):
        '''
        Parameters:
            - font
                The font to use.
                
            - text
                The text from the font to draw. This can be either a ligature, or a hex value
                escaped like so: "\uFFFF" 
        '''
        super(_FontIconEngine, self).__init__()
        
        self.font = QFont(font)
        self.text = text

    def pixmap(self, size, mode, state):
        '''
        Reimplemented to add alpha channel.
        
        Based on: http://stackoverflow.com/a/27616115
        '''
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(qRgba(0, 0, 0, 0))
        
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)
        
        painter = QPainter(pixmap)
        
        rectangle = QRect(QPoint(0.0, 0.0), size)
        
        self.paint(painter, rectangle, mode, state)
        
        return pixmap
        
    def paint(self, painter, rectangle, mode, state):
        '''
        Draw the font.
        '''
        painter.save()
        
        font = self.font
        font.setPixelSize(rectangle.width())
        painter.setFont(font)
        
        painter.drawText(rectangle, Qt.AlignCenter, self.text)
        
        painter.restore()
        
class FontIcon(QIcon):
    '''
    A font based icon.
    '''
    def __init__(self, font, text):
        '''
        Parameters:
            - font
                The font to use.
                
            - text
                The text from the font to draw. This can be either a ligature, or a hex value
                escaped like so: "\uFFFF" 
        '''
        engine = _FontIconEngine(font, text)
        
        super(FontIcon, self).__init__(engine)
