#!/usr/bin/env python

import os
import glob
import time
import redis

r = redis.Redis(host='127.0.0.1', port=6379)
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

def _read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
        
def _read_temp():
    lines = _read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = _read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

while True:
    try:
        temp_c, temp_f = _read_temp()
        r.set('temp_c', temp_c)
        r.set('temp_f', temp_f)
        time.sleep(10)
    except Exception, e:
        pass
