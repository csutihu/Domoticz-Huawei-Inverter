# Domoticz Huawei Inverter
#
# Domoticz plugin for Huawei Solar inverters via Modbus
#
# Author: JWGracht
#
# Prerequisites:
#    1. Modbus connection enabled at the inverter
#    2. python 3.x
#    3. pip3 install -U huawei-solar
#
"""
<plugin key="Domoticz-Huawei-Inverter" name="Huawei Solar inverter (modbus TCP/IP)" author="jwgracht" version="0.0.1" wikilink="" externallink="https://github.com/JWGracht/Domoticz-Huawei-Inverter/">
    <description>
        <p>Domoticz plugin for Huawei Solar inverters via Modbus.</p>
        <p>Required:
        <ul style="list-style-type:square">
            <li>Modbus connection enabled at the inverter</li>
            <li>python 3.x</li>
            <li>sudo pip3 install -U huawei-solar</li>
        </ul></p>
    </description>
    <params>
        <param field="Address" label="Your Huawei inverter IP Address" width="200px" required="true" default="192.168.200.1"/>
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

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        
        self.inverterserveraddress = Parameters["Address"].strip()
        self.inverterserverport = Parameters["Port"].strip()
        
        self.bridge = self._connectInverter()
        
        voltage_devices = ["PV_01_VOLTAGE", "PV_02_VOLTAGE", "PV_03_VOLTAGE", "PV_04_VOLTAGE", "PHASE_A_VOLTAGE", "PHASE_B_VOLTAGE", "PHASE_C_VOLTAGE", "GRID_A_VOLTAGE", "GRID_B_VOLTAGE", "GRID_C_VOLTAGE"]
        for device in voltage_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=243, Subtype=8, Used=0, DeviceID=device).Create() # create voltage devices
        
        current_devices = ["PV_01_CURRENT", "PV_02_CURRENT", "PV_03_CURRENT", "PV_04_CURRENT", "PHASE_A_CURRENT", "PHASE_B_CURRENT", "PHASE_C_CURRENT"]
        for device in current_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=243, Subtype=23, Used=0, DeviceID=device).Create() # create current devices
        
        power_devices = ["INPUT_POWER", "ACTIVE_POWER_FAST", "REACTIVE_POWER", "ACTIVE_GRID_A_POWER", "ACTIVE_GRID_B_POWER", "ACTIVE_GRID_C_POWER"]
        for device in power_devices:
            if self._getDevice(device) < 0 :
                iUnit = 0
                for x in range(1,256):
                    if x not in Devices:
                        iUnit=x
                        break
                if iUnit==0:
                    iUnit=len(Devices)+1
                Domoticz.Device(Name=device, Unit=iUnit, Type=248, Subtype=1, Used=0, DeviceID=device).Create() # create power devices
        
        Domoticz.Heartbeat(5)

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
        
        #Get data
        loop = get_event_loop()
        result = loop.run_until_complete(self.bridge.batch_update([rn.INPUT_POWER,
                                                                   rn.PHASE_A_VOLTAGE, rn.PHASE_B_VOLTAGE, rn.PHASE_C_VOLTAGE,
                                                                   rn.PHASE_A_CURRENT, rn.PHASE_B_CURRENT, rn.PHASE_C_CURRENT,
                                                                   rn.ACTIVE_POWER_FAST, rn.REACTIVE_POWER,
                                                                   rn.PV_01_VOLTAGE, rn.PV_01_CURRENT, rn.PV_02_VOLTAGE, rn.PV_02_CURRENT, rn.PV_03_VOLTAGE, rn.PV_03_CURRENT, rn.PV_04_VOLTAGE, rn.PV_04_CURRENT,
                                                                   rn.GRID_A_VOLTAGE, rn.GRID_B_VOLTAGE, rn.GRID_C_VOLTAGE,
                                                                   rn.ACTIVE_GRID_A_POWER, rn.ACTIVE_GRID_B_POWER, rn.ACTIVE_GRID_C_POWER]))
        pv_01_voltage = result['pv_01_voltage'][0]
        pv_02_voltage = result['pv_02_voltage'][0]
        pv_03_voltage = result['pv_03_voltage'][0]
        pv_04_voltage = result['pv_04_voltage'][0]
        pv_01_current = result['pv_01_current'][0]
        pv_02_current = result['pv_02_current'][0]
        pv_03_current = result['pv_03_current'][0]
        pv_04_current = result['pv_04_current'][0]
        input_power = result['input_power'][0]
        phase_A_voltage = result['phase_A_voltage'][0]
        phase_B_voltage = result['phase_B_voltage'][0]
        phase_C_voltage = result['phase_C_voltage'][0]
        phase_A_current = result['phase_A_current'][0]
        phase_B_current = result['phase_B_current'][0]
        phase_C_current = result['phase_C_current'][0]
        active_power_fast = result['active_power_fast'][0]
        reactive_power = result['reactive_power'][0]
        grid_A_voltage = result['grid_A_voltage'][0]
        grid_B_voltage = result['grid_B_voltage'][0]
        grid_C_voltage = result['grid_C_voltage'][0]
        active_grid_A_power = result['active_grid_A_power'][0]
        active_grid_B_power = result['active_grid_B_power'][0]
        active_grid_C_power = result['active_grid_C_power'][0]
        
        
        Devices[self._getDevice("PV_01_VOLTAGE")].Update(nValue=0,sValue=str(pv_01_voltage))
        Devices[self._getDevice("PV_02_VOLTAGE")].Update(nValue=0,sValue=str(pv_02_voltage))
        Devices[self._getDevice("PV_03_VOLTAGE")].Update(nValue=0,sValue=str(pv_03_voltage))
        Devices[self._getDevice("PV_04_VOLTAGE")].Update(nValue=0,sValue=str(pv_04_voltage))
        Devices[self._getDevice("PV_01_CURRENT")].Update(nValue=0,sValue=str(pv_01_current))
        Devices[self._getDevice("PV_02_CURRENT")].Update(nValue=0,sValue=str(pv_02_current))
        Devices[self._getDevice("PV_03_CURRENT")].Update(nValue=0,sValue=str(pv_03_current))
        Devices[self._getDevice("PV_04_CURRENT")].Update(nValue=0,sValue=str(pv_04_current))
        Devices[self._getDevice("INPUT_POWER")].Update(nValue=0,sValue=str(input_power))
        Devices[self._getDevice("PHASE_A_VOLTAGE")].Update(nValue=0,sValue=str(phase_A_voltage))
        Devices[self._getDevice("PHASE_B_VOLTAGE")].Update(nValue=0,sValue=str(phase_B_voltage))
        Devices[self._getDevice("PHASE_C_VOLTAGE")].Update(nValue=0,sValue=str(phase_C_voltage))
        Devices[self._getDevice("PHASE_A_CURRENT")].Update(nValue=0,sValue=str(phase_A_current))
        Devices[self._getDevice("PHASE_B_CURRENT")].Update(nValue=0,sValue=str(phase_B_current))
        Devices[self._getDevice("PHASE_C_CURRENT")].Update(nValue=0,sValue=str(phase_C_current))
        Devices[self._getDevice("ACTIVE_POWER_FAST")].Update(nValue=0,sValue=str(active_power_fast))
        Devices[self._getDevice("REACTIVE_POWER")].Update(nValue=0,sValue=str(reactive_power))
        Devices[self._getDevice("GRID_A_VOLTAGE")].Update(nValue=0,sValue=str(grid_A_voltage))
        Devices[self._getDevice("GRID_B_VOLTAGE")].Update(nValue=0,sValue=str(grid_B_voltage))
        Devices[self._getDevice("GRID_C_VOLTAGE")].Update(nValue=0,sValue=str(grid_C_voltage))
        Devices[self._getDevice("ACTIVE_GRID_A_POWER")].Update(nValue=0,sValue=str(active_grid_A_power))
        Devices[self._getDevice("ACTIVE_GRID_B_POWER")].Update(nValue=0,sValue=str(active_grid_B_power))
        Devices[self._getDevice("ACTIVE_GRID_C_POWER")].Update(nValue=0,sValue=str(active_grid_C_power))
        

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
