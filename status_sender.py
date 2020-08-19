import time
import socket
import json


status_dict = {"Video FPS"  : 24.3,
                "Telem FPS" : 22.0,
                "frame"     : 23832,
                "Last FPC"  : 13,
                "FOV"       : (60.5, 55.6),
                "Sensor"    : "VIS",
                "CVS state" : "Scout",
                "Counter"   : -999}


udp_receiver = ("127.0.0.1", 5005)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

counter = 0
while True:
    counter += 1
    status_dict["Counter"] = counter
    # Sending dict
    print(f"Sending {status_dict}")
    msg = str.encode(json.dumps(status_dict))
    sock.sendto(msg, udp_receiver)
    time.sleep(1/30)



