from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk

import time
import math

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from modbusutil import ModbusConnector
from hardware import TubeInterface


MAXFLOW = 5.0
INITFLOW = 1.0

# Class for settings page

class SettingsPage(ttk.Frame):

    paritytab = {"Even" : "E", "Odd" : "O", "None" : "N"}

    def __init__(self,parent,tube_interface):

        # Run parent frame setup before adding our own content
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        self.ports = ModbusConnector.get_serial_ports()

        self.port = StringVar()
        self.baudrate = IntVar()
        self.databits = IntVar(value=8)
        self.parity = StringVar()
        self.stopbit = IntVar()
        self.flowcontrol=StringVar()
        self.terminationchar=StringVar()

        ## Communications Settings
        companel = ttk.LabelFrame(self,text="Communications",width=250,height=300)
        companel.grid(row=0,column=1)
        companel.grid_propagate(0)

        ttk.Label(companel,text="COM Port: ").grid(column=1,row=1,sticky=E,pady=(10,0))
        ttk.Label(companel,text="Baud Rate: ").grid(column=1,row=2,sticky=E)
        ttk.Label(companel,text="Data Bits: ").grid(column=1,row=3,sticky=E)
        ttk.Label(companel,text="Parity: ").grid(column=1,row=4,sticky=E)
        ttk.Label(companel,text="Stop Bit: ").grid(column=1,row=5,sticky=E)

        
        self.psel = ttk.OptionMenu(companel, self.port,"",*self.ports)
        self.psel.grid(column=2,row=1,sticky=W,pady=(10,0))

        self.bsel = ttk.OptionMenu(companel,self.baudrate,38400,9600,19200,38400,57600,115200)
        self.bsel.grid(column=2,row=2,sticky=W)

        self.dsel = ttk.OptionMenu(companel,self.databits,7,7,8)
        self.dsel.grid(column=2,row=3,sticky=W)

        self.paritysel = ttk.OptionMenu(companel, self.parity, "Odd", "None", "Even", "Odd")
        self.paritysel.grid(column=2,row=4,sticky=W)

        self.ssel = ttk.OptionMenu(companel,self.stopbit,1,1,2)
        self.ssel.grid(column=2,row=5,sticky=W)

        self.connect_button = ttk.Button(companel, text="CONNECT", command=self.connect)
        self.connect_button.grid(column=1,row=6,columnspan=2,padx = 12, pady = 12)

        self.modbusc = ModbusConnector()

        ## Hardware Settings
        hpanel = ttk.LabelFrame(self,text="Hardware",width=250,height=300)
        hpanel.grid(row=0,column=2)
        hpanel.grid_propagate(0)
        
        ttk.Label(hpanel,text="Temperature Limits: ").grid(column=1,row=1)

    def connect(self):

        self.modbusc.set_params(port = self.port.get(),
                                baudrate = self.baudrate.get(),
                                databits = self.databits.get(),
                                parity = self.paritytab[self.parity.get()],
                                stopbits = self.stopbit.get())
        self.modbusc.connect()

    def update(self):
        pass


# Class for plotting page

