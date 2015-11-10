#!/usr/bin/env python

import argparse
import glob
import os
import sys
import time

from fnmatch import fnmatch
from subprocess import Popen

import serial

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


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
        script_name = kwargs.pop('script_name')
        write_to_file = kwargs.pop('write_to_file')

        super(TestRunnerEventHandler, self).__init__(*args, **kwargs)

        if not write_to_file:
            ports = serial_ports()
            for port in ports:
                print('Testing port: {}'.format(port))
                arduino = serial.Serial(port, timeout=1)
                time.sleep(2)
                arduino.write('a')
                line = arduino.read(10)
                if line.strip() == 'semaphore':
                    print('Found arduino semaphore at {}'.format(port))
                    break
            else:
                print('Arduino semaphone not found')
                sys.exit(1)
        else:
            arduino = open(write_to_file, 'a')

        self.arduino = arduino
        if len(script_name.split(' ')) == 1:
            self.program = os.path.abspath(script_name)
        else:
            self.program = script_name

        # TODO: check if the program exists
        # TODO: check if the program is executable

    def on_any_event(self, event):
        if event.is_directory:
            return

        ignore_list = ['*.swp', '*.swo', '.git/']
        for ignore_pattern in ignore_list:
            if fnmatch(event.src_path, ignore_pattern):
                return

            if event.src_path.startswith('./' + ignore_pattern):
                return

        print('File changed: {}'.format(event.src_path))

        self.arduino.write('y')

        process = Popen([self.program], shell=True)
        process.wait()
        if process.returncode == 0:
            self.arduino.write('g')
        else:
            self.arduino.write('r')

        # Needed mainly because of test file
        #   (check write_to_file argument)
        self.arduino.flush()


def main_loop():

    parser = argparse.ArgumentParser(description=(
        'Watch for changes in the target directory and control the '
        ' arduino traffic light.'
    ))
    parser.add_argument('--target', help='The target directory to be watched.',
                        default='.')
    parser.add_argument('--write-to-file', default=None, help=(
        'Write to given file instead of serial port. '
        'Mainly used for test and debugging.'
    ))
    parser.add_argument('command', help='The command to be executed')

    args = parser.parse_args()

    observer = Observer()
    handler = TestRunnerEventHandler(script_name=args.command,
                                     write_to_file=args.write_to_file)
    observer.schedule(handler, args.target, recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
        handler.arduino.close()

    observer.join()


if __name__ == '__main__':
    main_loop()
