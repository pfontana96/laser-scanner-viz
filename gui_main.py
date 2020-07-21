import numpy as np

from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
matplotlib.use("GTKAgg")

from threading import Thread, Lock, current_thread
from queue import Queue
import serial
import time

done = False
points = Queue()


def readSerial():
    global done
    
    ser = serial.Serial(
            port='COM3',\
            baudrate=9600,\
            parity=serial.PARITY_NONE,\
            stopbits=serial.STOPBITS_ONE,\
            bytesize=serial.EIGHTBITS,\
            timeout=0.01)

    print("Connected to serial port")

    while not done:
        cc=str(ser.readline())
        msg = cc[2:][:-5]
        if msg is not "":
            try:
                print(msg)
                unpacked = msg[1:].split('#')
                print(unpacked)
                points.put((int(unpacked[0]), int(unpacked[1]), int(unpacked[2])))
            except (ValueError, IndexError) as e:
                continue
        time.sleep(0.01)

def main():
    global done
    serial_thread = Thread(target=readSerial, name="serial_thread", daemon=True)
    serial_thread.start()

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    fig.show()

    while not done:
        try:
            x, y, z = points.get()
            # print(f"x:{x} y:{y} z:{z}")
            plt.pause(0.2)
            ax.scatter(x, y, z)
            plt.draw()
        except KeyboardInterrupt:
            done = True
            
if __name__ == "__main__":
    main()