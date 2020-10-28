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
    
    # Currently not in use. Using recv_select_list instead
    #def recv_select(self):
    #    readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)
    #    for s in readable:
    #        if s is self.sock:
    #            recv_data, address = s.recvfrom(4096)
    #            return json.loads(recv_data) # return dict
    #    return None

    
    def recv_select_list(self):
        chunk_list = []
        new_data_available = True
        while new_data_available:
            readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)
            if len(readable) == 0:
                new_data_available = False
            for s in readable:
                if s is self.sock:
                    recv_data, address = s.recvfrom(4096)
                    chunk_list.append(json.loads(recv_data))
        
        return chunk_list # return dict
            


class Compass_window():
    '''
    Class that implements window that containes compass
    '''
    def __init__(self, father_window, compass_msgs):
        self.draw_compass = tk.IntVar()
        self.draw_compass.set(0)
        self.father_window = father_window
        self.compass_msgs = compass_msgs # existing compass messages in the system
        self.compass_arrows = {} # existing arrows that represent 

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
        self.draw_compass_frame.grid(row=0, column=1, pady=0, rowspan = 2)

        # Create compass canvas
        self.compass_width = 400 # width and height of Canvas
        self.compass_center_x = self.compass_width/2
        self.compass_center_y = self.compass_width/2
        self.compass_radius = int((self.compass_width/2) * 0.9)
        self.compass_canvas = tk.Canvas(self.draw_compass_frame, width=self.compass_width, height=self.compass_width, background='white')
        self.compass_canvas.grid(row=0, column=0)
        
        # Create dial
        try:
            from PIL import ImageTk, Image
            # Adding a nice dial from PNG
            img = Image.open("compass.png")
            img = img.resize((int(img.width * 0.6), int(img.height * 0.6))) # resize the dial in a proper ratio
            self.compass_img = ImageTk.PhotoImage(img)
            img_top_left = (self.compass_center_x - (self.compass_img.width() // 2), self.compass_center_y - (self.compass_img.height() // 2))
            self.compass_canvas.create_image(img_top_left[0], img_top_left[1], anchor="nw", image=self.compass_img)
            self.compass_img.width()
            self.compass_img.height()
        except ImportError as e:
            print(e)
            print("PIL or some submodule is not found:( Can not load nice dial image. Drawing simple circle instead")
            # Adding a simple circle dial
            def _create_circle(self, x, y, r, **kwargs):
                return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
            self.compass_canvas.create_circle = _create_circle
            self.compass_canvas.create_circle(self.compass_canvas, self.compass_center_x, self.compass_center_y, self.compass_radius, fill="pale green", outline="#999", width=4)

        # Update idle tasks to redraw things
        self.compass_canvas.update_idletasks()

    def remove_draw_compass_frame(self):
        self.draw_compass_frame.destroy()
        self.compass_arrows = {}

    def create_compass_msg(self, compass_msg):
        self.compass_arrows[compass_msg.name] = CompassArrow(self, self.draw_compass_frame, compass_msg, len(self.compass_arrows))

    def update_compass(self, new_status_dict):
        for compass_msg in self.compass_msgs.values():
            if compass_msg.name not in self.compass_arrows:
                self.create_compass_msg(compass_msg) # Create CompassArrow and add to compass_arrows list
            
            #print("new msg:")
            #print(compass_msg.name)
            #print(compass_msg.value)
            #print(compass_msg.azimuth_value)
            #print(compass_msg.group)
            #print(compass_msg.color)

            # update arrow and labels from new compass_msg
            self.compass_arrows[compass_msg.name].text.set("{}: {:6.2f} ({})".format(compass_msg.name, compass_msg.azimuth_value, compass_msg.value))# Update compass label's text
            x = self.compass_center_x + int(self.compass_radius * math.sin(math.radians(compass_msg.value)))
            y = self.compass_center_y - int(self.compass_radius * math.cos(math.radians(compass_msg.value)))
            self.compass_canvas.coords(self.compass_arrows[compass_msg.name].arrow, self.compass_center_x, self.compass_center_y, x, y)


class CompassArrow():
    """
    Class that implements the compass arrow and its label
    """
    def __init__(self, compass_window_instance, master_frame, compass_msg, arrow_list_len):
        self.id = arrow_list_len
        self.text = tk.StringVar()              # Create new StringVar
        self.text.set("{}:".format(compass_msg.name))       # Update the StringVar (label's) text
        # Create the lable itself and assign a text
        self.label = tk.Label(master = master_frame, textvariable = self.text, anchor = "w", fg=compass_msg.color) # fg -> Text color
        self.label.grid(row=self.id + 1, column=0, sticky="W") # row = id + 1 (because 0 is the compass image)

        # Create arrow
        self.arrow = compass_window_instance.compass_canvas.create_line(compass_window_instance.compass_center_x, compass_window_instance.compass_center_y,compass_window_instance.compass_center_x, compass_window_instance.compass_center_y, fill=compass_msg.color, width=3, arrow=tk.LAST)


class StatusWindow():
    '''
    Window that containes Status messages
    '''
    def __init__(self, father_window):
        self.clear_fields()
        self.father_window = father_window

    def clear_fields(self):
        self.curr_fields_dict = {} # Zeroing current fields list

    def update_labels_text(self, new_status_dict):
        '''
        Refresh the text of the existing labels

        If new label detected => add_to_field_dict() is called and the list of the local labels is updated
        '''
        
        for field_name in new_status_dict:
            if field_name not in self.curr_fields_dict: # we have a new status field
                self.add_to_field_dict(field_name, new_status_dict)
            else:
                try:
                    ### Update the label's text (in existing label)
                    self.curr_fields_dict[field_name][0].set(new_status_dict[field_name].value) # Set text to the StringVar
                    self.update_labels_color(field_name, new_status_dict[field_name].color)
                except TypeError as e:
                    print("Type error in field '{}': {}".format(field_name, e))
                    self.curr_fields_dict[field_name][0].set("Wrong type") # Set text to the StringVar
                    self.update_labels_color(field_name, "#fffffffff")
                except Exception as e:
                    print("Exception in field '{}': {}".format(field_name, e))
                    print("Let's see.. a new exception during putting new_status_dict into GUI")
                    import pdb; pdb.set_trace()

    def add_to_field_dict(self, field_name, new_status_dict):
        '''
        Add new labels to the current labels list (self.curr_fields_dict)
        '''
        print("Add new field to the fields list: '{}'".format(field_name))
        # Add labels in frames to the main window (root)
        self.max_name_len = max({len(x) for x in new_status_dict.keys()})
        self.max_value_len = max({len(str(new_status_dict[x])) for x in new_status_dict.keys()})
        
        row_count = len(self.curr_fields_dict)

        # Create subframe for the field
        frm_msg = tk.Frame(master=self.father_window.dynamic_status_frame,
                    width=50,
                    height=10,
                    bg="grey",
                    borderwidth=0,
                    )
        self.father_window.dynamic_status_frame.rowconfigure(row_count, weight=1, minsize=20)
        self.father_window.dynamic_status_frame.columnconfigure(0, weight=1, minsize=50)
        frm_msg.grid(row=row_count, column=0, pady=0) # +1 because we have a frame of constant things before
        
        # Add new Label
        lbl_field_text_StringVar  = tk.StringVar()             # Create new StringVar
        # Update the label's text (in a new label)
        try:
            lbl_field_text_StringVar.set(new_status_dict[field_name].value) # Set text to the StringVar
            color = new_status_dict[field_name].color
        except TypeError as e:
            print("Type error in field '{}': {}".format(field_name, e))
            lbl_field_text_StringVar.set("Wrong type") # Set text to the StringVar
        # Create the lable itself and assign a text
        lbl_field_name = tk.Label(master = frm_msg, width=self.max_name_len, relief=tk.RAISED, bd=2, text = field_name)
        lbl_field_name.grid(row=0, column=0)
        lbl_field_text = tk.Label(master = frm_msg, width=self.max_value_len, relief=tk.RAISED, bd=2, textvariable = lbl_field_text_StringVar) # bind to StringVar
        lbl_field_text.grid(row=0, column=1)
        # Save label's and StringVar to the list
        self.curr_fields_dict[field_name] = [lbl_field_text_StringVar, lbl_field_name, lbl_field_text]
        # update label's color
        self.update_labels_color(field_name, color)
            
    
    def update_labels_color(self, field_name, color):
        self.curr_fields_dict[field_name][1].config(bg=color) # update lbl_field_name
        self.curr_fields_dict[field_name][2].config(bg=color) # update lbl_field_text


class StatusLine():
    """
    Class that implements one line in the message status list.
    (e.g line can be: [value, group, color] )
    Items which contains "compass" keywords will be added to the compassMsgs list
    """
    def __init__(self, msg_name, msg_content, compass_msgs):
        self.name = msg_name
        try:
            self.value = msg_content[0]
            self.group = msg_content[1]

            # color handle
            received_color = msg_content[2]
            if isinstance(received_color, int): # convert the color to string if the color was defined with enum and not as a '#00ff00' string
                if received_color == 0: # good color
                    self.color = "green"
                elif received_color == 1: # not so good color
                    self.color = "goldenrod1"
                elif received_color == 2: # bad color
                    self.color = "red"
                elif received_color == 3: # not defined color
                    self.color = "white"
            else: # if color was already defined as a string
                self.color = msg_content[2]

        except IndexError:
            self.value = -999
            self.group = 0
            self.color = "#ffffff" # not defined color
        
        # Handle compass messages
        compass_messages_list = ["yaw", "azimuth", "telem_azimuth", "blob: yaw", "blob: image_mapper_yaw"] # classify string names like this as a compass messages
        if msg_name in compass_messages_list:
            # convert to the value between [0,360)
            self.azimuth_value = float(self.value) % 360 # add azimuth value field
            # add message to the compass msgs list
            compass_msgs[msg_name] = self
        

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
        self.compass_msgs = {} # messages for the compass
        self.compass = Compass_window(self, self.compass_msgs)
        
        # Statuses Window
        self.curr_fields_dict = {} # Create local labels field names list
        self.status_window = StatusWindow(self)

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
        tk.Button(self.control_frame, text ="Clear labels", command = self.clear_button_click).grid(row=0, column=0, pady=0, sticky="W")
        # Add always on top checkbox
        tk.Checkbutton(self.control_frame, text="Always on top <t>", variable=self.always_on_top, command=self.always_on_top_toggle).grid(row=1, column=0, pady=0, sticky="W")
        # Add draw compass checkbox
        tk.Checkbutton(self.control_frame, text="Draw compass <c>", variable=self.compass.draw_compass, command=self.compass.draw_compass_toggle).grid(row=2, column=0, pady=0, sticky="W")
        # Add quit button
        tk.Button(self.control_frame, text ="Quit <q>", command = self.quit_all).grid(row=3, column=0, pady=0, sticky="W")

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
        self.status_window.clear_fields()

    def update_all(self):
        new_status_dict_list = self.conn.recv_select_list() # Get new_status_dict from UDP socket
        for new_status_dict in new_status_dict_list:
            if new_status_dict is not None:
                
                # Parse new status message with StatusLine class
                for field_name in new_status_dict:
                    # replace {..., "msg_name": [val, group, color], ... } to {..., StatusLine(), ... }
                    new_status_dict[field_name] = StatusLine(field_name, new_status_dict[field_name], self.compass_msgs)

                self.status_window.update_labels_text(new_status_dict)
                if self.compass.draw_compass.get(): # if draw compass checkbox is active
                    self.compass.update_compass(new_status_dict)
            else:
                pass # No new_status_dict received in this iteration
        
        self.master.after(10, self.update_all)

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
