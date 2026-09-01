from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk

from panels import settings_panel, gas_panel, plot_panel

UPDATE_RATE = 1000 # serial refresh rate, ms

class UserInterface():

    # Pass along update to all components
    def update_all(self):
        self.tube_interface.update()
        self.gaspanel.update()
        self.plotpanel.update()
        self.settingspanel.update()
        if self.tube_interface.is_connected():
            self.header_canvas.itemconfigure(self.con_light,fill="#00ff37")
        else:
            self.header_canvas.itemconfigure(self.con_light,fill="#014a2b")
        self.root.after(UPDATE_RATE,self.update_all)

    # Handle window close
    def on_close(self):
        self.modbusc.disconnect()
        self.root.destroy()

    def __init__(self, tube_interface,modbusc):

        self.tube_interface = tube_interface
        self.modbusc= modbusc

        # Set up TK window and main frame
        self.root = Tk()
        self.root.title("Vacuum Tube Interface")

        s=ttk.Style()
        s.theme_use("alt")

        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky = (N,W,E,S))

        # Create header with connection status
        self.header_canvas = Canvas(self.mainframe,width=1200,height=25,background="#d9d9d9",highlightthickness=0)

        self.header_canvas.create_text(1040,14,text="Connection Status:",anchor='center')
        self.con_light = self.header_canvas.create_oval(1100,4,1120,24,fill="#014a2b")


        # Use a TK notebook to group different interface windows
        self.tabs = ttk.Notebook(self.mainframe)

        # Initialize the interface tabs, which extend ttk.Frame
        self.gaspanel = gas_panel.GasPanel(self.tabs, self.tube_interface)
        self.tabs.add(self.gaspanel,text="Control")

        self.plotpanel = plot_panel.PlotPanel(self.tabs, self.tube_interface)
        self.tabs.add(self.plotpanel,text="Plotting")

        self.settingspanel = settings_panel.SettingsPanel(self.tabs, self.tube_interface)
        self.tabs.add(self.settingspanel,text="Settings")

        # Configure columns, rows, and set default padding for all widgets
        self.root.columnconfigure(0,weight=1)
        self.root.rowconfigure(0,weight=1)

        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(1, weight=1)

        self.header_canvas.grid(row=0, column=0, sticky=(W,E), pady=(5,0), padx=5)
        self.tabs.grid(row=1, column=0, sticky=(N,S,E,W), pady=(0,5), padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


        self.update_all()

    def start(self):              
        # Start TK main loop
        self.root.mainloop()









