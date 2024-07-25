import os
import time
import socket
import pickle
import threading
import numpy as np
import mujoco
import mujoco.viewer

class Main:

  def __init__(self):
    self.data = None
    self.snake_min = -3
    self.snake_max = 3
    self.frequency = 0
    self.old_frequency = 0
    self.amp = 0.5
    self.start=False
    self.offset = 0
    self.direction = 1
    self.theta = 0

  #TODO: implement change direct
  def run(self):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model = mujoco.MjModel.from_xml_path(f"{script_dir}/src/scene.xml")
    data = mujoco.MjData(model)

    self.time_step = model.opt.timestep

    with mujoco.viewer.launch_passive(model, data) as viewer:
      viewer.cam.type = 1
      viewer.cam.trackbodyid = 0
      viewer.cam.distance = 2

      mujoco.mj_step(model, data)
      viewer.sync()
      time.sleep(2)
      
      while viewer.is_running():
        step_start = time.time()
        if(self.data != None):
          if self.data[0] is not None:
            self.frequency = self.data[0]
          if self.data[1] is not None:
            self.offset = self.data[1]
          print(self.data)
          data.ctrl[:] = self.get_target_q()
        else:
          print("No data")
        mujoco.mj_step(model, data)
        viewer.sync()
        
        time_until_next_step = model.opt.timestep - (time.time() - step_start)
        if time_until_next_step > 0:
          time.sleep(time_until_next_step)    

  def media_pipe_communication(self):
    if(self.data != None):
      if self.data[0] is not None:
        if self.data[0] < 0:
          self.direction = -1
        else:
          self.direction = 1
        self.frequency = self.data[0]
      if self.data[1] is not None:
        self.offset = self.data[1]
      print(self.data)
    else:
      print("No data")



  def server(self, use_socket=False, ip="127.0.0.1", port=8000):
    if use_socket:
      server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      server_socket.bind((ip, port))
      server_socket.listen(1)

      client_socket, _ = server_socket.accept()

      while True:
        serialized_data = client_socket.recv(4096)
        if not serialized_data:
          break
        self.data = pickle.loads(serialized_data)
      
      client_socket.close()
      server_socket.close()

  def move_snake(self, amp, freq, offset, direction, phase=np.pi/4):
    p = np.zeros(12)
    self.theta+= freq*self.time_step
    for i in range(12):
      p[i] = np.clip(amp*np.sin(self.theta + direction*i*phase) + offset, -0.3, 0.3)
    return p

  #  make it theta += omega*timestep



  def get_target_q(self):
    # Snake controller
    return self.move_snake(self.amp, self.frequency, self.offset, self.direction)
    


if __name__ == "__main__":
  use_socket = True
  ip = "127.0.0.1"
  port = 8000

  main = Main()

  server_thread = threading.Thread(target=main.server, kwargs={"use_socket": use_socket, "ip": ip, "port": port})
  run_thread = threading.Thread(target=main.run)

  server_thread.start()
  run_thread.start()

  while True:
    time.sleep(1)
