# MODULE: phy-components
# CLASS: phy-mii-transceiver

from sim_core import *
from components import *
from base_components import *

class phy_mii_transceiver(component_object):
    classname = 'phy-mii-transceiver'
    basename = 'phy'
    description = "PHY component representing a general MII transceiver"
    connectors = {
        'mac' : {'type' : 'phy', 'direction' : 'up', 'empty_ok' : False,
                 'hotplug' : False,  'multi' : False},
        'eth' : {'type' : 'ethernet-link', 'direction' : 'down',
                 'empty_ok' : True, 'hotplug' : True, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.phy_id = 0
        self.mii_addr = 0

    def get_phy_id(self, idx):
        return self.phy_id

    def set_phy_id(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value

        self.phy_id = val
        return Sim_Set_Ok

    def get_mii_address(self, idx):
        return self.mii_addr

    def set_mii_address(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value

        self.mii_addr = val
        return Sim_Set_Ok

    def add_objects(self):
        self.o.phy = pre_obj('phy$', 'mii-transceiver')
        self.o.phy.registers = [0] * 32
        self.o.phy.registers[2] = (self.phy_id >> 16) & 0xffff
        self.o.phy.registers[3] = self.phy_id & 0xffff

    def add_connector_info(self):
        self.connector_info['mac'] = [self.o.phy, self.mii_addr]
        self.connector_info['eth'] = []

    def connect_phy(self, connector, mac):
        self.o.phy.mac = mac

    def connect_ethernet_link(self, connector, link):
        self.o.phy.link = link

    def disconnect_ethernet_link(self, connector):
        self.o.phy.link = None

register_component_class(phy_mii_transceiver,
                         [['phy_id', Sim_Attr_Optional, 'i', 'PHY ID'],
                          ['mii_address', Sim_Attr_Optional, 'i',
                           'PHY address on MII bus']])
