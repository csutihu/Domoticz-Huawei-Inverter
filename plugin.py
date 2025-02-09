"""
<plugin key="Domoticz-Huawei-Inverter" name="Huawei Solar inverter (modbus TCP/IP)" author="csuti" version="2.0" wikilink="" externallink="https://github.com/csutihu/Domoticz-Huawei-Inverter">
    <description>
        <p>Domoticz plugin for Huawei Solar inverters via Modbus</p>
        <p>Required:
        <ul style="list-style-type:square">
            <li>FixIP or static DHCP for inverter</li>
            <li>Modbus connection enabled at the inverter</li>
            <li>python modul for Huawei inverter - sudo pip3 install -U huawei-solar</li>
        </ul></p>
        <p>Based on a plugin written by JWGracht - Thanks for that!
        <ul style="list-style-type:square">
            <li>https://github.com/JWGracht/Domoticz-Huawei-Inverter</li>
        </ul></p>
    </description>
    <params>
        <param field="Address" label="Huawei inverter IP Address" width="200px" required="true"/>
        <param field="Port" label="Port" width="40px" required="true" default="502"/>
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
    minuteCounter = 0 #you can use if you would like to read data with different sequences
    accumulated_yield_energy = 0

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        
        self.minuteCounter = 0
        
        self.inverterserveraddress = Parameters["Address"].strip()
        self.inverterserverport = Parameters["Port"].strip()
        
        self.bridge = self._connectInverter()

        # create voltage sensors
        voltage_devices = ["PV1 Voltage", "PV2 Voltage", "L1 Voltage", "L2 Voltage", "L3 Voltage"]
        for device in voltage_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=243, Subtype=8, Used=0, DeviceID=device).Create()

        # create current sensors
        current_devices = ["PV1 Current", "PV2 Current", "L1 Current", "L2 Current", "L3 Current"]
        for device in current_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=243, Subtype=23, Used=0, DeviceID=device).Create()

        # create power sensors
        power_devices = ["Input Power", "Active Power", "Reactive Power"]
        for device in power_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=248, Subtype=1, Used=0, DeviceID=device).Create()

        #create temp sensors
        temp_devices = ["Internal Temp", "Anti Reverse Temp", "Inverter L1 Modul Temp", "Inverter L2 Modul Temp", "Inverter L3 Modul Temp"]
        for device in temp_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=80, Subtype=5, Used=0, DeviceID=device).Create()

        #create status and alert sensors
        temp_devices = ["Alert", "Device Status"]
        for device in temp_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=243, Subtype=19, Used=0, DeviceID=device).Create()



        #create Energy sensors
        energy_devices = ["Energy Meter", "Daily Energy Meter"]
        for device in energy_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=243, Subtype=29, Used=0, Switchtype=4, DeviceID=device).Create() # create kwh devices

        #create Energy counter sensor
        if self._getDevice("Total Energy") < 0 :
            iUnit = 0
            for x in range(1,256):
                if x not in Devices:
                    iUnit=x
                    break
            if iUnit==0:
                iUnit=len(Devices)+1
            Domoticz.Device(Name="Total Energy", Unit=iUnit, Type=113, Subtype=0, Used=0, Switchtype=0, DeviceID="Total Energy").Create() # create smart me>

        #create Efficiency sensor
        if self._getDevice("Inverter Efficiency") < 0 :
            iUnit = 0
            for x in range(1,256):
                if x not in Devices:
                    iUnit=x
                    break
            if iUnit==0:
                iUnit=len(Devices)+1
            Domoticz.Device(Name="Inverter Efficiency", Unit=iUnit, Type=243, Subtype=6, Used=0, DeviceID="Inverter Efficiency").Create() # create Inverter Efficiency

       
        Domoticz.Heartbeat(60)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, DeviceID, Unit, Command, Level, Color):
        Domoticz.Log("onCommand called for Device " + str(DeviceID) + " Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")

        #you can increase the counter each heartbeat, and make a decision based on the counter level
        #self.minuteCounter += 1
        #if self.minuteCounter >= 2:
        #     self.minuteCounter = 0
        
        loop = get_event_loop()
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
        Devices[self._getDevice("Alert")].Update(nValue=0,sValue=f"Fault code:{str(fault_code)}, Alarm:{str(alarm_1)}, {str(alarm_2)}, {str(alarm_3)}")


    def _connectInverter(self):
        loop = get_event_loop()
        Domoticz.Log("Connecting inverter")
        bridge = loop.run_until_complete(HuaweiSolarBridge.create(host = self.inverterserveraddress, port = int(self.inverterserverport), slave_id=1))
        Domoticz.Log("Inverter connected")
        return bridge

    def _getDevice(self, name):
        i = -1
        for Device in Devices:
            if (Devices[Device].DeviceID.strip() == name):
                i = Device
                break     
        return i


global _plugin
_plugin = HuaweiSolarPlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(DeviceID, Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(DeviceID, Unit, Command, Level, Color)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for DeviceName in Devices:
        Device = Devices[DeviceName]
        Domoticz.Debug("Device ID:       '" + str(Device.DeviceID) + "'")
        Domoticz.Debug("--->Unit Count:      '" + str(len(Device.Units)) + "'")
        for UnitNo in Device.Units:
            Unit = Device.Units[UnitNo]
            Domoticz.Debug("--->Unit:           " + str(UnitNo))
            Domoticz.Debug("--->Unit Name:     '" + Unit.Name + "'")
            Domoticz.Debug("--->Unit nValue:    " + str(Unit.nValue))
            Domoticz.Debug("--->Unit sValue:   '" + Unit.sValue + "'")
            Domoticz.Debug("--->Unit LastLevel: " + str(Unit.LastLevel))
    return

