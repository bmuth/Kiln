import KilnProfiler
import threading
from datetime import datetime, time
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QBrush
from PyQt5.QtCore import Qt, QRect, QSize, QObject, QFile, QIODevice
from picamera import PiCamera
from time import sleep
import paramiko
import scp

ui = None
preview = None
camera = None
x = 0 ; y = 0 ; w = 0 ;h = 0
bClipped = False
ssh = None
old_time = datetime.now()

def IsItTimeForSnap ():
    global old_time
    new_time = datetime.now()
    print ("time: {}".format((new_time - old_time).total_seconds()))
    ui.labTime.setText (datetime.now().strftime('%H:%M:%S'))
    if ((new_time - old_time).total_seconds() >= 15):
        TimeForSnap()
        old_time = new_time

def TimeForSnap ():
    global camera, ssh
    global bClipped
    if bClipped == False:
        return
    now = datetime.now()
    print (now)
    camera.capture ('snap.gif', use_video_port=True)
    ui.labImage.load ('snap.gif')
    orig_size = ui.labImage.myPixmap.size()
    pix = ui.labImage.myPixmap
    print ("orig image={0}, subimage={1},{2},{3},{4}".format(orig_size, x, y, w, h))
    clippedPixmap = pix.copy (x, y, w, h)
    filename = 'K' + now.strftime ("%Y-%m-%d %H.%M.%S") + ".png"
    file = QFile (filename) 
    #with QFile (filename) as file:
    file.open(QIODevice.WriteOnly)
    clippedPixmap.save(file, "PNG")
    file.close()
    file = None

    try:
        sc = None
        sc = scp.SCPClient (ssh.get_transport())
        sc.put(filename)
    except Exception as e:
        print (str(e))
        ui.labMsg.setText(str(e))            
    finally:
        if sc != None:
            sc.close()

    ui.labMsg.setText (filename)
    print ("scaling clipped image to {}".format (ui.labImage.PicSize))
    newpixmap = clippedPixmap.scaled (ui.labImage.PicSize, Qt.KeepAspectRatio)
    ui.labClippedImage.setPixmap (newpixmap)


class PreviewThread(threading.Thread):
    def __init__ (self):
        threading.Thread.__init__ (self)
        self.camera = None
        
    def run (self):
        if self.camera == None:
            self.camera = PiCamera()
        self.camera.resolution = (2592, 1944)
        self.camera.rotation = 270
        self.camera.start_preview(fullscreen=False, window=(ui.labImage.x(), ui.labImage.y(), ui.labImage.width(), ui.labImage.height()))

    def stop (self):
        if self.camera != None:
            self.camera.stop_preview()
            self.camera.close()
            self.camera = None
	
def onRun (checked):
    global camera, ssh
    if (checked):
        if camera == None:
            camera = PiCamera()
            camera.resolution = (2592, 1944)
            camera.rotation = 270
            camera.start_preview(fullscreen=False, window=(ui.labImage.x(), ui.labImage.y(), ui.labImage.width(), ui.labImage.height()))
    
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            key = paramiko.RSAKey.from_private_key_file ("Brian_rsa")
            ssh.connect ('192.168.2.27', username = 'brian', pkey = key)
        except Exception as e:
            print (str(e))
            ui.labMsg.setText(str(e))            

        TimeForSnap ()
        ui.timer.start (1000)
    else:
        ssh.close ()
        ssh = None
        ui.timer.stop()
        camera.stop_preview()
        camera.close()
        camera = None


def onExit (checked):
    global preview, camera, ssh
    if preview is not None:
        if preview.is_alive():
            preview.stop()
            preview.join()
    ui.timer.stop()
    if camera != None:
        camera.stop_preview()
        camera.close()
        camera = None     
    if ssh != None:
        ssh.close()
        ssh = None

    QtCore.QCoreApplication.instance().quit()

def onPreview(checked):
	global preview
	if (checked):
		preview = PreviewThread()
		preview.start()
	else:
		preview.stop()
		preview.join()

def onSnap(checked):
    with PiCamera() as camera:
        camera.resolution = (2592, 1944)
        camera.rotation = 270
        camera.start_preview(fullscreen=False, window=(ui.labImage.x(), ui.labImage.y(), ui.labImage.width(), ui.labImage.height()))
        sleep (2)
        camera.capture ('snap.gif', use_video_port=True)
        camera.close()       
        ui.labImage.load ('snap.gif')
 
def ShowClippedRegion (offset, fullsize, smallrect, pixmap):
    global x,y,w,h,bClipped
    print ('smallrect: {} bigmap: {} pixmap:{}'.format (smallrect.size(), fullsize, pixmap.size()))
    x = (smallrect.x () - offset.x ()) * pixmap.width () // fullsize.width ()
    y = (smallrect.y ()  - offset.y ()) * pixmap.height () // fullsize.height ()
    w = smallrect.width () * pixmap.width () // fullsize.width ()
    h = smallrect.height () * pixmap.height () // fullsize.height ()

    print ("pixmap size={}".format (pixmap.size()))
    print ("clipping from {},{},{},{}".format (x,y,w,h))
    clippedpixmap = pixmap.copy (x, y, w, h)
    newpixmap = clippedpixmap.scaled (fullsize, Qt.KeepAspectRatio)
    ui.labClippedImage.setPixmap (newpixmap)
    print (x, y, w, h)
    bClipped = True
    #print (ui.size())
    #ui.setFixedSize (ui.size ())

class MyDialog (KilnProfiler.Ui_Dialog):
    def __init__(self):
        KilnProfiler.Ui_Dialog.__init__(self)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect (IsItTimeForSnap)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = MyDialog()
    print (ui.__class__.__name__)
    ui.setupUi(Dialog)

    label = ui.labImage
    label.ClippedRegionDefined.connect (ShowClippedRegion)
    
    ui.btnPreview.clicked.connect (onPreview)
    ui.btnSnap.clicked.connect (onSnap)
    ui.btnExit.clicked.connect (onExit)
    ui.btnRun.clicked.connect (onRun)

    Dialog.show()
    app.exec_()