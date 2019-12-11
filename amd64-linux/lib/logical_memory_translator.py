
# MODULE: logical-memory-translator
# CLASS: logical-memory-translator

from cli import *
from sim_core import *
from text_console_common import wait_for_string
import sim_commands, string

from configuration import *

class_name = "logical-memory-translator"
instances = {}

# represent either a large page or a submap with small pages
class lmt_page_or_map:
    def __init__(self, page, translation = 0):
        if page:
            self.page = 1
            self.physical_address = translation
        else:
            self.page = 0
            self.submap = {}

# Logical Memory Translator instance
class lmt_instance:
    def __init__(self, conf_obj):
        global instances
        instances[conf_obj] = self
        self.obj = conf_obj

        # two hash tables to keep the mappings for data and instructions
        self.d_map = {}
        self.i_map = {}

        # list of cpus, and list of handles associated with cpus and haps
        self.cpu_list = []
        self.hh = {}

        # page sizes allowed
        self.possible_size_log2 = [13, 16, 19, 22]

        # the hash tables contains <high>-bit space information
        # this information is either a translation or another table
        # with <low>-bit elements
        self.high_size_log2 = 20
        self.high_mask = (0x10000000000000000L - (1 << self.high_size_log2))
        
        self.low_size_log2 = 12
        self.low_mask = (0x10000000000000000L - (1 << self.low_size_log2))

    # return a list containing the information of a given map.
    # the format is the following:
    # [[[mmu, context],
    #   [[address, size, physical_address], ...]],
    #  ...
    # ]
    def list_from_map(self, map):
        ret_list = []
        for (mmu,ctx) in map.keys():
            addr_list = []
            addr_map = map[(mmu, ctx)]
            for addr in addr_map.keys():
                high_item = addr_map[addr]
                if high_item.page:
                    # This is a single page
                    addr_list.append([addr, self.high_size_log2,
                                      high_item.physical_address])
                else:
                    # Multiple small pages
                    low_map = high_item.submap
                    for low_addr in low_map.keys():
                        low_item = low_map[low_addr]
                        addr_list.append([low_addr, self.low_size_log2,
                                          low_item.physical_address])
            ret_list.append([[mmu, ctx], addr_list])
        return ret_list

    # parse a list as described above and populate a map with it
    def map_from_list(self, list):
        ret_map = {}
        for cc in list:
            mmu_ctx_tuple = (cc[0][0], cc[0][1])
            addr_list = cc[1]
            ret_map[mmu_ctx_tuple] = {}
            for item in addr_list:
               self.map_add(ret_map[mmu_ctx_tuple], item[0], item[1], item[2])
        return ret_map
    
    # return the translation or None if no translation is found
    def map_translate(self, obj, ctx, address, map):
        high_map = map.get((obj,ctx))
        if high_map:
            high_tr = high_map.get(address & self.high_mask)
            if not high_tr:
                return None
            elif high_tr.page:
                return high_tr.physical_address | (address & ~self.high_mask)
            else:
                low_tr = high_tr.submap.get(address & self.low_mask)
                if low_tr:
                    return low_tr.physical_address | (address & ~self.low_mask)
                else:
                    return None

    # flush a page of size_log2 size in the given map
    def map_flush_loop(self, map, address, size_log2, map_size_log2, map_mask):
        for i in range(0, 1 << (size_log2 - map_size_log2)):
            map.pop(address & map_mask, None)
            address = address + (1 << map_size_log2)

    def map_flush(self, map, address, size_log2):
        if size_log2 >= self.high_size_log2:
            self.map_flush_loop(map, address, size_log2,
                                self.high_size_log2, self.high_mask)
        else:
            if map.get(address & self.high_mask):
                page_or_map = map[address & self.high_mask]
            else:
                return
            if page_or_map.page:
                print "[%s] Flushing a smaller are than what is mapped"%(self.name)
                print "  Replace 0x%016x -> 0x%016x (%2d, %d) with (%2d, %d)"%(address & self.high_mask, page_or_map.physical_address, self.high_size_log2, page_or_map.creation_time, size_log2, SIM_cycle_count(conf.cpu0))
                raise "Try to flush a smaller area than what is mapped"
            else:
                self.map_flush_loop(page_or_map.submap, address, size_log2,
                                    self.low_size_log2, self.low_mask)

    # add a page of size_log2 size in the given map
    def map_add_loop(self, map, address, size_log2, translation,
                     map_size_log2, map_mask):
        for i in range(0, 1 << (size_log2 - map_size_log2)):
            map[address & map_mask] = lmt_page_or_map(1, translation)
            address = address + (1 << map_size_log2)
            translation = translation + (1 << map_size_log2)

    def map_add(self, map, address, size_log2, translation):
        if size_log2 >= self.high_size_log2:
            self.map_add_loop(map, address, size_log2, translation,
                              self.high_size_log2, self.high_mask)
        else:
            try:
                page_or_map = map[address & self.high_mask]
            except:
                page_or_map = lmt_page_or_map(0)
                map[address & self.high_mask] = page_or_map
            self.map_add_loop(page_or_map.submap, address,
                              size_log2, translation,
                              self.low_size_log2, self.low_mask)

    # map hap handler
    def tlb_map(self, map, obj, tag, data):
        ctx = tag & 0x1fffL
        log_addr = tag & 0xffffffffffffe000L
        phys_addr = data & 0x1ffffffe000L
        size_log2 = self.possible_size_log2[(data >> 61) & 0x3]
        if not map.get((obj,ctx)):
            map[(obj,ctx)] = {}
        self.map_flush(map[(obj,ctx)], log_addr, size_log2)
        self.map_add(map[(obj,ctx)], log_addr, size_log2, phys_addr)
    
    def dtlb_map(self, dummy, obj, tag, data):
        self.tlb_map(self.d_map, obj, tag, data)

    def itlb_map(self, dummy, obj, tag, data):
        self.tlb_map(self.i_map, obj, tag, data)

    # demap, overwrite hap handler
    def tlb_demap(self, map, obj, tag, data, type):
        ctx = tag & 0x1fffL
        log_addr = tag & 0xffffffffffffe000L
        phys_addr = data & 0x1ffffffe000L
        size_log2 = self.possible_size_log2[(data >> 61) & 0x3]
        self.map_flush(map[(obj,ctx)], log_addr, size_log2)

    def dtlb_demap(self, dummy, obj, tag, data):
        self.tlb_demap(self.d_map, obj, tag, data, 0)

    def itlb_demap(self, dummy, obj, tag, data):
        self.tlb_demap(self.i_map, obj, tag, data, 0)

    def dtlb_overwrite(self, dummy, obj, tag, data):
        self.tlb_demap(self.d_map, obj, tag, data, 1)

    def itlb_overwrite(self, dummy, obj, tag, data):
        self.tlb_demap(self.i_map, obj, tag, data, 1)

        
