import time
import socket
import json


status_dict = {"status" : (0.0, 2, "#00ff00"),}


udp_monitor_addr = ("127.0.0.1", 5005)
udp_monitor_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_monitor_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

counter = 0
while True:
    counter += 1
    lst = list(status_dict["status"])
    lst[0] = counter
    status_dict["status"] = tuple(lst)
    
    # Sending dict
    print("Sending {}".format(status_dict))
    msg = str.encode(json.dumps(status_dict))
    udp_monitor_sock.sendto(msg, udp_monitor_addr)
    time.sleep(1)
