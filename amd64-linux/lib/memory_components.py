# MODULE: memory-components
# CLASS: ddr-memory-module
# CLASS: ddr2-memory-module
# CLASS: sdram-memory-module

from sim_core import *
from components import *
import math


### Memory Module


class memory_module_component(component_object):
    classname = 'memory-module'
    description = ('The "memory-module" component represents a memory module.')
    connectors = {
        'mem-bus' : {'type' : 'mem-bus', 'direction' : 'up',
                     'empty_ok' : True, 'hotplug' : False, 'multi' : False}}

    def __init__(self, parse_obj):
        component_object.__init__(self, parse_obj)
        self.byte = [0] * 256
        self.dflt_size_dep = ['r', 'c', 'd', 'b', 'w']
        self.user_size_dep = []
        self.user_rank_density = 0
        self.ddr2_rank_density = [
            [0x01,  1024],
            [0x02,  2048],
            [0x04,  4096],
            [0x08,  8192],
            [0x10, 16384],
            [0x20,   128],
            [0x40,   256],
            [0x80,   512]]
        self.ddr_rank_density_little = [
            [0x01,   4],
            [0x02,   8],
            [0x04,  16],
            [0x08,  32],
            [0x10,  64],
            [0x20, 128],
            [0x40, 256],
            [0x80, 512]]
        self.ddr_rank_density_big = [
            [0x01, 1024],
            [0x02, 2048],
            [0x04, 4096],
            [0x08,   32],
            [0x10,   64],
            [0x20,  128],
            [0x40,  256],
            [0x80,  512]]
        self.sdram_rank_density = self.ddr_rank_density_little
        # default bytes
        self.byte[0]  = 0x80   # Number of Serial PD Bytes written during module production
        self.byte[1]  = 0x08   # Total number of Bytes in Serial PD device
        self.byte[2]  = 0x07   # Fundamental Memory Type (FPM EDO SDRAM DDR DDR2)
        self.byte[3]  = 0x0d   # Number of Row Addresses on this assembly
        self.byte[4]  = 0x0a   # Number of Column Addresses on this assembly
        self.byte[5]  = 0x01   # Number of DIMM Banks/Ranks
        self.byte[6]  = 0x40   # Data Width of this assembly
        self.byte[7]  = 0x00   # Reserved
        self.byte[8]  = 0x04   # Voltage Interface Level of this assembly
        self.byte[9]  = 0x25   # SDRAM Cycle time at Maximum Supported CAS Latency (CL) CL=X
        self.byte[10] = 0x60   # SDRAM Access from Clock
        self.byte[11] = 0x00   # DIMM configuration type (Non-parity Parity or ECC)
        self.byte[12] = 0x82   # Refresh Rate/Type
        self.byte[13] = 0x08   # Primary SDRAM Width
        self.byte[14] = 0x00   # Error Checking SDRAM Width
        self.byte[15] = 0x00   # Minimum clock delay, back-to-back random column access
        self.byte[16] = 0x0c   # SDRAM Device Attributes: Burst Lengths Supported
        self.byte[17] = 0x04   # SDRAM Device Attributes: Number of Banks on SDRAM Device
        self.byte[18] = 0x38   # SDRAM Device Attributes: CAS Latency
        self.byte[19] = 0x00   # Reserved
        self.byte[20] = 0x02   # DIMM Type Information
        self.byte[21] = 0x00   # SDRAM Module Attributes
        self.byte[22] = 0x01   # SDRAM Device Attributes: General
        self.byte[23] = 0x50   # Minimum Clock Cycle at CLX-1
        self.byte[24] = 0x60   # Maximum Data Access Time (tAC) from Clock at CLX-1
        self.byte[25] = 0x50   # Minimum Clock Cycle at CLX-2
        self.byte[26] = 0x60   # Maximum Data Access Time (tAC) from Clock at CLX-2
        self.byte[27] = 0x3c   # Minimum Row Precharge Time (tRP)
        self.byte[28] = 0x1e   # Minimum Row Active to Row Active delay (tRRD)
        self.byte[29] = 0x3c   # Minimum RAS to CAS delay (tRCD)
        self.byte[30] = 0x2d   # Minimum Active to Precharge Time (tRAS)
        self.byte[31] = 0x40   # Module Rank Density
        self.byte[32] = 0x60   # Address and Command Input Setup Time Before Clock (tIS)
        self.byte[33] = 0x60   # Address and Command Input Hold Time After Clock (tIH)
        self.byte[34] = 0x40   # Data Input Setup Time Before Clock (tDS)
        self.byte[35] = 0x40   # Data Input Hold Time After Clock (tDH)
        self.byte[36] = 0x3c   # Write recovery time (tWR)
        self.byte[37] = 0x28   # Internal write to read command delay (tWTR)
        self.byte[38] = 0x1e   # Internal read to precharge command delay (tRTP)
        self.byte[39] = 0x00   # Memory Analysis Probe Characteristics
        self.byte[40] = 0x00   # Extension of Byte 41 tRC and Byte 42 tRFC
        self.byte[41] = 0x3c   # SDRAM Device Minimum Active to Active/Auto Refresh Time (tRC)
        self.byte[42] = 0x69   # SDRAM Device Minimum Auto-Refresh to Active/Auto-Refresh Command Period (tRFC)
        self.byte[43] = 0x43   # SDRAM Device Maximum device cycle time (tCKmax)
        self.byte[44] = 0x23   # SDRAM Device maximum skew between DQS and DQ signals (tDQSQ)
        self.byte[45] = 0x2d   # SDRAM Device Mazimum Read DataHold Skew Facktor (tQHS)
        self.byte[46] = 0x00   # PLL Relock Time

        # Some software accepts only Micron, Smart or Samsung memories.
        self.byte[64] = 0xce   # Manufacturer JEDEC ID Code (default Samsung)

    def add_objects(self):
        self.o.sdram_spd_image = pre_obj('sdram_spd$_image', 'image')
        self.o.sdram_spd_image.size = 0x2000
        self.o.sdram_spd = pre_obj('sdram_spd$', 'PCF8582C')
        self.o.sdram_spd.image = self.o.sdram_spd_image
        self.o.sdram_spd.address_bits = 8
        self.o.sdram_spd.address = 0;
        self.o.sdram_spd.address_mask = 0x7f

    def add_connector_info(self):
        self.connector_info['mem-bus'] = ([self.get_size(), self.get_ranks(0)],
                                          [self.byte[2],
                                           self.get_size(), self.get_ranks(0),
                                           self.get_module_data_width(0),
                                           self.get_ecc_width(0)])

    def connect_mem_bus(self, connector, i2c_bus, spd_address):
        self.o.sdram_spd.address = spd_address
        self.o.sdram_spd.i2c_bus = i2c_bus

    def instantiation_done(self):
        component_object.instantiation_done(self)
        self.set_spd()

    def is_po2(self, val):
        if val and not(val & (val - 1)):
            return 1
        return 0

    def order_size_dep(self, val):
        n = []
        for i in self.dflt_size_dep:
            if i != val:
                n.append(i)
            else:
                self.user_size_dep += i
        self.dflt_size_dep = n

    def get_size_params(self):
        d = self.get_rank_density(0)
        r = self.get_rows(0)
        c = self.get_columns(0)
        b = self.get_banks(0)
        w = self.get_module_data_width(0) - self.get_ecc_width(0)
        return (d, r, c, b, w)

    def size_dep_ok(self):
        (d, r, c, b, w) = self.get_size_params()
        return d == (2**(r + c - 23)) * b * w

    def calc_r(self):
        (d, r, c, b, w) = self.get_size_params()
        return int(math.log(d / ((2**(c - 23)) * b * w), 2))

    def calc_c(self):
        (d, r, c, b, w) = self.get_size_params()
        return int(math.log(d / ((2**(r - 23)) * b * w), 2))

    def calc_b(self):
        (d, r, c, b, w) = self.get_size_params()
        return int(d / (((2**(r + c - 23)) * w)))

    def calc_d(self):
        (d, r, c, b, w) = self.get_size_params()
        return int((2**(r + c - 23)) * b * w)

    def calc_w(self):
        (d, r, c, b, w) = self.get_size_params()
        return int(d / ((2**(r + c - 23)) * b))

    def calc_list(self, list):
        for i in list:
            if self.size_dep_ok():
                break
            if i == 'r':
                r = self.calc_r()
                self.set_val_rows(r)
            elif i == 'c':
                c = self.calc_c()
                self.set_val_columns(c)
            elif i == 'b':
                b = self.calc_b()
                self.set_val_banks(b)
            elif i == 'd':
                d = self.calc_d()
                self.set_val_rank_density(d)
            elif i == 'w':
                w = self.calc_w() + self.get_ecc_width(0)
                self.set_val_module_data_width(w)
            else:
                print "ERROR, no parameter."
                return

    def calc_size_dep(self):
        self.calc_list(self.dflt_size_dep)
        if self.size_dep_ok():
            return
        print ("Warning, conflicting memory SPD parameters, "
               "overiding user set values.")
        self.calc_list(self.user_size_dep)
        if not self.size_dep_ok():
            print "ERROR, could not find any non conflicting memory SPD parameters."
            if (self.get_ecc_width(0) > 0):
                print "NOTE, do not forget to specify module data width when setting ECC width."
            just = [Just_Left, Just_Right]
            t = []
            t += [["Rank density", self.get_rank_density(0)]]
            t += [["Rows", self.get_rows(0)]]
            t += [["Columns", self.get_columns(0)]]
            t += [["Banks", self.get_banks(0)]]
            t += [["Module data width", self.get_module_data_width(0)]]
            t += [["ECC data width", self.get_ecc_width(0)]]
            t = [["Parameter", "Value"]] + t
            print_columns(just, t)

    def set_spd(self):
        self.calc_size_dep()
        self.set_ecc_bytes()
        self.generate_checksum()
        for i in range(len(self.byte)):
            self.o.sdram_spd_image.byte_access[i] = self.byte[i]

    def get_size(self):
        return self.get_rank_density(0) * self.get_ranks(0)

    def generate_checksum(self):
        self.byte[63] = sum(self.byte) % 256

    def set_ecc_bytes(self):
        if self.byte[14] == 0:
            return
        self.byte[6] |= self.byte[14]
        self.byte[11] |= 0x2

    # rows
    def get_rows(self, idx):
        return self.byte[3]

    def set_val_rows(self, val):
        self.byte[3] = val

    def set_rows(self, val, idx):
        if val < 0:
            return Sim_Set_Illegal_Value
        self.set_val_rows(val)
        self.order_size_dep('r')
        return Sim_Set_Ok

    # columns
    def get_columns(self, idx):
        return self.byte[4]

    def set_val_columns(self, val):
        self.byte[4] = val

    def set_columns(self, val, idx):
        if val < 0:
            return Sim_Set_Illegal_Value
        self.set_val_columns(val)
        self.order_size_dep('c')
        return Sim_Set_Ok

    # ranks
    def get_ranks(self, idx):
        if self.type == "DDR2 SDRAM":
            return (self.byte[5] & 0x3) + 1
        elif self.type in ("DDR SDRAM", "SDRAM"):
            return self.byte[5]
        SIM_attribute_error("Unknown memory type")
        return 0

    def get_memory_megs(self, idx):
        return self.get_size()

    def set_val_ranks(self, val):
        if self.type == "DDR2 SDRAM":
            self.byte[5] = (self.byte[5] & 0xf8) | ((val - 1) & 0x3)
        elif self.type in ("DDR SDRAM", "SDRAM"):
            self.byte[5] = val
        else:
            SIM_attribute_error("Unknown memory type")
            return Sim_Set_Illegal_Value

    def set_ranks(self, val, idx):
        if not self.is_po2(val):
            return Sim_Set_Illegal_Value
        self.set_val_ranks(val)
        return Sim_Set_Ok

    # module data width
    def get_module_data_width(self, idx):
        return 256 * self.byte[7] + self.byte[6]

    def set_val_module_data_width(self, val):
        if val < 256:
            self.byte[6] = val
        else:
            self.byte[6] = val % 256
            self.byte[7] = val / 256

    def set_module_data_width(self, val, idx):
        self.set_val_module_data_width(val)
        self.order_size_dep('w')
        return Sim_Set_Ok

    # primary width
    def get_primary_width(self, idx):
        return self.byte[13]

    def set_primary_width(self, val, idx):
        if not self.is_po2(val):
            return Sim_Set_Illegal_Value
        self.byte[13] = val
        return Sim_Set_Ok

    # ecc width
    def get_ecc_width(self, idx):
        return self.byte[14]

    def set_ecc_width(self, val, idx):
        if not (self.is_po2(val) or val == 0):
            return Sim_Set_Illegal_Value
        self.byte[14] = val
        return Sim_Set_Ok

    # banks
    def get_banks(self, idx):
        return self.byte[17]

    def set_val_banks(self, val):
        self.byte[17] = val

    def set_banks(self, val, idx):
        if not self.is_po2(val):
            return Sim_Set_Illegal_Value
        self.set_val_banks(val)
        self.order_size_dep('b')
        return Sim_Set_Ok

    # rank density
    def get_rank_density(self, idx):
        if self.type == "SDRAM":
            list = self.sdram_rank_density
        elif (self.type == "DDR SDRAM"
            and self.user_rank_density <= 64 and self.user_rank_density != 0):
            list = self.ddr_rank_density_little
        elif self.type == "DDR SDRAM":
            list = self.ddr_rank_density_big
        else:
            list = self.ddr2_rank_density
        for i in list:
            if self.byte[31] == i[0]:
                return i[1]

    def set_val_rank_density(self, val):
        if self.type == "SDRAM":
            list = self.sdram_rank_density
        elif (self.type == "DDR SDRAM"
              and self.user_rank_density <= 64
              and self.user_rank_density != 0):
            list = self.ddr_rank_density_little
        elif self.type == "DDR SDRAM":
            list = self.ddr_rank_density_big
        else:
            list = self.ddr2_rank_density
        for i in list:
            if val == i[1]:
                self.byte[31] = i[0]
                return
        print "ERROR, unsupported rank density 0x%x" % val

    def set_rank_density(self, val, idx):
        if not self.is_po2(val):
            return Sim_Set_Illegal_Value
        self.user_rank_density = val
        self.set_val_rank_density(val)
        self.order_size_dep('d')
        return Sim_Set_Ok


    # module type
    def get_module_type(self, idx):
        if self.type == "DDR SDRAM" or self.type == "SDRAM" :
            if self.byte[21] & 0x26:
                return "RDIMM"
            else:
                 return "UDIMM"
        elif self.type == "DDR2 SDRAM":
            if self.byte[20] == 0x01:
                return "RDIMM"
            elif self.byte[20] == 0x02:
                return "UDIMM"
            elif self.byte[20] == 0x04:
                return "SO-DIMM"
            elif self.byte[20] == 0x08:
                return "Micro-DIMM"
            elif self.byte[20] == 0x10:
                return "Mini-RDIMM"
            elif self.byte[20] == 0x20:
                return "Mini-UDIMM"
        return "Unknown"

    def set_module_type(self, val, idx):
        if self.type == "DDR SDRAM" or self.type == "SDRAM" :
            if val == "RDIMM":
                self.byte[21] |= 0x26
            elif val == "UDIMM":
                self.byte[21] &= ~0x26
            else:
                return Sim_Set_Illegal_Value
        elif self.type == "DDR2 SDRAM":
            if val == "RDIMM":
                self.byte[20] = 0x01
            elif val == "UDIMM":
                self.byte[20] = 0x02
            elif val == "SO-DIMM":
                self.byte[20] = 0x04
            elif val == "Micro-DIMM":
                self.byte[20] = 0x08
            elif val == "Mini-RDIMM":
                self.byte[20] = 0x10
            elif val == "Mini-UDIMM":
                self.byte[20] = 0x20
            else:
                return Sim_Set_Illegal_Value
        else:
            return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_cas_latency(self, idx):
        return self.byte[18]

    def set_cas_latency(self, val, idx):
        self.byte[18] = val & 0xff
        return Sim_Set_Ok

