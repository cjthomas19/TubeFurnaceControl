from dataclasses import dataclass

import modbusutil

# Class to handle storing and accessing individual values and registers for PLC data

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
        # Note separation of PV (Process Value, currently measured)
        # and SV (Setpoint Value, commanded by software) - this allows
        # HMI software to request changes without directly modifying
        # actively used PLC variables.

        # Note that register addresses are temporary placeholders.
        
        self._registers = {

            "T1_PV" : Register(28672, 0, "Temperature 1 PV"),
            "T2_PV" : Register(28676, 0, "Temperature 2 PV"),
            "T3_PV" : Register(28680, 0, "Temperature 3 PV"),
            "GAS_FLOW" : Register(28684, 0, "Gas Flow Rate"),
            "GAS_SELECT" : Register(28686, 0, "Gas Selection"),
            "GAS_ACTIVE" : Register(28688, 0, "Gas Active"),
            "PRESSURE" : Register(28690, 0, "Pressure"),
            "T1_SV" : Register(28674, 0, "Temperature 1 SV"),
            "T2_SV" : Register(28678, 0, "Temperature 2 SV"),
            "T3_SV" : Register(28682, 0, "Temperature 3 SV")
            
        }

    # PROPERTY SETTER METHODS
    
    def set_temperature(self, temp_id, value):

        pass

    def set_gas(self, gas_id):

        pass

    def set_mfc_flow(self, flow_rate):

        pass

    # PROPERTY GETTER METHODS

    def get_register_names(self):
        return [reg.name for reg in self._registers.values()]

    def get_register_keys(self):
        return self._registers.keys()

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

    def is_connected(self):
        return self.modbusc.connected

    # UPDATE METHOD

    def update(self):

        pass
