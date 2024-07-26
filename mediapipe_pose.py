import socket
import pickle
import numpy as np
import cv2
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

prev_left_wrist_x = 0.5
prev_left_wrist_y = 0.5

min_coord = 0.05
width = 0.25 
height = 0.25

max_coord = 0.95
midpoint = 0.5

def main(use_socket=True, ip="127.0.0.1", port=8000):

  cap = cv2.VideoCapture(0)

  if use_socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))

  with mp_pose.Pose(
      min_coord_coord_detection_confidence=0.5,
      min_coord_coord_tracking_confidence=0.5) as pose:
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
      # Create a rectangle on the left side of the image
      image_height, image_width, _ = image.shape
      left_rectangle_x = int(image_width * min_coord)
      left_rectangle_y = int(image_height * midpoint - (height * image_height) / 2)
      left_rectangle_width = int(image_width * width)
      left_rectangle_height = int(image_height * height)
  
      cv2.rectangle(image, (left_rectangle_x, left_rectangle_y), (left_rectangle_x + left_rectangle_width, left_rectangle_y + left_rectangle_height), (0, 255, 0), 2)
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
    global prev_left_wrist_x, prev_left_wrist_y
    # Add your code here
    # For example, to get right shoulder location, use [results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
    # See link below for location of body parts
    # https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
    left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
    
    part_of_screen = 30
    #   print("Left wrist ", left_wrist.x, " Right wrist ",  left_wrist.y)
    multiplier = 1
    if(np.abs(left_wrist.y - prev_left_wrist_y) < 1/part_of_screen):
        multiplier = 2    
    else:
        print("speed ", left_wrist.y, " prev ", prev_left_wrist_y)
    if (left_wrist.y < max_coord and left_wrist.y > min_coord):
        speed=(left_wrist.y-0.5)*(-multiplier)
    else:
        speed = None

    multiplier = 0.2
    if(np.abs(left_wrist.x - prev_left_wrist_x) < 1/part_of_screen):
        multiplier = 0.75
    else:
        print("direction ", left_wrist.x, " prev ", prev_left_wrist_x)
    if (left_wrist.x < max_coord and left_wrist.x > min_coord):
        direction=(left_wrist.x-0.5)*multiplier
    else:
        direction = None
    
    if speed != None and direction != None: 
        command = [speed, direction]
    else: 
        command = None
    
    prev_left_wrist_x = left_wrist.x
    prev_left_wrist_y = left_wrist.y
    return command
  
if __name__ == "__main__":
  
  use_socket = True
  ip = "127.0.0.1"
  port = 8000

  main(use_socket=use_socket, ip=ip, port=port)