class PlotPage(ttk.Frame):

    def __init__(self, parent,tube_interface):
        # Run parent frame setup before adding our own content.
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        # Save reference to tube interface for later use
        self.tube_interface = tube_interface

        # Get values to plot from hardware list of registers
        self._REGISTERS = dict(zip(self.tube_interface.get_register_names(),self.tube_interface.get_register_keys()))
        
        # Each register gets empty list to store its readings over time.
        self.y_data = {name: [] for name in self._REGISTERS}

        # Track whether we are currently logging (True) or not (False).        
        self._logging = False
        # Will store the time logging started, used to calculate elapsed time.
        self._start_time = None

        # One True/False variable per register, linked to each checkbox.
        # First 3 (the temperature channels) start ticked, flow rates start unticked.
        self.enabled = {name: BooleanVar(value=(i < 3))
                        for i, name in enumerate(self._REGISTERS)}
        

        # Left panel box with border and title "Variables".
        left = ttk.LabelFrame(self, text="Variables", padding=(8,4))
        left.grid(column=1, row=1, sticky=(N,S), padx=(0,10), pady=4)

        # Header label above the checkboxes.
        ttk.Label(left, text="Check to plot:").grid(column=1, row=0, sticky=W, pady=(0,6))


        # Create one checkbox per register, each linked to its True/False variable.
        # row=i+1 places each checkbox one row below the previous one.
        for i, name in enumerate(self._REGISTERS):
            ttk.Checkbutton(left, text=name, variable=self.enabled[name],
                            command=self._refresh_lines).grid(column=1, row=i+1, sticky=W, pady=2)

        # Dividing line between checkboxes and live values.
        # Row offsets are computed from len(self.REGISTERS) so adding/removing
        # registers automatically shifts everything below without manual renumbering.
        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=len(self._REGISTERS)+1, sticky=(W,E), pady=8)

        # Header label above the live value readouts.
        ttk.Label(left, text="Live values:").grid(column=1, row=len(self._REGISTERS)+2, sticky=W, pady=(0,4))

        # Create two labels per register: name on left, current value on right.
        # self.live_labels saves the value labels so _poll can update them later.
        self.live_labels = {}
        for i, name in enumerate(self._REGISTERS):
            ttk.Label(left, text=name+":").grid(column=1, row=len(self._REGISTERS)+3+i, sticky=W, pady=1)
            lbl = ttk.Label(left, text="--", width=8, anchor="e")
            lbl.grid(column=2, row=len(self._REGISTERS)+3+i, sticky=E, pady=1)
            self.live_labels[name] = lbl

        # Dividing line between live values and buttons.
        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=len(self._REGISTERS)*2+4, columnspan=2, sticky=(W,E), pady=8)

        # Start button saved to self so it can be greyed out when logging starts.
        self.start_btn = ttk.Button(left, text="Start Logging", command=self._start)
        self.start_btn.grid(column=1, row=len(self._REGISTERS)*2+5, columnspan=2, sticky=(W,E), pady=2)

        # Stop button starts greyed out, only enabled once logging has started.
        self.stop_btn = ttk.Button(left, text="Stop Logging", command=self._stop, state=DISABLED)
        self.stop_btn.grid(column=1, row=len(self._REGISTERS)*2+6, columnspan=2, sticky=(W,E), pady=2)

        # Clear button always active, not saved to self as it never needs to be greyed out.
        ttk.Button(left, text="Clear Data", command=self._clear).grid(
            column=1, row=len(self._REGISTERS)*2+7, columnspan=2, sticky=(W,E), pady=2)

        # Status text at the bottom of the left panel, updates automatically when set() is called.
        self.status_var = StringVar(value="Not logging")
        ttk.Label(left, textvariable=self.status_var).grid(
            column=1, row=len(self._REGISTERS)*2+8, columnspan=2, sticky=W, pady=(8,0))

        # Create the matplotlib figure, grey background matches the rest of the app.
        self.fig = Figure(figsize=(7,5))
        self.fig.set_facecolor("#d9d9d9")
        
        # Add the graph area inside the figure.       
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Value")
        self.ax.set_title("Live Sensor Data")
        # Dashed grid lines at 50% transparency.
        #self.ax.grid(True, linestyle="--", alpha=0.5)
        # Prevent axis labels from being cut off at the edges.      
        self.fig.subplots_adjust(left=0.15)

        # Create one empty line per register, saved so _poll can update their data later.
        self.lines = {}
        for name in self._REGISTERS:
            line, = self.ax.plot([], [], label=name, linewidth=1.5)
            self.lines[name] = line

        # Legend identifying which line is which, small font to avoid blocking the plot.
        self.ax.legend(loc="upper left", fontsize=7)

        # Convert matplotlib figure into a tkinter widget and place it on the right side.
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(column=2, row=1, sticky=(N,S,E,W))

        # Make the plot expand to fill the window when resized.
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)

    def _refresh_lines(self):
        # Called when any checkbox is clicked, shows or hides each line accordingly.
        for name, line in self.lines.items():
            line.set_visible(self.enabled[name].get())
        self.canvas.draw_idle()

    def _start(self):
        # Refuse to start if not connected to the furnace 
        # (also, widget currently stops responding if this occurs).
        if self.tube_interface is None or not self.tube_interface.is_connected():
            self.status_var.set("Not connected — go to Settings first")
            return
        self._logging = True
        self._start_time = time.time()
        # Grey out Start, enable Stop.
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.status_var.set("Logging...")
        # Begin the polling loop.
        self._poll()

    def _stop(self):
        # Setting _logging to False causes _poll to exit on its next run.
        self._logging = False
        # Re-enable Start, grey out Stop.
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.status_var.set("Stopped")

    def _clear(self):
        # Wipe all stored data lists.
        for lst in self.y_data.values():
            lst.clear()
        # Reset all plot lines to empty.
        for line in self.lines.values():
            line.set_data([], [])
        # Reset all live value labels back to "--".
        for lbl in self.live_labels.values():
            lbl.config(text="--")
        # Reset axis limits and redraw.
        self.ax.relim()
        self.canvas.draw_idle()
        self.status_var.set("Data cleared")

    def _poll(self):
        # Exit if logging was stopped.
        if not self._logging:
            return
        # Exit if connection was lost.
        if self.tube_interface is None or not self.tube_interface.is_connected():
            self._stop()
            self.status_var.set("Lost connection")
            return

        # Calculate seconds elapsed since logging started.
        elapsed = time.time() - self._start_time

        for name, key in self._REGISTERS.items():
            
            val = self.tube_interface.get_value(key)
            self.y_data[name].append(val)
            
            # Update the live label, formatted to 2 decimal places (will update if equipment accuracy is better).
            self.live_labels[name].config(text=f"{val:.2f}")

            # Drop oldest reading once we exceed 100 points to keep a rolling window--should we keep a history log?
            # PLACEHOLDER: 100 points = ~50s at 500ms poll rate.
            if len(self.y_data[name]) > 100:  
                self.y_data[name].pop(0)

            # Only update the line if this register's checkbox is ticked.
            if self.enabled[name].get():
                self.lines[name].set_data(range(len(self.y_data[name])), self.y_data[name])

        # Rescale axes to fit new data and redraw.
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()
        self.status_var.set(f"Logging — {elapsed:.0f}s elapsed")

        # Schedule next poll in 500ms, keeps the loop running; matches 
        # SettingsPage poll rate, could change.
        self.after(500, self._poll)

    def update(self):
        pass

