from dataclasses import dataclass

import modbusutil

# Class to handle storing individual values and registers for PLC data

@dataclass
class Register:
    addr: int
    current_value: int
    name: str

# Class to handle communications with the tube furnace. Includes get and set methods for all variables of interest.

class TubeInterface:

    def __init__(self, modbusc):

        self.modbusc = modbusc

        # Registers in PLC memory for all variables of interest
        self.values = {

            "T1_PV" : Register(28672, 0, "Temperature 1 PV"),
            "T1_SV" : Register(0, 0, "Temperature 1 Set") 
        
        }
        pass

    # PROPERTY SETTER METHODS
    
    def set_temperature(self, temp_id, value):

        pass

    def set_gas(self, gas_id):

        pass

    def set_mfc_flow(self, flow_rate):

        pass

    # PROPERTY GETTER METHODS

    def get_temperature(self, temp_id):

        pass

    def get_pressure(self, p_id):

        pass

    def get_gas(self):

        pass

    def get_mfc_flow(self):

        pass

    def get_value(self, val_id):

        pass

    # UPDATE METHOD

    def update(self):

        pass
