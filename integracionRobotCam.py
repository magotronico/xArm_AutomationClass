#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2024, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

"""
# Notice
#   1. Changes to this file on Studio will not be preserved
#   2. The next conversion will overwrite the file with the same name
"""
import socket
import os
import sys
import math
import time
import datetime
import random
import traceback
import threading

"""
# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
# git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
# cd xArm-Python-SDK
# python setup.py install
"""
try:
    from xarm.tools import utils
except:
    pass
from xarm import version
from xarm.wrapper import XArmAPI

def pprint(*args, **kwargs):
    try:
        stack_tuple = traceback.extract_stack(limit=2)[0]
        print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
    except:
        print(*args, **kwargs)

pprint('xArm-Python-SDK Version:{}'.format(version.__version__))

""" Init xArm Object """
arm = XArmAPI('192.168.1.208')
arm.clean_warn()
arm.clean_error()
arm.motion_enable(True)
arm.set_mode(0)
arm.set_state(0)
time.sleep(1)

variables = {'height': 0, 'max_cubes': 0, 'COUNTER': 0}
params = {'speed': 100, 'acc': 2000, 'angle_speed': 20, 'angle_acc': 500, 'events': {}, 'variables': variables, 'callback_in_thread': True, 'quit': False}

""" Camara info """
HOST = "192.168.1.130"  # The server's hostname or IP address
PORT = 20000  # The port used by the server

# Register error/warn changed callback
def error_warn_change_callback(data):
    if data and data['error_code'] != 0:
        params['quit'] = True
        pprint('err={}, quit'.format(data['error_code']))
        arm.release_error_warn_changed_callback(error_warn_change_callback)
arm.register_error_warn_changed_callback(error_warn_change_callback)


# Register state changed callback
def state_changed_callback(data):
    if data and data['state'] == 4:
        if arm.version_number[0] > 1 or (arm.version_number[0] == 1 and arm.version_number[1] > 1):
            params['quit'] = True
            pprint('state=4, quit')
            arm.release_state_changed_callback(state_changed_callback)
arm.register_state_changed_callback(state_changed_callback)

