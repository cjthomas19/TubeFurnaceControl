
from interface import UserInterface
from modbusutil import ModbusConnector
from hardware import TubeInterface

# Initialize modbus connection and hardware handler with default parameters
modbusc = ModbusConnector()
tube_interface = TubeInterface(modbusc)
gui = UserInterface(tube_interface,modbusc)
gui.start()







