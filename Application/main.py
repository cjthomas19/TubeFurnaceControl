from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk


import interface
from modbusutil import ModbusConnector
from hardware import TubeInterface

UPDATE_RATE = 1000 # serial refresh rate, ms

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

# Create header with connection status
header_canvas = Canvas(mainframe,width=1200,height=25,background="#d9d9d9",highlightthickness=0)

header_canvas.create_text(1040,14,text="Connection Status:",anchor='center')
con_light = header_canvas.create_oval(1100,4,1120,24,fill="#014a2b")


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

mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(1, weight=1)

header_canvas.grid(row=0, column=0, sticky=(W,E), pady=(5,0), padx=5)
tabs.grid(row=1, column=0, sticky=(N,S,E,W), pady=(0,5), padx=5)


def update_all():
    tube_interface.update()
    gaspanel.update()
    plotting.update()
    settings.update()
    if tube_interface.is_connected():
        header_canvas.itemconfigure(con_light,fill="#00ff37")
    else:
        header_canvas.itemconfigure(con_light,fill="#014a2b")
    root.after(UPDATE_RATE,update_all)

update_all()
                        
# Handle window close
def on_close():
    modbusc.disconnect()
    root.destroy()
    
root.protocol("WM_DELETE_WINDOW", on_close)
# Start TK main loop
root.mainloop()

