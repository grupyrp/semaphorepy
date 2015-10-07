#!/usr/bin/env python
import hashlib
import os
import sys
import time
from subprocess import Popen

import serial

program = sys.argv[1]
program = os.path.abspath(program)

arduino_port = '/dev/cu.wchusbserial640' # raw_input('Arduino port: ')

arduino = serial.Serial(arduino_port)
time.sleep(2)


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



