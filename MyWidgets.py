from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal

class MyHighlight(QWidget):

    def __init__(self, parent):
        super(MyHighlight, self).__init__(parent) 
 
    def paintEvent (self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        r = self.geometry ()
        w = r.width()
        qp.fillRect(QRect (0, 0, r.width(), r.height()), QtGui.QBrush(QtGui.QColor(128, 128, 255, 128)));
        qp.end()

class ImageLabel (QLabel):
    ClippedRegionDefined = pyqtSignal(QPoint, QSize, QRect, QtGui.QPixmap)

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)
        #super().__init__()
        self.myPixmap = QtGui.QPixmap()
        self.myPixmap.load ('image7.jpg')
        self.myHighlight = None
    
    def load (self, filename):
        self.myPixmap.load (filename)
        self.myHighlight = None
        self.Resizing (self.size())

    def Resizing(self, size):    
        print("**Resizing {}".format (size))
        newpixmap = self.myPixmap.scaled (size, Qt.KeepAspectRatio)
        
        self.PicSize = newpixmap.size()
        print ("newpixmap rect {}".format(newpixmap.rect()))
        offset = self.size() -self.PicSize
        offset /= 2
        x = offset.width()
        y = offset.height()
 
        self.PicOffset = QPoint (x, y)
        print ("offset={}".format(self.PicOffset))
        print("LabImage size: {}".format(self.size()))
        self.setPixmap(newpixmap)

    def resizeEvent(self, event):
        self.Resizing (event.size())

    def mousePressEvent (self, event):
        print ('down position {}'.format (event.pos()))
        if self.myHighlight is not None:
            self.myHighlight.close ()
        self.myHighlight = MyHighlight(self)
        self.myHighlight.setGeometry (QRect (event.pos(), QSize (0,0)))
        self.myHighlight.show()

    def mouseReleaseEvent (self, event):
        self.Bottom = event.y()
        self.Right = event.x()
        print ('up {} {}'.format (self.Right, self.Bottom))
        print ("{} {}".format (self.size(), self.myHighlight.geometry ()))
        self.SubImageGeometry = self.myHighlight.geometry ()
        self.ClippedRegionDefined.emit (self.PicOffset, self.PicSize, self.myHighlight.geometry(), self.myPixmap)
        self.myHighlight.hide ()

    def mouseMoveEvent (self, event):
        print ('move {}'.format (event.pos()))
        r = self.myHighlight.geometry ()
        r.setBottomRight (event.pos ())
        self.myHighlight.setGeometry (r)

 