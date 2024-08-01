import time
import socket
import threading
import numpy as np
import mujoco_snake

class Main(mujoco_snake.Main):
    
    def __init__(self):
        super().__init__()
        self.log_file = open("target_q_log.txt", "w")  

    def run(self):
        snake_robot_ip = "192.168.1.207"
        snake_robot_port = 5000
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.time_step = 0.12
        while True:
            step_start = time.time()
            self.media_pipe_communication()

            target_q = self.get_target_q()
            message = ",".join(map(str, target_q))

            client_socket.sendto(message.encode(), (snake_robot_ip, snake_robot_port))
            
            # Log target_q
            print(self.log)
            if self.log:
              np.savetxt(self.log_file, [target_q], fmt='%.6f', delimiter=',')
              self.log_file.flush() 

            time_until_next_step = self.time_step - (time.time() - step_start)

            if time_until_next_step > 0:
              time.sleep(time_until_next_step)

    def __del__(self):
      if hasattr(self, 'log_file'):
        self.log_file.close()

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
