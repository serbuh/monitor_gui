import socket
import json
import sys
import math
import select

if sys.version_info[0] == 2:
    import Tkinter as tk # for python2
else:
    import tkinter as tk # for python3


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
            print("Socket error: {}".format(e))
    
    def recv_select(self):
        readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)
        for s in readable:
            if s is self.sock:
                recv_data, address = s.recvfrom(4096)
                return json.loads(recv_data) # return dict
        return None

class Compass_window():
    def __init__(self, father_window):
        self.draw_compass = tk.IntVar()
        self.draw_compass.set(0)
        self.father_window = father_window

    def draw_compass_toggle(self):
        checkbox_state = self.draw_compass.get()
        if checkbox_state:
            self.add_draw_compass_frame()
        else:
            self.remove_draw_compass_frame()

    def add_draw_compass_frame(self):
        # Add dynamic status frame
        self.draw_compass_frame = tk.LabelFrame(
                        text="Compass",
                        padx=10,
                        pady=10,
                        master=self.father_window.master,
                        width=50,
                        height=20,
                        borderwidth=1,
                        )
        self.draw_compass_frame.grid(row=1, column=1, pady=0)

        self.compass_width = 400 # width and height of Canvas
        self.compass_center_x = self.compass_width/2
        self.compass_center_y = self.compass_width/2
        self.compass_radius = int((self.compass_width/2) * 0.9)
        self.compass_canvas = tk.Canvas(self.draw_compass_frame, width=self.compass_width, height=self.compass_width, background='white')
        self.compass_canvas.grid(row=0, column=0)
        # Create dial
        def _create_circle(self, x, y, r, **kwargs):
            return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
        self.compass_canvas.create_circle = _create_circle
        self.compass_canvas.create_circle(self.compass_canvas, self.compass_center_x, self.compass_center_y, self.compass_radius, fill="pale green", outline="#999", width=4)
        # Create arrow
        self.compass_arrow = self.compass_canvas.create_line(self.compass_center_x, self.compass_center_y,self.compass_center_x, self.compass_center_y, fill='black', width=3, arrow=tk.LAST)
        self.compass_canvas.update_idletasks()

    def remove_draw_compass_frame(self):
        self.draw_compass_frame.destroy()

    def update_compass(self, new_status_dict):
        az = new_status_dict['azimuth'][0]
        x = self.compass_center_x + int(self.compass_radius * math.sin(math.radians(az)))
        y = self.compass_center_y - int(self.compass_radius * math.cos(math.radians(az)))
        self.compass_canvas.coords(self.compass_arrow, self.compass_center_x, self.compass_center_y, x, y)

class Window():
    def __init__(self, master, conn):
        self.conn = conn # UDP connection object
        self.master = master
        #self.master.geometry('300x300')
        self.master.title("Monitor")
        self.master.iconbitmap("bread.ico")
        self.master.bind("<q>", self.q_pressed)
        self.master.bind("<c>", self.c_pressed)
        self.master.bind("<t>", self.t_pressed)
        
        # always on top
        self.always_on_top = tk.IntVar()
        self.always_on_top.set(1)
        self.master.wm_attributes("-topmost", 1)
        
        # Compass
        self.compass = Compass_window(self)

        self.curr_fields_dict = {} # Create local labels field names list
        self.add_frames()
        self.master.after(10, self.update_all)

    def add_frames(self):
        '''
        Add constant frames to the GUI
        '''
        # Configure masters 0 column
        self.master.columnconfigure(0, weight=1, minsize=50)

        # Add constatn things frame
        self.control_frame = tk.LabelFrame(
                        text="Controll",
                        padx=10,
                        pady=10,
                        master=self.master,
                        width=50,
                        height=10,
                        borderwidth=1,
                        )
        # Configure masters 0 row
        self.master.rowconfigure(0, weight=1, minsize=20)
        self.control_frame.grid(row=0, column=0, pady=0)
        self.add_to_control_frame()

        # Add dynamic status frame
        self.dynamic_status_frame = tk.LabelFrame(
                        text="Status",
                        padx=10,
                        pady=10,
                        master=self.master,
                        width=50,
                        height=20,
                        borderwidth=1,
                        )
        # Configure masters 1 row
        self.master.rowconfigure(1, weight=1, minsize=20)
        self.dynamic_status_frame.grid(row=1, column=0, pady=0)
        self.add_to_dynamic_status_frame()


    def add_to_control_frame(self):
        # Add clear button
        tk.Button(self.control_frame, text ="Clear labels", command = self.clear_button_click).grid(row=0, column=0, pady=0)
        # Add always on top checkbox
        tk.Checkbutton(self.control_frame, text="Always on top <t>", variable=self.always_on_top, command=self.always_on_top_toggle).grid(row=1, column=0, pady=0)
        # Add draw compass checkbox
        tk.Checkbutton(self.control_frame, text="Draw compass <c>", variable=self.compass.draw_compass, command=self.compass.draw_compass_toggle).grid(row=2, column=0, pady=0)
        # Add quit button
        tk.Button(self.control_frame, text ="Quit <q>", command = self.quit_all).grid(row=3, column=0, pady=0)

    def add_to_dynamic_status_frame(self):
        pass

    def t_pressed(self, event):
        print("'T' pressed, toggling always on top")
        self.always_on_top.set(1 - self.always_on_top.get()) # toggle the checkbox state
        self.always_on_top_toggle()

    def always_on_top_toggle(self):
        self.master.wm_attributes("-topmost", self.always_on_top.get()) # Always on top - Windows

    def c_pressed(self, event):
        print("'C' pressed, toggling compass")
        self.compass.draw_compass.set(1 - self.compass.draw_compass.get()) # toggle the checkbox state
        self.compass.draw_compass_toggle()

    def clear_button_click(self):
        for child in self.dynamic_status_frame.winfo_children():
            child.destroy()
        self.curr_fields_dict = {} # Zeroing current fields list

    def update_all(self):
        new_status_dict = self.conn.recv_select() # Get new_status_dict from UDP socket
        if new_status_dict is not None:
            self.update_labels_text(new_status_dict)
            if self.compass.draw_compass.get(): # if draw compass checkbox is active
                self.compass.update_compass(new_status_dict)
        else:
            pass # No new_status_dict received in this iteration
        
        self.master.after(10, self.update_all)

    def update_labels_text(self, new_status_dict):
        '''
        Refresh the text of the existing labels

        If new label detected => update_labels_list() is called and the list of the local labels is updated
        '''
        
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
                    print("Type error in field '{}': {}".format(field_name, e))
                    self.curr_fields_dict[field_name][0].set("Wrong type") # Set text to the StringVar
                    color_id = 1 # set the color of the wrong type to 1 hardcoded
                    self.update_labels_color(field_name, color_id)
                except Exception as e:
                    print("Exception in field '{}': {}".format(field_name, e))
                    print("Let's see.. a new exception during putting new_status_dict into GUI")
                    import pdb; pdb.set_trace()

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
                print("Type error in field '{}': {}".format(field_name, e))
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
            color = "green"
        elif color_id == 1:
            color = "goldenrod1"
        elif color_id == 2:
            color = "red"
        self.curr_fields_dict[field_name][1].config(bg=color) # update lbl_field_name
        self.curr_fields_dict[field_name][2].config(bg=color) # update lbl_field_text

    def q_pressed(self, event):
        print("'Q' pressed. Exit.")
        self.quit_all()

    def quit_all(self):
        '''
        Destructor of GUI
        '''
        self.master.destroy()



root = tk.Tk()
conn = UDP(("127.0.0.1", 5005)) # UDP connection object
Window(root, conn)
root.mainloop()