def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    lmt_instance(obj)
    return obj

def register_haps(obj, cpu_list):
    inst = instances[obj]
    for c in cpu_list:
        o = c.mmu
        inst.hh[(o, "dtlb_map")] = SIM_hap_add_callback_obj(
            "MMU_Data_TLB_Map", o, 0, inst.dtlb_map, None)
        inst.hh[(o, "itlb_map")] = SIM_hap_add_callback_obj(
            "MMU_Instruction_TLB_Map", o, 0, inst.itlb_map, None)
        inst.hh[(o, "dtlb_demap")] = SIM_hap_add_callback_obj(
            "MMU_Data_TLB_Demap", o, 0, inst.dtlb_demap, None)
        inst.hh[(o, "itlb_demap")] = SIM_hap_add_callback_obj(
            "MMU_Instruction_TLB_Demap", o, 0, inst.itlb_demap, None)

        # listen to overwrite to get specifically overwritten pages
        # in fully-associative TLB
        inst.hh[(o, "dtlb_ow")] = SIM_hap_add_callback_obj(
            "MMU_Data_TLB_Overwrite", o, 0, inst.dtlb_overwrite, None)
        inst.hh[(o, "itlb_ow")] = SIM_hap_add_callback_obj(
            "MMU_Instruction_TLB_Overwrite", o, 0, inst.itlb_overwrite, None)

def unregister_haps(obj, cpu_list):
    inst = instances[obj]
    for c in cpu_list:
        o = c.mmu
        SIM_hap_delete_callback_id("MMU_Data_TLB_Map",
                                   inst.hh[(o, "dtlb_map")])
        SIM_hap_delete_callback_id("MMU_Instruction_TLB_Map",
                                   inst.hh[(o, "itlb_map")])
        SIM_hap_delete_callback_id("MMU_Data_TLB_Demap",
                                   inst.hh[(o, "dtlb_demap")])
        SIM_hap_delete_callback_id("MMU_Instruction_TLB_Demap",
                                   inst.hh[(o, "itlb_demap")])
        SIM_hap_delete_callback_id("MMU_Data_TLB_Overwrite",
                                   inst.hh[(o, "dtlb_ow")])
        SIM_hap_delete_callback_id("MMU_Instruction_TLB_Overwrite",
                                   inst.hh[(o, "itlb_ow")])
        
