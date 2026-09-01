from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk

import time
import math

MAXFLOW = 5.0
INITFLOW = 1.0

# Class to control gas panel items: valve states, selected gas, and MFC flows

class GasPanel(ttk.Frame):

    # UI Functions to create valves, pipes, and pumps
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


    # TODO improve validation function
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
        self.lock_img = ImageTk.PhotoImage(Image.open("lock.png").resize((25,25),resample=Image.Resampling.HAMMING))

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

        # Add lock symbols
        self.o2_lock = self.canvas.create_image(125,175, image=self.lock_img, anchor='center')
        self.fg_lock = self.canvas.create_image(75,275, image=self.lock_img, anchor='center')

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

        self.purge_timer = StringVar(value="-- / 60 min")
        
        self.canvas.create_window(411,629,window=ttk.Label(self.canvas,textvariable=self.t1_str,background='white',font=('Calibri',10)))
        self.canvas.create_window(499,629,window=ttk.Label(self.canvas,textvariable=self.t2_str,background='white',font=('Calibri',10)))        
        self.canvas.create_window(587,629,window=ttk.Label(self.canvas,textvariable=self.t3_str,background='white',font=('Calibri',10)))

        self.t1_indicator = self.canvas.create_oval(432,595,452,615,fill='white',outline='black')
        self.t2_indicator = self.canvas.create_oval(520,595,540,615,fill='white',outline='black')
        self.t3_indicator = self.canvas.create_oval(608,595,628,615,fill='white',outline='black')


        ### Gas Control layout
        gpanel = ttk.LabelFrame(self,text="Gas Control",padding=(8,4),width=200,height=350)
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
            lambda: self.tube_interface.is_connected() and self.tube_interface.active_gas != 2 and self.tube_interface.get_purge_status()
        ))
        
        fgbutton = ttk.Button(gpanel, text="Forming Gas", command=lambda: self.tube_interface.set_gas(3))
        fgbutton.grid(column=1,row=3,sticky=N,columnspan=2)
        self.controls.append((
            fgbutton,
            lambda: self.tube_interface.is_connected() and self.tube_interface.active_gas != 3 and self.tube_interface.get_purge_status()
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
        disablebutton.grid(column=1,row=6,sticky=N,columnspan=2,pady=(20,10))
        self.controls.append((
            disablebutton,
            lambda: self.tube_interface.is_connected() and self.tube_interface.active_gas != 0
        ))

        ttk.Label(gpanel,text="Purge (> 2 slm N2):").grid(column=1,row=7,pady=10,sticky=W)

        self.purgelabel = ttk.Label(gpanel,textvariable=self.purge_timer)
        self.purgelabel.grid(column=1,row=8,sticky=N,columnspan=2,pady=(0,20))
        
        self.canvas.create_window(300,200,window=gpanel)

        ### Temp Control Layout
        tpanel = ttk.LabelFrame(self,text="Temp. Control",padding=(8,4),width=200,height=350)
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

        
        self.canvas.create_window(500,200,window=tpanel)

        ### Process Control Layout
        ppanel = ttk.LabelFrame(self,text="Process Control",padding=(8,4),width=200,height=350)
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


        self.canvas.create_window(700,200,window=ppanel)

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
            
            if self.tube_interface.get_status(1) == 1:
                self.canvas.itemconfigure(self.t1_indicator,fill='orange')
            else:
                self.canvas.itemconfigure(self.t1_indicator,fill='white')

            if self.tube_interface.get_status(2) == 1:
                self.canvas.itemconfigure(self.t2_indicator,fill='orange')
            else:
                self.canvas.itemconfigure(self.t2_indicator,fill='white')

            if self.tube_interface.get_status(3) == 1:
                self.canvas.itemconfigure(self.t3_indicator,fill='orange')
            else:
                self.canvas.itemconfigure(self.t3_indicator,fill='white')


            self.purge_timer.set(str(self.tube_interface.get_value("PURGE_T")) + " / 60 min")
        
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

        if self.tube_interface.get_purge_status():
            self.canvas.itemconfigure(self.o2_lock,state='hidden')
            self.canvas.itemconfigure(self.fg_lock,state='hidden')
        else:
            self.canvas.itemconfigure(self.o2_lock,state='normal')
            self.canvas.itemconfigure(self.fg_lock,state='normal')


        for entry in self.controls:
            
            if entry[1]():
                if str(entry[0]['state'])=='disabled':
                    entry[0].configure(state = 'normal')
            else:
                if str(entry[0]['state']) != 'disabled':
                    entry[0].configure(state= 'disabled')
