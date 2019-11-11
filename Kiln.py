import KilnProfiler
import threading
from datetime import datetime, time
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QBrush
from PyQt5.QtCore import Qt, QRect, QSize, QObject, QFile, QIODevice
from picamera import PiCamera
from time import sleep
# import paramiko
# import scp
import os
import socket
import struct

ui = None
preview = None
x = 0 ; y = 0 ; w = 0 ;h = 0
bClipped = False
#ssh = None
camera = None
old_time = datetime.now()
PATH = "/home/pi/Documents/Projects/KilnProfiler"
HOST = '192.168.2.11'
PORT = 65432        # The port used by the server

# def SubmitFile (filename):

#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.connect((host, PORT))
#             with open(filename, "rb") as f:
#                 byte = f.read(4096)
#                 while byte != b"":
#                     sa.send (byte)
#                     byte = f.read(4096)
#                 data = s.recv(1024)
#                 print('Response: [{0}]'.format (data.decode('utf-8')))
#     except ConnectionError as e:
#         msg = "connection error for host {0} {1} {2}".format(host, e.errno, e.strerror)
#         print (msg)
#         raise Exception (msg)

#     except IOError as e:
#         msg = "transmission error on file {0} {1} {2}".format(filename, e.errno, e.strerror)
#         print (msg)
#         raise Exception (msg)

def SubmitFile (orig_filename):
    host = socket.gethostbyname(HOST)

    filename = os.path.join (PATH, orig_filename)

    try:
        fs = int (os.path.getsize(filename))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((host, PORT))
            c = 'F'

            # 1 byte command
            # 4 bytes for file size
            # 100 bytes for file name
            # total 105 bytes to be sent
            data = struct.pack ('=cI100s', c.encode('utf-8'), fs, "{:<100}".format (orig_filename).encode ('utf-8'))
            s.send (data)
            total = 0
            with open(filename, "rb") as f:
                byte = f.read(4096)
                while byte != b"":
                    total += len(byte)
                    s.send (byte)
                    print ("Sent {0} bytes".format (total))
                    byte = f.read(4096)
                data = s.recv(1024)
                print('Response: [{0}]'.format (data.decode('utf-8')))
                return
    except ConnectionError as e:
        msg = "connection error for host {0} {1}".format(host, str(e))
        print (msg)
        raise

    except FileNotFoundError:
        msg = "file {0} not found".format (filename)
        print (msg)
        raise

    except IOError as e:
        msg = "transmission error on file {0} {1}".format(orig_filename, str(e))
        print (msg)
        raise

def IsItTimeForSnap ():
    global old_time
    new_time = datetime.now()
    print ("time: {}".format((new_time - old_time).total_seconds()))
    ui.labTime.setText (datetime.now().strftime('%H:%M:%S'))
    if ((new_time - old_time).total_seconds() >= 120):
        TimeForSnap()
        old_time = new_time

def TimeForSnap ():
    #global camera, ssh
    global camera
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

    # Submit the file
    # ---------------
    # try:
    #     sc = None
    #     sc = scp.SCPClient (ssh.get_transport())
    #     sc.put(filename)
    # except Exception as e:
    #     print (str(e))
    #     ui.labMsg.setText(str(e))            
    # finally:
    #     if sc != None:
    #         sc.close()
    
    temp = ''
    try:
        temp = SubmitFile (filename)
    except Exception as e:
        ui.labMsg.setText (str(e))
    else:
        ui.labMsg.setText (filename)
    print ("temp={0}".format(temp))

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
    #global camera, ssh
    global camera
    if (checked):
        if camera == None:
            camera = PiCamera()
            camera.resolution = (2592, 1944)
            camera.rotation = 270
            camera.start_preview(fullscreen=False, window=(ui.labImage.x(), ui.labImage.y(), ui.labImage.width(), ui.labImage.height()))
    
        # try:
        #     ssh = paramiko.SSHClient()
        #     ssh.load_system_host_keys()
        #     key = paramiko.RSAKey.from_private_key_file ("Brian_rsa")
        #     ssh.connect ('192.168.2.27', username = 'brian', pkey = key)
        # except Exception as e:
        #     print (str(e))
        #     ui.labMsg.setText(str(e))            

        TimeForSnap ()
        ui.timer.start (1000)
    else:
        # ssh.close ()
        # ssh = None
        ui.timer.stop()
        camera.stop_preview()
        camera.close()
        camera = None


def onExit (checked):
    #global preview, camera, ssh
    global preview, camera
    if preview is not None:
        if preview.is_alive():
            preview.stop()
            preview.join()
    ui.timer.stop()
    if camera != None:
        camera.stop_preview()
        camera.close()
        camera = None     
    # if ssh != None:
    #     ssh.close()
    #     ssh = None

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