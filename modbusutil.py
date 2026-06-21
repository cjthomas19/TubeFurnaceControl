import sys
import glob
import serial

from pymodbus.client import ModbusSerialClient
from pymodbus.transport import CommParams
from pymodbus.exceptions import ConnectionException, ModbusIOException


# Class containing utility methods and state information for modbus PLC connection
# TO-DO:
# * Implement error handling
# * Add "get" methods for additional datatypes (int, bool, potentially str)

class ModbusConnector:

    @classmethod
    def get_serial_ports(cls):

        # Utility function to list available serial ports
        # code modified from:
        # https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python

        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platfor.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
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


    # Constructor - default values based on AutomationDirect Click PLC defaults
    
    def __init__(self, port: str = "", baudrate: int = 38400, parity: str = "O",
                 databits: int = 8, stopbits: int = 1):

        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.databits = databits
        self.stopbits = stopbits

        self._test_register = 12345
        
        # Store connection state
        self.connected = False

        # Use pymodbus base level class for communication
        self.modbusc = ModbusSerialClient(port = self.port, baudrate = self.baudrate, parity = self.parity, bytesize = self.databits, stopbits = self.stopbits)


    # Initialize connection
    def connect(self):

        self.modbusc.connect()
        self.connected = False
        msg = ""
        try:
            self.modbusc.read_holding_registers(self._test_register)
        except ModbusIOException:
            msg = "Timeout"
        except ConnectionException:
            msg = "Connection Failed"
        else:
            msg = "Connected"
            self.connected = True
        
        return (self.connected, msg)

    # Close connection
    def disconnect(self):
        self.modbusc.close()
        self.connected = False

    # Change parameters by resetting connection
    def set_params(self,port: str, baudrate: int = 38400, parity: str = "O",
                 databits: int = 8, stopbits: int = 1):

        # Use method arguments to reset connection properties
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.databits = databits
        self.stopbits = stopbits

        # Disconnect before modifying connections
        if self.modbusc.is_socket_open():
            self.disconnect()

        # Create new modbus serial client object
        self.modbusc = ModbusSerialClient(port = self.port, baudrate = self.baudrate, parity = self.parity, bytesize = self.databits, stopbits = self.stopbits)

        # Re-connect only if we were already connected
        if self.connected:
            self.connect()

    # Read a floating point number from the given register
    def get_float(self, register):

        # 32-bit floats are stored in 2 consecutive registers
        resp = self.modbusc.read_holding_registers(register,count=2)
        
        # Convert to a 32-bit float datatype
        val = ModbusSerialClient.convert_from_registers(resp.registers,ModbusSerialClient.DATATYPE.FLOAT32,word_order="little")

        return val
        
