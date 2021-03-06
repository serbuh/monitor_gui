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
    
    def recv_select_list(self): # returns a list of a new status batches [{batch}, {batch}, {batch}]
        chunk_list = []
        new_data_available = True
        while new_data_available:
            readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)
            if len(readable) == 0:
                new_data_available = False
            for s in readable:
                if s is self.sock:
                    recv_data, address = s.recvfrom(4096)
                    if isinstance(recv_data, bytes):
                        recv_data = recv_data.decode() # recvfrom returnes bytes in python3. json.loads() receives str.
                    chunk_list.append(json.loads(recv_data))
        
        return chunk_list # return dict
            

class CompassWindow():
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
                        master=self.father_window,
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

    def update_compass(self):
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
    Status lines frame
    '''
    def __init__(self, father_window):
        self.father_window = father_window
        self.status_groups = StatusGroups(father_window)

    def handle_received_status_lines(self, StatusLinesMsgsList):
        '''
        New status line received  
        Update groups and labels
        '''
        # iterate over a batch of new status lines
        for oneStatusLineMsg in StatusLinesMsgsList:
            self.status_groups.handle_status_line(oneStatusLineMsg)


class OneStatusLineMsg():
    """
    Class that implements one line in the list of status.
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
            self.group = "None"
            self.color = "#ffffff" # not defined color
        
        # Handle compass messages
        compass_messages_list = ["Compass"] # classify string names like this as a compass messages
        if self.group in compass_messages_list:
            # convert to the value between [0,360)
            self.azimuth_value = float(self.value) % 360 # add azimuth value field
            # add message to the compass msgs list
            compass_msgs[msg_name] = self


class StatusGroups():
    '''
    Holds a list of existing status groups
    '''
    def __init__(self, father_window):
        self.curr_status_groups = {}
        self.groups_count = 0
        self.father_window = father_window
    
    def handle_status_line(self, oneStatusLineMsg):
        '''
        Every received (new and existing) status lines are getting here
        '''
        if oneStatusLineMsg.group not in self.curr_status_groups:
            print("--> [{}]{}".format(self.groups_count,oneStatusLineMsg.group))
            self.curr_status_groups[oneStatusLineMsg.group] = OneStatusGroup(oneStatusLineMsg, self.father_window, self.groups_count) # Create new group {..., "group_name": oneStatusGroup, ...}
            self.groups_count += 1
        
        # Handle status line in already existing group
        self.curr_status_groups[oneStatusLineMsg.group].handle_status_line(oneStatusLineMsg)
    
    def clear_all_groups(self):
        # TODO destruct GUI Elements for each group
        self.curr_status_groups = {} # Zeroing current status groups list

    def clear_group(self, group_name):
        # TODO destruct GUI Elements for group_name
        self.curr_status_groups.pop(group_name) # Remove "group_name" from status groups list


class OneStatusGroup():
    '''
    A group of status lines. Holds a list of status lines in the group
    '''
    def __init__(self, oneStatusLineMsg, father_window, group_number):
        '''
        Creates a new group
        '''
        self.group_name = oneStatusLineMsg.group
        self.group_number = group_number
        self.group_lines_count = 0
        self.father_window = father_window
        self.curr_status_lines = {}
        self.init_group_gui_elements(oneStatusLineMsg)

    def init_group_gui_elements(self, oneStatusLineMsg):
        self.group_gui_elements = OneStatusGroupGUIElements(oneStatusLineMsg, self.father_window, self.group_number)
    
    def handle_status_line(self, oneStatusLineMsg):
        '''
        Handle status line in existing group
        '''
        if oneStatusLineMsg.name not in self.curr_status_lines:
            print("--> [{}]{} [{}]{}".format(self.group_number, oneStatusLineMsg.group, self.group_lines_count, oneStatusLineMsg.name))
            self.curr_status_lines[oneStatusLineMsg.name] = OneStatusLine(oneStatusLineMsg, self.group_gui_elements.frame_status_lines, self.group_lines_count) # Create new line in a current group {..., "line_name": oneStatusLineMsg, ...}
            self.group_lines_count += 1

        # Handle status line (line already exist)
        self.curr_status_lines[oneStatusLineMsg.name].handle_status_line(oneStatusLineMsg)

    def clear_all_groups(self):
        pass

    def clear_group(self, group_name):
        pass


class OneStatusLine():
    def __init__(self, oneStatusLineMsg, father_window, line_number):
        self.father_window = father_window
        self.line_number = line_number
        self.init_line_gui_elements(oneStatusLineMsg)

    def init_line_gui_elements(self, oneStatusLineMsg):
        self.line_gui_elements = OneStatusLineGUIElements(oneStatusLineMsg, self.father_window, self.line_number)

    def handle_status_line(self, oneStatusLineMsg):
        self.line_gui_elements.update(oneStatusLineMsg) # update line GUI Elements


class OneStatusGroupGUIElements():
    '''
    GUI Elements of the status group
    '''
    def __init__(self, oneStatusLineMsg, father_window, group_number):
        '''
        Init new group GUI Elements
        '''
        print("    [{}]{} - Creating gui elements".format(group_number, oneStatusLineMsg.group))
        self.father_window = father_window
        self.group_number = group_number

        # Create subframe for group
        self.frame_group = tk.Frame(
                        padx=1,
                        pady=1,
                        master=self.father_window,
                        width=50,
                        height=20,
                        borderwidth=1,
                        )
        self.frame_group.grid(row=self.group_number, column=0, pady=0, sticky="W")

        # Add show/hide button
        self.show_frame = 1
        #self.show_hide_btn_text = tk.StringVar()
        #self.show_hide_btn_text.set("Hide")
        self.show_hide_btn = tk.Button(self.frame_group, text =oneStatusLineMsg.group, command = self.toggle_show_hide_group).grid(row=0, column=0, pady=0, sticky="NW")

        # Create subframe for group statuses
        self.frame_status_lines = tk.Frame(
                        padx=2,
                        pady=2,
                        master=self.frame_group,
                        width=50,
                        height=20,
                        borderwidth=1,
                        )
        self.frame_status_lines.grid(row=1, column=0, pady=0)

    
    def toggle_show_hide_group(self):
        if self.show_frame == 0:
            # Show frame
            self.frame_status_lines.grid()
            self.show_frame = 1
            #self.show_hide_btn_text.set("Hide")
        elif self.show_frame == 1:
            # Hide frame
            self.frame_status_lines.grid_remove()
            self.show_frame = 0
            #self.show_hide_btn_text.set("Show")



    def update(self, oneStatusLineMsg):
        '''
        update existing group GUI Elements
        '''
        pass


class OneStatusLineGUIElements():
    '''
    GUI Elements of the status line in a group
    '''
    def __init__(self, oneStatusLineMsg, father_window, line_number):
        '''
        Init new line GUI Elements
        '''
        self.line_number = line_number
        print("    [{}]{} [{}]{} - Creating gui elements".format(self.line_number, oneStatusLineMsg.group, line_number, oneStatusLineMsg.name))
        self.father_window = father_window

        # Create subframe for line
        self.frame = tk.Frame(
                        master=self.father_window,
                        width=50,
                        height=20,
                        bg="grey",
                        borderwidth=0,
                        )
        self.father_window.rowconfigure(self.line_number, weight=1, minsize=20)
        self.father_window.columnconfigure(0, weight=1, minsize=50)
        self.frame.grid(row=self.line_number, column=0, pady=0)

        # Create field name lable
        max_name_len = max(50, len(oneStatusLineMsg.name))
        self.field_name_label = tk.Label(master = self.frame, width=max_name_len, relief=tk.RAISED, bd=2, text = oneStatusLineMsg.name)
        self.field_name_label.grid(row=0, column=0)

        # Create field value lable (and it's text variable)
        self.label_text = tk.StringVar()             # Create value label StringVar
        max_value_len = max(50, len(str(oneStatusLineMsg.value)))
        self.field_value_label = tk.Label(master = self.frame, width=max_value_len, relief=tk.RAISED, bd=2, textvariable = self.label_text) # bind to StringVar
        self.field_value_label.grid(row=0, column=1)

        # update label's color
        self.update_labels_color(oneStatusLineMsg.name, oneStatusLineMsg.color)

    def update_labels_color(self, field_name, color):
        self.field_name_label.config(bg=color) # update self.field_name_label
        self.field_value_label.config(bg=color) # update self.field_value_label

    def update(self, oneStatusLineMsg):
        '''
        update existing line GUI Elements
        '''
        # Update the vlue label text
        try:
            self.label_text.set(oneStatusLineMsg.value) # Set text to the StringVar
            self.update_labels_color(oneStatusLineMsg.name, oneStatusLineMsg.color)
        except TypeError as e:
            print("Type error in field '{}': {}".format(oneStatusLineMsg.name, e))
            self.label_text.set("Wrong type") # Set text to the StringVar
            self.update_labels_color(oneStatusLineMsg.name, "#fffffffff")
        except Exception as e:
            print("Exception in field '{}': {}".format(oneStatusLineMsg.name, e))
            print("Let's see.. a new exception during putting NewStatusBatchMsg into GUI")
            import pdb; pdb.set_trace()



class MainWindow():
    '''
    Main window - GUI entry point
    '''
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
        
        # Initialize Compass window
        self.compass_msgs = {} # messages for the compass
        self.compassWindow = CompassWindow(self.master, self.compass_msgs)
        
        # add frames before adding elements to it
        self.add_frames()

        # Initialize Statuses MainWindow
        self.statusWindow = StatusWindow(self.dynamic_status_frame)

        self.master.after(10, self.get_new_status_msg)

    def add_frames(self):
        '''
        Add constant frames to the GUI
        '''
        # Configure masters 0 column
        self.master.columnconfigure(0, weight=1, minsize=250)

        # Add constatn things frame
        self.control_frame = tk.LabelFrame(
                        text="Controll",
                        padx=5,
                        pady=2,
                        master=self.master,
                        width=50,
                        height=10,
                        borderwidth=1,
                        )
        # Configure masters 0 row
        self.master.rowconfigure(0, weight=1, minsize=20)
        self.control_frame.grid(row=0, column=0, pady=0, sticky="w")
        self.add_to_control_frame()

        # Add dynamic status frame
        self.dynamic_status_frame = tk.LabelFrame(
                        text="Status",
                        padx=5,
                        pady=2,
                        master=self.master,
                        width=20,
                        height=20,
                        borderwidth=1,
                        )
        # Configure masters 1 row
        self.master.rowconfigure(1, weight=1, minsize=20)
        self.dynamic_status_frame.grid(row=1, column=0, pady=0, sticky="w")
        self.add_to_dynamic_status_frame()

    def add_to_control_frame(self):
        # Add clear button
        tk.Button(self.control_frame, text ="Clear labels", command = self.clear_button_click).grid(row=0, column=0, pady=0, sticky="W")
        # Add always on top checkbox
        tk.Checkbutton(self.control_frame, text="Always on top <t>", variable=self.always_on_top, command=self.always_on_top_toggle).grid(row=1, column=0, pady=0, sticky="W")
        # Add draw compass checkbox
        tk.Checkbutton(self.control_frame, text="Draw compass <c>", variable=self.compassWindow.draw_compass, command=self.compassWindow.draw_compass_toggle).grid(row=2, column=0, pady=0, sticky="W")
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
        self.compassWindow.draw_compass.set(1 - self.compassWindow.draw_compass.get()) # toggle the checkbox state
        self.compassWindow.draw_compass_toggle()

    def clear_button_click(self):
        for child in self.dynamic_status_frame.winfo_children():
            child.destroy()
        print("TODO! clear status lines")
        import pdb; pdb.set_trace()#self.statusWindow.clear_status_lines()

    def get_new_status_msg(self):
        NewStatusBatchList = self.conn.recv_select_list() # Get NewStatusLines from UDP socket
        # iterate over a list of status line batches
        for NewStatusBatchMsg in NewStatusBatchList:
            if NewStatusBatchMsg is not None:
                
                StatusLinesMsgsList = []
                # Parse new batch of status lines to list of OneStatusLineMsg classes
                for field_name in NewStatusBatchMsg:
                    # parse {..., "msg_name": [val, group, color], ... } to [..., OneStatusLineMsg, ... }
                    StatusLinesMsgsList.append(OneStatusLineMsg(field_name, NewStatusBatchMsg[field_name], self.compass_msgs))

                self.statusWindow.handle_received_status_lines(StatusLinesMsgsList)

                if self.compassWindow.draw_compass.get(): # if draw compass checkbox is active
                    self.compassWindow.update_compass()
            else:
                pass # No NewStatusBatchMsg received in this iteration
        
        self.master.after(10, self.get_new_status_msg)

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
MainWindow(root, conn)
root.mainloop()