memory_module_attributes = [
    ['rows', Sim_Attr_Optional, 'i', 'Number of rows.'],
    ['columns', Sim_Attr_Optional, 'i', 'Number of columns.'],
    ['ranks', Sim_Attr_Optional, 'i', 'Number of ranks (logical banks).'],
    ['module_data_width', Sim_Attr_Optional, 'i', 'The module SDRAM width.'],
    ['primary_width', Sim_Attr_Optional, 'i', 'Primary SDRAM width.'],
    ['ecc_width', Sim_Attr_Optional, 'i', 'The error correction width.'],
    ['banks', Sim_Attr_Optional, 'i', 'Number of banks.'],
    ['rank_density', Sim_Attr_Optional, 'i', 'The rank density.'],
    ['memory_megs', Sim_Attr_Pseudo, 'i', 'Total about of memory in MB.'],
    ['module_type', Sim_Attr_Optional, 's', 'Type of memory.'],
    ['cas_latency', Sim_Attr_Optional, 'i',
     'CAS-latency; each set bit corresponds to a latency the memory can handle']]

### DDR Memory Module


class ddr_memory_module_component(memory_module_component):
    classname = 'ddr-memory-module'
    basename = 'ddr_memory'
    description = ('The "ddr-memory-module" component represents a DDR memory module.')
    connectors = memory_module_component.connectors.copy()

    def __init__(self, parse_obj):
        memory_module_component.__init__(self, parse_obj)
        self.type = "DDR SDRAM"
        self.speed = "none"

    # speed
    def get_speed(self, idx):
        return self.speed

    def set_speed(self, val, idx):
        if val == "PC2700":
            self.speed = val
            self.byte[8] = 0x40
            self.byte[9] = 0x60
            self.byte[10] = 0x70
            self.byte[12] = 0x82
            self.byte[15] = 0x01
            self.byte[16] = 0x0e
            self.byte[18] = 0x0c
            self.byte[19] = 0x01
            self.byte[20] = 0x02
            self.byte[22] = 0xc0
            self.byte[23] = 0x75
            self.byte[24] = 0x70
            self.byte[25] = 0
            self.byte[26] = 0
            self.byte[27] = 0x48
            self.byte[28] = 0x30
            self.byte[29] = 0x48
            self.byte[30] = 0x2a
            self.byte[32] = 0x75
            self.byte[33] = 0x75
            self.byte[34] = 0x45
            self.byte[35] = 0x45
            self.byte[36] = 0
            self.byte[37] = 0
            self.byte[38] = 0
            self.byte[39] = 0
            self.byte[40] = 0
            self.byte[41] = 0x3c
            self.byte[42] = 0x48
            self.byte[43] = 0x30
            self.byte[44] = 0x2d
            self.byte[45] = 0x55
            self.byte[46] = 0x00
            return Sim_Set_Ok
        elif val == "none":
            self.speed = val
            return Sim_Set_Ok
        else:
            return Sim_Set_Illegal_Value

