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
