import socket
import json
import tkinter as tk
import select

class UDP():
    def __init__(self, udp_receiver):
        self.udp_receiver = udp_receiver
        self.bind_recv(udp_receiver)
        
    def bind_recv(self, udp_receiver):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(udp_receiver)
        self.sock.setblocking(0)

    def recv(self): # Not in use
        try:
            recv_data, address = self.sock.recvfrom(4096)
            return json.loads(recv_data) # return dict
        except BlockingIOError as e:
            print(f"Socket error: {e}")
    
    def recv_select(self):
        readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)
        for s in readable:
            if s is self.sock:
                recv_data, address = s.recvfrom(4096)
                return json.loads(recv_data) # return dict
        return None



class Window():
    def __init__(self, master, conn):
        self.conn = conn # UDP connection object
        self.master = master
        #self.master.geometry('300x300')
        self.master.bind("<q>", self.quit_all)
        self.add_frames()
        self.master.after(10, self.update_labels_text)

    def add_frames(self):
        '''
        Add constant frames to the GUI
        '''
        # Configure masters 0 column
        self.master.columnconfigure(0, weight=1, minsize=50)

        # Add constatn things frame
        self.constant_things_frame = tk.Frame(
                        master=self.master,
                        width=50,
                        height=10,
                        borderwidth=0,
                        )
        # Configure masters 0 row
        self.master.rowconfigure(0, weight=1, minsize=20)
        self.constant_things_frame.grid(row=0, column=0, pady=0)
        self.add_to_constant_things_frame()

        # Add dynamic status frame
        self.dynamic_status_frame = tk.Frame(
                        master=self.master,
                        width=50,
                        height=10,
                        borderwidth=0,
                        )
        # Configure masters 1 row
        self.master.rowconfigure(1, weight=1, minsize=20)
        self.dynamic_status_frame.grid(row=1, column=0, pady=0)
        self.add_to_dynamic_status_frame()

    def add_to_constant_things_frame(self):
        # Add clear button
        tk.Button(self.constant_things_frame, text ="Clear", command = self.clear_button_click).grid(row=0, column=0, pady=0)
    
    def add_to_dynamic_status_frame(self):
        pass

    def clear_button_click(self):
        pass

    def update_labels_text(self):
        '''
        Refresh the text of the existing labels

        If new label detected => update_labels_list() is called and the list of the local labels is updated
        '''

        status_dict = self.conn.recv_select() # Get status_dict from UDP socket

        try:
            for field_name in status_dict:
                self.curr_fields_dict[field_name].set(status_dict[field_name]) # Set text to the StringVar
        except KeyError: # New field added / removed
            self.update_labels_list(status_dict)
        except AttributeError: # curr_fields_dict is still does not exist (First run)
            self.update_labels_list(status_dict)
        except TypeError: # Probably status_dict is None (nothing received) => do nothing
            pass

        self.master.after(10, self.update_labels_text)

    def update_labels_list(self, status_dict):
        '''
        Refresh the local labels list
        '''
        # Add labels in frames to the main window (root)
        max_name_len = max({len(x) for x in status_dict.keys()})
        max_value_len = max({len(str(status_dict[x])) for x in status_dict.keys()})
        self.curr_fields_dict = {} # Create / zeroing current fields list
        
        # destroy all the childrenof the status frame
        #for child in self.curr_fields_dict.winfo_children():
        #    child.destroy()
        
        for row_count, field_name in enumerate(status_dict.keys()):
            # Frame
            frm_msg = tk.Frame(master=self.dynamic_status_frame,
                        width=50,
                        height=10,
                        bg="grey",
                        borderwidth=0,
                        )
            self.dynamic_status_frame.rowconfigure(row_count, weight=1, minsize=20)
            self.dynamic_status_frame.columnconfigure(0, weight=1, minsize=50)
            frm_msg.grid(row=row_count, column=0, pady=0) # +1 because we have a frame of constant things before
            
            # Label
            self.curr_fields_dict[field_name] = tk.StringVar()             # Create new StringVar
            self.curr_fields_dict[field_name].set(status_dict[field_name]) # Set text to the StringVar
            tk.Label(master = frm_msg, width=max_name_len, relief=tk.RAISED, bd=2, text = field_name).grid(row=0, column=0)
            tk.Label(master = frm_msg, width=max_value_len, relief=tk.RAISED, bd=2, textvariable = self.curr_fields_dict[field_name]).grid(row=0, column=1) # bind to StringVar


    def quit_all(self, event):
        '''
        Destructor of GUI
        '''
        print("'Q' pressed. Exit.")
        self.master.destroy()



root = tk.Tk()
conn = UDP(("127.0.0.1", 5005)) # UDP connection object
Window(root, conn)
root.mainloop()