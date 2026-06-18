from tkinter import *
from tkinter import ttk


import interface
from modbusutil import ModbusConnector
from hardware import TubeInterface

# Initialize modbus connection and hardware handler with default parameters
modbusc = ModbusConnector()
tube_interface = TubeInterface(modbusc)

# Set up TK window and main frame
root = Tk()
root.title("Vacuum Tube Interface")

s=ttk.Style()
s.theme_use("alt")

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky = (N,W,E,S))

# Use a TK notebook to group different interface windows
tabs = ttk.Notebook(mainframe)

# Initialize the interface tabs, which extend ttk.Frame
gaspanel = interface.GasPanel(tabs, tube_interface)
tabs.add(gaspanel,text="Control")

plotting = interface.PlotPage(tabs, tube_interface)
tabs.add(plotting,text="Plotting")

settings = interface.SettingsPage(tabs, tube_interface)
tabs.add(settings,text="Settings")

# Configure columns, rows, and set default padding for all widgets
root.columnconfigure(0,weight=1)
root.rowconfigure(0,weight=1)

mainframe.columnconfigure(3,weight=1)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)


# Start TK main loop
root.mainloop()

