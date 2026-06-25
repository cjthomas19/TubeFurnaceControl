from dataclasses import dataclass

import modbusutil

# Class to handle storing and accessing individual values and registers for PLC data

@dataclass
class Register:
    addr: int
    value: int
    name: str
    dtype: str

# Class to handle communications with the tube furnace. Includes get and set methods for all variables of interest.
# Gases:
#   0: None 
#   1: Nitrogen
#   2: Oxygen
#   3: Forming Gas

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

            "T1_PV" : Register(9, 0, "Temperature 1 PV",'int'),
            "T2_PV" : Register(19, 0, "Temperature 2 PV",'int'),
            "T3_PV" : Register(29, 0, "Temperature 3 PV",'int'),
            "FLOW_PV" : Register(28694, 0, "Mass Flow Rate",'float'),
            "FLOW_SV" : Register(28696, 0, "Mass Flow Set",'float'),
            "GAS_SELECT" : Register(1, 0, "Gas Selection",'float'),
            "PRESSURE" : Register(28684, 0, "Pressure",'float'),
##            "T1_SV" : Register(28674, 0, "Temperature 1 SV"),
##            "T2_SV" : Register(28678, 0, "Temperature 2 SV"),
##            "T3_SV" : Register(28682, 0, "Temperature 3 SV")
            
        }

        # Default to no gases active
        self.active_gas = 0

    # PROPERTY SETTER METHODS
    
    def set_temperature(self, temp_id, value):

        pass

    def set_gas(self, gas_id):

        # TO-DO : Send message to PLC to swap gas
        #         Wait for PLC to swap back
        if gas_id >= 0 and gas_id <= 3:
            self.active_gas = gas_id
        if self.modbusc.connected:
            self.modbusc.set_int(0,gas_id)

    def set_mfc_flow(self, flow_rate):

        if self.modbusc.connected:
            self.modbusc.set_float(28696, flow_rate)

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
        return self.active_gas

    def get_mfc_flow(self):

        pass

    def is_connected(self):
        return self.modbusc.connected

    def get_value(self, reg_id):
        return self._registers[reg_id].value

    def update_value(self, reg_id):
        reg = self._registers[reg_id]
        if reg.dtype == 'float':
            reg.value = self.modbusc.get_float(reg.addr)
        elif reg.dtype == 'int':
            reg.value = self.modbusc.get_int(reg.addr)
            
    # UPDATE METHOD
    def update(self):
        if self.modbusc.connected:
            for reg in self._registers:
                self.update_value(reg)