ddr_module_attributes = memory_module_attributes + [['speed', Sim_Attr_Optional, 's', 'PC standard speed. Supported values are PC2700 and none.']]

register_component_class(ddr_memory_module_component,
                         ddr_module_attributes)


### DDR2 Memory Module


class ddr2_memory_module_component(memory_module_component):
    classname = 'ddr2-memory-module'
    basename = 'ddr2_memory'
    description = ('The "ddr2-memory-module" component represents a DDR2 memory module.')
    connectors = memory_module_component.connectors.copy()

    def __init__(self, parse_obj):
        memory_module_component.__init__(self, parse_obj)
        self.type = "DDR2 SDRAM"
        self.byte[2]  = 0x08   # Fundamental Memory Type (FPM EDO SDRAM DDR DDR2)
        self.byte[5]  = 0x60   # Number of DIMM Ranks
        self.byte[8]  = 0x05   # Voltage Interface Level of this assembly
        self.byte[17] = 0x08   # SDRAM Device Attributes: Number of Banks on SDRAM Device
        self.byte[18] = 0x3c   # CL (2, 3, 4, 5, 6)
        self.byte[23] = 0x05   # CAS X - 1
        self.byte[24] = 0x05   # CL X - 1
        self.byte[31] = 0x80   # Module Rank Density

