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

rectangle_coord = 0.45
width = 0.5
height = 0.7

min_x = 0.05
max_x = 0.95
min_y = 0.05
max_y = 0.95
boundaries = (min_x, min_y, max_x, max_y)

min_coord = 0.05
max_coord = 0.95
midpoint = 0.5

_prev_speed = 0
_prev_direction = 0

def main(use_socket=True, ip="127.0.0.1", port=8000):
  global boundaries
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

      # Create a rectangle on the left side of the image
      image_height, image_width, _ = image.shape
    
      left_rectangle_x = int(image_width * rectangle_coord)
      left_rectangle_y = int(image_height * midpoint - (height * image_height) / 2)
      left_rectangle_width = int(image_width * width)
      left_rectangle_height = int(image_height * height)

      boundaries = ((left_rectangle_x/image_width), 1-(left_rectangle_y/image_height), 1-(left_rectangle_x + left_rectangle_width)/image_width, 1-(left_rectangle_y + left_rectangle_height)/image_height)
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
def smoother_function(current_speed, wanted_speed, dv):
    if current_speed < wanted_speed:
        current_speed += dv
    elif current_speed > wanted_speed:
        current_speed -= dv
    return current_speed
def get_joint_angles(results):
    global prev_left_wrist_x, prev_left_wrist_y, _prev_speed, _prev_direction
    # Add your code here
    # For example, to get right shoulder location, use [results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
    # See link below for location of body parts
    # https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
    left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
    # print(boundaries)
    # (0.45, 0.15, 0.050000000000000044, 0.85)

    if (left_wrist.x > boundaries[0]) and (left_wrist.x < 1-boundaries[2]) and left_wrist.y <  boundaries[1] and left_wrist.y > boundaries[3]:
        # Hand is within boundaries
        # Add your code here
        midpoint = boundaries[0] + (1-boundaries[2] - boundaries[0])/2
        
        if (left_wrist.y < max_coord and left_wrist.y > min_coord):
            #max is +/- 1.5 
            speed=(left_wrist.y-0.5)*(-5)
            if(speed > 1.5):
                speed = 1.5
            elif(speed < -1.5):
                speed = -1.5
            if(speed > 0 and _prev_speed < 0):
                _prev_speed = 0
            if(speed < 0 and _prev_speed > 0):
                _prev_speed = 0
            speed = smoother_function(_prev_speed, speed, 0.05)
        else:
            speed = None
        if speed is not None:
            _prev_speed = speed

        if (left_wrist.x < max_coord and left_wrist.x > min_coord):
            direction=(left_wrist.x-midpoint)*1
            #max is +/- 0.25
            if(direction > 0.25):
                direction = 0.25
            elif(direction < -0.25):
                direction = -0.25
            if(direction > 0 and _prev_direction < 0):
                _prev_direction = 0
            if(direction < 0 and _prev_direction > 0):
                _prev_direction = 0
            direction = smoother_function(_prev_direction, direction, 0.01)
        else:
            direction = None

        if direction is not None:
            _prev_direction = direction
        
        if speed != None and direction != None: 
            command = [speed, direction]
        else: 
            command = None  
        
        prev_left_wrist_x = left_wrist.x
        prev_left_wrist_y = left_wrist.y
    else:
        command = None
    print(command)  
    # command = None
    return command

  
if __name__ == "__main__":
  
  use_socket = True
  ip = "127.0.0.1"
  port = 8000

  main(use_socket=use_socket, ip=ip, port=port)