def finalize_instance(obj):
    register_haps(obj, instances[obj].cpu_list)

# cpu_list
def get_cpu_list(data, obj, idx):
    return instances[obj].cpu_list

def set_cpu_list(data, obj, val, idx):
    inst = instances[obj]
    if obj.configured:
        unregister_haps(obj, inst.cpu_list)
        register_haps(obj, val)
    inst.cpu_list = val
    return Sim_Set_Ok

# instruction_translations
def get_instruction_translation(data, obj, idx):
    inst = instances[obj]
    return inst.list_from_map(inst.i_map)

def set_instruction_translation(data, obj, val, idx):
    inst = instances[obj]
    inst.i_map = inst.map_from_list(val)
    return Sim_Set_Ok

# data_translations
def get_data_translation(data, obj, idx):
    inst = instances[obj]
    return inst.list_from_map(inst.d_map)

def set_data_translation(data, obj, val, idx):
    inst = instances[obj]
    inst.d_map = inst.map_from_list(val)
    return Sim_Set_Ok


# "init_local"
class_data = class_data_t()
class_data.new_instance = new_instance
class_data.finalize_instance = finalize_instance
class_data.description = """
Keeps track of all translations inserted in the MMUs of the cpus listed in <attr>cpu_list</attr>, unless they are specifically marked invalid and flushed. The translations gathered allow access to virtual memory areas that are not currently present in the TLBs. The only architecture supported by this class is SPARCv9.
"""
SIM_register_class(class_name, class_data)

SIM_register_typed_attribute(
    class_name, "cpu_list",
    get_cpu_list, None,
    set_cpu_list, None,
    Sim_Attr_Required,
    "[o*]", None,
    "List of cpus for which TLB events are recorded in the LMT.")

SIM_register_typed_attribute(
    class_name, "data_translations",
    get_data_translation, None,
    set_data_translation, None,
    Sim_Attr_Optional,
    "[[[o,i][[iii]*]]*]", None,
    "Data translations present in the LMT. The format of the returned value is [[[mmu_object, context number], [[page_logical_address, log2_of_page_size, page_physical_address], [-another page-], ...]], -other (mmu, context) information-, ...].")

SIM_register_typed_attribute(
    class_name, "instruction_translations",
    get_instruction_translation, None,
    set_instruction_translation, None,
    Sim_Attr_Optional,
    "[[[o,i],[[iii]*]]*]", None,
    "Instruction translations present in the LMT. The format of the returned value is [[[mmu_object, context number], [[page_logical_address, log2_of_page_size, page_physical_address], [-another page-], ...]], -other (mmu, context) information-, ...].")




# commands

def data_or_instr_expander(string):
    return get_completions(string, ["data", "instruction"]);

def lmt_x_cmd(obj, cpu, address, context, type, size):
    inst = instances[obj]
    pa = inst.map_translate(cpu.mmu, context, address,
                            iff(type == "data", inst.d_map, inst.i_map))
    if pa:
        print "[%s:%s] ctxt:%d v:%x"%(cpu_name, type, context, address)
        sim_commands.x_cmd(cpu_name, ("p", pa), size)
    else:
        print "no translation found"

new_command("x", lmt_x_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name"),
             arg(int_t, "address"),
             arg(int_t, "context", "?", 0),
             arg(str_t, "type", "?", "data", expander = data_or_instr_expander),
             arg(int_t, "size", "?", 16)],
            short = "examine raw memory contents using the LMT translations",
            namespace = "logical-memory-translator",
            doc="""
Use the LMT translation to print out the contents of the memory area defined by the start virtual address <arg>address</arg> and the size <arg>size</arg> for the cpu <arg>cpu-name</arg> in the context <arg>context</arg>, looking from translations in the <arg>type</arg> TLB (either data or instruction). Note that this command does not handle areas that cross page boundaries.
""")

def lmt_da_cmd(obj, cpu, address, context, count):
    inst = instances[obj]
    pa = inst.map_translate(cpu.mmu, context, address, inst.i_map)
    if pa:
        print "[%s] ctxt:%d v:%x"%(cpu_name, context, address)
        sim_commands.disassemble_cmd(cpu_name, ("p", pa), count)
    else:
        print "no translation found"

