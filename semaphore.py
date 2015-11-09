#!/usr/bin/env python

import glob
import os
import sys
import time
from subprocess import Popen

import serial

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


program = sys.argv[1]
program = os.path.abspath(program)


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class TestRunnerEventHandler(FileSystemEventHandler):

    def __init__(self, *args, **kwargs):
        super(TestRunnerEventHandler, self).__init__(*args, **kwargs)

        ports = serial_ports()
        for port in ports:
            print 'Testing port', port
            arduino = serial.Serial(port, timeout=1)
            time.sleep(2)
            arduino.write('a')
            line = arduino.read(10)
            if line.strip() == 'semaphore':
                print 'Found arduino semaphore at', port
                break
        else:
            print 'Arduino semaphone not found'
            sys.exit(1)

        self.arduino = arduino

    def on_any_event(self, event):
        self.arduino.write('y')

        process = Popen([program])
        process.wait()
        if process.returncode == 0:
            self.arduino.write('g')
        else:
            self.arduino.write('r')


def main_loop():

    observer = Observer()
    handler = TestRunnerEventHandler()
    observer.schedule(handler, 'test/')

    observer.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
        handler.close()

    observer.join()


if __name__ == '__main__':
    main_loop()
