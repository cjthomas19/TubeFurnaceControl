from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk

import time
import math

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from modbusutil import ModbusConnector
from hardware import TubeInterface

import csv
from tkinter import filedialog


MAXFLOW = 5.0
INITFLOW = 1.0

def add_scrollbars(container):
    """
    Wraps all content of `container` (a ttk.Frame/page) in both a
    horizontally and vertically scrollable canvas, and returns an inner
    frame to grid all of the page's widgets onto instead of `container`
    directly.

    When left as self, the widget was being placed directly on the page, outside
    the scrollable canvas, and the scrollbars had no effect on it so
    it still got clipped when the window shrunk.

    Both scrollbars are always present but only do something once the
    page's content is wider/taller than the visible window.
    """
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=1)

    canvas = Canvas(container, highlightthickness=0, background="#d9d9d9")
    hbar = ttk.Scrollbar(container, orient=HORIZONTAL, command=canvas.xview)
    vbar = ttk.Scrollbar(container, orient=VERTICAL, command=canvas.yview)
    canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    canvas.grid(column=0, row=0, sticky=(N,S,E,W))
    vbar.grid(column=1, row=0, sticky=(N,S))
    hbar.grid(column=0, row=1, sticky=(W,E))

    inner = ttk.Frame(canvas)
    inner_id = canvas.create_window((0,0), window=inner, anchor='nw')

    def _update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
    inner.bind("<Configure>", _update_scrollregion)

    def _scroll_step(delta):
        # Windows evidently reports delta in multiples of 120, while
        # macOS trackpads report small raw values (e.g., +-1..3). Normalize
        # both so scrolling will actually do something on both platforms.
        if abs(delta) >= 120:
            return int(-delta / 120)
        return -1 if delta > 0 else 1

    def _on_mousewheel_y(event):
        canvas.yview_scroll(_scroll_step(event.delta), "units")
    def _on_mousewheel_x(event):
        canvas.xview_scroll(_scroll_step(event.delta), "units")
    def _on_button4(event):
        canvas.yview_scroll(-1, "units")
    def _on_button5(event):
        canvas.yview_scroll(1, "units")
    def _on_shift_button4(event):
        canvas.xview_scroll(-1, "units")
    def _on_shift_button5(event):
        canvas.xview_scroll(1, "units")

    def _on_arrow_key(event):
        # Don't overrun arrow-key cursor movement while typing in a field.
        if isinstance(event.widget, (Entry, ttk.Entry, Text, Spinbox)):
            return
        step = {"Up": (0,-1), "Down": (0,1), "Left": (-1,0), "Right": (1,0),
                "Prior": (0,-1), "Next": (0,1)}.get(event.keysym)
        if step is None:
            return
        dx, dy = step
        unit = "pages" if event.keysym in ("Prior", "Next") else "units"
        if dx:
            canvas.xview_scroll(dx, unit)
        if dy:
            canvas.yview_scroll(dy, unit)

    _wheel_bindings = {
        "<MouseWheel>": _on_mousewheel_y,
        "<Shift-MouseWheel>": _on_mousewheel_x,
        "<Button-4>": _on_button4,
        "<Button-5>": _on_button5,
        "<Shift-Button-4>": _on_shift_button4,
        "<Shift-Button-5>": _on_shift_button5,
        "<Up>": _on_arrow_key, "<Down>": _on_arrow_key,
        "<Left>": _on_arrow_key, "<Right>": _on_arrow_key,
        "<Prior>": _on_arrow_key, "<Next>": _on_arrow_key,
    }

    def _bind_wheel(event):
        for seq, handler in _wheel_bindings.items():
            canvas.bind_all(seq, handler)
    def _unbind_wheel(event):
        for seq in _wheel_bindings:
            canvas.unbind_all(seq)
    canvas.bind("<Enter>", _bind_wheel)
    canvas.bind("<Leave>", _unbind_wheel)

    # Exposed so callers can force a scrollregion refresh after dynamically
    # showing/hiding content (e.g. toggling an extra graph on) rather than
    # relying on the <Configure> event to catch up.
    inner.scroll_canvas = canvas

    return inner

# Class for settings page

class SettingsPage(ttk.Frame):

    paritytab = {"Even" : "E", "Odd" : "O", "None" : "N"}

    def __init__(self,parent,tube_interface):

        # Run parent frame setup before adding our own content.
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        self.ports = ModbusConnector.get_serial_ports()

        self.tube_interface = tube_interface

        self.port = StringVar()
        self.baudrate = IntVar()
        self.databits = IntVar(value=8)
        self.parity = StringVar()
        self.stopbit = IntVar()
        self.flowcontrol=StringVar()
        self.terminationchar=StringVar()

        self.inner = add_scrollbars(self)
        
        ## Communications Settings
        companel = ttk.LabelFrame(self.inner,text="Communications",width=250,height=300)
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

        self.dsel = ttk.OptionMenu(companel,self.databits,8,7,8)
        self.dsel.grid(column=2,row=3,sticky=W)

        self.paritysel = ttk.OptionMenu(companel, self.parity, "Odd", "None", "Even", "Odd")
        self.paritysel.grid(column=2,row=4,sticky=W)

        self.ssel = ttk.OptionMenu(companel,self.stopbit,1,1,2)
        self.ssel.grid(column=2,row=5,sticky=W)

        self.connect_button = ttk.Button(companel, text="CONNECT", command=self.connect)
        self.connect_button.grid(column=1,row=6,columnspan=2,padx = 12, pady = 12)

        self.status_var = StringVar()
        ttk.Label(companel,textvariable=self.status_var).grid(column=1,row=7,pady=12,columnspan=2)

        ## Hardware Settings
        hpanel = ttk.LabelFrame(self.inner,text="Hardware",width=250,height=300)
        hpanel.grid(row=0,column=2)
        hpanel.grid_propagate(0)

        ttk.Label(hpanel,text="Control Mode: ").grid(column=1,row=0)

        self.mode = StringVar()
        self.modesel = ttk.OptionMenu(hpanel, self.mode, "Gas Only","Gas Only", "Full Control")
        self.modesel.grid(row=1,column=1,pady=6)
        
        ttk.Label(hpanel,text="Temperature Limits: ").grid(column=1,row=2)

    def connect(self):

        self.status_var.set("Connecting...")

        self.tube_interface.modbusc.set_params(
                port = self.port.get(),
                baudrate = self.baudrate.get(),
                databits = self.databits.get(),
                parity = self.paritytab[self.parity.get()],
                stopbits = self.stopbit.get()
            )

        status, msg = self.tube_interface.modbusc.connect()

        if status:
            self.status_var.set("Connected")
        else:
            self.status_var.set(msg)


    def update(self):
        pass


