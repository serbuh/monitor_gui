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
        self.curr_fields_dict = {} # Create local labels field names list
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
        tk.Button(self.constant_things_frame, text ="Clear labels", command = self.clear_button_click).grid(row=0, column=0, pady=0)
    
    def add_to_dynamic_status_frame(self):
        pass

    def clear_button_click(self):
        for child in self.dynamic_status_frame.winfo_children():
            child.destroy()
        self.curr_fields_dict = {} # Zeroing current fields list

    def update_labels_text(self):
        '''
        Refresh the text of the existing labels

        If new label detected => update_labels_list() is called and the list of the local labels is updated
        '''

        new_status_dict = self.conn.recv_select() # Get new_status_dict from UDP socket

        
        if new_status_dict is not None:
            for field_name in new_status_dict:
                if field_name not in self.curr_fields_dict: # we have a new status field
                    self.update_labels_list(new_status_dict)
                else:
                    try:
                        ### Update the label's text (in existing label)
                        self.curr_fields_dict[field_name][0].set(new_status_dict[field_name][0]) # Set text to the StringVar
                        color_id = new_status_dict[field_name][1]
                        self.update_labels_color(field_name, color_id)
                    except TypeError as e:
                        print(f"Type error in field '{field_name}': {e}")
                        self.curr_fields_dict[field_name][0].set("Wrong type") # Set text to the StringVar
                        color_id = 1 # set the color of the wrong type to 1 hardcoded
                        self.update_labels_color(field_name, color_id)
                    except Exception as e:
                        print(f"Exception in field '{field_name}': {e}")
                        print("Let's see.. a new exception during putting new_status_dict into GUI")
                        import pdb; pdb.set_trace()
        else:
            pass # No new_status_dict received in this iteration

        

        self.master.after(10, self.update_labels_text)

    def update_labels_list(self, new_status_dict):
        '''
        Refresh the local labels list
        '''
        print("update labels list")
        # Add labels in frames to the main window (root)
        max_name_len = max({len(x) for x in new_status_dict.keys()})
        max_value_len = max({len(str(new_status_dict[x])) for x in new_status_dict.keys()})
        self.curr_fields_dict = {} # Zeroing current fields list
        
        for row_count, field_name in enumerate(new_status_dict.keys()):
            # Create subframe for the field
            frm_msg = tk.Frame(master=self.dynamic_status_frame,
                        width=50,
                        height=10,
                        bg="grey",
                        borderwidth=0,
                        )
            self.dynamic_status_frame.rowconfigure(row_count, weight=1, minsize=20)
            self.dynamic_status_frame.columnconfigure(0, weight=1, minsize=50)
            frm_msg.grid(row=row_count, column=0, pady=0) # +1 because we have a frame of constant things before
            
            # Add new Label
            lbl_field_text_StringVar  = tk.StringVar()             # Create new StringVar
            # Update the label's text (in a new label)
            try:
                lbl_field_text_StringVar.set(new_status_dict[field_name][0]) # Set text to the StringVar
                color_id = new_status_dict[field_name][1]
            except TypeError as e:
                print(f"Type error in field '{field_name}': {e}")
                lbl_field_text_StringVar.set("Wrong type") # Set text to the StringVar
            # Create the lable itself and assign a text
            lbl_field_name = tk.Label(master = frm_msg, width=max_name_len, relief=tk.RAISED, bd=2, text = field_name)
            lbl_field_name.grid(row=0, column=0)
            lbl_field_text = tk.Label(master = frm_msg, width=max_value_len, relief=tk.RAISED, bd=2, textvariable = lbl_field_text_StringVar) # bind to StringVar
            lbl_field_text.grid(row=0, column=1)
            # Save label's and StringVar to the list
            self.curr_fields_dict[field_name] = [lbl_field_text_StringVar, lbl_field_name, lbl_field_text]
            # update label's color
            self.update_labels_color(field_name, color_id)
            
    def update_labels_color(self, field_name, color_id):
        if color_id == 0:
            self.curr_fields_dict[field_name][1].config(bg="green") # update lbl_field_name
            self.curr_fields_dict[field_name][2].config(bg="green") # update lbl_field_text
        elif color_id == 1:
            self.curr_fields_dict[field_name][1].config(bg="red") # update lbl_field_name
            self.curr_fields_dict[field_name][2].config(bg="red") # update lbl_field_text

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