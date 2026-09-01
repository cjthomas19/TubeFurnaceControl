from dataclasses import dataclass

import modbusutil

# Class to handle storing and accessing individual values and registers for PLC data

@dataclass
class Register:
    addr: int
    value: int
    name: str
    dtype: str
    graph: bool
    factor: int = 1

# Class to handle communications with the tube furnace. Includes get and set methods for all variables of interest.
# Gases:
#   0: None 
#   1: Nitrogen
#   2: Oxygen
#   3: Forming Gas
# Status:
#   0: Reset
#   1: Running Recipe

class TubeInterface:

    def __init__(self, modbusc):

        self.modbusc = modbusc

        self.ramp_factor = 10
        self.temp_factor = 1

        # Registers in PLC memory for all variables of interest
        # Note separation of PV (Process Value, currently measured)
        # and SV (Setpoint Value, commanded by software) - this allows
        # HMI software to request changes without directly modifying
        # actively used PLC variables.

        
        self._registers = {

            "T1_PV" : Register(9, 0, "Zone 1 PV",'int',True,self.temp_factor),
            "T2_PV" : Register(19, 0, "Zone 2 PV",'int',True,self.temp_factor),
            "T3_PV" : Register(29, 0, "Zone 3 PV",'int',True,self.temp_factor),
            "T1_SV" : Register(13, 0, "Zone 1 SV",'int',True,self.temp_factor),
            "T2_SV" : Register(23, 0, "Zone 2 SV",'int', True,self.temp_factor),
            "T3_SV" : Register(33, 0, "Zone 3 SV",'int', True,self.temp_factor),
            "FLOW_PV" : Register(28694, 0, "Mass Flow Rate",'float',True),
            "FLOW_SV" : Register(28696, 0, "Mass Flow Set",'float',True),
            "GAS_SELECT" : Register(4, 0, "Gas Selection",'int',False),
            "PRESSURE" : Register(28684, 0, "Pressure",'float',True),
            
            "T1_STAT" : Register(14, 0, "Zone 1 Status",'int',False),
            "T2_STAT" : Register(24, 0, "Zone 2 Status",'int',False),
            "T3_STAT" : Register(34, 0, "Zone 3 Status",'int',False),
            "PURGE_T" : Register(45061, 0, "Purge Time",'int',False),
            "PURGE_STAT" : Register(45061, False, "Purge Complete", 'bool', False)
        }

        

        # Default to no gases active
        self.active_gas = 0

    # PROPERTY SETTER METHODS
    
    def set_temperature(self, temp_id, value):
        pass

    def set_gas(self, gas_id):
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

    def get_plot_names(self):
        return [reg.name for reg in self._registers.values() if reg.graph]

    def get_plot_keys(self):
        return [key for key in self._registers.keys() if self._registers[key].graph]

    def get_temperature_pv(self, zone_id):
        if zone_id > 0 and zone_id < 4:
            return self.get_value("T" + str(zone_id) + "_PV")
        else:
            return None

    def get_status(self,zone_id):
        if zone_id > 0 and zone_id < 4:
            return self.get_value("T" + str(zone_id) + "_STAT")
        else:
            return None

    def get_pressure(self, p_id):
        pass

    def get_gas(self):
        return self.active_gas

    def get_mfc_flow(self):
        pass

    def get_purge_status(self):
        return self._registers["PURGE_STAT"].value

    def is_connected(self):
        return self.modbusc.connected

    def get_value(self, reg_id):
        return self._registers[reg_id].value / self._registers[reg_id].factor

    def update_value(self, reg_id):
        reg = self._registers[reg_id]
        
        if reg.dtype == 'float':
            reg.value = self.modbusc.get_float(reg.addr)
        elif reg.dtype == 'int':
            reg.value = self.modbusc.get_int(reg.addr)
        elif reg.dtype == 'bool':
            reg.value = self.modbusc.get_coil(reg.addr)

    def send_recipe_params(self, sp, rr, dw, sp2, rr2, dw2):

        self.modbusc.set_int(100,int(dw))
        self.modbusc.set_int(101,int(sp*self.temp_factor))
        self.modbusc.set_int(102,int(rr*self.ramp_factor))
        self.modbusc.set_int(103,int(dw2))
        self.modbusc.set_int(104,int(sp2*self.temp_factor))
        self.modbusc.set_int(105,int(rr2*self.ramp_factor))

        self.modbusc.set_coil(16384,True)

    def start_recipe(self):
        self.modbusc.set_coil(16388,True)

    def stop_recipe(self):
        self.modbusc.set_coil(16392,True)
        
            
    # UPDATE METHOD
    def update(self):
        if self.modbusc.connected:
            for reg in self._registers:
                self.update_value(reg)

        self.active_gas = self._registers["GAS_SELECT"].value
