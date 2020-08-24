import time
import socket
import json


status_dict = {"Video FPS"  : (24.3,0),
                "Telem FPS" : (22.0,1),
                "frame"     : (23832,2),
                "Last FPC"  : (13,1),
                "FOV"       : ((60.5, 55.6), 1),
                "Sensor"    : ("VIS", 0),
                "CVS state" : ("Scout", 1),
                "Counter"   : (-999, 0)}


udp_receiver = ("127.0.0.1", 5005)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

counter = 0
while True:
    counter += 1
    if counter < 150:
        status_dict["Counter"] = (counter,1)
    else:
        status_dict["Counter"] = (counter,0)
    # Sending dict
    print(f"Sending {status_dict}")
    msg = str.encode(json.dumps(status_dict))
    sock.sendto(msg, udp_receiver)
    time.sleep(1/30)



