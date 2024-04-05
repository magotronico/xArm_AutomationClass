#!/usr/bin/env python3

"""
Code for xArm and hand tracking to control gripper using a GPIO and OpenCV.
"""

import os
import sys
import time

# Ensure the parent directory of xarm.wrapper is in PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
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

def main():
    ip = get_xarm_ip()
    arm = initialize_arm(ip)

    for _ in range(20):
        if _%2 == 0:
            arm.set_cgpio_digital(0, 1)  # Open the gripper
        else:
            arm.set_cgpio_digital(0, 0)  # Close the gripper
        time.sleep(1)

    arm.disconnect()

if __name__ == '__main__':
    main()