# Class for plotting page

class PlotPage(ttk.Frame):

    def __init__(self, parent,tube_interface):
        # Run parent frame setup before adding our own content.
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        # Save reference to tube interface for later use.
        self.tube_interface = tube_interface

        # Get values to plot from hardware list of registers.
        self._REGISTERS = dict(zip(self.tube_interface.get_register_names(),self.tube_interface.get_register_keys()))
        
        # Each register gets empty list to store its readings over time.
        self.y_data = {name: [] for name in self._REGISTERS}

        # Track whether currently logging (True) or not (False).        
        self._logging = False
        # Will store the time logging started, used to calculate elapsed time.
        self._start_time = None

        # Stores one elapsed-time value per poll cycle, parallel to y_data.
        self.timestamps = []
        
        # Path to write autosave snapshots to, chosen once when logging starts.
        self.autosave_path = None
        # Holds the id returned by self.after() so autosave can be cancelled on stop.
        self._autosave_job = None

        # One True/False variable per register, linked to each checkbox.
        # First 3 (the temperature channels) start ticked, flow rates start unticked.
        self.enabled = {name: BooleanVar(value=(i < 3))
                        for i, name in enumerate(self._REGISTERS)}
        

        self.inner = add_scrollbars(self)
        
        # Left panel box with border and title "Variables".
        left = ttk.LabelFrame(self.inner, text="Variables", padding=(8,4))
        left.grid(column=1, row=1, sticky=(N,S), padx=(0,10), pady=4)

        names = list(self._REGISTERS.keys())
        row = 0

        ttk.Label(left, text="Check to plot:").grid(column=1, row=row, columnspan=2, sticky=W, pady=(0,6))
        row += 1

        # Two-column grid of checkboxes, packed into its own sub-frame so it
        # only uses ONE row in `left`'s grid.
        checkbox_frame = ttk.Frame(left)
        checkbox_frame.grid(column=1, row=row, columnspan=2, sticky=W)
        for i, name in enumerate(names):
            c, r = i % 2, i // 2
            ttk.Checkbutton(checkbox_frame, text=name, variable=self.enabled[name],
                            command=self._refresh_lines).grid(column=c, row=r, sticky=W, padx=(0,12), pady=2)
        row += 1

        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=row, columnspan=2, sticky=(W,E), pady=8)
        row += 1

        ttk.Label(left, text="Live values:").grid(column=1, row=row, columnspan=2, sticky=W, pady=(0,4))
        row += 1

        self.live_labels = {}
        for name in names:
            ttk.Label(left, text=name+":").grid(column=1, row=row, sticky=W, pady=1)
            lbl = ttk.Label(left, text="--", width=8, anchor="e")
            lbl.grid(column=2, row=row, sticky=E, pady=1)
            self.live_labels[name] = lbl
            row += 1

        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=row, columnspan=2, sticky=(W,E), pady=8)
        row += 1

        self.start_btn = ttk.Button(left, text="Start Logging", command=self._start)
        self.start_btn.grid(column=1, row=row, columnspan=2, sticky=(W,E), pady=2)
        row += 1

        self.stop_btn = ttk.Button(left, text="Stop Logging", command=self._stop, state=DISABLED)
        self.stop_btn.grid(column=1, row=row, columnspan=2, sticky=(W,E), pady=2)
        row += 1

        ttk.Button(left, text="Clear Data", command=self._clear).grid(
            column=1, row=row, columnspan=2, sticky=(W,E), pady=2)
        row += 1

        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=row, columnspan=2, sticky=(W,E), pady=8)
        row += 1

        ttk.Button(left, text="Save to CSV", command=self._save_csv).grid(
            column=1, row=row, columnspan=2, sticky=(W,E), pady=2)
        row += 1

        self.autosave_enabled = BooleanVar(value=False)
        ttk.Checkbutton(left, text="Autosave every", variable=self.autosave_enabled).grid(
            column=1, row=row, columnspan=2, sticky=W, pady=(8,2))
        row += 1

        autosave_frame = ttk.Frame(left)
        autosave_frame.grid(column=1, row=row, columnspan=2, sticky=W, pady=(0,8))
        row += 1

        self.autosave_interval = IntVar(value=5)
        vcmd_int = self.register(self._validate_interval)
        ttk.Entry(autosave_frame, textvariable=self.autosave_interval, width=5,
                  justify='center', validate='all', validatecommand=(vcmd_int, '%P')).grid(column=1, row=0)
        ttk.Label(autosave_frame, text="minutes").grid(column=2, row=0, padx=(4,0))

        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=row, columnspan=2, sticky=(W,E), pady=8)
        row += 1

        # Rescale controls 
        ttk.Label(left, text="Rescale Graph:").grid(column=1, row=row, columnspan=2, sticky=W, pady=(0,4))
        row += 1

        vcmd_float = self.register(self._validate_float)
        self.autoscale_x = BooleanVar(value=True)
        self.autoscale_y = BooleanVar(value=True)
        self.xmin, self.xmax = StringVar(), StringVar()
        self.ymin, self.ymax = StringVar(), StringVar()

        ttk.Checkbutton(left, text="Auto X", variable=self.autoscale_x,
                        command=self._apply_axis_limits).grid(column=1, row=row, columnspan=2, sticky=W)
        row += 1
        ttk.Label(left, text="X min:").grid(column=1, row=row, sticky=E)
        ttk.Entry(left, textvariable=self.xmin, width=8, validate='all',
                  validatecommand=(vcmd_float, '%P'), justify='center').grid(column=2, row=row, sticky=W)
        row += 1
        ttk.Label(left, text="X max:").grid(column=1, row=row, sticky=E)
        ttk.Entry(left, textvariable=self.xmax, width=8, validate='all',
                  validatecommand=(vcmd_float, '%P'), justify='center').grid(column=2, row=row, sticky=W)
        row += 1

        ttk.Checkbutton(left, text="Auto Y", variable=self.autoscale_y,
                        command=self._apply_axis_limits).grid(column=1, row=row, columnspan=2, sticky=W, pady=(6,0))
        row += 1
        ttk.Label(left, text="Y min:").grid(column=1, row=row, sticky=E)
        ttk.Entry(left, textvariable=self.ymin, width=8, validate='all',
                  validatecommand=(vcmd_float, '%P'), justify='center').grid(column=2, row=row, sticky=W)
        row += 1
        ttk.Label(left, text="Y max:").grid(column=1, row=row, sticky=E)
        ttk.Entry(left, textvariable=self.ymax, width=8, validate='all',
                  validatecommand=(vcmd_float, '%P'), justify='center').grid(column=2, row=row, sticky=W)
        row += 1

        ttk.Button(left, text="Apply", command=self._apply_axis_limits).grid(
            column=1, row=row, columnspan=2, sticky=(W,E), pady=(4,8))
        row += 1

        ttk.Label(left, text="Fit Y to line:").grid(column=1, row=row, columnspan=2, sticky=W)
        row += 1
        self.fit_target = StringVar(value=names[0] if names else "")
        ttk.OptionMenu(left, self.fit_target, self.fit_target.get(), *names).grid(column=1, row=row, sticky=W)
        ttk.Button(left, text="Fit", command=self._fit_to_line).grid(column=2, row=row, sticky=W)
        row += 1

        ttk.Separator(left, orient=HORIZONTAL).grid(column=1, row=row, columnspan=2, sticky=(W,E), pady=8)
        row += 1

        # Extra graph toggles: 3 additional graphs arranged around the
        # main plot (bottom-left, top-right, bottom-right), each with its
        # own on/off checkbox and independently chosen X/Y axes.
        axis_choices = ["Time"] + names
        extra_labels = ["Extra Graph 1 (bottom-left)", "Extra Graph 2 (top-right)", "Extra Graph 3 (bottom-right)"]
        self.extra_enabled = []
        self.extra_x_var = []
        self.extra_y_var = []

        for i in range(3):
            enabled_var = BooleanVar(value=False)
            x_var = StringVar(value="Time")
            y_var = StringVar(value=names[0] if names else "")
            self.extra_enabled.append(enabled_var)
            self.extra_x_var.append(x_var)
            self.extra_y_var.append(y_var)

            ttk.Checkbutton(left, text=f"Show {extra_labels[i]}", variable=enabled_var,
                            command=lambda i=i: self._toggle_extra_graph(i)).grid(
                column=1, row=row, columnspan=2, sticky=W, pady=(10 if i == 0 else 8, 4))
            row += 1

            ttk.Label(left, text="X axis:").grid(column=1, row=row, sticky=E)
            ttk.OptionMenu(left, x_var, x_var.get(), *axis_choices,
                           command=lambda _=None, i=i: self._refresh_extra_graph(i)).grid(column=2, row=row, sticky=W)
            row += 1
            ttk.Label(left, text="Y axis:").grid(column=1, row=row, sticky=E)
            ttk.OptionMenu(left, y_var, y_var.get(), *names,
                           command=lambda _=None, i=i: self._refresh_extra_graph(i)).grid(column=2, row=row, sticky=W)
            row += 1

        self.status_var = StringVar(value="Not logging")
        ttk.Label(left, textvariable=self.status_var).grid(column=1, row=row, columnspan=2, sticky=W, pady=(8,0))

        # Graph area with two columns: Left column = main plot + its own
        # toolbar. Right column = Single figure containing all 3 extra graphs
        # as stacked subplots (instead of 3 separate Figures), plus a
        # single shared toolbar where dragging pan/zoom in any one of the 3
        # subplots affects only that subplot (standard matplotlib toolbar).
        self.graph_container = ttk.Frame(self.inner)
        self.graph_container.grid(column=2, row=1, sticky=(N,S,E,W))
        self.graph_container.columnconfigure(0, weight=1)
        self.graph_container.columnconfigure(1, weight=1)
        self.graph_container.rowconfigure(0, weight=1)
        self.graph_container.rowconfigure(1, weight=0)

        # Main plot (left column)
        self.fig = Figure(figsize=(7,5))
        self.fig.set_facecolor("#d9d9d9")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Value")
        self.ax.set_title("Live Sensor Data")
        self.fig.subplots_adjust(left=0.15)

        self.lines = {}
        for name in names:
            line, = self.ax.plot([], [], label=name, linewidth=1.5)
            self.lines[name] = line
        self.ax.legend(loc="upper left", fontsize=7)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_container)
        self.canvas.get_tk_widget().grid(column=0, row=0, sticky=(N,S,E,W))

        # True while the main toolbar's pan or zoom tool is active, so
        # _poll and _apply_axis_limits know to leave the axes alone rather
        # than fight the user's manual view with autoscale every second.
        self._toolbar_nav_active = False

        toolbar_frame = ttk.Frame(self.graph_container)
        toolbar_frame.grid(column=0, row=1, sticky=(W,E))
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame, pack_toolbar=False)
        self.toolbar.pack(side=LEFT)
        self.toolbar.update()

        _orig_pan = self.toolbar.pan
        _orig_zoom = self.toolbar.zoom

        def _tracked_pan(*args):
            _orig_pan(*args)
            self._toolbar_nav_active = self.toolbar.mode.name == "PAN"

        def _tracked_zoom(*args):
            _orig_zoom(*args)
            self._toolbar_nav_active = self.toolbar.mode.name == "ZOOM"

        self.toolbar.pan = _tracked_pan
        self.toolbar.zoom = _tracked_zoom

        # Extra graphs (right column): one figure, three stacked
        # subplots. `hspace` sets the vertical gap between them, which is
        # the wspace/hspace parameter from before, actually in use
        # since these are subplots of a single Figure.
        self.extras_fig = Figure(figsize=(7,7))
        self.extras_fig.set_facecolor("#d9d9d9")
        self.extras_fig.subplots_adjust(left=0.15, hspace=0.5)

        extra_colors = ['tab:orange', 'tab:green', 'tab:purple']
        self.extra_axes = []
        self.extra_lines = []
        for i in range(3):
            ax = self.extras_fig.add_subplot(3, 1, i + 1)
            line, = ax.plot([], [], linewidth=1.5, color=extra_colors[i])
            ax.set_visible(False)  # hidden until its checkbox is ticked
            self.extra_axes.append(ax)
            self.extra_lines.append(line)

        self.extras_canvas = FigureCanvasTkAgg(self.extras_fig, master=self.graph_container)
        self.extras_canvas.get_tk_widget().grid(column=1, row=0, sticky=(N,S,E,W), padx=(8,0))

        # Same pan/zoom-vs-autoscale tracking as the main toolbar, but for
        # whichever of the 3 extra subplots is currently being dragged in.
        self._extras_toolbar_nav_active = False

        extras_toolbar_frame = ttk.Frame(self.graph_container)
        extras_toolbar_frame.grid(column=1, row=1, sticky=(W,E), padx=(8,0))
        self.extras_toolbar = NavigationToolbar2Tk(self.extras_canvas, extras_toolbar_frame, pack_toolbar=False)
        self.extras_toolbar.pack(side=LEFT)
        self.extras_toolbar.update()

        _orig_extras_pan = self.extras_toolbar.pan
        _orig_extras_zoom = self.extras_toolbar.zoom

        def _tracked_extras_pan(*args):
            _orig_extras_pan(*args)
            self._extras_toolbar_nav_active = self.extras_toolbar.mode.name == "PAN"

        def _tracked_extras_zoom(*args):
            _orig_extras_zoom(*args)
            self._extras_toolbar_nav_active = self.extras_toolbar.mode.name == "ZOOM"

        self.extras_toolbar.pan = _tracked_extras_pan
        self.extras_toolbar.zoom = _tracked_extras_zoom

        self.inner.columnconfigure(2, weight=1)
        self.inner.rowconfigure(1, weight=1)

    def _validate_interval(self, P):
        # Only allow digits (whole minutes) or an empty field while typing.
        return P.isdigit() or P == ""

    def _refresh_lines(self):
        # Called when any checkbox is clicked, shows or hides each line accordingly.
        for name, line in self.lines.items():
            line.set_visible(self.enabled[name].get())
        self.canvas.draw_idle()

    def _validate_float(self, P):
        if P in ("", "-", "."):
            return True
        try:
            float(P)
            return True
        except ValueError:
            return False

    def _apply_axis_limits(self):
        # Turn off the toolbar's pan/zoom tool if it's on, since the user will
        # be taking manual control of the view via these fields.
        # Re-invoking whichever tool is currently active toggles it off the
        # same way clicking its button would, keeping the button's pressed
        # state and internal mode synced.
        if self._toolbar_nav_active:
            if self.toolbar.mode.name == "PAN":
                self.toolbar.pan()
            elif self.toolbar.mode.name == "ZOOM":
                self.toolbar.zoom()

        if self.autoscale_x.get():
            self.ax.autoscale(axis='x')
        else:
            try:
                self.ax.set_xlim(float(self.xmin.get()), float(self.xmax.get()))
            except ValueError:
                pass

        if self.autoscale_y.get():
            self.ax.autoscale(axis='y')
        else:
            try:
                self.ax.set_ylim(float(self.ymin.get()), float(self.ymax.get()))
            except ValueError:
                pass

        self.canvas.draw_idle()

    def _fit_to_line(self):
        data = self.y_data.get(self.fit_target.get(), [])
        if not data:
            return
        ymin, ymax = min(data), max(data)
        pad = (ymax - ymin) * 0.05 or 0.5
        self.autoscale_y.set(False)
        self.ymin.set(f"{ymin - pad:.3f}")
        self.ymax.set(f"{ymax + pad:.3f}")
        self._apply_axis_limits()

    def _toggle_extra_graph(self, i):
        # All 3 extra subplots live in one shared figure now, so toggling
        # just shows/hides that particular subplot rather than adding or
        # removing a widget from the grid — the layout never changes size.
        self.extra_axes[i].set_visible(self.extra_enabled[i].get())
        if self.extra_enabled[i].get():
            self._refresh_extra_graph(i)
        self.extras_canvas.draw_idle()

    def _refresh_extra_graph(self, i):
        if not self.extra_enabled[i].get():
            return
        xchoice, ychoice = self.extra_x_var[i].get(), self.extra_y_var[i].get()
        ydata = self.y_data.get(ychoice, [])
        xdata = self.timestamps if xchoice == "Time" else self.y_data.get(xchoice, [])
        n = min(len(xdata), len(ydata))
        self.extra_lines[i].set_data(xdata[:n], ydata[:n])
        self.extra_axes[i].set_xlabel(xchoice)
        self.extra_axes[i].set_ylabel(ychoice)
        # Don't fight the extras toolbar's pan/zoom tool while it's active.
        if not self._extras_toolbar_nav_active:
            self.extra_axes[i].relim()
            self.extra_axes[i].autoscale_view()
    
    def _start(self):
        # Refuse to start if not connected to the furnace 
        # (also, widget currently stops responding if this occurs).
        if self.tube_interface is None or not self.tube_interface.is_connected():
            self.status_var.set("Not connected; go to Settings first")
            return

        # If autosave is ticked, ask where to save before logging begins,
        # so it doesn't prompt mid-run. Cancel start if user backs out.
        if self.autosave_enabled.get():
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=time.strftime("tube_log_%Y%m%d_%H%M%S.csv"),
                title="Choose autosave location"
            )
            if not filepath:
                self.status_var.set("Autosave cancelled. logging not started")
                return
            self.autosave_path = filepath
        else:
            self.autosave_path = None

        self._logging = True
        self._start_time = time.time()
        # Grey out Start, enable Stop.
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.status_var.set("Logging...")
        # Begin the polling loop.
        self._poll()

        # Begin the autosave timer if enabled.
        if self.autosave_enabled.get():
            interval_ms = max(self.autosave_interval.get(), 1) * 60 * 1000
            self._autosave_job = self.after(interval_ms, self._autosave_tick)

    def _stop(self):
        # Setting _logging to False causes _poll to exit on its next run.
        self._logging = False
        # Re-enable Start, grey out Stop.
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.status_var.set("Stopped")

        # Cancel any pending autosave tick so it doesn't run after stopping.
        if self._autosave_job is not None:
            self.after_cancel(self._autosave_job)
            self._autosave_job = None

    def _clear(self):
        # Wipe all stored data lists.
        for lst in self.y_data.values():
            lst.clear()
        self.timestamps.clear()
        # Reset all plot lines to empty.
        for line in self.lines.values():
            line.set_data([], [])
        # Reset all live value labels back to "--".
        for lbl in self.live_labels.values():
            lbl.config(text="--")
        for line in self.extra_lines:
            line.set_data([], [])
        for ax in self.extra_axes:
            ax.relim()
        self.ax.relim()
        self.canvas.draw_idle()
        self.extras_canvas.draw_idle()
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
        self.timestamps.append(elapsed)

        for name, key in self._REGISTERS.items():
            
            val = self.tube_interface.get_value(key)
            self.y_data[name].append(val)
            
            # Update the live label, formatted to 2 decimal places (will update if equipment accuracy is better).
            self.live_labels[name].config(text=f"{val:.2f}")

            # Only update the line if this register's checkbox is ticked.
            # Full history is always plotted; zoom/pan via the axis controls
            # below to view earlier data instead of it being discarded.
            if self.enabled[name].get():
                data = self.y_data[name]
                self.lines[name].set_data(range(len(data)), data)

        # Only autoscale the axes the user hasn't pinned to manual limits,
        # and never fight the toolbar's pan/zoom tool while it's active.
        if not self._toolbar_nav_active:
            self.ax.relim()
            if self.autoscale_x.get():
                self.ax.autoscale_view(scalex=True, scaley=False)
            if self.autoscale_y.get():
                self.ax.autoscale_view(scalex=False, scaley=True)
        self.canvas.draw_idle()
        for i in range(3):
            self._refresh_extra_graph(i)
        self.extras_canvas.draw_idle()
        self.status_var.set(f"Logging: {elapsed:.0f}s elapsed")

    def update(self):
        self._poll()
        
    def _save_csv(self, path=None, silent=False):
        # Writes all recorded data to CSV. If path is None, prompts the user;
        # silent=True suppresses "no data" message and uses status update
        # (used by the autosave timer so as to not interrupt manual saves).
        if not self.timestamps:
            if not silent:
                self.status_var.set("No data to save")
            return

        filepath = path
        if filepath is None:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=time.strftime("tube_log_%Y%m%d_%H%M%S.csv")
            )
            if not filepath:
                return  # user cancelled

        names = list(self._REGISTERS.keys())

        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Elapsed (s)"] + names)
                for i, t in enumerate(self.timestamps):
                    row = [f"{t:.2f}"]
                    for name in names:
                        vals = self.y_data[name]
                        row.append(vals[i] if i < len(vals) else "")
                    writer.writerow(row)
            if silent:
                self.status_var.set(f"Autosaved: {time.strftime('%H:%M:%S')}")
            else:
                self.status_var.set(f"Saved to {filepath.split('/')[-1]}")
        except Exception as e:
            self.status_var.set(f"Save failed: {e}")

    def _autosave_tick(self):
        # Runs every N minutes while logging is active and autosave is enabled.
        if not self._logging:
            return
        if self.autosave_enabled.get() and self.autosave_path:
            self._save_csv(path=self.autosave_path, silent=True)

        interval_ms = max(self.autosave_interval.get(), 1) * 60 * 1000
        self._autosave_job = self.after(interval_ms, self._autosave_tick)


