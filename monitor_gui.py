import socket
import json
import tkinter as tk

class UDP():
    def __init__(self, udp_receiver):
        self.bind_recv(udp_receiver)

    def bind_recv(self, udp_receiver):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(udp_receiver)

    def recv(self):
        recv_data, address = self.sock.recvfrom(4096)
        return json.loads(recv_data) # return dict


class Window():
    def __init__(self, master, conn):
        self.conn = conn # UDP connection object
        self.master = master
        #self.master.geometry('300x300')
        self.master.bind("<q>", self.quit_all)

        # Get first
        #self.add_labels(status_dict)
        self.master.after(10, self.update_labels_text)
        
    def update_labels_text(self):
        status_dict = self.conn.recv() # Get status_dict from UDP socket

        # Add labels in frames to the main window (root)
        max_name_len = max({len(x) for x in status_dict.keys()})
        max_value_len = max({len(str(status_dict[x])) for x in status_dict.keys()})
        self.curr_fields_dict = {} # Create / zeroing current fields list
        for row_count, field_name in enumerate(status_dict.keys()):
            # Frame
            frm_msg = tk.Frame(master=self.master,
                        width=50,
                        height=10,
                        bg="grey",
                        borderwidth=0,
                        )
            self.master.rowconfigure(row_count, weight=1, minsize=20)
            self.master.columnconfigure(0, weight=1, minsize=50)
            frm_msg.grid(row=row_count, column=0, pady=0)
            
            # Label
            self.curr_fields_dict[field_name] = tk.StringVar()             # Create new StringVar
            self.curr_fields_dict[field_name].set(status_dict[field_name]) # Set text to the StringVar
            tk.Label(master = frm_msg, width=max_name_len, relief=tk.RAISED, bd=2, text = field_name).grid(row=0, column=0)
            tk.Label(master = frm_msg, width=max_value_len, relief=tk.RAISED, bd=2, textvariable = self.curr_fields_dict[field_name]).grid(row=0, column=1) # bind to StringVar
            
        print("Listening ...")
        self.master.after(10, self.refresh_labels)
    
    def refresh_labels(self):
        status_dict = self.conn.recv() # Get status_dict from UDP socket
        for field_name in status_dict:
            try:
                self.curr_fields_dict[field_name].set(status_dict[field_name]) # Set text to the StringVar
            except KeyError:
                pass # received message with unknown label. Nothing to update
                # Consider implementing online add_new_labels() function
        
        self.master.after(10, self.refresh_labels)
    def quit_all(self, event):
        print("pressed Q => Exit()")
        self.master.destroy()



root = tk.Tk()
conn = UDP(("127.0.0.1", 5005)) # UDP connection object
Window(root, conn)
root.mainloop()