#!/usr/bin/env python
"""
Full integration of Robot (xArm), PC (python, SDK and Snap7), PLC (S7-1200) and HMI (KTP700 Basic)
"""

# Import Libraries
import snap7
import socket
import time
import traceback
import functools
try:
    from xarm.tools import utils
except:
    pass
from xarm import version
from xarm.wrapper import XArmAPI

# Define Functions
# Print with timestamp and file name
def pprint(*args, **kwargs):
    try:
        stack_tuple = traceback.extract_stack(limit=2)[0]
        print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
    except:
        print(*args, **kwargs)

# Init PLC Object
def init_plc():
    plc = snap7.client.Client()
    plc.connect('192.168.1.1', 0, 1)
    print(plc.get_cpu_state())
    return plc

# Register error/warn changed callback for robot
def error_warn_change_callback(data,arm,params):
    if data and data['error_code'] != 0:
        params['quit'] = True
        pprint('err={}, quit'.format(data['error_code']))
        arm.release_error_warn_changed_callback(error_warn_change_callback)

# Register counter value changed callback
def count_changed_callback(data, params):
    if not params['quit']:
        pprint('counter val: {}'.format(data['count']))

# Register state changed callback for robot
def state_changed_callback(data,arm,params):
    if data and data['state'] == 4:
        if arm.version_number[0] > 1 or (arm.version_number[0] == 1 and arm.version_number[1] > 1):
            params['quit'] = True
            pprint('state=4, quit')
            arm.release_state_changed_callback(state_changed_callback)

# Register connect changed callback
def connect_changed_callback(data, arm, params):
    if data and not data['connected']:
        params['quit'] = True
        pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
        arm.release_connect_changed_callback(error_warn_change_callback)

# Init xArm Object
def init_robot():
    """ Init xArm Object """
    arm = XArmAPI('192.168.1.208')
    arm.clean_warn()
    arm.clean_error()
    arm.motion_enable(True)
    arm.set_mode(0)
    arm.set_state(0)
    time.sleep(1)
    
    # Set initial variables
    variables = {'counterScrap': 0, 'isScrap': 0, 'max_cubes': 0, 'height': 0, 'counterPz': 0}
    params = {'speed': 150, 'acc': 2000, 'angle_speed': 20, 'angle_acc': 500, 'events': {}, 'variables': variables, 'callback_in_thread': True, 'quit': False}

    # Register callbacks
    partialfunc = functools.partial(error_warn_change_callback,arm, params)
    arm.register_error_warn_changed_callback(partialfunc)
    partialfunc = functools.partial(state_changed_callback,arm, params)
    arm.register_state_changed_callback(partialfunc)
    partialfunc = functools.partial(count_changed_callback, params)
    arm.register_count_changed_callback(partialfunc)
    partialfunc = functools.partial(connect_changed_callback, arm, params)
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
        params['variables']['counterPz'] = 0
    if not params['quit']:
        params['variables']['counterScrap'] = 0
    if not params['quit']:
        params['variables']['max_cubes'] = 3
    if not params['quit']:
        params['variables']['height'] = 55
    if not params['quit']:
        params['variables']['isScrap'] = 1

    return arm, params

# Init camera info
def init_camera():
    """ Camara info """
    HOST = "192.168.1.130"  # The server's hostname or IP address
    PORT = 20000  # The port used by the server

    return HOST, PORT

# Function to request the pose from the camera
def rqst_pose(arm, HOST, PORT):
    arm.set_cgpio_digital(2, 1)

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
def compute_new_pose(arm, HOST, PORT):
    print("requested pose")
    x,y,r = rqst_pose(arm, HOST, PORT)
    print("requested pose")
    x_mm, y_mm = pix2mm(x, y)
    print(f"Received: x={x_mm}mm, y={y_mm}mm, r={r} degrees")
    new_x = -72.2 - x_mm
    new_y = 325.9 + y_mm
    new_yaw = -0.2 - r
    print(f"New pose: x={new_x}mm, y={new_y}mm, r={new_yaw} degrees")
    return new_x, new_y, new_yaw

def robotRoutine(arm, params, HOST, PORT):
    if params['quit']:
        return
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
        time.sleep(1)
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[-55.1, 399.5, 14.0, 180.0, 0.2, 88.2], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[-55.1,399.5,14,180,0.2,88.2], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[-55.1,399.5,-50,180,0.2,88.2], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_cgpio_digital(0, 1, delay_sec=0)
        if code != 0:
            params['quit'] = True
            pprint('set_cgpio_digital, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[-55.1, 399.5, 14.0, 180.0, 0.2, 88.2], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_position(*[284,(0 + (params['variables'].get('counterPz', 0) * params['variables'].get('height', 0))),30,180,0,0], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
        if code != 0:
            params['quit'] = True
            pprint('set_position, code={}'.format(code))
    if params['variables'].get('isScrap', 0) == 0:
        if params['variables'].get('counterPz', 0) == params['variables'].get('max_cubes', 0):
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[284.0, -80.0, -85.0, 179.9, 0.0, 0.0], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_cgpio_digital(0, 0, delay_sec=0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_cgpio_digital, code={}'.format(code))
            if not params['quit']:
                params['variables']['counterPz'] = 1
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
                code = arm.set_position(*[260,(-80 + (params['variables'].get('counterPz', 0) * params['variables'].get('height', 0))),-85,180,0,0], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_cgpio_digital(0, 0, delay_sec=0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_cgpio_digital, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[260,(-80 + (params['variables'].get('counterPz', 0) * params['variables'].get('height', 0))),-85,180,0,0], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[0.0, -70.0, -20.0, 0.0, 90.0, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if not params['quit']:
                params['variables']['counterPz'] = (params['variables'].get('counterPz', 0) + 1)
    else:
        if params['variables'].get('counterScrap', 0) == params['variables'].get('max_cubes', 0):
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[230.0, -80.0, -85.0, 179.9, 0.0, 0.0], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_cgpio_digital(0, 0, delay_sec=0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_cgpio_digital, code={}'.format(code))
            if not params['quit']:
                params['variables']['counterScrap'] = 1
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
                code = arm.set_position(*[340,(-80 + (params['variables'].get('counterScrap', 0) * params['variables'].get('height', 0))),-85,180,0,0], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_cgpio_digital(0, 0, delay_sec=0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_cgpio_digital, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[340,(-80 + (params['variables'].get('counterScrap', 0) * params['variables'].get('height', 0))),-85,180,0,0], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_servo_angle(angle=[0.0, -70.0, -20.0, 0.0, 90.0, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
                if code != 0:
                    params['quit'] = True
                    pprint('set_servo_angle, code={}'.format(code))
            if not params['quit']:
                params['variables']['counterScrap'] = (params['variables'].get('counterScrap', 0) + 1)

def main():
    pprint('xArm-Python-SDK Version:{}'.format(version.__version__))
    arm, params = init_robot()
    plc = init_plc()
    HOST, PORT = init_camera()

    # To modify the value of params isScrap variable:   params['variables'].get('isScrap', 0)
    # Start the robot routine
    while True:
        sensor = True
        stopEmergency = False

        if params['quit'] or stopEmergency:
            break
        elif sensor:
            robotRoutine(arm, params, HOST, PORT)
        else:
            pass


    # Disconnect the robot
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)
    arm.release_error_warn_changed_callback(state_changed_callback)
    arm.release_state_changed_callback(state_changed_callback)
    arm.release_connect_changed_callback(error_warn_change_callback)

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("Program stopped by user")
        
    except Exception as e:
        print('Program sttoped due to an error.\nException:', e)