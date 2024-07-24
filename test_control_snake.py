from socket import socket,AF_INET,SOCK_DGRAM
import time
import keyboard
from math import pi

PORT=5000
CLIENT="10.240.77.116" #snake robot IP address


def main():
    sock=socket(AF_INET,SOCK_DGRAM)

    while True:

        try:
            if keyboard.read_key()=="d":
                msg=f"{pi/9.2},0,0,0,0,0,0,0,0,0,0,0" #'msg' is each servo motor's radian. Maximum value is |pi/9.2|.
            elif keyboard.read_key()=="a":
                msg=f"{-pi/9.2},0,0,0,0,0,0,0,0,0,0,0"
            else:
                msg="0,0,0,0,0,0,0,0,0,0,0,0"
                 
            sock.sendto(msg.encode("utf-8"),(CLIENT,PORT))

        except KeyboardInterrupt:
            break

        print("your message : ",msg)
        time.sleep(0.12) #ラズパイ側の制御周期が0.12なのでこれで合わせると楽. (ラズパイ側を変えればここは自由にできるけど...)


if __name__=="__main__":
    main()

