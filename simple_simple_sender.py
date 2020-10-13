import time
import socket
import json


status_dict = {"Video FPS"  : (24.3,0,0),
                "Telem FPS" : (22.0,0,1),
                "frame"     : (23832,0,2),
                "Last FPC"  : (13,1,1),
                "FOV"       : ((60.5, 55.6), 1, 1),
                "Sensor"    : ("VIS", 0, 0),
                "CVS state" : ("Scout", 0, 1),
                "Counter"   : (-999, 0, 0),
                "yaw"       : (0.0, 0, 0),
                "telem_yaw_in" : (0.0, 1, 0),
                "telem_yaw_out" : (0.0, 2, 0),}


udp_monitor_addr = ("127.0.0.1", 5005)
udp_monitor_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_monitor_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

counter = 0
while True:
    counter += 1
    if counter < 150:
        lst = list(status_dict["Counter"])
        lst[0] = counter
        lst[2] = 1
        status_dict["Counter"] = tuple(lst)
    else:
        lst = list(status_dict["Counter"])
        lst[0] = counter
        status_dict["Counter"] = tuple(lst)
    
    lst = list(status_dict["telem_yaw_in"])
    lst[0] = (0.5 * counter) % 360
    status_dict["telem_yaw_in"] = tuple(lst)

    lst = list(status_dict["telem_yaw_in"])
    lst[0] = 360 - lst[0] + 60
    status_dict["yaw"] = tuple(lst)

    # Sending dict
    print("Sending {}".format(status_dict))
    msg = str.encode(json.dumps(status_dict))
    udp_monitor_sock.sendto(msg, udp_monitor_addr)
    time.sleep(1/30.0)