new_command("disassemble", lmt_da_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name"),
             arg(int_t, "address"),
             arg(int_t, "context", "?", 0),
             arg(int_t, "count", "?", 1)],
            alias = "da",
            short = "disassemble instructions using the LMT translations",
            namespace = "logical-memory-translator",
            doc="""
Use the LMT translations to disassemble <arg>count</arg> instructions starting from the virtual address <arg>address</arg>, for the cpu <arg>cpu-name</arg> and the context <arg>context</arg>. Note that this command can not disassemble across page boundaries.
""")

def lmt_set_cmd(obj, cpu, address, value, size, context, type, le, be):
    phys_mem = cpu.physical_memory
    inst = instances[obj]
    pa = inst.map_translate(cpu.mmu, context, address,
                            iff(type == "data", inst.d_map, inst.i_map))
    if pa:
        sim_commands.obj_set_cmd(phys_mem, pa, value, size, le, be)
    else:
        print "no translation found"

new_command("set", lmt_set_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name"),
             arg(int_t, "address"),
             arg(int_t, "value"),
             arg(int_t, "size", "?", 4),
             arg(int_t, "context", "?", 0),
             arg(str_t, "type", "?", "data", expander = data_or_instr_expander),
             arg(flag_t, "-l"),
             arg(flag_t, "-b")],
            short = "set a value in memory using the LMT translations",
            namespace = "logical-memory-translator",
            doc="""
Use the LMT translations to set the value <arg>value</arg> with a size of <arg>size</arg> at the virtual address <arg>address</arg>, for the cpu <arg>cpu-name</arg> and the context <arg>context</arg>, looking from translations in the <arg>type</arg> TLB (either data or instruction). The <arg>-l</arg> flag sets little-endian semantics, while the <arg>-b</arg> flag sets big-endian semantics. If none is given, the endianness of <arg>cpu-name</arg> is used. Note that this command can not set values across page boundaries.
""")

def lmt_get_cmd(obj, cpu, address, size, context, type, le, be):
    phys_mem = cpu.physical_memory
    inst = instances[obj]
    pa = inst.map_translate(cpu.mmu, context, address,
                            iff(type == "data", inst.d_map, inst.i_map))
    if pa:
        return sim_commands.obj_get_cmd(phys_mem, pa, size, le, be)
    else:
        print "no translation found"

new_command("get", lmt_get_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name"),
             arg(int_t, "address"),
             arg(int_t, "size", "?", 4),
             arg(int_t, "context", "?", 0),
             arg(str_t, "type", "?", "data", expander = data_or_instr_expander),
             arg(flag_t, "-l"),
             arg(flag_t, "-b")],
            short = "get memory value using the LMT translations",
            namespace = "logical-memory-translator",
            doc="""
Use the LMT translations to get the value present at the virtual address <arg>address</arg> with a size of <arg>size</arg>, for the cpu <arg>cpu-name</arg> and the context <arg>context</arg>, looking from translations in the <arg>type</arg> TLB (either data or instruction). The <arg>-l</arg> flag sets little-endian semantics, while the <arg>-b</arg> flag sets big-endian semantics. If none is given, the endianness of <arg>cpu-name</arg> is used. Note that this command can not get values across page boundaries.            
""")

def lmt_l2p_cmd(obj, cpu, address, context, type):
    inst = instances[obj]
    pa = inst.map_translate(cpu.mmu, context, address,
                            iff(type == "data", inst.d_map, inst.i_map))
    if pa:
        return pa
    else:
        print "no translation found"

new_command("logical-to-physical", lmt_l2p_cmd,
            [arg(obj_t('processor', 'processor'), "cpu-name"),
             arg(int_t, "address"),
             arg(int_t, "context", "?", 0),
             arg(str_t, "type", "?", "data", expander = data_or_instr_expander)],
            alias = "l2p",
            short = "translate virtual address using the LMT translations",
            namespace = "logical-memory-translator",
            doc="""
Use the LMT translations to translate the virtual address <arg>address</arg>, for the cpu <arg>cpu-name</arg> and the context <arg>context</arg>, looking from translations in the <arg>type</arg> TLB (either data or instruction).
""")

def lmt_start_lmt_cmd():
    cl = []
    for o in SIM_all_objects():
        if SIM_object_is_processor(o):
            cl.append(o)
    SIM_set_configuration([
        OBJECT("lmt", "logical-memory-translator",
               cpu_list = cl)])

new_command("start-logical-memory-translator", lmt_start_lmt_cmd,
            [],
            short = "start the logical memory translator on all cpus",
            doc="""
Create a logical memory translator and plug it to all cpus available in the system.
""")
