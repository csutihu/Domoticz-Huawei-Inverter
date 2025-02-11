"""
<plugin key="Domoticz-Huawei-Inverter" name="Huawei Solar inverter (modbus TCP/IP)" author="csuti" version="2.0" wikilink="" externallink="https://github.com/csutihu/Domoticz-Huawei-Inverter">
    <description>
        <p>Domoticz plugin for Huawei Solar inverters via Modbus</p>
        <p>Notes:
        <ul style="list-style-type:square">
            <li>Based on a plugin written by JWGracht - Thanks for that! / https://github.com/JWGracht/Domoticz-Huawei-Inverter</li>
            <li>FixIP or static DHCP for inverter</li>
            <li>Modbus connection enabled at the inverter</li>
            <li>python modul for Huawei inverter - sudo pip3 install -U huawei-solar</li>
            <li>The plugin automatically generates the required devices in Domoticz</li>
            <li>All devices are updated every minute</li>
            <li>Communication error handling is included</li>
            <li><b>Minimum Data Refresh Interval is 60 seconds due to Modbus communication error handling!</b></li>
        </ul></p>
    </description>
    <params>
        <param field="Address" label="Huawei inverter IP Address" width="200px" required="true"/>
        <param field="Port" label="Port" width="40px" required="true" default="502"/>
        <param field="Mode1" label="Data Refresh Interval (sec)" width="40px" required="true" default="60"/>
    </params>
</plugin>
"""
import Domoticz
from asyncio import get_event_loop
from huawei_solar import HuaweiSolarBridge
from huawei_solar import register_names as rn