# Function to request the pose from the camera
def rqst_pose(arm):
    arm.set_cgpio_digital(1, 1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(None)  # Disable the timeout
        s.connect((HOST, PORT))
        s.sendall(b"cmd Online")
        s.sendall(b"cmd trigger")
        data = s.recv(24) #IMPORTANTE REVISAR EL TAMAÑO DEL STRING QUE SE ENVÍA PARA SELECCIONAR LOS BITES ADECUADOS 

    print(f"Received2 {data!r}")

    str1 = data.decode('UTF-8')
    t=str1.split(" ")   #IMPORTANTE REVISAR CUAL ES EL CARACTER USADO PARA DELIMITAR CADA DATO
    x=float(t[0])
    y=float(t[1])
    r=float(t[2])
    arm.set_cgpio_digital(1, 0)

    return x, y, r

# Funciton to convert from pixeceles (cam) to mm (robot)
def pix2mm(x, y):
    if x == 0 and y == 0:
        return 0, 0
    else:
        x_mm = (x - 295) / 4.9715
        y_mm = (y - 235) / 4.9715
    return x_mm, y_mm

# Function to compute new pose with the camera info
def compute_new_pose(arm):
    x,y,r = rqst_pose(arm)
    x_mm, y_mm = pix2mm(x, y)
    print(f"Received: x={x_mm}mm, y={y_mm}mm, r={r} degrees")
    new_x = -463.8 + x_mm
    new_y = 610.1 + y_mm
    new_yaw = 89.9 - r
    print(f"New pose: x={new_x}mm, y={new_y}mm, r={new_yaw} degrees")
    return new_x, new_y, new_yaw

# Register counter value changed callback
if hasattr(arm, 'register_count_changed_callback'):
    def count_changed_callback(data):
        if not params['quit']:
            pprint('counter val: {}'.format(data['count']))
    arm.register_count_changed_callback(count_changed_callback)


# Register connect changed callback
def connect_changed_callback(data):
    if data and not data['connected']:
        params['quit'] = True
        pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
        arm.release_connect_changed_callback(error_warn_change_callback)
arm.register_connect_changed_callback(connect_changed_callback)

# Set initial parameters
if arm.error_code == 0 and not params['quit']:
    code = arm.set_tgpio_digital(0, 0, delay_sec=0)
    if code != 0:
        params['quit'] = True
        pprint('set_tgpio_digital, code={}'.format(code))
if not params['quit']:
    params['speed'] = 400
if not params['quit']:
    params['acc'] = 300
if not params['quit']:
    params['angle_speed'] = 70
if not params['quit']:
    params['angle_acc'] = 500
if arm.error_code == 0 and not params['quit']:
    arm.set_pause_time(0.5)
if not params['quit']:
    params['variables']['COUNTER'] = 0
if not params['quit']:
    params['variables']['max_cubes'] = 3
if not params['quit']:
    params['variables']['height'] = 48

# Main loop
while True:
    if params['quit']:
        break
    if arm.get_cgpio_digital(6)[1]:
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_cgpio_digital(0, 0, delay_sec=0)
            if code != 0:
                params['quit'] = True
                pprint('set_cgpio_digital, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_servo_angle(angle=[0.0, -70.0, -20.0, 0.0, 90.0, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
            if code != 0:
                params['quit'] = True
                pprint('set_servo_angle, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_servo_angle(angle=[102.5, -22.7, -79.1, 0.0, 102.0, 14.3], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
            if code != 0:
                params['quit'] = True
                pprint('set_servo_angle, code={}'.format(code))
        if not params['quit']:
            """" Time to wait for the robot to reach the position"""
            time.sleep(2)
            new_x, new_y, new_yaw = compute_new_pose(arm)
            time.sleep(2)
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_position(*[-463.8, 610.1, 39.4, 180.0, 0.2, 89.9], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True)
            if code != 0:
                params['quit'] = True
                pprint('set_position, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            print(f"will be sent to: x={new_x}mm, y={new_y}mm, r={new_yaw} degrees")
            code = arm.set_position(*[new_x, new_y, 39.4,180,0.2, new_yaw], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
            if code != 0:
                params['quit'] = True
                pprint('set_position, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_position(*[new_x, new_y, -56.1,180,0.2, new_yaw], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
            if code != 0:
                params['quit'] = True
                pprint('set_position, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_cgpio_digital(0, 1, delay_sec=0)
            if code != 0:
                params['quit'] = True
                pprint('set_cgpio_digital, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_position(*[-466.4, 623.5, 115.8, 180.0, 0.1, 92.2], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True)
            if code != 0:
                params['quit'] = True
                pprint('set_position, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_position(*[-50,(200 + (params['variables'].get('COUNTER', 0) * params['variables'].get('height', 0))),117,-179,1,88], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
            if code != 0:
                params['quit'] = True
                pprint('set_position, code={}'.format(code))
        if params['variables'].get('COUNTER', 0) == params['variables'].get('max_cubes', 0):
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[-69.0, 158.0, -58.8, 179.9, -2.0, 92.5], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_cgpio_digital(0, 0, delay_sec=0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_cgpio_digital, code={}'.format(code))
            if not params['quit']:
                params['variables']['COUNTER'] = 1
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[0.0, -30.7, -38.9, 0.0, 70.0, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[0.0, -70.0, -20.0, 0.0, 90.0, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
        else:
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[-50,(158 + (params['variables'].get('COUNTER', 0) * params['variables'].get('height', 0))),-85,-179,1,88], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_cgpio_digital(0, 0, delay_sec=0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_cgpio_digital, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[-50,(158 + (params['variables'].get('COUNTER', 0) * params['variables'].get('height', 0))),-85,-179,1,88], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[0.0, -70.0, -20.0, 0.0, 90.0, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if not params['quit']:
                params['variables']['COUNTER'] = (params['variables'].get('COUNTER', 0) + 1)

# release all event
if hasattr(arm, 'release_count_changed_callback'):
    arm.release_count_changed_callback(count_changed_callback)
arm.release_error_warn_changed_callback(state_changed_callback)
arm.release_state_changed_callback(state_changed_callback)
arm.release_connect_changed_callback(error_warn_change_callback)
