from tkinter import *
from tkinter import ttk

import sys
import glob
import serial

import time

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from pymodbus.client import ModbusSerialClient

def serial_ports():

    # lists serial port names
    # code from here: https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python

    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    else:
        raise EnvironmentError('Unsupported Platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)

        except (OSError, serial.SerialException):
            pass
        
    return result

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

        ttk.Entry(self,textvariable=self.flowSet,width=15,validate='all',validatecommand=(self.vcmd,'%P')).grid(column=3,row=2,sticky=(W,E))
        ttk.Scale(self,variable=self.flowSet,orient=VERTICAL,from_=MAXFLOW,to=0.0).grid(column=4,row=1,rowspan=3,sticky=(W,E))

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


class SettingsPage(ttk.Frame):

    def __init__(self,parent):
        ttk.Frame.__init__(self,parent,padding=(3,12,12,12))

        self.ports = serial_ports()

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

        self.connected = False
        self.modbusc = None

        self.x_data = []
        self.y_data = []
        

        self.fig = Figure(figsize=(4,3))
        self.ax = self.fig.add_subplot(111)
        self.line,=self.ax.plot([],[],'k-',label="Live Data")
        self.ax.set_ylim(60,90)

        self.canvas = FigureCanvasTkAgg(self.fig,master=self)
        self.canvas.get_tk_widget().grid(column=3,row=1,rowspan=6,padx=12,pady=12)

        

    def check_int(self,P):

        return P=='' or P.isdigit()

    def update_plot(self):
        self.x_data.append(time.time() % 50)
        self.y_data.append(self.get_value())

        if len(self.x_data) > 50:
            self.x_data.pop(0)
            self.y_data.pop(0)

        self.line.set_data(range(len(self.y_data)),self.y_data)
        self.ax.set_xlim(0,len(self.y_data))
        self.canvas.draw()

        self.after(500,self.update_plot)

    def get_value(self):

        if self.modbusc.is_socket_open():
            pass
        else:
            self.modbusc.connect()

        resp = self.modbusc.read_holding_registers(28672,count=2)
        retval= ModbusSerialClient.convert_from_registers(resp.registers,ModbusSerialClient.DATATYPE.FLOAT32,word_order="little")

        return retval

    def connect(self):

        paritytab = {"Even" : "E", "Odd" : "O", "None" : "N"}

        print(self.port.get(),self.baudrate.get(),self.databits.get(),paritytab[self.parity.get()],self.stopbit.get())

        self.modbusc = ModbusSerialClient(port = self.port.get(), baudrate = self.baudrate.get(),
                                          bytesize=self.databits.get(), parity=paritytab[self.parity.get()],stopbits=self.stopbit.get())

        print("CONNECTING")

        print(self.modbusc.connect())
        print(self.modbusc.is_socket_open())

        resp = self.modbusc.read_holding_registers(28672,count=2)


        fl=ModbusSerialClient.convert_from_registers(resp.registers,ModbusSerialClient.DATATYPE.FLOAT32,word_order="little")
        print(fl)

        self.modbusc.close()

        self.update_plot()

        return

        

MAXFLOW = 5.0
INITFLOW = 1.0

root = Tk()
root.title("Vacuum Tube Interface")

s=ttk.Style()
print(s.theme_names())
s.theme_use("alt")

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky = (N,W,E,S))

tabs = ttk.Notebook(mainframe)

controls = ControlPage(tabs)
tabs.add(controls,text="Controls")

gaspanel = ttk.Frame(tabs)
tabs.add(gaspanel,text="Gas Panel")

plotting = ttk.Frame(tabs)
tabs.add(plotting,text="Plotting")

settings = SettingsPage(tabs)
tabs.add(settings,text="Settings")


root.columnconfigure(0,weight=1)
root.rowconfigure(0,weight=1)

mainframe.columnconfigure(3,weight=1)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.mainloop()
