#!/usr/bin/env python3

"""
Code for xArm and hand tracking to control gripper using a GPIO and OpenCV.
"""

import os
import sys
import time
import cv2
import mediapipe as mp

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
        parser.read(r'C:\Users\dilan\Documents\Github\xArm_AutomationClass\xArm-Python-SDK\example\wrapper\robot.conf')
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

def control_gripper(arm, hand):
    """Control the xArm gripper based on the pinky position."""
    pinky_tip = hand.landmark[20]
    pinky_base = hand.landmark[18]
    if pinky_tip.y < pinky_base.y:
        arm.set_cgpio_digital(0, 0)  # Close the gripper
    elif pinky_tip.y > pinky_base.y:
        arm.set_cgpio_digital(0, 1)  # Open the gripper

def finger_position(hand, finger_tip_index, finger_pip_index):
    """Check if a finger is up or down based on the positions of its tip and PIP joint."""
    finger_tip = hand.landmark[finger_tip_index]
    finger_pip = hand.landmark[finger_pip_index]
    return finger_tip.y > finger_pip.y  # Finger is considered up if tip is above PIP

def adjust_arm_position(arm, index_up, middle_up):
    """Adjust the xArm's Z position based on the fingers' positions."""
    # Get the current position of the arm
    current_position = arm.get_position()

    # Create a copy of the tuple
    new_position = tuple(current_position)
    print(new_position)

    if index_up and not middle_up:
        # Move arm +Z
        new_position = (new_position[1][0], new_position[1][1], new_position[1][2] + 10)  # Increase the z-coordinate by 10
        arm.set_position(new_position)
    elif index_up and middle_up:
        # Move arm -Z
        new_position = (new_position[1][0], new_position[1][1], new_position[1][2] - 10)  # Decrease the z-coordinate by 10
        arm.set_position(new_position)

def control_gripper_and_arm_position(arm, hand):
    """Control the xArm gripper and adjust arm position based on finger positions."""
    # Check positions of index, middle, and pinky fingers
    index_up = finger_position(hand, 8, 6)  # Index finger tip and PIP joint indices
    middle_up = finger_position(hand, 12, 10)  # Middle finger tip and PIP joint indices
    pinky_up = finger_position(hand, 20, 18)  # Pinky finger tip and PIP joint indices

    # Control gripper based on pinky position
    if pinky_up:
        arm.set_cgpio_digital(0, 1)  # Open the gripper
    else:
        arm.set_cgpio_digital(0, 0)  # Close the gripper
    
    # Adjust arm position based on index and middle finger positions
    adjust_arm_position(arm, index_up, middle_up)

def main():
    ip = get_xarm_ip()
    arm = initialize_arm(ip)

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    cap = cv2.VideoCapture(0)

    with mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks is not None:
                for hand in results.multi_hand_landmarks:
                #### This part is to show all hand landmarks and connections
                #     mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS,
                #                               mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                #                               mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2))
                    
                    #### This part is to show only the pinky landmarks and connection
                    landmarks_to_draw = [hand.landmark[18], hand.landmark[20]]
                    
                    for landmark in landmarks_to_draw:
                        # Convert landmark position to pixel coordinates
                        landmark_px = mp_drawing._normalized_to_pixel_coordinates(landmark.x, landmark.y, frame.shape[1], frame.shape[0])
                        
                        if landmark_px:  # Check if the conversion was successful
                            cv2.circle(frame, landmark_px, 5, (121, 22, 76), thickness=-1)  # Draw the landmark point

                        control_gripper(arm, hand)

            cv2.imshow("Frame", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        time.sleep(10)

    cap.release()
    cv2.destroyAllWindows()
    arm.disconnect()

if __name__ == '__main__':
    main()
