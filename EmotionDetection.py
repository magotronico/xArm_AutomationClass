import os
import numpy as np
import cv2
import tempfile
import pandas as pd
import torch
from datetime import datetime
from feat import Detector
from PIL import Image

# Set the path where you want to save the data (CSV and images)
os.chdir(r'C:\Users\dilan\Documents\Github\xArm_AutomationClass\datos_FR')

# Create a DataFrame to store the data
df = pd.DataFrame(columns=['Date', 'Hour', 'Detected emotion', 'Data'])

# Set the device to use (GPU if available, otherwise CPU)
if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

# Initialize the Detector object
detector = Detector(face_model="retinaface", landmark_model="mobilefacenet", au_model="xgb", emotion_model="svm", facepose_model="img2pose", device=device)

# Function to create directories for images and CSV files
def crear_carpetas():
    if not os.path.exists('imagenes'):
        os.makedirs('imagenes')
    if not os.path.exists('csv'):
        os.makedirs('csv')

# Function to initialize the camera
def init_camera():
    video_capture = cv2.VideoCapture(0)
    # Change resolution to 1920x1080
    ret = video_capture.set(3, 1920)  # Width
    ret = video_capture.set(4, 1080)  # Height
    return video_capture

# Function to display the frame
def show_frame(frame):
    # Display the resulting image frame in the PAC
    cv2.imshow('Video1', frame)

# Function to detect face and emotions
def find_face_emotion(frame):
    single_face_prediction = detector.detect_image(frame)
    data = single_face_prediction.emotions
    if len(data) == 1 and data.isnull().all().all():
        emotion_list = []
    else:
        emotion_dict = data.idxmax(axis=1).to_dict()
        emotion_list = list(emotion_dict.values())
    return emotion_list, data

# Function to acquire an image from the camera
def acquire_image(video_capture, max_attempts=3):
    attempts = 0
    while attempts < max_attempts:
        # Grab a single frame of video
        ret, frame = video_capture.read()
        if ret:
            scaled_rgb_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            scaled_rgb_frame = np.ascontiguousarray(scaled_rgb_frame[:, :, ::-1])
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, "temp_frame.jpg")
            cv2.imwrite(temp_file, scaled_rgb_frame)
            return frame, scaled_rgb_frame, temp_file
        else:
            attempts += 1
            print("--------No se pudo capturar la imagen / Fin del video------")
            return None, None, None

# Initialize the camera
video_capture = init_camera()

# Create directories for images and CSV files
crear_carpetas()

try:
    while True:
        # Get the current date and time
        now = datetime.now()
        date = now.strftime("%d-%m-%Y")
        hour = now.strftime("%H_%M_%S")

        # Acquire an image from the camera
        rgb_frame, scaled_rgb_frame, temp_file = acquire_image(video_capture)
        if rgb_frame is None:
            break

        # Detect face and emotions
        face_emotions, data = find_face_emotion(temp_file)

        try:
            # Save the image with the detected emotion as the filename
            filename = f'{date}_{hour}_{face_emotions[0]}.jpg'
            im = Image.open(temp_file)
            im = im.save("imagenes/" + filename)

            # Add a new row to the DataFrame
            newrow = {'Date': date, 'Hour': hour, 'Detected emotion': face_emotions[0], 'Data': data}
            print(newrow)
            df.loc[len(df)] = newrow

            # Display the frame
            show_frame(rgb_frame)

            # Save the DataFrame to a CSV file
            filename = f'Estacion#_{date}_{hour}.csv'
            df.to_csv('csv/' + filename)
            
        except IndexError:
            print('No face is detected.')

        

except KeyboardInterrupt:
    # Save the DataFrame to a CSV file if the program is interrupted
    filename = f'Estacion#_{date}_{hour}.csv'
    df.to_csv('csv/' + filename)
    cv2.destroyAllWindows()