register_component_class(ddr2_memory_module_component,
                         memory_module_attributes)


### SDRAM Memory Module


class sdram_memory_module_component(memory_module_component):
    classname = 'sdram-memory-module'
    basename = 'sdram_memory'
    description = ('The "sdram-memory-module" component represents a '
                   'SRAM memory module.')
    connectors = memory_module_component.connectors.copy()

    def __init__(self, parse_obj):
        memory_module_component.__init__(self, parse_obj)
        self.type = "SDRAM"
        self.byte[2]  = 0x04 # Fundamental Memory Type (FPM EDO SDRAM DDR DDR2)
        self.byte[5]  = 0x01 # Number of DIMM Ranks
        self.byte[8]  = 0x05 # Voltage Interface Level of this assembly
        self.byte[17] = 0x04 # SDRAM Device Attr: Nbr of Banks on SDRAM Device
        self.byte[18] = 0x06 # SDRAM Device Attributes: CAS Latency
        self.byte[31] = 0x10 # Module Rank (ROW) Density

register_component_class(sdram_memory_module_component,
                         memory_module_attributes)


#
# Help function
#

def create_and_connect_ddr(system, memory_megs, organization, ranks_per_module,
                           min_module_size, max_module_size, ecc):

    def is_po2(val):
        if val and not(val & (val - 1)):
            return 1
        return 0

    def organization_ok(dl):
        for idx_a in range(len(organization)):
            if organization[idx_a] == '-':
                if dl[idx_a] != 0:
                    return 0
                continue
            l = []
            for idx_b in range(len(organization)):
                if organization[idx_a] == organization[idx_b]:
                    l.append(idx_b)
            val = -1
            for idx_c in l:
                if (organization[idx_a].islower() and dl[idx_c] > 0) or (organization[idx_a].isupper()):
                    if val == -1:
                        val = dl[idx_c]
                    elif val != dl[idx_c]:
                        return 0
        return 1

    def loop(dl, pos):
        if pos == len(organization):
            return (0, dl)
        for i in dimm_sizes:
            dl[pos] = i
            (res, dl) = loop(dl, pos + 1)
            if res == 0:
                if sum(dl) == memory_megs and organization_ok(dl):
                    dimms = dl
                    return (1, dl)
            else:
                return (1, dl)
        return (0, dl)

    if not is_po2(ranks_per_module):
        print "Error, ranks_per_module must be power of 2."
        SIM_command_has_problem()
        return

    if not is_po2(min_module_size):
        print "Error, min_module_size must be power of 2."
        SIM_command_has_problem()
        return

    if not is_po2(max_module_size):
        print "Error, max_module_size must be power of 2."
        SIM_command_has_problem()
        return

    if max_module_size < min_module_size:
        print "Error, min_module_size can not be less than max_module_size."
        SIM_command_has_problem()
        return

    dimm_sizes = [(2**x) for x in range(int(math.log(max_module_size, 2)),
                                        int(math.log(min_module_size, 2)) - 1, -1)] + [0]
    (res, dimms) = loop([0 for x in range(len(organization))], 0)

    if res == 0:
        print "Error, could not find any combination of memory modules to get total %d MB memory" % memory_megs
        SIM_command_has_problem()
        return

    for i in range(len(dimms)):
        if dimms[i] != 0:
            create_str = "$dimms[%d] = (create-ddr-memory-module " % i
            create_str += "ranks = %d " % ranks_per_module
            create_str += "rank_density = %d " % (dimms[i] / ranks_per_module)
            if ecc:
                create_str += "module_data_width = 72 "
                create_str += "ecc_width = 8 "
            create_str += ")"
            eval_cli_line(create_str)
            # TODO: find slot name in some better way
            eval_cli_line("connect-components %s ddr-slot%d $dimms[%d] mem-bus" % (system, i, i))

