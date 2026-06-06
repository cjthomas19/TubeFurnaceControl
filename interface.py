from tkinter import *
from tkinter import ttk

import time

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from modbusutil import ModbusConnector


MAXFLOW = 5.0
INITFLOW = 1.0

# Class for control page functionality

class ControlPage(ttk.Frame):

    def __init__(self,parent):
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        self.activeGas = StringVar()
        self.flowSet = DoubleVar(value=2.5)
        self.activeGas.set("Nitrogen")

        self.vcmd = parent.register(self.validateFlow)


        ttk.Label(self,anchor="center",text="Active Gas:").grid(column=2,row=1,sticky=(W,E))

        ttk.Button(self, text="Nitrogen", command=lambda: self.setGas("Nitrogen")).grid(column=1,row=1,sticky=W)
        ttk.Button(self, text="Oxygen", command=lambda: self.setGas("Oxygen")).grid(column=1,row=2,sticky=W)
        ttk.Button(self, text="Forming Gas", command=lambda: self.setGas("Forming Gas")).grid(column=1,row=3,sticky=W)
        ttk.Label(self,anchor="center",textvariable=self.activeGas).grid(column=2,row=2,sticky=(W,E))

        ttk.Entry(self,textvariable=self.flowSet,width=3,validate='all',validatecommand=(self.vcmd,'%P')).grid(column=3,row=2,sticky=(W,E))
        self.flowscale = ttk.Scale(self,variable=self.flowSet,orient=VERTICAL,from_=MAXFLOW,to=0.0)
        self.flowscale['command'] = lambda val : self.flowSet.set(f'{float(val):.02f}')
        self.flowscale.grid(column=4,row=1,rowspan=3,sticky=(W,E))

        
        
        self.canvas = Canvas(self,width=700,height=400)
        self.canvas.grid(column=1,row=4,columnspan=4)

        self.tube_img = PhotoImage(file='tubedwg.png').subsample(5,5)

        self.canvas.create_image(350,200,image=self.tube_img,anchor='center')
        self.canvas.create_text(237,290,text='300 C')
        self.canvas.create_text(348,290,text='300 C')
        self.canvas.create_text(459,290,text='300 C')

    def setGas(self,toGas):
        try:
            self.activeGas.set(toGas)
        except ValueError:
            pass

    def validateFlow(self,P):
        valid = (P.replace('.','',1).isdigit() or P=="")
        return valid



# Class for settings page

class SettingsPage(ttk.Frame):

    paritytab = {"Even" : "E", "Odd" : "O", "None" : "N"}

    def __init__(self,parent):
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        self.ports = ModbusConnector.get_serial_ports()

        self.port = StringVar()
        self.baudrate=IntVar()
        self.databits = IntVar(value=8)
        self.parity = StringVar()
        self.stopbit = IntVar()
        self.flowcontrol=StringVar()
        self.terminationchar=StringVar()

        ttk.Label(self,text="COM Port: ").grid(column=1,row=1,sticky=E)
        ttk.Label(self,text="Baud Rate: ").grid(column=1,row=2,sticky=E)
        ttk.Label(self,text="Data Bits: ").grid(column=1,row=3,sticky=E)
        ttk.Label(self,text="Parity: ").grid(column=1,row=4,sticky=E)
        ttk.Label(self,text="Stop Bit: ").grid(column=1,row=5,sticky=E)


        self.psel = ttk.OptionMenu(self, self.port,"",*self.ports)
        self.psel.grid(column=2,row=1,sticky=W)

        self.bsel = ttk.OptionMenu(self,self.baudrate,38400,9600,19200,38400,57600,115200)
        self.bsel.grid(column=2,row=2,sticky=W)

        self.dsel = ttk.Entry(self,textvariable=self.databits,validate='all',validatecommand=(self.check_int,'%P'),width=10,justify='center')
        self.dsel.grid(column=2,row=3,sticky=W)

        self.paritysel = ttk.OptionMenu(self, self.parity, "Odd", "None", "Even", "Odd")
        self.paritysel.grid(column=2,row=4,sticky=W)

        self.ssel = ttk.OptionMenu(self,self.stopbit,1,1,2)
        self.ssel.grid(column=2,row=5,sticky=W)

        self.connect_button = ttk.Button(self, text="CONNECT", command=self.connect)
        self.connect_button.grid(column=2,row=6,padx = 12, pady = 12)

        self.modbusc = ModbusConnector()

        self.x_data = []
        self.y_data = []
        
        self.fig = Figure(figsize=(4,3))
        self.ax = self.fig.add_subplot(111)
        self.line,=self.ax.plot([],[],'k-',label="Live Data")
        self.ax.set_ylim(60,90)
        self.fig.set_facecolor("#d9d9d9")

        self.canvas = FigureCanvasTkAgg(self.fig,master=self)
        self.canvas.get_tk_widget().grid(column=3,row=1,rowspan=6,padx=12,pady=12)

        

    def check_int(self,P):

        return P=='' or P.isdigit()

    def update_plot(self):
        self.x_data.append(time.time() % 50)
        self.y_data.append(self.modbusc.get_float(28672))

        if len(self.x_data) > 50:
            self.x_data.pop(0)
            self.y_data.pop(0)

        self.line.set_data(range(len(self.y_data)),self.y_data)
        self.ax.set_xlim(0,len(self.y_data))
        self.canvas.draw()

        self.after(500,self.update_plot)

    def connect(self):

        self.modbusc.set_params(port = self.port.get(),
                                baudrate = self.baudrate.get(),
                                databits = self.databits.get(),
                                parity = self.paritytab[self.parity.get()],
                                stopbits = self.stopbit.get())
        self.modbusc.connect()

        self.update_plot()

# Class for plotting page

