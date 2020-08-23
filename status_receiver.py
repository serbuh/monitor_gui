import time
import socket
import json

udp_receiver = ("127.0.0.1", 5005)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(udp_receiver)

while True:
    recv_data, address = sock.recvfrom(4096)

    recv_dict = json.loads(recv_data)
    print(f"Receiving {recv_dict}")
    time.sleep(1/30)



