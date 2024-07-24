import socket
import pickle
import numpy as np
import cv2
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

def main(use_socket=False, ip="127.0.0.1", port=8000):
  # For webcam input:
  cap = cv2.VideoCapture(0)

  if use_socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))

  with mp_pose.Pose(
      min_detection_confidence=0.5,
      min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
      success, image = cap.read()
      if not success:
        print("Ignoring empty camera frame.")
        # If loading a video, use 'break' instead of 'continue'.
        continue

      # To improve performance, optionally mark the image as not writeable to
      # pass by reference.
      image.flags.writeable = False
      image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
      results = pose.process(image)

      # Draw the pose annotation on the image.
      image.flags.writeable = True
      image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
      mp_drawing.draw_landmarks(
          image,
          results.pose_landmarks,
          mp_pose.POSE_CONNECTIONS,
          landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
      # Flip the image horizontally for a selfie-view display.
      cv2.imshow('Output', cv2.flip(image, 1))

      if results.pose_landmarks:
        data = get_joint_angles(results)
      else:
        data = None
      
      if use_socket:
        serialized_data = pickle.dumps(data)
        client_socket.send(serialized_data)  

      if cv2.waitKey(5) & 0xFF == 27:
        break

  cap.release()

  if use_socket:
    client_socket.close()

def get_joint_angles(results):
  # Add your code here
  # For example, to get right shoulder location, use [results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
  # See link below for location of body parts
  # https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
  left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
  midpoint = 0.5
  max = 0.95
  min = 0.05
  print("Left wrist ", left_wrist.x, " Right wrist ",  left_wrist.y)
  if (left_wrist.y < max and left_wrist.y > min):
    speed=(left_wrist.y-0.5)*(-8)
  else:
    speed = None
  
  if (left_wrist.x < max and left_wrist.x > min):
    direction=(left_wrist.x-0.5)*0.75
  else:
    direction = None

  
  if speed != None and direction != None: 
    command = [speed, direction]
  else: 
    command = None
  return command
  
if __name__ == "__main__":
  use_socket = True
  ip = "127.0.0.1"
  port = 8000

  main(use_socket=use_socket, ip=ip, port=port)