# Class to control gas panel items: valve states, selected gas, and MFC flows

class GasPanel(ttk.Frame):

    def create_valve(self,x,y,size,third_port,rot=0):

        # Create triangle vertices and rotate by rot:
        vert = [(size/2,size/2*math.sqrt(3)),(-size/2,size/2*math.sqrt(3))]

        vert[0] = (vert[0][0] * math.cos(rot) + vert[0][1] * math.sin(rot), vert[0][0] * -math.sin(rot) + vert[0][1] * math.cos(rot))
        vert[1] = (vert[1][0] * math.cos(rot) + vert[1][1] * math.sin(rot), vert[1][0] * -math.sin(rot) + vert[1][1] * math.cos(rot))

        # Create a list of polygons (triangles) making up the valve and return.
        poly_list = []
        poly_list.append(self.canvas.create_polygon(x,y,x+vert[0][0],y+vert[0][1],x+vert[1][0],y+vert[1][1],fill='white',outline='black'))
        poly_list.append(self.canvas.create_polygon(x,y,x-vert[0][0],y-vert[0][1],x-vert[1][0],y-vert[1][1],fill='white',outline='black'))

        if third_port==1:
            poly_list.append(self.canvas.create_polygon(x,y,x+size/2*math.sqrt(3),y+size/2,x+size/2*math.sqrt(3),y-size/2,fill='white',outline='black'))
        elif third_port==-1:
            poly_list.append(self.canvas.create_polygon(x,y,x-size/2*math.sqrt(3),y+size/2,x-size/2*math.sqrt(3),y-size/2,fill='white',outline='black'))

        return poly_list

    def create_pipe(self,x1,y1,x2,y2):
        return self.canvas.create_line(x1,y1,x2,y2)

    def create_pump(self, x, y, size):
        self.canvas.create_oval(x-size/2,y-size/2,x+size/2,y+size/2,fill='white',outline='black')
        self.canvas.create_line(x-size/2*math.cos(math.pi/4),y+size/2*math.sin(math.pi/4),x+size/2*math.cos(math.pi/12),y+size/2*math.sin(math.pi/12))
        self.canvas.create_line(x-size/2*math.cos(math.pi/4),y-size/2*math.sin(math.pi/4),x+size/2*math.cos(math.pi/12),y-size/2*math.sin(math.pi/12))

    def _validateFlow(self,P):
        valid = (P.replace('.','',1).isdigit() or P=="")
        return valid
        

    def __init__(self, parent,tube_interface):
        # Run parent frame setup before adding our own content.
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        # Store reference to tube interface for later use.
        self.tube_interface = tube_interface

        # Rescale tube image using HAMMING filter (5) for sharper image.
        self.tube_img = ImageTk.PhotoImage(Image.open("tubedwg.png").resize((500,300),resample=Image.Resampling.HAMMING))

        # Container frame holds the canvas + horizontal scrollbar, so the
        # canvas can be scrolled when the window is narrower than 1200px
        # (e.g. when partially minimized to fit multiple tabs side by side).
        canvas_frame = ttk.Frame(self)
        canvas_frame.grid(column=1,row=1,columnspan=4,sticky=(N,S,E,W))
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

        # Prepare canvas
        self.canvas = Canvas(canvas_frame,width=1200,height=700,background="#d9d9d9",highlightthickness=0)
        self.canvas.grid(column=0,row=0,sticky=(N,S,E,W))

        self.vbar = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=self.canvas.yview)
        self.vbar.grid(column=1,row=0,sticky=(N,S))

        self.hbar = ttk.Scrollbar(canvas_frame, orient=HORIZONTAL, command=self.canvas.xview)
        self.hbar.grid(column=0,row=1,sticky=(W,E))
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)        

        # Store pipes for specific valve states
        self.pipes = [[],[],[],[]]
        # Draw P&ID pipes and valves
        p1 = self.create_pipe(100,50, 100,100)
        self.pipes[0].append(p1)    
        self.pipes[1].append(p1)

        p2 = self.create_pipe(100,100,100,200)
        self.pipes[0].append(p2)
        self.pipes[1].append(p2)

        p3 = self.create_pipe(100,200,160,200)
        self.pipes[0].append(p3)
        self.pipes[2].append(p3)
        p4 = self.create_pipe(160,200,160,50)
        self.pipes[0].append(p4)
        self.pipes[2].append(p4)

        p5 = self.create_pipe(100,200,100,300)
        self.pipes[0].append(p5)
        self.pipes[1].append(p5)
        self.pipes[2].append(p5)

        p6 = self.create_pipe(100,300,40, 300)
        self.pipes[0].append(p6)
        self.pipes[3].append(p6)

        p7 = self.create_pipe(40, 300,40, 50)
        self.pipes[0].append(p7)
        self.pipes[3].append(p7)

        p8 = self.create_pipe(100,300,100,500)
        self.pipes[0].append(p8)
        self.pipes[1].append(p8)
        self.pipes[2].append(p8)
        self.pipes[3].append(p8)

        p9 = self.create_pipe(100,500,400,500)
        self.pipes[0].append(p9)
        self.pipes[1].append(p9)
        self.pipes[2].append(p9)
        self.pipes[3].append(p9)

        self.create_pipe(400,500,1100,500)
        self.create_pipe(900,500,900,425)
        self.create_pipe(900,425,1050,425)
        self.create_pipe(1050,425,1050,500)
        
        self.valves = {}
        self.valves[1] = self.create_valve(100,100,25,0,0)
        self.valves[2] = self.create_valve(100,200,25,1,0)
        self.valves[3] = self.create_valve(100,300,25,-1,0)

        self.create_valve(950,500,25,0,math.pi/2)
        self.create_valve(975,425,25,0,math.pi/2)

        self.create_pump(1010,500,35)

        # Add labels
        self.canvas.create_text(100,35,text="N2",font=('Calibri', 15))
        self.canvas.create_text(160,35,text="O2",font=('Calibri', 15))
        self.canvas.create_text(40,35,text="N2/H2",font=('Calibri', 15))

        # MFC & PT Data box templates
        self.mfc_flow = StringVar(value="---")
        self.canvas.create_rectangle(150,480,225,520,fill='white',outline='black')
        self.canvas.create_window(187.5,500,window=ttk.Label(
            self.canvas,textvariable=self.mfc_flow,background='white',font=('Calibri',10)))

        self.tube_pressure = StringVar(value="---")
        self.canvas.create_rectangle(775,480,850,520,fill='white',outline='black')
        self.canvas.create_window(812.5,500,window=ttk.Label(
            self.canvas,textvariable=self.tube_pressure,background='white',font=('Calibri',10)))
        
        self.canvas.create_image(500,545,image=self.tube_img,anchor='center')
        self.t1_str = StringVar(value="---")
        self.t2_str = StringVar(value="---")
        self.t3_str = StringVar(value="---")

        self.canvas.create_window(499,629,window=ttk.Label(
            self.canvas,textvariable=self.t1_str,background='white',font=('Calibri',10)))
        self.canvas.create_window(411,629,window=ttk.Label(
            self.canvas,textvariable=self.t2_str,background='white',font=('Calibri',10)))
        self.canvas.create_window(587,629,window=ttk.Label(
            self.canvas,textvariable=self.t3_str,background='white',font=('Calibri',10)))

        ### Gas Control layout
        gpanel = ttk.LabelFrame(self,text="Gas Control",padding=(8,4),width=200,height=300)
        gpanel.grid_propagate(0)

        # Store controls for enabling & disabling
        self.controls = []

        # Register validation function with tkinter frame
        self.flowSet = DoubleVar(value=0.0)
        self.vcmd = parent.register(self._validateFlow)

        self.tempSet = IntVar(value=150)
        self.tRamp = IntVar(value=5)
        self.dwell = IntVar(value=60)

        self.tempSet2 = IntVar(value=150)
        self.tRamp2 = IntVar(value=5)
        self.dwell2 = IntVar(value=60)

        # Header label above the controls.
        ttk.Label(gpanel, text="Gas Selection:").grid(column=1, row=0, sticky=W, pady=(0,6))

        # Add controls
        n2button = ttk.Button(gpanel, text="Nitrogen", command=lambda: self.tube_interface.set_gas(1))
        n2button.grid(column=1,row=1,sticky=N,columnspan=2)
        self.controls.append((
            n2button,
            lambda: self.tube_interface.is_connected() and self.tube_interface.active_gas != 1
        ))

        o2button = ttk.Button(gpanel, text="Oxygen", command=lambda: self.tube_interface.set_gas(2))
        o2button.grid(column=1,row=2,sticky=N,columnspan=2)
        self.controls.append((
            o2button,
            lambda: self.tube_interface.is_connected() and self.tube_interface.active_gas != 2
        ))
        
        fgbutton = ttk.Button(gpanel, text="Forming Gas", command=lambda: self.tube_interface.set_gas(3))
        fgbutton.grid(column=1,row=3,sticky=N,columnspan=2)
        self.controls.append((
            fgbutton,
            lambda: self.tube_interface.is_connected() and self.tube_interface.active_gas != 3
        ))
        
        ttk.Label(gpanel, text="MFC Setpoint:").grid(column=1, row=4, sticky=W, pady=(20,0))

        mfcentry = ttk.Entry(gpanel,textvariable=self.flowSet,validate='all',width=10,validatecommand=(self.vcmd,'%P'),justify='center')
        mfcentry.grid(column=1,row=5)
        self.controls.append((
            mfcentry,
            lambda: self.tube_interface.is_connected() 
        ))

        self.flowscale = ttk.Scale(gpanel,variable=self.flowSet,orient=VERTICAL,from_=MAXFLOW,to=0.0,length=50)
        self.flowscale['command'] = lambda val : self.flowSet.set(f'{float(val):.02f}')
        self.flowscale.grid(column=2,row=5,sticky=(W,E),padx=10)
        self.controls.append((
            self.flowscale,
            lambda: self.tube_interface.is_connected()
        ))

        disablebutton = ttk.Button(gpanel,text="Disable Gases", command=lambda: self.tube_interface.set_gas(0))
        disablebutton.grid(column=1,row=6,sticky=N,columnspan=2,pady=20)
        self.controls.append((
            disablebutton,
            lambda: self.tube_interface.is_connected() and self.tube_interface.active_gas != 0
        ))
        
        self.canvas.create_window(300,175,window=gpanel)

        ### Temp Control Layout
        tpanel = ttk.LabelFrame(self,text="Temp. Control",padding=(8,4),width=200,height=300)
        tpanel.grid_propagate(0)

        ttk.Label(tpanel, text = "Stage 1:",justify='center').grid(column=1,row=0,sticky=(W,E),pady=(0,6),columnspan=3)
        ttk.Label(tpanel, text = "SP: ").grid(column=1,row=1,pady=3,padx = 3, sticky=E)
        tempentry = ttk.Entry(tpanel,textvariable=self.tempSet,validate='all',validatecommand=(self.vcmd,'%P'),width=6,justify='center')
        tempentry.grid(column=2,row=1,sticky=W)
        self.controls.append((
            tempentry,
            lambda: self.tube_interface.is_connected()
        ))
        ttk.Label(tpanel, text = " °C").grid(column=3,row=1,sticky=W)

        ttk.Label(tpanel, text = "Ramp: ").grid(column=1,row=2,sticky=E,pady=6,padx = 3)
        rampentry = ttk.Entry(tpanel,textvariable=self.tRamp,validate='all',validatecommand=(self.vcmd,'%P'),width=6,justify='center')
        rampentry.grid(column=2,row=2,sticky=W)
        self.controls.append((
            rampentry,
            lambda: self.tube_interface.is_connected()
        ))
        ttk.Label(tpanel, text = " °C/min").grid(column=3,row=2,sticky=W)

        ttk.Label(tpanel, text = "Dwell: ").grid(column=1,row=3,sticky=E,pady=6,padx=3)
        dwellentry = ttk.Entry(tpanel,textvariable=self.dwell,validate='all',validatecommand=(self.vcmd,'%P'),width=6,justify='center')
        dwellentry.grid(column=2,row=3,sticky=W)
        self.controls.append((
            dwellentry,
            lambda: self.tube_interface.is_connected()
        ))
        ttk.Label(tpanel, text = " min").grid(column=3,row=3,sticky=W)

        ttk.Label(tpanel, text = "Stage 2:",justify='center').grid(column=1,row=4,sticky=(N,S,W,E),pady=6)
        
        self.use_second_step = StringVar(value='0')
        ttk.Checkbutton(tpanel,variable=self.use_second_step).grid(column=2,row=4,pady=6)
        
        ttk.Label(tpanel, text = "SP: ").grid(column=1,row=5,pady=3,padx = 3, sticky=E)
        tempentry2 = ttk.Entry(tpanel,textvariable=self.tempSet2,validate='all',validatecommand=(self.vcmd,'%P'),width=6,justify='center')
        tempentry2.grid(column=2,row=5,sticky=W)
        self.controls.append((
            tempentry2,
            lambda: self.tube_interface.is_connected() and self.use_second_step.get() == '1'
        ))
        ttk.Label(tpanel, text = " °C").grid(column=3,row=5,sticky=W)

        ttk.Label(tpanel, text = "Ramp: ").grid(column=1,row=6,sticky=E,pady=6,padx = 3)
        rampentry2 = ttk.Entry(tpanel,textvariable=self.tRamp2,validate='all',validatecommand=(self.vcmd,'%P'),width=6,justify='center')
        rampentry2.grid(column=2,row=6,sticky=W)
        self.controls.append((
            rampentry2,
            lambda: self.tube_interface.is_connected() and self.use_second_step.get() == '1'
        ))
        ttk.Label(tpanel, text = " °C/min").grid(column=3,row=6,sticky=W)

        ttk.Label(tpanel, text = "Dwell: ").grid(column=1,row=7,sticky=E,pady=6,padx=3)
        dwellentry2 = ttk.Entry(tpanel,textvariable=self.dwell2,validate='all',validatecommand=(self.vcmd,'%P'),width=6,justify='center')
        dwellentry2.grid(column=2,row=7,sticky=W)
        self.controls.append((
            dwellentry2,
            lambda: self.tube_interface.is_connected() and self.use_second_step.get() == '1'
        ))
        ttk.Label(tpanel, text = " min").grid(column=3,row=7,sticky=W)

        
        self.canvas.create_window(500,175,window=tpanel)

        ### Process Control Layout
        ppanel = ttk.LabelFrame(self,text="Process Control",padding=(8,4),width=200,height=300)
        ppanel.grid_propagate(0)

        ttk.Label(ppanel,text="Process:").grid(column=1,row=0,sticky=(N,W,E),pady=(0,6))
        startbutton = ttk.Button(ppanel,text="Start",command=self.start_recipe)
        startbutton.grid(column=1,row=1,sticky=N)
        self.controls.append((
            startbutton,
            lambda: self.tube_interface.is_connected()
        ))
        stopbutton = ttk.Button(ppanel,text="Stop",command=self.stop_recipe,state='disabled')
        stopbutton.grid(column=1,row=2,sticky=N)
        self.controls.append((
            stopbutton,
            lambda: self.tube_interface.is_connected()
        ))

        ttk.Label(ppanel,text="Return all to Idle:").grid(column=1,row=3,sticky=(N,W,E),pady=6)
        idlebutton = ttk.Button(ppanel,text="Idle",command=lambda: print("Placeholder"))
        idlebutton.grid(column=1,row=4,sticky=N)
        self.controls.append((
            idlebutton,
            lambda: self.tube_interface.is_connected()
        ))

        ttk.Label(ppanel,text="Recipe:").grid(column=1,row=5,sticky=(N,W,E),pady=6)
        sendbutton = ttk.Button(ppanel,text="Send", command = self.send_recipe)
        sendbutton.grid(column=1,row=6,sticky=N)
        self.controls.append((
            sendbutton,
            lambda: self.tube_interface.is_connected()
        ))


        self.canvas.create_window(700,175,window=ppanel)

        # Must run last, after every item/window has been drawn on the
        # canvas, so bbox("all") covers the full extent of the diagram.
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    
    def send_recipe(self):

        if self.tube_interface.is_connected():

            self.tube_interface.send_recipe_params(self.tempSet.get(), self.tRamp.get(), self.dwell.get(), self.tempSet2.get(), self.tRamp2.get(), self.dwell2.get())
            
    def start_recipe(self):

        if self.tube_interface.is_connected():

            self.tube_interface.start_recipe()

    def stop_recipe(self):

        if self.tube_interface.is_connected():

            self.tube_interface.stop_recipe()
        
    def update(self):

        if self.tube_interface.is_connected():
            self.mfc_flow.set('{0:.2f}'.format(self.tube_interface.get_value("FLOW_PV")))
            self.t1_str.set(self.tube_interface.get_value("T1_PV"))
            self.t2_str.set(self.tube_interface.get_value("T2_PV"))
            self.t3_str.set(self.tube_interface.get_value("T3_PV"))
        
            self.tube_interface.set_mfc_flow(self.flowSet.get())

        # Set valve & pipe highlights based on active gas
        # TO-DO: Set valve states directly from PLC registers
        for k,v in self.valves.items():
            if k == self.tube_interface.active_gas:
                self.canvas.itemconfigure(v[0],fill='black')
                if len(v) > 2:
                    self.canvas.itemconfigure(v[1],fill='white')
                    self.canvas.itemconfigure(v[2],fill='black')
                else:
                    self.canvas.itemconfigure(v[1],fill='black')

            elif k > self.tube_interface.active_gas and self.tube_interface.active_gas != 0:
                if len(v) > 2:
                    self.canvas.itemconfigure(v[0],fill='black')
                    self.canvas.itemconfigure(v[1],fill='black')
                    self.canvas.itemconfigure(v[2],fill='white')
                else:
                    self.canvas.itemconfigure(v[0],fill='white')
                    self.canvas.itemconfigure(v[1],fill='white')
            else:
                for valve in v:
                    self.canvas.itemconfigure(valve,fill='white')

        for pipe in self.pipes[0]:
            self.canvas.itemconfigure(pipe,width=1)

        if self.tube_interface.active_gas != 0:
            for pipe in self.pipes[self.tube_interface.active_gas]:
                self.canvas.itemconfigure(pipe,width=4,fill='black')

        for entry in self.controls:
            
            if entry[1]():
                if str(entry[0]['state'])=='disabled':
                    entry[0].configure(state = 'normal')
            else:
                if str(entry[0]['state']) != 'disabled':
                    entry[0].configure(state= 'disabled')
