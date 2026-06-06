from tkinter import *
from tkinter import ttk


from pymodbus.client import ModbusSerialClient
import interface


# Set up TK window and main frame
root = Tk()
root.title("Vacuum Tube Interface")

s=ttk.Style()
s.theme_use("alt")

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky = (N,W,E,S))

# Use a TK notebook to group different interface windows
tabs = ttk.Notebook(mainframe)

controls = interface.ControlPage(tabs)
tabs.add(controls,text="Controls")

gaspanel = ttk.Frame(tabs)
tabs.add(gaspanel,text="Gas Panel")

settings = interface.SettingsPage(tabs)

plotting = interface.PlotPage(tabs, settings_page=settings)
tabs.add(plotting,text="Plotting")

tabs.add(settings,text="Settings")


# Configure columns, rows, and set default padding for all widgets
root.columnconfigure(0,weight=1)
root.rowconfigure(0,weight=1)

mainframe.columnconfigure(3,weight=1)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

# Start TK main loop
root.mainloop()
