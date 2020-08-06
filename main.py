from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np

import serial
from serial.tools.list_ports import comports
from serial.serialutil import SerialException
import time
from colour import Color

class SerialThread(pg.QtCore.QThread):
    # ser = serial.Serial(
    #         port='COM3',\
    #         baudrate=9600,\
    #         parity=serial.PARITY_NONE,\
    #         stopbits=serial.STOPBITS_ONE,\
    #         bytesize=serial.EIGHTBITS,\
    #         timeout=0.01)
    newData = pg.QtCore.Signal(object)

    def __init__(self, ser):

        super().__init__()
        self.ser = ser   
        self.done = False

    def run(self):

        pcd = np.array([]).reshape(-1,3)
        nb_max = 20

        it = 0

        while not self.done:
            # pcd = np.append(pcd, np.random.rand(1,3)*100, axis=0)
            # if len(pcd[:,0]) is nb_max:
            #     print("entered")
            #     self.newData.emit(pcd)
            #     pcd = np.array([]).reshape(-1,3)
            #     it+=1
            # if it == 200:
            #     break

            msg = self.ser.readline().decode('utf-8')
            # print(msg)
            if msg is not "":
                try:
                    unpacked = [int(s) for s in msg[1:].split('#')]
                    print(unpacked)
                    if len(unpacked) == 3: 
                        pcd = np.append(pcd, np.array(unpacked).reshape(-1,3), axis=0)
                    if pcd[:,0].size is nb_max:
                        print("entered")
                        self.newData.emit(pcd)
                        pcd = np.array([]).reshape(-1,3)
                        it+=1
                    if it == 200:
                        break

                    time.sleep(0.01)
                except (ValueError, IndexError) as e:
                    continue

class MyWidget(pg.GraphicsWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.glvw = gl.GLViewWidget()
        # self.plt3d_item = gl.GLScatterPlotItem(size = 5, pxMode=True)

        self.axis = gl.GLAxisItem()
        self.axis.setSize(x = 50, y = 50, z = 50)

        self.grid = gl.GLGridItem()
        self.grid.setSize(x = 300, y=300)

        # self.glvw.addItem(self.plt3d_item)
        self.glvw.addItem(self.axis)
        self.glvw.addItem(self.grid)

        self.serial_button = QtGui.QPushButton('Connect', self.glvw)
        self.serial_button.setCheckable(True)
        self.serial_button.clicked.connect(self.onClickConnect)

        self.start_button = QtGui.QPushButton('Start', self.glvw)
        self.start_button.move(80,0)
        self.start_button.setCheckable(True)
        self.start_button.clicked.connect(self.onClickStart)
        self.start_button.setEnabled(False)

        self.mainLayout = QtGui.QGridLayout()
        self.setLayout(self.mainLayout)

        self.mainLayout.addWidget(self.glvw, 0, 0)

        self.glvw.sizeHint = lambda: pg.QtCore.QSize(100, 100)

        rgb = np.array([x.rgb for x in list(Color("red").range_to(Color("green"), 100))])
        self.colors = np.concatenate((rgb, np.ones((len(rgb[:, 0]), 1), dtype=float)), axis=1)

        self.ser = None
        self.serial_thread = None
        # self.serial_thread = SerialThread(1)
        # self.serial_thread.newData.connect(self.update)
        # self.serial_thread.finished.connect(self.onSerialThreadFinished)


    def update(self, data):
        # self.plt3d_item.setData(pos=data, color=self.colors[data[:,2].astype(int)])
        plot_item = gl.GLScatterPlotItem(pos = data, color=self.colors[data[:,2].astype(int)], size = 5, pxMode = True)
        self.glvw.addItem(plot_item)

    # @QtCore.pyqtSlot()
    # def onSerialThreadFinished(self):
    #     # We reinitialise the thread
    #     print("thread exited")
    #     self.serial_thread = SerialThread(1)
    #     self.serial_thread.newData.connect(self.update)
    #     self.serial_thread.finished.connect(self.onSerialThreadFinished)

    @QtCore.pyqtSlot()
    def onClickConnect(self):
        if self.serial_button.isChecked():

            win = QtWidgets.QDialog(self)
            win.setWindowTitle("Serial connection")
            win.setMinimumSize(80, 50)
            win.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                 QtWidgets.QSizePolicy.MinimumExpanding))
            label = QtWidgets.QLabel(win)
            label.setText('Select COM port: ')
            label.move(20,10)

            com_ports_list = list(comports())
            ports = QtWidgets.QComboBox(win)
            self.selected_port = None
            for port in com_ports_list:
                ports.addItem(port.device + " - " + port.description)
            ports.currentIndexChanged[str].connect(self.onCOMPortChanged)
            ports.move(110, 8)

            button = QtWidgets.QPushButton('Connect', win)
            button.move(60, 50)
            button.clicked.connect(lambda: self.onClickConnectCOMPort(win))

            self.onCOMPortChanged(ports.currentText())
            win.show()

            # self.showPopUp()
        else:
            # We're connected to the scanner and we want to end connection
            if self.serial_thread is not None:
                self.serial_thread.done = True
            self.serial_button.setText('Connect')
            if self.start_button.isChecked():
                self.start_button.click()
            self.start_button.setEnabled(False)

    @QtCore.pyqtSlot()
    def onClickConnectCOMPort(self, win):
        if self.selected_port is not None:
            try:
                self.ser = serial.Serial(   port=self.selected_port,\
                                            baudrate=9600,\
                                            parity=serial.PARITY_NONE,\
                                            stopbits=serial.STOPBITS_ONE,\
                                            bytesize=serial.EIGHTBITS,\
                                            timeout=0.01)

                # We're not connected to the scanner
                self.serial_thread = SerialThread(self.ser)
                self.serial_thread.newData.connect(self.update) 
                self.serial_button.setText('Disconnect')
                self.start_button.setEnabled(True)

            except SerialException:
                self.serial_button.click()
                self.showPopUp()
        else:
            self.serial_button.click()
            self.showPopUp()
        win.close()


    @QtCore.pyqtSlot()
    def onCOMPortChanged(self, index):
        if len(index.split()):
            self.selected_port = index.split()[0]
        # print(index.split()[0])

    @QtCore.pyqtSlot()
    def onClickStart(self):
        """
            Send start and pause condition to scanner
        """
        if self.start_button.isChecked():
            self.start_button.setText('Pause')
            self.serial_thread.start()
            self.ser.write(str.encode('s')) # Sending start condition
        else:
            self.start_button.setText('Start')

    def showPopUp(self):
        win = QtWidgets.QMessageBox()
        win.setWindowTitle('Warning')
        win.setText('Could not establish a connection')
        win.setIcon(QtWidgets.QMessageBox.Critical)
        win.setStandardButtons(QtWidgets.QMessageBox.Ok)
        win.exec_()

def main():
    app = QtWidgets.QApplication([])

    pg.setConfigOptions(antialias=False) # True seems to work as well

    win = MyWidget()
    win.show()
    win.resize(800,600) 
    win.raise_()

    # thread = SerialThread(1)
    # thread.newData.connect(win.update)
    # thread.start()

    app.exec_()

if __name__ == "__main__":
    main()