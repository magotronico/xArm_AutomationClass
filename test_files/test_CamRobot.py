#!/usr/bin/env python3

"""
Code for xArm and hand tracking to control gripper using a GPIO and OpenCV.
"""

import os
import sys
import socket
import time

HOST = "192.168.1.130"  # The server's hostname or IP address
PORT = 20000  # The port used by the server

# Ensure the parent directory of xarm.wrapper is in PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from numpy import deg2rad
from xarm.wrapper import XArmAPI

def get_xarm_ip():
    """Retrieve the xArm IP from command line arguments or configuration file."""
    if len(sys.argv) >= 2:
        return sys.argv[1]
    try:
        from configparser import ConfigParser
        parser = ConfigParser()
        parser.read(r'C:\Users\dilan\Documents\Github\xArm_AutomationClass\xArm-Python-SDK-master\example\wrapper\robot.conf')
        return parser.get('xArm', 'ip')
    except:
        ip = input('Please input the xArm IP address: ')
        if not ip:
            print('Input error, exit.')
            sys.exit(1)
        return ip

def error_warn_callback(item):
    """Handle error and warning messages from xArm."""
    print(f'ErrorCode: {item["error_code"]}, WarnCode: {item["warn_code"]}')

def initialize_arm(ip):
    """Initialize and connect to the xArm."""
    arm = XArmAPI(ip, do_not_open=True)
    arm.register_error_warn_changed_callback(error_warn_callback)
    arm.connect()
    arm.motion_enable(enable=True)
    arm.set_mode(0)  # Position control mode
    arm.set_state(state=0)  # Sport state
    return arm

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
        x_mm = (x - 295) / 4.9029
        y_mm = (y - 235) / 4.9029
    return x_mm, y_mm

def compute_new_pose(arm):
    x,y,r = rqst_pose(arm)
    x_mm, y_mm = pix2mm(x, y)
    print(f"Received: x={x_mm}mm, y={y_mm}mm, r={r} degrees")

    return 463.8 + x_mm, 623.5 + y_mm, 89.9 + r

def main():
    ip = get_xarm_ip()
    arm = initialize_arm(ip)

    try:
        while True:
            # Assuming rqst_pose returns a boolean indicating whether to continue
            x,y,r = rqst_pose(arm)
            x_mm, y_mm = pix2mm(x, y)

            print(f"Received: x={x_mm}mm, y={y_mm}mm, r={r} degrees")

            time.sleep(2)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        arm.disconnect()

if __name__ == '__main__':
    main()