class PlotPage(ttk.Frame):
    
    # PLACEHOLDERS: register addresses incremented by 2 from 28672 (the one known 
    # address from SettingsPage). Will need to verify against actual register map.
    # --> Dictionary of modbus register addresses to read from the furnace.
    REGISTERS = {
        "Load Temp (°C)":   28672,
        "Center Temp (°C)": 28674,
        "Source Temp (°C)": 28676,
        "N2 Flow (SLPM)":   28680,
        "O2 Flow (SLPM)":   28682,
        "H2 Flow (SLPM)":   28684,
    }

    def __init__(self, parent, settings_page=None):
        # Run standard frame setup before adding our own content.
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        # Save reference to SettingsPage so we can borrow its Modbus connection.
        self.settings_page = settings_page
        
        # Each register gets empty list to store its readings over time.
        self.y_data = {name: [] for name in self.REGISTERS}

        # Track whether we are currently logging (True) or not (False).        
        self._logging = False
        # Will store the time logging started, used to calculate elapsed time.
        self._start_time = None

        # One True/False variable per register, linked to each checkbox.
        # First 3 (the temperature channels) start ticked, flow rates start unticked.
        self.enabled = {name: BooleanVar(value=(i < 3))
                        for i, name in enumerate(self.REGISTERS)}

        # Left panel box with border and title "Variables".
        left = ttk.LabelFrame(self, text="Variables", padding=(8,4))
        left.grid(column=1, row=1, sticky=(N,S), padx=(0,10), pady=4)

        # Header label above the checkboxes.
        ttk.Label(left, text="Check to plot:").grid(column=1, row=0, sticky=W, pady=(0,6))


        # Create one checkbox per register, each linked to its True/False variable.
        # row=i+1 places each checkbox one row below the previous one.
        for i, name in enumerate(self.REGISTERS):
            ttk.Checkbutton(left, text=name, variable=self.enabled[name],
                            command=self._refresh_lines).grid(column=1, row=i+1, sticky=W, pady=2)

        # Dividing line between checkboxes and live values.
        # Row offsets are computed from len(self.REGISTERS) so adding/removing
        # registers automatically shifts everything below without manual renumbering.
        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=len(self.REGISTERS)+1, sticky=(W,E), pady=8)

        # Header label above the live value readouts.
        ttk.Label(left, text="Live values:").grid(column=1, row=len(self.REGISTERS)+2, sticky=W, pady=(0,4))

        # Create two labels per register: name on left, current value on right.
        # self.live_labels saves the value labels so _poll can update them later.
        self.live_labels = {}
        for i, name in enumerate(self.REGISTERS):
            ttk.Label(left, text=name+":").grid(column=1, row=len(self.REGISTERS)+3+i, sticky=W, pady=1)
            lbl = ttk.Label(left, text="--", width=8, anchor="e")
            lbl.grid(column=2, row=len(self.REGISTERS)+3+i, sticky=E, pady=1)
            self.live_labels[name] = lbl

        # Dividing line between live values and buttons.
        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=len(self.REGISTERS)*2+4, columnspan=2, sticky=(W,E), pady=8)

        # Start button saved to self so it can be greyed out when logging starts.
        self.start_btn = ttk.Button(left, text="Start Logging", command=self._start)
        self.start_btn.grid(column=1, row=len(self.REGISTERS)*2+5, columnspan=2, sticky=(W,E), pady=2)

        # Stop button starts greyed out, only enabled once logging has started.
        self.stop_btn = ttk.Button(left, text="Stop Logging", command=self._stop, state=DISABLED)
        self.stop_btn.grid(column=1, row=len(self.REGISTERS)*2+6, columnspan=2, sticky=(W,E), pady=2)

        # Clear button always active, not saved to self as it never needs to be greyed out.
        ttk.Button(left, text="Clear Data", command=self._clear).grid(
            column=1, row=len(self.REGISTERS)*2+7, columnspan=2, sticky=(W,E), pady=2)

        # Status text at the bottom of the left panel, updates automatically when set() is called.
        self.status_var = StringVar(value="Not logging")
        ttk.Label(left, textvariable=self.status_var).grid(
            column=1, row=len(self.REGISTERS)*2+8, columnspan=2, sticky=W, pady=(8,0))

        # Create the matplotlib figure, grey background matches the rest of the app.
        self.fig = Figure(figsize=(7,5))
        self.fig.set_facecolor("#d9d9d9")
        
        # Add the graph area inside the figure.       
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Value")
        self.ax.set_title("Live Sensor Data")
        # Dashed grid lines at 50% transparency.
        self.ax.grid(True, linestyle="--", alpha=0.5)
        # Prevent axis labels from being cut off at the edges.      
        self.fig.tight_layout()

        # Create one empty line per register, saved so _poll can update their data later.
        self.lines = {}
        for name in self.REGISTERS:
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
        if self.settings_page is None or not self.settings_page.modbusc.connected:
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
        if self.settings_page is None or not self.settings_page.modbusc.connected:
            self._stop()
            self.status_var.set("Lost connection")
            return

        # Calculate seconds elapsed since logging started.
        elapsed = time.time() - self._start_time

        for name, address in self.REGISTERS.items():
            try:
                # Read the current value from the furnace at this register address.
                val = self.settings_page.modbusc.get_float(address)
                self.y_data[name].append(val)
                # Update the live label, formatted to 2 decimal places.
                self.live_labels[name].config(text=f"{val:.2f}")
            except Exception:
                # If read failed, repeat the last known value to keep list lengths equal.
                prev = self.y_data[name][-1] if self.y_data[name] else 0
                self.y_data[name].append(prev)
                self.live_labels[name].config(text="ERR")

            # Drop oldest reading once we exceed 100 points to keep a rolling window.
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
