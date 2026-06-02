import sys
import glob
import serial

from pymodbus.client import ModbusSerialClient
from pymodbus.transport import CommParams


# Class containing utility methods and state information for modbus PLC connection

class ModbusConnector:

    @classmethod
    def get_serial_ports(cls):

        # Utility function to list available serial ports
        # code modified from:
        # https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python

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


    # Constructor
    
    def __init__(self, port: str = "", baudrate: int = 37800, parity: str = "O",
                 databits: int = 8, stopbits: int = 1):

        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.databits = databits
        self.stopbits = stopbits

        self.connected = False

        self.modbusc = ModbusSerialClient(port = self.port, baudrate = self.baudrate, parity = self.parity, bytesize = self.databits, stopbits = self.stopbits)


    def connect(self):

        self.modbusc.connect()

        self.connected = True

    def disconnect(self):

        self.modbusc.close()

        self.connected = False

    def set_params(self,port: str, baudrate: int = 37800, parity: str = "O",
                 databits: int = 8, stopbits: int = 1):

        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.databits = databits
        self.stopbits = stopbits

        if self.modbusc.is_socket_open():
            self.disconnect()

        self.modbusc = ModbusSerialClient(port = self.port, baudrate = self.baudrate, parity = self.parity, bytesize = self.databits, stopbits = self.stopbits)

        if self.connected:
            self.connect()

    def get_float(self, register):

        resp = self.modbusc.read_holding_registers(register,count=2)
        val = ModbusSerialClient.convert_from_registers(resp.registers,ModbusSerialClient.DATATYPE.FLOAT32,word_order="little")

        return val
        
