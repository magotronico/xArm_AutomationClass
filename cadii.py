#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2022, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

"""
# Notice
#   1. Changes to this file on Studio will not be preserved
#   2. The next conversion will overwrite the file with the same name
# 
# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
#   1. git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
#   2. cd xArm-Python-SDK
#   3. python setup.py install
"""
import sys
import math
import time
import queue
import datetime
import random
import traceback
import threading
from xarm import version
from xarm.wrapper import XArmAPI
import socket

"""
Para agregar funcionalidad de comunicación por sockets TCP/IP, siga estos pasos:
1. Importe la librería `socket` (import socket).
2. Dentro del método `def _robot_init(self)`, agregue la línea `self._init_socket()`.
3. Copie y pegue el método `def _init_socket(self)` para inicializar el socket.
4. Copie y pegue el método `def recv_data(self)` para recibir datos a través del socket.
5. Dentro del método `def run(self)`, agregue la línea `self.recv_data()` donde quiera empezar a escuchar datos a través del socket.
"""

class RobotMain(object):
    """Robot Main Class"""
    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._tcp_speed = 100
        self._tcp_acc = 2000
        self._angle_speed = 20
        self._angle_acc = 500
        self._vars = {}
        self._funcs = {}
        self._robot_init()

    # Robot init
    def _robot_init(self):
        self._arm.clean_warn()
        self._arm.clean_error()
        self._arm.motion_enable(True)
        self._arm.set_mode(0)
        self._arm.set_state(0)
        time.sleep(1)
        self._arm.register_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.register_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'register_count_changed_callback'):
            self._arm.register_count_changed_callback(self._count_changed_callback)
        self._init_socket()

    def _init_socket(self):
        # Define the server address and port
        self.server_address = ('192.168.1.28', 20000)
        # Create a TCP/IP socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Client created')

    # Register error/warn changed callback
    def _error_warn_changed_callback(self, data):
        if data and data['error_code'] != 0:
            self.alive = False
            self.pprint('err={}, quit'.format(data['error_code']))
            self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)

    # Register state changed callback
    def _state_changed_callback(self, data):
        if data and data['state'] == 4:
            self.alive = False
            self.pprint('state=4, quit')
            self._arm.release_state_changed_callback(self._state_changed_callback)

    # Register count changed callback
    def _count_changed_callback(self, data):
        if self.is_alive:
            self.pprint('counter val: {}'.format(data['count']))

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._arm.get_state()
            ret2 = self._arm.get_err_warn_code()
            self.pprint('{}, code={}, connected={}, state={}, error={}, ret1={}. ret2={}'.format(label, code, self._arm.connected, self._arm.state, self._arm.error_code, ret1, ret2))
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
        except:
            print(*args, **kwargs)

    @property
    def arm(self):
        return self._arm

    @property
    def VARS(self):
        return self._vars

    @property
    def FUNCS(self):
        return self._funcs

    @property
    def is_alive(self):
        if self.alive and self._arm.connected and self._arm.error_code == 0:
            if self._arm.state == 5:
                cnt = 0
                while self._arm.state == 5 and cnt < 5:
                    cnt += 1
                    time.sleep(0.1)
            return self._arm.state < 4
        else:
            return False
    
    def recv_data(self):
        while True:
            try:
                # Connect to the server
                self.client_socket.connect(self.server_address)
                print(f'Connected to server at {self.server_address}')

                # # Send data
                # message = b'This is a test message.'
                # client_socket.sendall(message)
                # print(f'Sent: {message}')

                # Receive response
                data = self.client_socket.recv(1024)
                print(f'Received: {data}')

            finally:
                # Clean up the connection
                self.client_socket.close()
                print('Connection closed')
                break

    # Robot Main Run
    def run(self):
        try:
            self._tcp_speed = 104
            self._tcp_acc = 1000
            self._angle_speed = 19
            self._angle_acc = 200
            for i in range(int(1)):
                if not self.is_alive:
                    break
                t1 = time.monotonic()
                code = self._arm.set_cgpio_digital(5, 0, delay_sec=0)
                if not self._check_code(code, 'set_cgpio_digital'):
                    return
                time.sleep(1)
                code = self._arm.set_cgpio_digital(5, 1, delay_sec=0)
                if not self._check_code(code, 'set_cgpio_digital'):
                    return
                time.sleep(1)
                code = self._arm.set_cgpio_digital(2, 1, delay_sec=0)
                if not self._check_code(code, 'set_cgpio_digital'):
                    return
                time.sleep(1)
                code = self._arm.set_cgpio_digital(2, 0, delay_sec=0)
                if not self._check_code(code, 'set_cgpio_digital'):
                    return
                # Receive data from Raspberry Pi 5
                self.recv_data()

                interval = time.monotonic() - t1
                if interval < 0.01:
                    time.sleep(0.01 - interval)
        except Exception as e:
            self.pprint('MainException: {}'.format(e))
        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)


if __name__ == '__main__':
    RobotMain.pprint('xArm-Python-SDK Version:{}'.format(version.__version__))
    arm = XArmAPI('192.168.1.208', baud_checkset=False)
    robot_main = RobotMain(arm)
    robot_main.run()