class HuaweiSolarPlugin:
    enabled = False
    inverterserveraddress = "127.0.0.1"
    inverterserverport = "502"
    bridge = None
    heartbeat_counter = 0
    data_refresh_interval = 60
    
    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("onStart called")
             
        self.inverterserveraddress = Parameters["Address"].strip()
        self.inverterserverport = Parameters["Port"].strip()
        self.heartbeat_counter = 0
        self.bridge = self._connectInverter()

        self.initialize_devices()

        try:
            self.data_refresh_interval = int(Parameters["Mode1"].strip())
            if self.data_refresh_interval < 60:  # Check if we get a positive number
                Domoticz.Error("Data refresh interval cannot be less than 60 seconds. Using default 60 seconds.")
                self.data_refresh_interval = 60
        except ValueError:  # If it fails to convert to int
            Domoticz.Error("Invalid data refresh interval. Using default 60 seconds.")
            self.data_refresh_interval = 60

        Domoticz.Log(self.data_refresh_interval)
        Domoticz.Heartbeat(30)


    def initialize_devices(self):
        devices_config = [
            (7, "PV1 Voltage", 243, 8, None, "PV1 Voltage"),
            (22, "PV2 Voltage", 243, 8, None, "PV2 Voltage"),
            (27, "L1 Voltage", 243, 8, None, "L1 Voltage"),
            (28, "L2 Voltage", 243, 8, None, "L2 Voltage"),
            (29, "L3 Voltage", 243, 8, None, "L3 Voltage"),
            (30, "PV1 Current", 243, 23, None, "PV1 Current"),
            (31, "PV2 Current", 243, 23, None, "PV2 Current"),
            (32, "L1 Current", 243, 23, None, "L1 Current"),
            (33, "L2 Current", 243, 23, None, "L2 Current"),
            (34, "L3 Current", 243, 23, None, "L3 Current"),
            (35, "Input Power", 248, 1, None, "Input Power"),
            (36, "Active Power", 248, 1, None, "Active Power"),
            (37, "Reactive Power", 248, 1, None, "Reactive Power"),
            (38, "Internal Temp", 80, 5, None, "Internal Temp"),
            (39, "Anti Reverse Temp", 80, 5, None, "Anti Reverse Temp"),
            (40, "Inverter L1 Modul Temp", 80, 5, None, "Inverter L1 Modul Temp"),
            (41, "Inverter L2 Modul Temp", 80, 5, None, "Inverter L2 Modul Temp"),
            (42, "Inverter L3 Modul Temp", 80, 5, None, "Inverter L3 Modul Temp"),
            (14, "Alert", 243, 19, None, "Alert"),
            (43, "Device Status", 243, 19, None, "Device Status"),
            (23, "Energy Meter", 243, 29, 4, "Energy Meter"), #Switchtype 4 - kWh
            (1, "Daily Energy Meter", 243, 29, 4, "Daily Energy Meter"), #Switchtype 4 - kWh
            (26, "Total Energy", 113, 0, None, "Total Energy"),
            (6, "Inverter Efficiency", 243, 6, None, "Inverter Efficiency")
        ]

        for unit, name, dtype, stype, switchtype, deviceid in devices_config:
            if self._getDevice(deviceid) < 0:
                params = {  # Szótár a paraméterekhez
                    "Unit": unit,
                    "Name": name,
                    "Type": dtype,
                    "Subtype": stype,
                    "DeviceID": deviceid
                }
                if switchtype is not None:  # Only if switchtype exists
                    params["Switchtype"] = switchtype

                Domoticz.Device(**params).Create()  # **params unpacks the dictionary
                Domoticz.Log(f"Device created: {name} (Unit: {unit})")


    def _getDevice(self, deviceid):
        i = -1
        for Device in Devices:
            if (Devices[Device].DeviceID.strip() == deviceid): # Search based on deviceid
                i = Device
                break
        return i


    def onStop(self):
        Domoticz.Log("onStop called")
        if self.bridge:
            try:
                loop = get_event_loop()
                if loop.is_running(): # Check if the loop is running
                    loop.stop()  # Stop the loop
                self.bridge = None  # Delete the bridge object
                Domoticz.Log("Inverter connection stopped.")
            except Exception as e:
                Domoticz.Error(f"Error stopping inverter connection: {e}")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")

        self.heartbeat_counter += 1  # Increment the counter
        if self.heartbeat_counter * 30 >= self.data_refresh_interval:  # Use the stored value

            if self.bridge is None:  # Verify that a connection is established
                Domoticz.Error("Inverter connection is not established. Trying to reconnect...")
                try:
                    self.bridge = self._connectInverter()
                    if self.bridge:
                        Domoticz.Log("Reconnected successfully.")
                    else:
                        Domoticz.Error("Reconnection failed.")
                except Exception as e:
                    Domoticz.Error(f"Reconnection attempt failed with error: {e}")
                return # If no connection, don't try to query


            loop = get_event_loop()
            try:
                result = loop.run_until_complete(self.bridge.batch_update([rn.PHASE_A_VOLTAGE, rn.PHASE_B_VOLTAGE, rn.PHASE_C_VOLTAGE,
                                                                           rn.PHASE_A_CURRENT, rn.PHASE_B_CURRENT, rn.PHASE_C_CURRENT,
                                                                           rn.ACTIVE_POWER, rn.REACTIVE_POWER, rn.INPUT_POWER,
                                                                           rn.PV_01_VOLTAGE, rn.PV_01_CURRENT, rn.PV_02_VOLTAGE, rn.PV_02_CURRENT,
                                                                           rn.INTERNAL_TEMPERATURE, rn.ANTI_REVERSE_MODULE_1_TEMP, rn.INV_MODULE_A_TEMP, rn.INV_MODULE_B_TEMP, rn.INV_MODULE_C_TEMP,
                                                                           rn.EFFICIENCY,
                                                                           rn.DEVICE_STATUS, rn.FAULT_CODE, rn.ALARM_1, rn.ALARM_2, rn.ALARM_3,
                                                                           rn.ACCUMULATED_YIELD_ENERGY, rn.DAILY_YIELD_ENERGY]))

                pv_01_voltage = result['pv_01_voltage'][0]
                pv_02_voltage = result['pv_02_voltage'][0]
                pv_01_current = result['pv_01_current'][0]
                pv_02_current = result['pv_02_current'][0]
                input_power = result['input_power'][0]
                phase_A_voltage = result['phase_A_voltage'][0]
                phase_B_voltage = result['phase_B_voltage'][0]
                phase_C_voltage = result['phase_C_voltage'][0]
                phase_A_current = result['phase_A_current'][0]
                phase_B_current = result['phase_B_current'][0]
                phase_C_current = result['phase_C_current'][0]
                active_power = result['active_power'][0]
                reactive_power = result['reactive_power'][0]
                efficiency = result['efficiency'][0]
                internal_temperature = result['internal_temperature'][0]
                anti_reverse_module_1_temp = result['anti_reverse_module_1_temp'][0]
                inv_module_a_temp = result['inv_module_a_temp'][0]
                inv_module_b_temp = result['inv_module_b_temp'][0]
                inv_module_c_temp = result['inv_module_c_temp'][0]
                device_status = result['device_status'][0]
                fault_code = result['fault_code'][0]
                alarm_1 = result['alarm_1'][0]
                alarm_2 = result['alarm_2'][0]
                alarm_3 = result['alarm_3'][0]
                alert_svalue = f"Fault code:{str(fault_code)}, Alarm:{str(alarm_1)}, {str(alarm_2)}, {str(alarm_3)}"
                accumulated_yield_energy = (result['accumulated_yield_energy'][0]*1000)
                daily_yield_energy = (result['daily_yield_energy'][0]*1000)

 
                #update Domoticz devices
                Devices[self._getDevice("PV1 Voltage")].Update(nValue=0,sValue=str(pv_01_voltage))
                Devices[self._getDevice("PV2 Voltage")].Update(nValue=0,sValue=str(pv_02_voltage))
                Devices[self._getDevice("PV1 Current")].Update(nValue=0,sValue=str(pv_01_current))
                Devices[self._getDevice("PV2 Current")].Update(nValue=0,sValue=str(pv_02_current))
                Devices[self._getDevice("Input Power")].Update(nValue=0,sValue=str(input_power))
                Devices[self._getDevice("L1 Voltage")].Update(nValue=0,sValue=str(phase_A_voltage))
                Devices[self._getDevice("L2 Voltage")].Update(nValue=0,sValue=str(phase_B_voltage))
                Devices[self._getDevice("L3 Voltage")].Update(nValue=0,sValue=str(phase_C_voltage))
                Devices[self._getDevice("L1 Current")].Update(nValue=0,sValue=str(phase_A_current))
                Devices[self._getDevice("L2 Current")].Update(nValue=0,sValue=str(phase_B_current))
                Devices[self._getDevice("L3 Current")].Update(nValue=0,sValue=str(phase_C_current))
                Devices[self._getDevice("Active Power")].Update(nValue=0,sValue=str(active_power))
                Devices[self._getDevice("Reactive Power")].Update(nValue=0,sValue=str(reactive_power))
                Devices[self._getDevice("Energy Meter")].Update(nValue=0,sValue=str(active_power)+";"+str(accumulated_yield_energy))
                Devices[self._getDevice("Daily Energy Meter")].Update(nValue=0,sValue=f"0;{str(daily_yield_energy)}")
                Devices[self._getDevice("Total Energy")].Update(nValue=0,sValue=str(accumulated_yield_energy))
                Devices[self._getDevice("Inverter Efficiency")].Update(nValue=0,sValue=str(efficiency))
                Devices[self._getDevice("Internal Temp")].Update(nValue=0,sValue=str(internal_temperature))
                Devices[self._getDevice("Anti Reverse Temp")].Update(nValue=0,sValue=str(anti_reverse_module_1_temp))
                Devices[self._getDevice("Inverter L1 Modul Temp")].Update(nValue=0,sValue=str(inv_module_a_temp))
                Devices[self._getDevice("Inverter L2 Modul Temp")].Update(nValue=0,sValue=str(inv_module_b_temp))
                Devices[self._getDevice("Inverter L3 Modul Temp")].Update(nValue=0,sValue=str(inv_module_c_temp))
                Devices[self._getDevice("Device Status")].Update(nValue=0,sValue=str(device_status))
                # Verify if the value is "Error code and alarm free status
                if alert_svalue == "Fault code:0, Alarm:[], [], []":
                    alert_svalue = "Error code and alarm free status"
                Devices[self._getDevice("Alert")].Update(nValue=0, sValue=alert_svalue)

                self.heartbeat_counter = 0

            except (TimeoutError, Exception) as e: # TimeoutError and other error handling
                Domoticz.Error(f"Connection/Timeout/Other Error: {e}")
                Domoticz.Log("Trying to reconnect to inverter...")
                try:
                    self.bridge = self._connectInverter()
                    if self.bridge:
                        Domoticz.Log("Reconnected successfully.")
                    else:
                        Domoticz.Error("Reconnection failed.")
                except Exception as e:
                    Domoticz.Error(f"Reconnection attempt failed with error: {e}")
                return # If no connection, don't try to query


    def _connectInverter(self):
        loop = get_event_loop()
        Domoticz.Log("Connecting inverter")
        try:
            bridge = loop.run_until_complete(HuaweiSolarBridge.create(host = self.inverterserveraddress, port = int(self.inverterserverport), slave_id=1))
            Domoticz.Log("Inverter connected")
            return bridge
        except Exception as e:
            Domoticz.Error("Inverter connection failed!")
            return None # ensure to return None if the connection is not established


global _plugin
_plugin = HuaweiSolarPlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions for development process
#def DumpConfigToLog():
#    for x in Parameters:
#        if Parameters[x] != "":
#            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
#    Domoticz.Debug("Device count: " + str(len(Devices)))
#    for DeviceName in Devices:
#        Device = Devices[DeviceName]
#        Domoticz.Debug("Device ID:       '" + str(Device.DeviceID) + "'")
#        Domoticz.Debug("--->Unit Count:      '" + str(len(Device.Units)) + "'")
#        for UnitNo in Device.Units:
#            Unit = Device.Units[UnitNo]
#            Domoticz.Debug("--->Unit:           " + str(UnitNo))
#            Domoticz.Debug("--->Unit Name:     '" + Unit.Name + "'")
#            Domoticz.Debug("--->Unit nValue:    " + str(Unit.nValue))
#            Domoticz.Debug("--->Unit sValue:   '" + Unit.sValue + "'")
#            Domoticz.Debug("--->Unit LastLevel: " + str(Unit.LastLevel))
#    return