new_command('create-and-connect-ddr-memory',
            create_and_connect_ddr,
            [arg(str_t, "system"),
             arg(int_t, "memory_megs"),
             arg(str_t, "organization"),
             arg(int_t, "ranks_per_module", "?", 1),
             arg(int_t, "min_module_size", "?", 4),
             arg(int_t, "max_module_size", "?", 4096),
             arg(int_t, "ecc", "?", 0)],
            type = ["Components"],
            short = 'create and connect memory modules to the system',
            doc = """
Create and connect DDR memory modules to the <arg>system</arg>.
The <arg>memory_megs</arg> attribute defines the total module
memory size in MB. It is possible to create different kind of
module combinations with the <arg>organization</arg> parameter.
The <arg>organization</arg> is a string. Each character in the
string represents a module. The first character is module 0,
second character is module 1, etc. Supported characters are
a-z and A-Z. Two modules can have the same character. An equal
upper case character means that the modules must be of identical
size. An equal lower case character means that the modules must
be identical or unpopulated. The character '-' indicates that
the slot should not contain any modules.

Example 1: AB
Create one or two modules with any size (all slots need not be populated).

Example 2: AA
Create two modules with identical size.

Example 3: aa
Create one module or two modules with identical size.

Optional arguments are <arg>ranks_per_module</arg>, <arg>min_module_size</arg>,
<arg>max_module_size</arg>, and <arg>ecc</arg>.
"""
)

