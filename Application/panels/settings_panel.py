from tkinter import *
from tkinter import ttk

from modbusutil import ModbusConnector
from hardware import TubeInterface

# Class for settings page

class SettingsPanel(ttk.Frame):

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
        hpanel = ttk.LabelFrame(self,text="Hardware",width=250,height=300)
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
