#!/usr/bin/env python

import glob
import hashlib
import os
import sys
import time
from subprocess import Popen

import serial

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


def main_loop():

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
        md5 = None
        last_md5 = None

    while True:
        time.sleep(0.5)

        with open(program) as f:
            md5 = hashlib.md5(f.read()).hexdigest()

        if md5 == last_md5:
            continue

        arduino.write('y')
        last_md5 = md5
        try:
            process = Popen([program])
            process.wait()
            if process.returncode == 0:
                arduino.write('g')
            else:
                arduino.write('r')

        except KeyboardInterrupt:
            sys.exit()

    arduino.close()


if __name__ == '__main__':
    main_loop()