# Class to control gas panel items - valve states, selected gas, and MFC flows

class GasPanel(ttk.Frame):

    def add_valve(self,x,y,size,third_port):
        self.canvas.create_polygon(x,y,x+size/2,y+size/2*math.sqrt(3),x-size/2,y+size/2*math.sqrt(3),fill='white',outline='black')
        self.canvas.create_polygon(x,y,x+size/2,y-size/2*math.sqrt(3),x-size/2,y-size/2*math.sqrt(3),fill='white',outline='black')

        if third_port==1:
            self.canvas.create_polygon(x,y,x+size/2*math.sqrt(3),y+size/2,x+size/2*math.sqrt(3),y-size/2,fill='white',outline='black')
        elif third_port==-1:
            self.canvas.create_polygon(x,y,x-size/2*math.sqrt(3),y+size/2,x-size/2*math.sqrt(3),y-size/2,fill='white',outline='black')

    def add_pipe(self,x1,y1,x2,y2):
        self.canvas.create_line(x1,y1,x2,y2)

    def add_pump(self, x, y, size):
        self.canvas.create_oval(x-size/2,y-size/2,x+size/2,y+size/2,fill='white',outline='black')
        self.canvas.create_line(x-size/2*math.cos(math.pi/4),y+size/2*math.sin(math.pi/4),x+size/2,y)
        self.canvas.create_line(x-size/2*math.cos(math.pi/4),y-size/2*math.sin(math.pi/4),x+size/2,y)

    def _validateFlow(self,P):
        valid = (P.replace('.','',1).isdigit() or P=="")
        return valid
        

    def __init__(self, parent,tube_interface):
        # Run parent frame setup before adding our own content.
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        # Store reference to tube interface for later use
        self.tube_interface = tube_interface

        # Rescale tube image using HAMMING filter (5) for sharper image
        self.tube_img = ImageTk.PhotoImage(Image.open("tubedwg.png").resize((400,200),5))

        # Prepare canvas
        self.canvas = Canvas(self,width=800,height=600,background="#d9d9d9",highlightthickness=0)
        self.canvas.grid(column=1,row=1,columnspan=4)

        # Draw P&ID pipes and valves
        self.add_pipe(100,50, 100,100)
    
        self.add_pipe(100,100,100,200)
        self.add_pipe(100,200,150,200)
        self.add_pipe(150,200,150,50)
        
        self.add_pipe(100,200,100,300)
        self.add_pipe(100,300,50, 300)
        self.add_pipe(50, 300,50, 50)

        self.add_pipe(100,300,100,400)
        self.add_pipe(100,400,400,400)

        self.add_pipe(400,400,750,400)
        
        self.add_valve(100,100,20,0)
        self.add_valve(100,200,20,1)
        self.add_valve(100,300,20,-1)

        self.add_pump(725,400,30)

        # Add labels
        self.canvas.create_text(100,40,text="N2")
        self.canvas.create_text(150,40,text="O2")
        self.canvas.create_text(50,40,text="N2/H2")

        # MFC & PT Data box templates
        self.canvas.create_rectangle(125,380,200,420,fill='white',outline='black')
        self.canvas.create_rectangle(600,380,675,420,fill='white',outline='black')
        
        
        self.canvas.create_image(400,430,image=self.tube_img,anchor='center')

        ### Gas Control layout
        gpanel = ttk.LabelFrame(self,text="Gas Control",padding=(8,4),width=150,height=300)
        gpanel.grid_propagate(0)

        # Register validation function with tkinter frame
        self.flowSet = DoubleVar(value=2.5)
        self.vcmd = parent.register(self._validateFlow)

        self.tempSet = DoubleVar(value=150)

        # Header label above the controls.
        ttk.Label(gpanel, text="Gas Selection:").grid(column=1, row=0, sticky=W, pady=(0,6))
        ttk.Button(gpanel, text="Nitrogen", command=lambda: self.tube_interface.set_gas("Nitrogen")).grid(column=1,row=1,sticky=N,columnspan=2)
        ttk.Button(gpanel, text="Oxygen", command=lambda: self.tube_interface.set_gas("Oxygen")).grid(column=1,row=2,sticky=N,columnspan=2)
        ttk.Button(gpanel, text="Forming Gas", command=lambda: self.tube_interface.set_gas("Forming Gas")).grid(column=1,row=3,sticky=N,columnspan=2)
        ttk.Label(gpanel, text="MFC Setpoint:").grid(column=1, row=4, sticky=W, pady=(20,0))

        ttk.Entry(gpanel,textvariable=self.flowSet,validate='all',width=10,validatecommand=(self.vcmd,'%P'),justify='center').grid(column=1,row=5)
        self.flowscale = ttk.Scale(gpanel,variable=self.flowSet,orient=VERTICAL,from_=MAXFLOW,to=0.0,length=50)
        self.flowscale['command'] = lambda val : self.flowSet.set(f'{float(val):.02f}')
        self.flowscale.grid(column=2,row=5,sticky=(W,E),padx=10)

        self.canvas.create_window(300,175,window=gpanel)

        ### Temp Control Layout
        tpanel = ttk.LabelFrame(self,text="Temp. Control",padding=(8,4),width=150,height=300)
        tpanel.grid_propagate(0)

        ttk.Label(tpanel, text = "Setpoint").grid(column=1,row=0,sticky=(N,W,E),pady=(0,6))
        ttk.Entry(tpanel,textvariable=self.tempSet,validate='all',validatecommand=(self.vcmd,'%P'),width=10,justify='center').grid(column=1,row=1)

        self.canvas.create_window(450,175,window=tpanel)

        ### Process Control Layout
        ppanel = ttk.LabelFrame(self,text="Process Control",padding=(8,4),width=150,height=300)
        ppanel.grid_propagate(0)

        ttk.Label(ppanel,text="Start Process").grid(column=1,row=0,sticky=(N,W,E),pady=(0,6))

        self.canvas.create_window(600,175,window=ppanel)
        
    def update(self):
        pass
        
