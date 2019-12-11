/*
  pci-device.c - Generic PCI device in C

  Copyright 2000-2007 Virtutech AB
  
  The contents herein are Source Code which are a subset of Licensed
  Software pursuant to the terms of the Virtutech Simics Software
  License Agreement (the "Agreement"), and are being distributed under
  the Agreement.  You should have received a copy of the Agreement with
  this Licensed Software; if not, please contact Virtutech for a copy
  of the Agreement prior to using this Licensed Software.
  
  By using this Source Code, you agree to be bound by all of the terms
  of the Agreement, and use of this Source Code is subject to the terms
  the Agreement.
  
  This Source Code and any derivatives thereof are provided on an "as
  is" basis.  Virtutech makes no warranties with respect to the Source
  Code or any derivatives thereof and disclaims all implied warranties,
  including, without limitation, warranties of merchantability and
  fitness for a particular purpose and non-infringement.

*/

#include <stdio.h>
#include <string.h>

#include <simics/api.h>
#include <simics/alloc.h>
#include <simics/utils.h>

#define PCI_DEVICE_PRIVATE
#include "pci-device.h"

typedef struct pci_map_info {
        uint64 base;
        uint64 size;
        addr_space_t space_type;
        int function;
        int flags;
        int priority;
        uint64 target_offset;
        conf_object_t *target;  // only set if not device itself or ROM
        int align_size;
        int reverse_endian;
} pci_map_info_t;

/* Note that the info command for PCI devices uses the flag attribute */
#define PCI_FLAGS_ALWAYS_ON_R(f)        GET_BITS(f, 4, 1)
#define PCI_FLAGS_ALWAYS_ON_W(f, v)     SET_BITS(f, 4, 1, v)
#define PCI_FLAGS_MAP_IGNORE_COMMAND_R(f)    GET_BITS(f, 3, 1)
#define PCI_FLAGS_MAP_IGNORE_COMMAND_W(f, v) SET_BITS(f, 3, 1, v)
#define PCI_FLAGS_ROM_R(f)        GET_BITS(f, 2, 1)
#define PCI_FLAGS_ROM_W(f, v)     SET_BITS(f, 2, 1, v)
#define PCI_FLAGS_64BIT_R(f)      GET_BITS(f, 1, 1)
#define PCI_FLAGS_64BIT_W(f, v)   SET_BITS(f, 1, 1, v)
#define PCI_FLAGS_ENABLED_R(f)    GET_BITS(f, 0, 1)
#define PCI_FLAGS_ENABLED_W(f, v) SET_BITS(f, 0, 1, v)

typedef struct tmp_map_info {
        pci_device_t *pci;
        addr_space_t space_type;
} tmp_map_info_t;


#define SET_TYPE0_INFO(p, o, n, s, m)                          \
do {                                                           \
        (p)->config_reg_info[PCI_TYPE_0_HEADER][o].name = n;   \
        (p)->config_reg_info[PCI_TYPE_0_HEADER][o].size = s;   \
        (p)->config_reg_info[PCI_TYPE_0_HEADER][o].mask = m;   \
        (p)->config_reg_info[PCI_TYPE_0_HEADER][o].offset = o; \
} while (0)

#define SET_TYPE1_INFO(p, o, n, s, m)                          \
do {                                                           \
        (p)->config_reg_info[PCI_TYPE_1_HEADER][o].name = n;   \
        (p)->config_reg_info[PCI_TYPE_1_HEADER][o].size = s;   \
        (p)->config_reg_info[PCI_TYPE_1_HEADER][o].mask = m;   \
        (p)->config_reg_info[PCI_TYPE_1_HEADER][o].offset = o; \
} while (0)


static void
init_reg_info(pci_device_t *pci)
{       
        SET_TYPE0_INFO(pci, PCI_VENDOR_ID,            "Vendor ID",                   2,     0x0000);
        SET_TYPE0_INFO(pci, PCI_DEVICE_ID,            "Device ID",                   2,     0x0000);
        SET_TYPE0_INFO(pci, PCI_COMMAND,              "Command",                     2,     0x03ff);
        SET_TYPE0_INFO(pci, PCI_STATUS,               "Status",                      2,     0xf900);
        SET_TYPE0_INFO(pci, PCI_REVISION_ID,          "Revision ID",                 1,       0x00);
        SET_TYPE0_INFO(pci, PCI_CLASS_CODE,           "Class Code",                  3,       0x00);
        SET_TYPE0_INFO(pci, PCI_CACHE_LINE_SIZE,      "Cache Line Size",             1,       0xff);
        SET_TYPE0_INFO(pci, PCI_LATENCY_TIMER,        "Latency Timer",               1,       0xff);
        SET_TYPE0_INFO(pci, PCI_HEADER_TYPE,          "Header Type",                 1,       0x00);
        SET_TYPE0_INFO(pci, PCI_BIST,                 "BIST",                        1,       0x40);
        SET_TYPE0_INFO(pci, PCI_BASE_ADDRESS_0,       "Base Address 0",              4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_BASE_ADDRESS_1,       "Base Address 1",              4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_BASE_ADDRESS_2,       "Base_Address 2",              4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_BASE_ADDRESS_3,       "Base_Address 3",              4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_BASE_ADDRESS_4,       "Base_Address 4",              4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_BASE_ADDRESS_5,       "Base_Address 5",              4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_CARDBUS_CIS_PTR,      "Cardbus CIS Ptr",             4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_SUBSYSTEM_VENDOR_ID,  "Subsystem Vendor ID",         2,     0x0000);
        SET_TYPE0_INFO(pci, PCI_SUBSYSTEM_ID,         "Subsystem ID",                2,     0x0000);
        SET_TYPE0_INFO(pci, PCI_EXPANSION_ROM_BASE,   "Expansion ROM Base",          4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_CAPABILITIES_POINTER, "Capabilities Pointer",        1,       0x00);
        SET_TYPE0_INFO(pci, PCI_RESERVED1,            "Reserved",                    3,   0x000000);
        SET_TYPE0_INFO(pci, PCI_RESERVED2,            "Reserved",                    4, 0x00000000);
        SET_TYPE0_INFO(pci, PCI_INTERRUPT_LINE,       "Interrupt Line",              1,       0xff);
        SET_TYPE0_INFO(pci, PCI_INTERRUPT_PIN,        "Interrupt Pin",               1,       0x00);
        SET_TYPE0_INFO(pci, PCI_MIN_GNT,              "Min_Gnt",                     1,       0x00);
        SET_TYPE0_INFO(pci, PCI_MAX_LAT,              "Max_Lat",                     1,       0x00);

        SET_TYPE1_INFO(pci, PCI_VENDOR_ID,                   "Vendor ID",                   2,     0x0000);
        SET_TYPE1_INFO(pci, PCI_DEVICE_ID,                   "Device ID",                   2,     0x0000);
        SET_TYPE1_INFO(pci, PCI_COMMAND,                     "Command",                     2,     0x03ff);
        SET_TYPE1_INFO(pci, PCI_STATUS,                      "Status",                      2,     0xf900);
        SET_TYPE1_INFO(pci, PCI_REVISION_ID,                 "Revision ID",                 1,       0x00);
        SET_TYPE1_INFO(pci, PCI_CLASS_CODE,                  "Class Code",                  3,   0x000000);
        SET_TYPE1_INFO(pci, PCI_CACHE_LINE_SIZE,             "Cache Line Size",             1,       0xff);
        SET_TYPE1_INFO(pci, PCI_LATENCY_TIMER,               "Latency Timer",               1,       0xff);
        SET_TYPE1_INFO(pci, PCI_HEADER_TYPE,                 "Header Type",                 1,       0x00);
        SET_TYPE1_INFO(pci, PCI_BIST,                        "BIST",                        1,       0x40);
        SET_TYPE1_INFO(pci, PCI_BASE_ADDRESS_0,              "Base Address 0",              4, 0x00000000);
        SET_TYPE1_INFO(pci, PCI_BASE_ADDRESS_1,              "Base Address 1",              4, 0x00000000);
        SET_TYPE1_INFO(pci, PCI_PRIMARY_BUS_NUMBER,          "Primary Bus Number",          1,       0xff);
        SET_TYPE1_INFO(pci, PCI_SECONDARY_BUS_NUMBER,        "Secondary Bus Number",        1,       0xff);
        SET_TYPE1_INFO(pci, PCI_SUBORDINATE_BUS_NUMBER,      "Subordinate Bus Number",      1,       0xff);
        SET_TYPE1_INFO(pci, PCI_SECONDARY_LATENCY_TIMER,     "Secondary Latency Timer",     1,       0xff);
        SET_TYPE1_INFO(pci, PCI_IO_BASE,                     "I/O Base",                    1,       0xf0);
        SET_TYPE1_INFO(pci, PCI_IO_LIMIT,                    "I/O Limit",                   1,       0xf0);
        SET_TYPE1_INFO(pci, PCI_SECONDARY_STATUS,            "Secondary Status",            2,     0xf800);
        SET_TYPE1_INFO(pci, PCI_MEMORY_BASE,                 "Memory Base",                 2,     0xfff0);
        SET_TYPE1_INFO(pci, PCI_MEMORY_LIMIT,                "Memory Limit",                2,     0xfff0);
        SET_TYPE1_INFO(pci, PCI_PREFETCHABLE_MEMORY_BASE,    "Prefetchable Memory Base",    2,     0xfff0);
        SET_TYPE1_INFO(pci, PCI_PREFETCHABLE_MEMORY_LIMIT,   "Prefetchable Memory Limit",   2,     0xfff0);
        SET_TYPE1_INFO(pci, PCI_PREFETCHABLE_BASE_UPPER_32,  "Prefetchable Base Upper 32",  4, 0x00000000);
        SET_TYPE1_INFO(pci, PCI_PREFETCHABLE_LIMIT_UPPER_32, "Prefetchable Limit Upper 32", 4, 0x00000000);
        SET_TYPE1_INFO(pci, PCI_IO_BASE_UPPER_16,            "I/O Base Upper 16",           2,     0xffff);
        SET_TYPE1_INFO(pci, PCI_IO_LIMIT_UPPER_16,           "I/O Limit Upper 16",          2,     0xffff);
        SET_TYPE1_INFO(pci, PCI_CAPABILITIES_POINTER,        "Capabilities Pointer",        1,       0x00);
        SET_TYPE1_INFO(pci, PCI_RESERVED1,                   "Reserved",                    3,       0x00);
        SET_TYPE1_INFO(pci, PCI_INTERRUPT_LINE,              "Interrupt Line",              1,       0xff);
        SET_TYPE1_INFO(pci, PCI_INTERRUPT_PIN,               "Interrupt Pin",               1,       0x00);
        SET_TYPE1_INFO(pci, PCI_BRIDGE_EXPANSION_ROM_BASE,   "Expansion ROM Base",          4, 0x00000000);
        SET_TYPE1_INFO(pci, PCI_BRIDGE_CONTROL,              "Bridge Control",              2,     0x0fef);
}

/* next ones are only set by type1 devices (pci-bridge.c) */
void (*type1_configuration_register_write)(pci_device_t *pci, uint32 offset,
                                           uint32 size, uint32 value);
void (*type1_reset)(pci_device_t *pci);
void (*get_bridge_bus_info)(pci_device_t *pci);

static int
remove_map(ht_table_t *table, uint64 reg, void *_map, void *user)
{
        pci_map_info_t *map_info = _map;
        tmp_map_info_t *tmp_info = user;
        pci_device_t *pci = tmp_info->pci;
        conf_object_t *map_obj;
        const char *desc;

        if (tmp_info->space_type != map_info->space_type)
                return 1;

        if (map_info->target)
                map_obj = map_info->target;
        else
                map_obj = &pci->log->obj;

        if (PCI_FLAGS_ROM_R(map_info->flags))
                desc = "expansion ROM";
        else if (map_info->space_type == Sim_Addr_Space_IO)
                desc = "I/O space";
        else
                desc = "memory space";

	SIM_log_info(2, pci->log, pci->log_group,
                     "Removing %s mapping (function %d)",
                     desc,
                     map_info->function);

        if (pci->pci_bus) {
                pci->pci_bus_interface.remove_map(pci->pci_bus, map_obj,
                                                  map_info->space_type,
                                                  map_info->function);
        }
        return 1;
}

static int
add_map(ht_table_t *table, uint64 reg, void *_map, void *user)
{
        map_info_t info;
        pci_map_info_t *map_info = _map;
        tmp_map_info_t *tmp_info = user;
        pci_device_t *pci = tmp_info->pci;
        conf_object_t *map_obj;
        const char *desc;

        if (tmp_info->space_type != map_info->space_type)
                return 1;

        if (!PCI_FLAGS_ENABLED_R(map_info->flags))
                return 1;

        /* expansion rom has an extra enable bit in the base register */
        if ((reg == PCI_EXPANSION_ROM_BASE
             || reg == PCI_BRIDGE_EXPANSION_ROM_BASE)
            && !(PCI_read_config_register(pci, reg) & 1))
                return 1;

        if (map_info->target)
                map_obj = map_info->target;
        else
                map_obj = &pci->log->obj;
        
        if (PCI_FLAGS_ROM_R(map_info->flags))
                desc = "expansion ROM";
        else if (map_info->space_type == Sim_Addr_Space_IO)
                desc = "I/O space";
        else
                desc = "memory space";

	// add this new mapping
        if (pci->pci_bus) {
                memset(&info, 0, sizeof(map_info_t));
                info.base = map_info->base;
                info.start = map_info->target_offset;
                info.length = map_info->size;
                info.function = map_info->function;
                info.priority = map_info->priority;
                info.align_size = map_info->align_size;
                info.reverse_endian = map_info->reverse_endian;
                pci->pci_bus_interface.add_map(pci->pci_bus, map_obj,
                                               tmp_info->space_type, 0, info);
        	SIM_log_info(2, pci->log, pci->log_group,
                             "New %s mapping (function %d): "
                             "base = 0x%llx, length = 0x%llx",
                             desc,
                             map_info->function,
                             map_info->base,
                             map_info->size);
        }
        return 1;
}

static int
try_remove_map(ht_table_t *table, uint64 reg, void *_map, void *user)
{
        pci_map_info_t *map_info = _map;

        if (PCI_FLAGS_ALWAYS_ON_R(map_info->flags))
                return 1;

        return remove_map(table, reg, _map, user);
}

static void
try_remove_mappings(pci_device_t *pci, addr_space_t space_type)
{
        tmp_map_info_t map;
        map.pci = pci;
        map.space_type = space_type;
        ht_for_each_entry(pci->map_table, try_remove_map, &map);
}

static void
remove_mappings(pci_device_t *pci, addr_space_t space_type)
{
        tmp_map_info_t map;
        map.pci = pci;
        map.space_type = space_type;
        ht_for_each_entry(pci->map_table, remove_map, &map);
}

static void
add_mappings(pci_device_t *pci, addr_space_t space_type)
{
        tmp_map_info_t map;

        /* first remove previous mappings */
        remove_mappings(pci, space_type);

        map.pci = pci;
        map.space_type = space_type;
        ht_for_each_entry(pci->map_table, add_map, &map);
}


static void
add_pci_space(pci_device_t *pci, int reg, pci_map_info_t *pci_map)
{
        int cmd;
        tmp_map_info_t map;

        /* allow early map changes */
        if (!pci->log->obj.configured)
                return;

        map.pci = pci;
        map.space_type = pci_map->space_type;

        remove_map(NULL, reg, pci_map, &map);

        cmd = PCI_read_config_register(pci, PCI_COMMAND);

        if (!PCI_FLAGS_MAP_IGNORE_COMMAND_R(pci_map->flags)
            && pci_map->space_type == Sim_Addr_Space_IO && !(cmd & 1))
                return; /* IO mappings disabled */

        if (!PCI_FLAGS_MAP_IGNORE_COMMAND_R(pci_map->flags)
            && pci_map->space_type == Sim_Addr_Space_Memory && !(cmd & 2))
                return; /* memory mappings disabled */

        add_map(NULL, reg, pci_map, &map);
}


/* <add-fun id="pci device api">
   <short>add device specific configuration register</short>
   Adds a device specific configuration register to the generic
   PCI device. When the generic PCI code knows the size of the
   register, it can handle overlapping register accesses. This
   means that the <tt>conf_write_func</tt> function (registered
   with <fun>PCI_device_init</fun>) always will be called with an
   offset that is the start of a register. It is not possible to
   override the standard configuration registers using this
   function. The <arg>mask</arg> argument is the write mask. Only
   bits set in this mask will be writable in the register. Note that
   register names and sizes are not checkpointed and always has to
   be initialized when a device is instantiated. The mask, however,
   is checkpointed since it may be changed at run-time.

   The newly created config register will contain <arg>initial_value</arg>.
   </add-fun>
*/
void
PCI_add_config_register(pci_device_t *pci, uint32 offset,
                        const char *name, int size, uint32 mask,
                        uint32 initial_value)
{
        config_reg_info_t *info;

        ASSERT(size > 0 && size <= 4);
        ASSERT(PCI_config_register_size(pci, offset) == 0);
        ASSERT((offset >= STANDARD_CONFIGURATION_SIZE)
               && (offset < CONFIGURATION_SPACE_SIZE));

        info = MM_ZALLOC(1, config_reg_info_t);
        info->name = name;
        info->size = size;
        info->mask = mask;
        info->offset = offset;
        ht_update_int(pci->user_reg_table, offset, info);

        PCI_write_sized_config_register(pci, offset, initial_value, size);
}


/* <add-fun id="pci device api">
   <short>set write mask of a configuration register</short>
   This function sets the write mask of a configuration register.
   Only bits set to 1 in <arg>mask</arg> are writable. Many PCI devices
   do not implement all bits in their configuration registers. By
   setting a write mask for such registers, the default access handling
   in the generic PCI device code can still be used.
   </add-fun>
*/
void
PCI_set_config_register_mask(pci_device_t *pci, uint32 offset, uint32 mask)
{
	if (offset < STANDARD_CONFIGURATION_SIZE) {
                int htype = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
                pci->config_reg_info[htype][offset].mask = mask;
        } else {
                config_reg_info_t *info =
                        ht_lookup_int(pci->user_reg_table, offset);
                ASSERT(info);
                info->mask = mask;
        }
}


/* <add-fun id="pci device api">
   <short>get write mask of a configuration register</short>
   Returns the write mask for a configuration register.
   <doc-item name="RETURN VALUE">
   Configuration register write mask.
   </doc-item>
   </add-fun>
*/
uint32
PCI_get_config_register_mask(pci_device_t *pci, uint32 offset)
{
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;

	if (offset < STANDARD_CONFIGURATION_SIZE)
                return pci->config_reg_info[header_type][offset].mask;

        config_reg_info_t *info = ht_lookup_int(pci->user_reg_table, offset);
        if (info)
                return info->mask;
        else
                return 0xffffffff;
}


/* <add-fun id="pci device api">
   <short>return name of a configuration register</short>
   Returns the name of a configuration register, specified by a
   byte offset into the configuration header. Only standard configuration
   registers, i.e. as defined in the PCI specification, are handled.
   The header type of the PCI device affects the result.
   <doc-item name="RETURN VALUE">
   The name of the configuration register is returned if the offset
   corresponds to a valid configuration register. If not, NULL is
   returned.
   </doc-item>
   </add-fun>
*/
const char *
PCI_config_register_name(pci_device_t *pci, uint32 offset)
{
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;

	if (offset < STANDARD_CONFIGURATION_SIZE)
                return pci->config_reg_info[header_type][offset].name;

        config_reg_info_t *info = ht_lookup_int(pci->user_reg_table, offset);
        if (info)
                return info->name;
        return NULL;
}


/* <add-fun id="pci device api">
   <short>return size of a configuration register</short>
   Returns the size of a configuration register, specified by a
   byte offset into the configuration header. Only standard configuration
   registers, i.e. as defined in the PCI specification, are handled.
   The header type of the PCI device affects the result.
   <doc-item name="RETURN VALUE">
   The size (in bytes) of the configuration register is returned if the
   offset corresponds to a valid configuration register. If not, 0 is
   returned.
   </doc-item>
   </add-fun>
*/
uint32
PCI_config_register_size(pci_device_t *pci, uint32 offset)
{
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;

	if (offset < STANDARD_CONFIGURATION_SIZE)
                return pci->config_reg_info[header_type][offset].size;

        config_reg_info_t *info = ht_lookup_int(pci->user_reg_table, offset);
        if (info)
                return info->size;
        return 0;
}


/* <add-fun id="pci device api">
   <short>read a configuration register</short>
   Returns the value of a configuration register specified by a byte
   offset into the configuration header. The <fun>PCI_read_config_register</fun>
   function can only be used to read standard configuration registers, i.e. as
   defined in the PCI specification, and registers that are added with
   <fun>PCI_add_config_register</fun>. For other configuration registers
   the <fun>PCI_read_sized_config_register</fun> should be used, since the sizes
   of those registers are not known to the generic PCI device.
   <doc-item name="RETURN VALUE">
   The value, in host endian order, of the configuration register.
   </doc-item>
   </add-fun>
*/
uint32
PCI_read_sized_config_register(pci_device_t *pci, uint32 offset, 
                               uint32 size)
{
	uint32 value = 0;
	
	ASSERT(offset < CONFIGURATION_SPACE_SIZE);

	switch(size) {
	case 1:
		return pci->config_registers[offset];
	case 2:
		memcpy((char *)&value, &pci->config_registers[offset], 2);
		return CONVERT_LE32(value);
	case 3:
		memcpy((char *)&value, &pci->config_registers[offset], 3);
		return CONVERT_LE32(value);
	case 4:
		memcpy((char *)&value, &pci->config_registers[offset], 4);
		return CONVERT_LE32(value);
        default:
                ASSERT(0);
                return 0;
	}
}


/* <append-fun id="PCI_read_sized_config_register"/> */
uint32
PCI_read_config_register(pci_device_t *pci, uint32 offset)
{
	uint32 size = PCI_config_register_size(pci, offset);
        ASSERT(size);
	return PCI_read_sized_config_register(pci, offset, size);
}


/* <add-fun id="pci device api">
   <short>write a configuration register</short>
   Writes a value, in host endian order, to a configuration register
   specified by a byte offset into the configuration header. The
   <fun>PCI_write_config_register</fun> function can only be used to
   write standard configuration registers, i.e. as defined in the PCI
   specification. <fun>PCI_write_sized_config_register</fun> is
   typically used to write device specific configuration registers
   since the sizes of those registers are not known to the generic PCI
   device.
   <doc-item name="NOTE">
   No side effects are triggered by writing configuration registers with
   these functions. <fun>PCI_default_configuration_write_access</fun>
   can be used to get the side effects handled by the generic PCI device.
   </doc-item>
   </add-fun>
*/
void
PCI_write_sized_config_register(pci_device_t *pci, uint32 offset, 
                                uint32 value, uint32 size)
{
	ASSERT(offset < CONFIGURATION_SPACE_SIZE);

	switch(size) {
	case 1:
		pci->config_registers[offset] = value;
		break;
	case 2:
		value = CONVERT_LE32(value);
		memcpy(&pci->config_registers[offset], (char *)&value, 2);
		break;
	case 3:
		value = CONVERT_LE32(value);
		memcpy(&pci->config_registers[offset], (char *)&value, 3);
		break;
	case 4:
		value = CONVERT_LE32(value);
		memcpy(&pci->config_registers[offset], (char *)&value, 4);
		break;
	default:
		ASSERT(0);
	}	       

}


/* <append-fun id="PCI_read_sized_config_register"/> */
void
PCI_write_config_register(pci_device_t *pci, uint32 offset, 
                          uint32 value)
{
	uint32 size = PCI_config_register_size(pci, offset);
	ASSERT(size);
	PCI_write_sized_config_register(pci, offset, value, size);
}


static void
create_map32(pci_device_t *pci, pci_map_info_t *pci_map, uint32 offset, uint32 value)
{
        uint32 base, mask;
        
        /* write access to a valid base register */
        mask = -pci_map->size;
        // update the base register
        base = PCI_read_config_register(pci, offset);
        base &= ~mask;
        base |= value & mask;

        /* use new enable bit */
        if ((offset == PCI_EXPANSION_ROM_BASE) || (offset == PCI_BRIDGE_EXPANSION_ROM_BASE))
                base = (base & ~1) | (value & 1);

        PCI_write_config_register(pci, offset, base);
        pci_map->base = base & mask;
        add_pci_space(pci, offset, pci_map);
}


static void
create_map64(pci_device_t *pci, pci_map_info_t *pci_map, uint32 offset, uint32 lvalue, uint32 hvalue)
{
        uint64 base, mask, value;

        value = ((uint64)hvalue << 32) | lvalue;
        
        /* write access to a valid base register */
        mask = -pci_map->size;
        // update the base register
        base = ((uint64)PCI_read_config_register(pci, offset + 4) << 32)
                | PCI_read_config_register(pci, offset);
        base &= ~mask;
        base |= value & mask;
        PCI_write_config_register(pci, offset + 0, (uint32)base);
        PCI_write_config_register(pci, offset + 4, base >> 32);
        pci_map->base = base & mask;
        
        add_pci_space(pci, offset, pci_map);
}

void
base_address_write(pci_device_t *pci, uint32 offset, uint32 value)
{
        int access_hi = 0;

        pci_map_info_t *pci_map = ht_lookup_int(pci->map_table, offset);
        if (pci_map == NULL && offset > PCI_BASE_ADDRESS_0) {
                pci_map = ht_lookup_int(pci->map_table, offset - 4);
                if (pci_map && PCI_FLAGS_64BIT_R(pci_map->flags))
                        access_hi = 1;
                else
                        pci_map = NULL;
        }
        if (pci_map && PCI_FLAGS_ENABLED_R(pci_map->flags)) {
                if (PCI_FLAGS_64BIT_R(pci_map->flags)) {
                        create_map64(pci, pci_map,
                                     access_hi ? offset - 4 : offset,
                                     access_hi ? PCI_read_config_register(pci, offset- 4) : value,
                                     access_hi ? value : PCI_read_config_register(pci, offset + 4));
                } else {
                        create_map32(pci, pci_map, offset, value);
                }
        }
}


/* <add-fun id="pci device api">
   <short>default function for configuration register reads</short>
   A PCI device can override this default configuration read function
   with a function specified in the <fun>PCI_device_init</fun> call.
   The overriding function can then call this default function for
   configuration registers that it does not handle itself.
   <doc-item name="RETURN VALUE">
   The value of the configuration register is returned.
   </doc-item>
   </add-fun>
*/
uint32
PCI_default_configuration_read_access(conf_object_t *obj, 
                                      uint32 offset, uint32 size)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
	return PCI_read_sized_config_register(pci, offset, size);
}


/* both type 0 and type 1 */
void
common_configuration_register_write(pci_device_t *pci, uint32 offset, uint32 size, uint32 value)
{
	switch (offset) {
        case PCI_VENDOR_ID:
        case PCI_DEVICE_ID:
        case PCI_REVISION_ID:
        case PCI_CLASS_CODE:
        case PCI_HEADER_TYPE:
        case PCI_CAPABILITIES_POINTER:
        case PCI_RESERVED1:
        case PCI_INTERRUPT_PIN:
                break; /* read-only */

	case PCI_COMMAND:
                if (value & 1)
                        add_mappings(pci, Sim_Addr_Space_IO);
                else
                        try_remove_mappings(pci, Sim_Addr_Space_IO);
                if (value & 2)
                        add_mappings(pci, Sim_Addr_Space_Memory);
                else
                        try_remove_mappings(pci, Sim_Addr_Space_Memory);

                PCI_write_sized_config_register(pci, offset, value, size);
                break;

	case PCI_STATUS: {
                uint16 status = PCI_read_sized_config_register(pci, offset, size);
                value &= 0xf800; // only bit 15-11 writable
                /* bits set in value clears the corresponding ones in status */
                value = (status & (value ^ status)) | (status & 0x7ff);
                PCI_write_sized_config_register(pci, offset, value, size);
                break;
        }

        case PCI_BASE_ADDRESS_0:
        case PCI_BASE_ADDRESS_1:
                base_address_write(pci, offset, value);
                break;

        case PCI_CACHE_LINE_SIZE:
        case PCI_LATENCY_TIMER:
        case PCI_BIST:
        case PCI_INTERRUPT_LINE:
        default:
                PCI_write_sized_config_register(pci, offset, value, size);
                break;
        }
}


static void
type0_configuration_register_write(pci_device_t *pci, uint32 offset, uint32 size, uint32 value)
{
	switch (offset) {
        case PCI_BASE_ADDRESS_2:
        case PCI_BASE_ADDRESS_3:
        case PCI_BASE_ADDRESS_4:
        case PCI_BASE_ADDRESS_5:
        case PCI_EXPANSION_ROM_BASE:
                base_address_write(pci, offset, value);
                break;

        case PCI_CARDBUS_CIS_PTR:
        case PCI_RESERVED2:
        case PCI_MIN_GNT:
        case PCI_MAX_LAT:
                break; /* read-only */
        default:
                common_configuration_register_write(pci, offset, size, value);
        }
}


/* <add-fun id="pci device api">
   <short>default function for configuration register writes</short>
   A PCI device can override this default configuration wite function
   with a function specified in the <fun>PCI_device_init</fun> call.
   The overriding function can then call this default function for
   configuration registers that it does not handle itself. Side-effects
   for the <tt>Command</tt>, <tt>Status</tt>, <tt>Base Address</tt>,
   <tt>Secondary Status</tt> and <tt>Expansion ROM Base</tt>
   registers are handled.
   </add-fun>
*/
void
PCI_default_configuration_write_access(conf_object_t *obj, 
                                       uint32 offset, uint32 size, 
                                       uint32 value)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
        int reg_size = PCI_config_register_size(pci, offset);

        // partial access etc should already be handled
        if (reg_size) // allow accesses to unknown registers for now
                ASSERT(PCI_config_register_size(pci, offset) == size);

        switch(header_type) {
        case PCI_TYPE_0_HEADER:
                type0_configuration_register_write(pci, offset, size, value);
                break;
        case PCI_TYPE_1_HEADER:
                if (type1_configuration_register_write) {
                        type1_configuration_register_write(pci, offset, size,
                                                           value);
                }
                break;
        default:
                ASSERT(0);
        }
}

static ht_table_t *
make_intkey_hash_table(void)
{
        ht_table_t *ht = MM_MALLOC(1, ht_table_t);
        ht_init_table(ht, 1);
        return ht;
}

/* <add-fun id="pci device api">
   <short>initialize the generic PCI device</short>
   Initializes the generic PCI device and optionally overrides some default
   functions. The arguments <arg>log</arg> and <arg>pci</arg> are pointers
   within the device structure, and <arg>log_group</arg> is the log group
   (as defined by <fun>SIM_log_register_groups</fun>) that the generic PCI
   device should use for configuration related logging. Use 0 if no log groups
   are defined. The <arg>unused</arg> function should be NULL.
   PCI bus resets are delivered to each PCI device by calling the
   installed <arg>pci_bus_reset</arg> function.
   The <arg>conf_read_func</arg> and <arg>conf_write_func</arg> functions
   are optional, they can be used to override the default behavior on
   accesses to the device's configuration registers. When called, the
   <arg>offset</arg> and <arg>size</arg> arguments corresponds to a complete
   configuration register if it is known. It is therefore recommended that
   device specific registers are added with <fun>PCI_add_config_register</fun>.
   I.e. partial and overlapping accesses are handled by the generic PCI device
   code before these callbacks are called. Accesses that do not correspond
   to known registers are handled byte by byte.
   The <arg>pci_irq_ack</arg> function is also optional, it is only used if
   the device responds to <i>Interrupt Acknowledge</i> cycles on the PCI bus.
   The last argument, <arg>pci_operation</arg>, is required. This function is
   called for all accesses to the memory and I/O mappings of the device. Memory
   and I/O space mappings can be created with <fun>PCI_handle_mapping32</fun>
   and <fun>PCI_handle_mapping64</fun>.

   The generic PCI device code will use the <tt>object_data</tt> field of the
   conf_object_t struct, it should not be modified by the code implementing
   a specific device.
   </add-fun>
*/
void
PCI_device_init(log_object_t *log, int log_group,
                pci_device_t *pci,
                pci_device_t *(*unused)(conf_object_t *), /* call with NULL */
                void (*pci_bus_reset)(conf_object_t *obj),
                uint32 (*conf_read_func)(conf_object_t *obj, 
                                         uint32 offset, 
                                         uint32 size),
                void (*conf_write_func)(conf_object_t *obj, 
                                        uint32 offset, 
                                        uint32 size, 
                                        uint32 value),
                exception_type_t (*pci_operation)(
                        conf_object_t *obj,
                        generic_transaction_t *mem_op,
                        map_info_t map_info))
{
        ASSERT(log);
        ASSERT(pci_operation);

        pci->log = log;
        pci->log_group = log_group;
        pci->log->obj.object_data = pci;
        pci->pci_operation = pci_operation;

        init_reg_info(pci);

        pci->bus_address = (uint32)-1;

        if (pci_bus_reset)
                pci->pci_bus_reset = pci_bus_reset;
        else
                pci->pci_bus_reset = PCI_default_device_reset;

        if (conf_read_func)
                pci->conf_read_func = conf_read_func;
        else
                pci->conf_read_func = PCI_default_configuration_read_access;
        if (conf_write_func)
                pci->conf_write_func = conf_write_func;
        else
                pci->conf_write_func = PCI_default_configuration_write_access;

        pci->map_table = make_intkey_hash_table();
        pci->user_reg_table = make_intkey_hash_table();
}


/* <add-fun id="pci device api">
   <short>handle base address register</short>
   Tells the generic PCI device code to handle the memory mapping associated
   with the base address at configuration header offset <arg>reg</arg>. All
   read and write accesses to the base address will be handled, and the
   mappings will be enabled and disabled according to the enable bits in the
   PCI <tt>command</tt> register, and for expansion ROM also the enable bit
   in the base address register itself. The lowest bits in the base address
   register will be set to indicate space type and if the device is 32 or
   64 bit addressable. 64 bit mappings are registered with
   <fun>PCI_handle_mapping64</fun>, and 32 bit ones with
   <fun>PCI_handle_mapping32</fun>.

   The <arg>space</arg> argument specifies if the memory or I/O space is used.
   The <arg>size</arg> argument is the size of the memory mappings,  and
   <arg>function</arg> a function number used to identify the mapping. The
   <arg>priority</arg> should be 0, unless the device can have mappings that
   overlap, in that case each mapping must have unique priority. By default
   the device itself is mapped at the base address, but in some cases another
   object should be the target. In that case, the <arg>target</arg> argument
   can be set, and <arg>target_offset</arg> to the byte offset into the target.
   It is also possible to set an alignment boundary size, and an inverse
   endian flags. These are documented with the <tt>map</tt> attribute in the
   <tt>memory-space</tt> class.

   There are also functions in the PCI Device API that can be used to
   modify the mapping in run-time. This is not needed for standard PCI
   devices.
   </add-fun>
*/
void
PCI_handle_mapping32(pci_device_t *pci, int reg,
                     addr_space_t space,
                     uint32 size, int function, int priority,
                     uint64 target_offset,
                     conf_object_t *target,
                     int alignment, int inverse_endian)
{
        pci_map_info_t *pci_map;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
        int rom = 0;

        if ((reg == PCI_EXPANSION_ROM_BASE) || (reg == PCI_BRIDGE_EXPANSION_ROM_BASE))
                rom = 1;

#if !defined(PCI_HANDLE_ANY_BASE_ADDRESS)
        if ((header_type == PCI_TYPE_0_HEADER)
            && (reg != PCI_BASE_ADDRESS_0)
            && (reg != PCI_BASE_ADDRESS_1)
            && (reg != PCI_BASE_ADDRESS_2)
            && (reg != PCI_BASE_ADDRESS_3)
            && (reg != PCI_BASE_ADDRESS_4)
            && (reg != PCI_BASE_ADDRESS_5)
            && (reg != PCI_EXPANSION_ROM_BASE))
                ASSERT_MSG(0, "Illegal base register in handle_pci_mapping()");
#endif

        if ((header_type == PCI_TYPE_1_HEADER)
            && (reg != PCI_BASE_ADDRESS_0)
            && (reg != PCI_BASE_ADDRESS_1)
            && (reg != PCI_BRIDGE_EXPANSION_ROM_BASE))
                ASSERT_MSG(0, "Illegal base register in handle_pci_mapping()");

        /* ignore if we already got the map-info from a checkpoint */
        if (ht_lookup_int(pci->map_table, reg))
                return;
        
        pci_map = MM_ZALLOC(1, pci_map_info_t);
        pci_map->size = size;
        pci_map->function = function;
        pci_map->priority = priority;
        pci_map->space_type = space;
        pci_map->target_offset = target_offset;
        pci_map->target = target;
        pci_map->align_size = alignment;
        pci_map->reverse_endian = inverse_endian;
        PCI_FLAGS_ENABLED_W(pci_map->flags, 1);
        if (rom)
                PCI_FLAGS_ROM_W(pci_map->flags, 1);

        if (space == Sim_Addr_Space_IO) {
                // TODO: set mask according to size
                PCI_set_config_register_mask(pci, reg, 0xfffffffc);
                /* bit 0 should be set for IO base registers */
                PCI_write_config_register(pci, reg, PCI_read_config_register(pci, reg) | 1);
        } else if (space == Sim_Addr_Space_Memory) {
                // TODO: set mask according to size (now handled in map functions)
                if (rom)
                        PCI_set_config_register_mask(pci, reg, 0xfffff801);
                else
                        PCI_set_config_register_mask(pci, reg, 0xfffffff0);
        } else {
                ASSERT_MSG(0, "Illegal space type in handle_pci_mapping()");
        }
        
        ht_update_int(pci->map_table, reg, pci_map);
}


/* <append-fun id="PCI_handle_mapping32"/> */
void
PCI_handle_mapping64(pci_device_t *pci, int reg,
                     uint64 size, int function, int priority,
                     uint64 target_offset,
                     conf_object_t *target,
                     int alignment, int inverse_endian)
{
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
        pci_map_info_t *pci_map;

        if ((header_type == PCI_TYPE_0_HEADER)
            && (reg != PCI_BASE_ADDRESS_0)
            && (reg != PCI_BASE_ADDRESS_1)
            && (reg != PCI_BASE_ADDRESS_2)
            && (reg != PCI_BASE_ADDRESS_3)
            && (reg != PCI_BASE_ADDRESS_4))
                ASSERT_MSG(0, "Illegal base register in handle_pci_mapping64()");

        if ((header_type == PCI_TYPE_1_HEADER)
            && (reg != PCI_BASE_ADDRESS_0))
                ASSERT_MSG(0, "Illegal base register in handle_pci_mapping64()");
        
        pci_map = MM_ZALLOC(1, pci_map_info_t);
        pci_map->size = size;
        pci_map->function = function;
        pci_map->priority = priority;
        pci_map->space_type = Sim_Addr_Space_Memory;
        pci_map->target_offset = target_offset,
        pci_map->target = target;
        pci_map->align_size = alignment;
        pci_map->reverse_endian = inverse_endian;
        PCI_FLAGS_ENABLED_W(pci_map->flags, 1);
        PCI_FLAGS_64BIT_W(pci_map->flags, 1);

        // TODO: set mask according to size
        PCI_set_config_register_mask(pci, reg, 0xfffffff0);
        PCI_set_config_register_mask(pci, reg + 4, 0xffffffff);

        /* bit 2:1 should be set to 0b10 in the low base register */
        PCI_write_config_register(pci, reg,
                                  PCI_read_config_register(pci, reg) | 0x4);
        ht_update_int(pci->map_table, reg, pci_map);
}


/* <add-fun id="pci device api">
   <short>Specifies if memory accesses are stallable</short>
   The <fun>PCI_set_may_stall</fun> function can be used to
   enable and disable stallable memory accesses. By default all
   accesses initiated by the device are not stallable.
   <fun>PCI_get_may_stall</fun> is used to query if stallable
   accesses are enabled or not.
   </add-fun>
*/
void
PCI_set_may_stall(pci_device_t *pci, int may_stall)
{
        pci->may_stall = may_stall;
}


/* <append-fun id="PCI_set_may_stall"/> */
int
PCI_get_may_stall(pci_device_t *pci)
{
        return pci->may_stall;
}

static pci_map_info_t *
get_pci_map(pci_device_t *pci, int reg)
{
        pci_map_info_t *pm = ht_lookup_int(pci->map_table, reg);
        if (!pm) {
                SIM_log_error(pci->log, pci->log_group,
                              "Internal access of unknown PCI mapping"
                              " (Register %d).",
                              reg);
        }
        return pm;
}

/* <add-fun id="pci device api">
   <short>query and modify base address mapping</short>
   The following functions can be used to modify base address mappings
   that have been registered with <fun>PCI_handle_mapping32</fun> and
   <fun>PCI_handle_mapping64</fun>. Standard PCI devices typically
   doesn't have to modify the mappings, but some bridges and special
   devices have alternative registers to modify the memory mappings.
   <fun>PCI_set_map_base</fun> changes the base address, and also
   the contents of the base address register. <fun>PCI_set_map_size</fun>
   changes the size of the memory mapping. The size should be changed
   with care, since it may create an non-sized aligned mapping. The
   <fun>PCI_set_map_enable</fun> function can be used to enable and
   disable a mapping, this enable is in addition to the standard
   PCI enable/disable. Finally the <fun>PCI_set_map_offset</fun> changes
   the target offset of the mapping. The <tt>_get_</tt> functions can
   be used to query the current state of a mapping.
   </add-fun>
*/

void
PCI_set_map_base(pci_device_t *pci, int reg, uint64 base)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return;

        if (base == pci_map->base)
                return;

        if (PCI_FLAGS_64BIT_R(pci_map->flags))
                create_map64(pci, pci_map, reg, base, base >> 32);
        else
                create_map32(pci, pci_map, reg, base);

        /* possibly remap */
        add_pci_space(pci, reg, pci_map);
}


/* <append-fun id="PCI_set_map_base"/> */
uint64
PCI_get_map_base(pci_device_t *pci, int reg)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return 0;
        return pci_map->base;
}


/* <append-fun id="PCI_set_map_base"/> */
void
PCI_set_map_size(pci_device_t *pci, int reg, uint64 size)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return;

        if (size == pci_map->size)
                return;

        pci_map->size = size;

        /* possibly remap */
        add_pci_space(pci, reg, pci_map);
}


/* <append-fun id="PCI_set_map_base"/> */
uint64
PCI_get_map_size(pci_device_t *pci, int reg)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return 0;
        return pci_map->size;
}


/* <append-fun id="PCI_set_map_base"/> */
void
PCI_set_map_enable(pci_device_t *pci, int reg, int enable)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return;

        if (enable == PCI_FLAGS_ENABLED_R(pci_map->flags))
                return;

        PCI_FLAGS_ENABLED_W(pci_map->flags, enable);

        /* possibly remap */
        add_pci_space(pci, reg, pci_map);
}


/* <append-fun id="PCI_set_map_base"/> */
int
PCI_get_map_enable(pci_device_t *pci, int reg)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return 0;
        return PCI_FLAGS_ENABLED_R(pci_map->flags);
}


/* <append-fun id="PCI_set_map_base"/> */
void
PCI_set_map_offset(pci_device_t *pci, int reg, uint64 target_offset)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return;

        if (target_offset == pci_map->target_offset)
                return;

        pci_map->target_offset = target_offset;

        /* possibly remap */
        add_pci_space(pci, reg, pci_map);
}


/* <append-fun id="PCI_set_map_base"/> */
uint64
PCI_get_map_offset(pci_device_t *pci, int reg)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return 0;
        return pci_map->target_offset;
}


/* <append-fun id="PCI_set_map_base"/> */
void
PCI_set_map_ignore_command(pci_device_t *pci, int reg, int map_ignore_command)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return;

        if (map_ignore_command
            == PCI_FLAGS_MAP_IGNORE_COMMAND_R(pci_map->flags))
                return;

        PCI_FLAGS_MAP_IGNORE_COMMAND_W(pci_map->flags, map_ignore_command);

        /* possibly remap */
        add_pci_space(pci, reg, pci_map);
}


/* <append-fun id="PCI_set_map_base"/> */
int
PCI_get_map_ignore_command(pci_device_t *pci, int reg)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return 0;
        return PCI_FLAGS_MAP_IGNORE_COMMAND_R(pci_map->flags);
}

/* <append-fun id="PCI_set_map_base"/> */
void
PCI_set_map_always_on(pci_device_t *pci, int reg, int always_on)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return;

        if (always_on == PCI_FLAGS_ALWAYS_ON_R(pci_map->flags))
                return;

        PCI_FLAGS_ALWAYS_ON_W(pci_map->flags, always_on);

        /* possibly remap */
        add_pci_space(pci, reg, pci_map);
}

/* <append-fun id="PCI_set_map_base"/> */
int
PCI_get_map_always_on(pci_device_t *pci, int reg)
{
        pci_map_info_t *pci_map = get_pci_map(pci, reg);
        if (!pci_map)
                return 0;
        return PCI_FLAGS_ALWAYS_ON_R(pci_map->flags);
}


/* will always be called with the start of a register (if possible) */
uint64
read_pci_registers(pci_device_t *pci,
                   int offset,            // start of first register
                   int start_offset,      // access offset into first register
                   int tot_size)          // patched size (to start of first reg)
{
        uint64 value = 0;
        int val_pos = 0;

        while (tot_size > 0) {
                uint32 reg_size = PCI_config_register_size(pci, offset);
                uint32 reg_mask = PCI_get_config_register_mask(pci, offset);
                uint32 val_part;

                if (reg_size == 0) {
                        int next_offset;
                        /* 
                         * unknown register following a known one, access one
                         * byte at a time to make sure we hit other known regs
                         */
                        // not yet, some devices has to 'add_config_reg' first
                        // pr("[%s] unknown reg 0x%x using size %d\n", pci->log->obj.name, offset, tot_size);
                        reg_size = tot_size;
                        for (next_offset = offset + 1; next_offset < tot_size + offset; next_offset++) {
                                if (PCI_config_register_size(pci, next_offset)) {
                                        reg_size = next_offset - offset;
                                        break;
                                }
                        }
                        reg_mask = ((uint64)1 << (reg_size * 8)) - 1;
                }

                val_part = pci->conf_read_func(&pci->log->obj, offset, reg_size);

                SIM_log_info(3, pci->log, pci->log_group,
                             "Read config register (%s): offset 0x%x, size 0x%x, value 0x%x",
                             PCI_config_register_name(pci, offset)
                             ? PCI_config_register_name(pci, offset)
                             : "unknown",
                             offset, reg_size, val_part);

                /* adjust for partial access of last register */
                val_part &= (UINT64_C(1) << (MIN(reg_size, tot_size) * 8)) - 1;
                /* allow access in middle of register using start_offset */
                value |= (val_part >> (start_offset * 8)) << (val_pos * 8);
                val_pos += (reg_size - start_offset);

                tot_size -= reg_size;
                offset += reg_size;
                start_offset = 0;
        }
        return value;
}


/* will always be called with the start of a register (if possible) */
void
write_pci_registers(pci_device_t *pci,
                    int offset,            // start of first register
                    int start_offset,      // access offset into first register
                    int tot_size,          // patched size (to start of first reg)
                    uint64 value)
{
        while (tot_size > 0) {
                uint32 reg_size = PCI_config_register_size(pci, offset);
                uint32 reg_mask = PCI_get_config_register_mask(pci, offset);
                uint32 val_part, bits;
                uint32 write_mask;

                if (reg_size == 0) {
                        int next_offset;
                        /* 
                         * unknown register following a known one, access one
                         * byte at a time to make sure we hit other known regs
                         */
                        // not yet, some devices has to 'add_config_reg' first
                        // pr("[%s] unknown reg 0x%x using size %d\n", pci->log->obj.name, offset, tot_size);
                        reg_size = tot_size;
                        for (next_offset = offset + 1; next_offset < tot_size + offset; next_offset++) {
                                if (PCI_config_register_size(pci, next_offset)) {
                                        reg_size = next_offset - offset;
                                        break;
                                }
                        }
                        reg_mask = ((uint64)1 << (reg_size * 8)) - 1;
                }

                /* allow access in middle of register using start_offset */
                bits = (reg_size - start_offset) * 8;
                write_mask = (UINT64_C(1) << bits) - 1;
                val_part = value & write_mask;
                value >>= bits;
                val_part <<= start_offset * 8;
                reg_mask &= write_mask << (start_offset * 8);

                /* apply write mask, keep old bits */
                val_part &= reg_mask;
                val_part |= PCI_read_sized_config_register(pci, offset, reg_size) & ~reg_mask;

                SIM_log_info(2, pci->log, pci->log_group,
                             "Write config register (%s): offset 0x%x, size 0x%x, value 0x%x",
                             PCI_config_register_name(pci, offset)
                             ? PCI_config_register_name(pci, offset)
                             : "unknown",
                             offset, reg_size, val_part);
                
                pci->conf_write_func(&pci->log->obj, offset, reg_size, val_part);

                offset += reg_size;
                tot_size -= reg_size;
                start_offset = 0;
        }
}


/* <add-fun id="pci device api">
   <short>access the configuration space</short>
   The <fun>PCI_configuration_access</fun> function performs an access
   to the configuration header registers. It handles overlapping accesses
   and both reads and writes. This function is typically only needed for
   PCI device that map the configuration space in the I/O and/or memory
   space mappings. The PCI device can then call this function. Accesses
   using the configuration space it handled by the generic PCI device
   itself (by calling this function).
   <doc-item name="RETURN VALUE">
   The returned value is always <tt>Sim_PE_No_Exception</tt>.
   </doc-item>
   </add-fun>
*/
exception_type_t
PCI_configuration_access(pci_device_t *pci, 
                         generic_transaction_t *mop)
{
#if defined(PCI_EXPRESS)
        int offset = mop->physical_address & 0xfff;
#else   /* !PCI_EXPRESS */
        int offset = mop->physical_address & 0xff;
#endif  /* !PCI_EXPRESS */
        int reg_size = PCI_config_register_size(pci, offset);
        int tot_size, start, start_offset = 0;

        if (reg_size) {
                start = offset;
        } else {
                /* first offset is not a known register, look for one  */
                for (start = offset - 1; start > offset - 4; start--) {
                        reg_size = PCI_config_register_size(pci, start);
                        if (reg_size + start > offset) {
                                start_offset = offset - start;
                                break; /* access register */
                        }
                }
        }

        /* 
         * if the first address covers a known register, we set
         * offset to point to it. Also adjust the total size to
         * include this register completely.
         */
        offset -= start_offset;
        tot_size = mop->size + start_offset;

        if (SIM_mem_op_is_read(mop)) {
                SIM_set_mem_op_value_le(mop,
                                        read_pci_registers(pci,
                                                           offset,
                                                           start_offset,
                                                           tot_size));
        } else {
                write_pci_registers(pci,
                                    offset,
                                    start_offset,
                                    tot_size,
                                    SIM_get_mem_op_value_le(mop));
        }
        return Sim_PE_No_Exception;
}


/* <add-fun id="pci device api">
   <short>default PCI device reset handling</short>
   A PCI device can override this default reset function with a
   function specified in the <fun>PCI_device_init</fun> call.
   The overriding function can then call this default function to
   get the default behavior as well.  All memory mappings are
   disabled, and the following registers are cleared: <tt>Command</tt>,
   <tt>Status</tt>, <tt>Cache Line Size</tt>, <tt>Latency Timer</tt>,
   <tt>BIST</tt>, <tt>Interrupt Line</tt> and all base address registers.
   </add-fun>
*/
void
PCI_default_device_reset(conf_object_t *obj)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;

        SIM_log_info(2, pci->log, pci->log_group,
                     "PCI bus reset received");

        PCI_write_config_register(pci, PCI_COMMAND, 0);
        PCI_write_config_register(pci, PCI_STATUS,
                                  PCI_read_config_register(pci,
                                                           PCI_STATUS) & 0x7ff);

        PCI_write_config_register(pci, PCI_CACHE_LINE_SIZE, 0);
        PCI_write_config_register(pci, PCI_LATENCY_TIMER, 0);
        PCI_write_config_register(pci, PCI_BIST, 0);
        PCI_write_config_register(pci, PCI_INTERRUPT_LINE, 0);

        switch (header_type) {
        case PCI_TYPE_0_HEADER:
                base_address_write(pci, PCI_BASE_ADDRESS_0, 0);
                base_address_write(pci, PCI_BASE_ADDRESS_1, 0);
                base_address_write(pci, PCI_BASE_ADDRESS_2, 0);
                base_address_write(pci, PCI_BASE_ADDRESS_3, 0);
                base_address_write(pci, PCI_BASE_ADDRESS_4, 0);
                base_address_write(pci, PCI_BASE_ADDRESS_5, 0);
                base_address_write(pci, PCI_EXPANSION_ROM_BASE, 0);
                break;
        case PCI_TYPE_1_HEADER:
                if (type1_reset)
                        type1_reset(pci);
                break;
        default:
                ASSERT(0);
        }
}


static void
pci_device_bus_reset_callback(conf_object_t *obj)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        pci->pci_bus_reset(obj);
}


/* <add-fun id="pci device api">
   <short>raise and lower a PCI interrupt</short>
   <fun>PCI_raise_interrupt</fun> raises an interrupt on the pin defined
   by the <tt>PCI_INTERRUPT_PIN</tt> configuration register. If an interrupt
   is already asserted, the call has no effect. Similarly for
   <fun>PCI_lower_interrupt</fun> that lowers the interrupt level if it already
   is raised. The <fun>PCI_raise_interrupt_pin</fun> and <fun>PCI_lower_interrupt_pin</fun>
   functions take an extra argument that is the interrupt pin. These two functions
   should not be used by most PCI devices, but bridges may need them.
   <doc-item name="NOTE">
   A raise triggers an interrupt, and refers to the logical signal. It does
   not reflect the actual physical signal level on the PCI bus where
   interrupt lines are active low.
   </doc-item>
   </add-fun>
*/
void
PCI_raise_interrupt(pci_device_t *pci)
{
        int pin = PCI_read_config_register(pci, PCI_INTERRUPT_PIN) - 1;

        ASSERT(pin >= 0 && pin < 4);

        if (!pci->interrupt_pin[pin]) {
                if (pci->pci_bus) {
                        pci->pci_bus_interface.raise_interrupt(
                                pci->pci_bus, &pci->log->obj, pin);
                }
                pci->interrupt_pin[pin] = 1;
        }
}


/* <append-fun id="PCI_raise_interrupt"/> */
void
PCI_lower_interrupt(pci_device_t *pci)
{
        int pin = PCI_read_config_register(pci, PCI_INTERRUPT_PIN) - 1;

        ASSERT(pin >= 0 && pin < 4);

        if (pci->interrupt_pin[pin]) {
                if (pci->pci_bus) {
                        pci->pci_bus_interface.lower_interrupt(
                                pci->pci_bus, &pci->log->obj, pin);
                }
                pci->interrupt_pin[pin] = 0;
        }
}

/* <append-fun id="PCI_raise_interrupt"/> */
void
PCI_raise_interrupt_pin(pci_device_t *pci, int pin)
{
        ASSERT(pin >= 0 && pin < 4);

        if (!pci->interrupt_pin[pin]) {
                if (pci->pci_bus) {
                        pci->pci_bus_interface.raise_interrupt(
                                pci->pci_bus, &pci->log->obj, pin);
                }
                pci->interrupt_pin[pin] = 1;
        }
}


/* <append-fun id="PCI_raise_interrupt"/> */
void
PCI_lower_interrupt_pin(pci_device_t *pci, int pin)
{
        ASSERT(pin >= 0 && pin < 4);

        if (pci->interrupt_pin[pin]) {
                if (pci->pci_bus) {
                        pci->pci_bus_interface.lower_interrupt(
                                pci->pci_bus, &pci->log->obj, pin);
                }
                pci->interrupt_pin[pin] = 0;
        }
}

/* <add-fun id="pci device api">
   <short>send a message to root complex</short>

   Send a PCI Express message to the root complex, of a given
   <param>type</param> with a possibly empty <param>payload</param>. This
   function is only available to PCI Express devices.

   The <type>pcie_message_type_t</type> has the following definition:
   <insert id="pcie_message_type_t def"/>

  </add-fun>
*/
#if defined(DOC) || defined(PCI_EXPRESS)
void
PCIE_send_message(pci_device_t *pci, pcie_message_type_t type, 
                  byte_string_t payload)
{
        if (pci->pci_bus) {
                pci->pci_bus_interface.send_message(pci->pci_bus,
                                                    &pci->log->obj,
                                                    type, payload);
        }
}
#endif

static exception_type_t
pci_device_operation_callback(conf_object_t *obj, 
                              generic_transaction_t *trans, 
                              map_info_t info)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;

        if (info.function == DEVICE_CONF_FUNC)
                return PCI_configuration_access(pci, trans);
        else
                return pci->pci_operation(obj, trans, info);
}


/* <add-fun id="pci device api">
   <short>read/write raw data from memory space</short>
   <fun>PCI_data_from_memory</fun> reads data from a memory-space
   specified by <arg>space</arg>, and places it in a buffer
   pointed to by <arg>buffer</arg>. No endian conversion is
   performed. <fun>PCI_data_to_memory</fun> writes data to the
   memory space.
   <doc-item name="RETURN VALUE">
   The pseudo exception from the memory-space is returned.
   </doc-item>
   </add-fun>
*/
exception_type_t
PCI_data_from_memory(pci_device_t *pci, addr_space_t space,
                     uint8 *buffer, uint64 address, uint64 size)
{
	pci_memory_transaction_t trans;
	map_info_t info;
        exception_type_t ex;
        uint16 cmd = PCI_read_config_register(pci, PCI_COMMAND);

        if (!(cmd & (1 << 2))) {
                SIM_log_info(2, pci->log, pci->log_group,
                             "Trying to access PCI bus, but not a master.");
                /* only warn now, check all devices first */
                // return Sim_PE_...
        }

	memset(&trans, 0, sizeof(trans));

	trans.s.physical_address = address;
        SIM_set_mem_op_type(&trans.s, Sim_Trans_Load);
	trans.original_size = size;
	trans.s.size = size;
	trans.s.block_STC = 1;
	trans.s.may_stall = pci->may_stall;

        trans.s.ini_type = Sim_Initiator_PCI_Device;
        trans.s.ini_ptr = &pci->log->obj;
        trans.s.real_address = (void *)buffer;

        if (pci->pci_bus && pci->bus_address == -1) {
                pci->bus_address =
                        pci->pci_bus_interface.get_bus_address(pci->pci_bus, 
                                                               &pci->log->obj);
        }
        trans.bus_address = pci->bus_address;

	memset(&info, 0, sizeof(map_info_t));
	info.function = space;

        if (pci->pci_bus) {
                ex = pci->pci_bus_mem_interface.operation(pci->pci_bus,
                                                          &trans.s, info);
        } else {
                ex = Sim_PE_IO_Error;
        }
        
        if (ex == Sim_PE_IO_Not_Taken) {
                /* master abort */
                PCI_write_config_register(pci, PCI_STATUS,
                                          PCI_read_config_register(pci, PCI_STATUS)
                                          | (1 << 13));
        } else if (ex == Sim_PE_IO_Error) {
                /* target abort */
                PCI_write_config_register(pci, PCI_STATUS,
                                          PCI_read_config_register(pci, PCI_STATUS)
                                          | (1 << 12));
        } else if (((ex == Sim_PE_Stall_Cpu) && !pci->may_stall)
                   || (ex != Sim_PE_No_Exception)) {
                SIM_log_error(pci->log, pci->log_group,
                              "Unknown exception received on PCI bus: 0x%x", ex);
        }
        return ex;
}


/* <append-fun id="PCI_data_from_memory"/> */
exception_type_t
PCI_data_to_memory(pci_device_t *pci, addr_space_t space,
                   uint8 *buffer, uint64 address, uint64 size)
{
	pci_memory_transaction_t trans;
	map_info_t info;
        exception_type_t ex;
        uint16 cmd = PCI_read_config_register(pci, PCI_COMMAND);

        if (!(cmd & (1 << 2))) {
                SIM_log_info(2, pci->log, pci->log_group,
                             "Trying to access PCI bus, but not a master.");
                /* only warn now, check all devices first */
                // return Sim_PE_...
        }

	memset(&trans, 0, sizeof(trans));

	trans.s.physical_address = address;
        SIM_set_mem_op_type(&trans.s, Sim_Trans_Store);
	trans.original_size = size;
	trans.s.size = size;
	trans.s.block_STC = 1;
	trans.s.may_stall = pci->may_stall;
        
        trans.s.ini_type = Sim_Initiator_PCI_Device;
        trans.s.ini_ptr = &pci->log->obj;
        trans.s.real_address = (void *)buffer;

        if (pci->pci_bus && pci->bus_address == -1) {
                pci->bus_address =
                        pci->pci_bus_interface.get_bus_address(pci->pci_bus, 
                                                               &pci->log->obj);
        }
        trans.bus_address = pci->bus_address;

	memset(&info, 0, sizeof(map_info_t));
	info.function = space;

        if (pci->pci_bus) {
                ex = pci->pci_bus_mem_interface.operation(pci->pci_bus,
                                                          &trans.s, info);
        } else {
                ex = Sim_PE_IO_Error;
        }

        if (ex == Sim_PE_IO_Not_Taken) {
                /* master abort */
                PCI_write_config_register(pci, PCI_STATUS,
                                          PCI_read_config_register(pci, PCI_STATUS)
                                          | (1 << 13));
        } else if (ex == Sim_PE_IO_Error) {
                /* target abort */
                PCI_write_config_register(pci, PCI_STATUS,
                                          PCI_read_config_register(pci, PCI_STATUS)
                                          | (1 << 12));
        } else if (((ex == Sim_PE_Stall_Cpu) && !pci->may_stall)
                   || (ex != Sim_PE_No_Exception)) {
                SIM_log_error(pci->log, pci->log_group,
                              "Unknown exception received on PCI bus: 0x%x", ex);
        }
        return ex;
}


/* <add-fun id="pci device api">
   <short>read/write value from memory space</short>
   <fun>PCI_value_from_memory</fun> reads data from a memory-space
   specified by <arg>space</arg>, and returns it in the endian
   byte-order of the host, i.e. as a value. <fun>PCI_value_to_memory</fun>
   writes <arg>value</arg> to the memory space.
   <doc-item name="RETURN VALUE">
   The pseudo exception from the memory-space is returned.
   </doc-item>
   </add-fun>
*/
uint64
PCI_value_from_memory(pci_device_t *pci, addr_space_t space,
                      exception_type_t *ex,
                      uint64 address, uint32 size)
{
        uint64 value = 0;
        exception_type_t ret_ex;

        ASSERT(size <= 8);

        ret_ex = PCI_data_from_memory(pci, space, (uint8 *)&value, address, size);

        if (ex)
                *ex = ret_ex;
        return CONVERT_LE64(value);
}


/* <append-fun id="PCI_value_from_memory"/> */
exception_type_t
PCI_value_to_memory(pci_device_t *pci, addr_space_t space,
                      uint64 value,
                      uint64 address, uint32 size)
{
        uint64 val = CONVERT_LE64(value);

        ASSERT(size <= 8);

        return PCI_data_to_memory(pci, space, (uint8 *)&val, address, size);
}


/* <add-fun id="pci device api">
   <short>assert system error</short>
   Triggers a system error on the PCI bus, i.e asserts the SERR# line.
   System Errors are used for asynchronous signalling of unrecoverable
   errors, and are usually handled by the host-to-PCI bridge.
   </add-fun>
*/
void
PCI_system_error(pci_device_t *pci)
{
        /* only if SERR# enable in the command register */
        if (PCI_read_config_register(pci, PCI_COMMAND) & (1 << 8)) {
                if (pci->pci_bus)
                        pci->pci_bus_interface.system_error(pci->pci_bus);

                /* set 'signalling system-error' */
                PCI_write_config_register(pci, PCI_STATUS,
                                          PCI_read_config_register(pci, PCI_STATUS)
                                          | (1 << 14));
        }
}


/* <add-fun id="pci device api">
   <short>get the bus address of a device</short>
   Returns the PCI bus address for the device.
   <doc-item name="RETURN VALUE">
   The PCI bus address, in PCI Type 1 address format. I.e.
   <tt>bus &lt;&lt; 16 | device &lt;&lt; 11 | function &lt;&lt; 8</tt>.
   On error, if the device isn't found on the bus, -1 is returned.
   </doc-item>
   </add-fun>
*/
int
PCI_get_bus_address(pci_device_t *pci)
{
        return pci->pci_bus
                ? pci->pci_bus_interface.get_bus_address(pci->pci_bus,
                                                         &pci->log->obj)
                : 0;
}


static set_error_t
pci_device_set_pci_bus(void *arg, conf_object_t *obj, attr_value_t *val,
                       attr_value_t *idx)
{
        conf_object_t *bus_obj;
	pci_bus_interface_t *bus_int;
	io_memory_interface_t *mem_int;
#if defined(PCI_EXPRESS)
        pci_express_interface_t *pcie_int;
#endif   /* PCI_EXPRESS */
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;

        if (val->kind == Sim_Val_Nil) {
                pci->pci_bus = NULL;
                return Sim_Set_Ok;
        }
        
	bus_obj = val->u.object;        
	bus_int = (pci_bus_interface_t *)SIM_get_interface(bus_obj,
                                                           PCI_BUS_INTERFACE);
	if(!bus_int)
		return Sim_Set_Interface_Not_Found;
	
	mem_int = (io_memory_interface_t *)
                SIM_get_interface(bus_obj, IO_MEMORY_INTERFACE);
	if (!mem_int)
		return Sim_Set_Interface_Not_Found;

#if defined(PCI_EXPRESS)
        pcie_int = (pci_express_interface_t *)
                SIM_get_interface(bus_obj, PCI_EXPRESS_INTERFACE);
        if (!pcie_int)
                return Sim_Set_Interface_Not_Found;
#endif   /* PCI_EXPRESS */

	pci->pci_bus = bus_obj;
	pci->pci_bus_interface = *bus_int;
	pci->pci_bus_mem_interface = *mem_int;
#if defined(PCI_EXPRESS)
        pci->pcie_bus_interface = *pcie_int;
#endif   /* PCI_EXPRESS */

        /* update info when hotplugging */
        if (obj->configured && get_bridge_bus_info && header_type == PCI_TYPE_1_HEADER)
                get_bridge_bus_info(pci);

	return Sim_Set_Ok;
}


static attr_value_t
pci_device_get_pci_bus(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        return SIM_make_attr_object(pci->pci_bus);
}


static set_error_t
pci_device_set_interrupt_pin(void *dummy, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        int i;
        for (i = 0; i < 4; i++)
                pci->interrupt_pin[i] = val->u.list.vector[i].u.integer ? 1 : 0;
        return Sim_Set_Ok;
}


static attr_value_t
pci_device_get_interrupt_pin(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        return SIM_make_attr_list(4,
                                  SIM_make_attr_integer(pci->interrupt_pin[0]),
                                  SIM_make_attr_integer(pci->interrupt_pin[1]),
                                  SIM_make_attr_integer(pci->interrupt_pin[2]),
                                  SIM_make_attr_integer(pci->interrupt_pin[3]));
}


static set_error_t
pci_device_set_config_registers(void *dummy, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
	uint32 *config_regs = (uint32 *)pci->config_registers;

        if (idx->kind == Sim_Val_Nil) {
                int i;

                for(i = 0; i < CONFIGURATION_SPACE_REGS ; i++) 
                        config_regs[i] = CONVERT_LE32(val->u.list.vector[i].u.integer);
                
        } else if ((idx->kind == Sim_Val_Integer)
                   && (idx->u.integer >= 0)
                   && (idx->u.integer < CONFIGURATION_SPACE_REGS)) {
                
                config_regs[idx->u.integer] = CONVERT_LE32(val->u.integer);
        } else {
                return Sim_Set_Illegal_Value;
        }
        
        return Sim_Set_Ok;
}


static attr_value_t
pci_device_get_config_registers(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
	uint32 *config_regs = (uint32 *)pci->config_registers;
        
        if (idx->kind == Sim_Val_Nil) {
                attr_value_t ret = SIM_alloc_attr_list(CONFIGURATION_SPACE_REGS);
                int i;

                for(i = 0; i < CONFIGURATION_SPACE_REGS; i++)
                        ret.u.list.vector[i] = SIM_make_attr_integer(CONVERT_LE32(config_regs[i]));
                return ret;
                
        } else if ((idx->kind == Sim_Val_Integer)
                   && (idx->u.integer >= 0)
                   && (idx->u.integer < CONFIGURATION_SPACE_REGS)) {

                return SIM_make_attr_integer(CONVERT_LE32(config_regs[idx->u.integer]));
        } else {
                return SIM_make_attr_invalid();
        }
}


static set_error_t
pci_device_set_write_masks(void *dummy, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
        int i;

        for (i = 0; i < val->u.list.size; i++) {
                int offset = val->u.list.vector[i].u.list.vector[0].u.integer;
                int mask   = val->u.list.vector[i].u.list.vector[1].u.integer;

                if (offset < STANDARD_CONFIGURATION_SIZE) {
                        if (pci->config_reg_info[header_type][offset].size
                            == 0)
                                return Sim_Set_Illegal_Value;
                        pci->config_reg_info[header_type][offset].mask = mask;
                } else {
                        config_reg_info_t *info =
                                ht_lookup_int(pci->user_reg_table, offset);
                        if (!info)
                                return Sim_Set_Illegal_Value;
                        info->mask = mask;
                }
        }
        return Sim_Set_Ok;
}


static int
get_write_masks(ht_table_t *ht, uint64 reg, void *_info, void *user)
{
        config_reg_info_t *info = _info;
        attr_value_t *ret = user;
        int size = ret->u.list.size;

        ret->u.list.vector =
                MM_REALLOC(ret->u.list.vector, size + 1, attr_value_t);
        ret->u.list.vector[size] =
                SIM_make_attr_list(2,
                                   SIM_make_attr_integer(info->offset),
                                   SIM_make_attr_integer(info->mask));
        ret->u.list.size = size + 1;
        return 1;
}


static attr_value_t
pci_device_get_write_masks(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
        attr_value_t ret = SIM_alloc_attr_list(0);
        int i;

        for (i = 0; i < STANDARD_CONFIGURATION_SIZE; i++) {

                if (pci->config_reg_info[header_type][i].size == 0)
                        continue;

                ret.u.list.vector = MM_REALLOC(ret.u.list.vector,
                                               ret.u.list.size + 1, attr_value_t);
                ret.u.list.vector[ret.u.list.size] =
                        SIM_make_attr_list(2,
                                           SIM_make_attr_integer(pci->config_reg_info[header_type][i].offset),
                                           SIM_make_attr_integer(pci->config_reg_info[header_type][i].mask));
                ret.u.list.size += 1;
        }

        ht_for_each_entry(pci->user_reg_table, get_write_masks, &ret);
        return ret;

}


static int
get_register_info(ht_table_t *ht, uint64 reg, void *_info, void *user)
{
        config_reg_info_t *info = _info;
        attr_value_t *ret = user;
        int size = ret->u.list.size;

        ret->u.list.vector =
                MM_REALLOC(ret->u.list.vector, size + 1, attr_value_t);
        ret->u.list.vector[size] =
                SIM_make_attr_list(4,
                                   SIM_make_attr_integer(info->offset),
                                   SIM_make_attr_string(info->name),
                                   SIM_make_attr_integer(info->size),
                                   SIM_make_attr_integer(info->mask));
        ret->u.list.size = size + 1;
        return 1;
}

static attr_value_t
pci_device_get_register_info(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
        attr_value_t ret = SIM_alloc_attr_list(0);
        int i;

        for (i = 0; i < STANDARD_CONFIGURATION_SIZE; i++) {

                if (pci->config_reg_info[header_type][i].size == 0)
                        continue;

                ret.u.list.vector = MM_REALLOC(ret.u.list.vector,
                                               ret.u.list.size + 1, attr_value_t);
                ret.u.list.vector[ret.u.list.size] =
                        SIM_make_attr_list(4,
                                           SIM_make_attr_integer(pci->config_reg_info[header_type][i].offset),
                                           SIM_make_attr_string(pci->config_reg_info[header_type][i].name),
                                           SIM_make_attr_integer(pci->config_reg_info[header_type][i].size),
                                           SIM_make_attr_integer(pci->config_reg_info[header_type][i].mask));
                ret.u.list.size += 1;
        }

        ht_for_each_entry(pci->user_reg_table, get_register_info, &ret);
        return ret;
}


static int
get_mappings2(ht_table_t *ht, uint64 reg, void *_map, void *user)
{
        pci_map_info_t *map_info = (pci_map_info_t *)_map;
        attr_value_t *ret = (attr_value_t *)user;
        int size = ret->u.list.size;
        int space_type;

        space_type = map_info->space_type == Sim_Addr_Space_Memory ? 0 : 1;

        ret->u.list.vector = MM_REALLOC(ret->u.list.vector, size + 1, attr_value_t);
        ret->u.list.vector[size] = SIM_make_attr_list(11,
                                                      SIM_make_attr_integer(reg),
                                                      SIM_make_attr_integer(map_info->base),
                                                      SIM_make_attr_integer(map_info->size),
                                                      SIM_make_attr_integer(space_type),
                                                      SIM_make_attr_integer(map_info->function),
                                                      SIM_make_attr_integer(map_info->flags),
                                                      SIM_make_attr_integer(map_info->priority),
                                                      SIM_make_attr_integer(map_info->target_offset),
                                                      SIM_make_attr_object(map_info->target),
                                                      SIM_make_attr_integer(map_info->align_size),
                                                      SIM_make_attr_integer(map_info->reverse_endian));

        ret->u.list.size = size + 1;
        return 1;
}


static attr_value_t
get_mappings(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
        attr_value_t ret;
	pci_device_t *pci = (pci_device_t *)obj->object_data;

        ret = SIM_alloc_attr_list(0);
        ht_for_each_entry(pci->map_table, get_mappings2, &ret);
        return ret;
}


static set_error_t
set_mappings(void *dummy, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        pci_map_info_t *pci_map;
        int i, reg, len, space_type;
        
        for (i = 0; i < val->u.list.size; i++) {

                len = val->u.list.vector[i].u.list.size;
                
                pci_map = MM_ZALLOC(1, pci_map_info_t);
                reg =                 val->u.list.vector[i].u.list.vector[0].u.integer;
                pci_map->base =       val->u.list.vector[i].u.list.vector[1].u.integer;
                pci_map->size =       val->u.list.vector[i].u.list.vector[2].u.integer;
                space_type =          val->u.list.vector[i].u.list.vector[3].u.integer;
                pci_map->function =   val->u.list.vector[i].u.list.vector[4].u.integer;

                if (space_type == 0)
                        pci_map->space_type = Sim_Addr_Space_Memory;
                else
                        pci_map->space_type = Sim_Addr_Space_IO;

                if (len > 5)
                        pci_map->flags = val->u.list.vector[i].u.list.vector[5].u.integer;
                else
                        pci_map->flags = 1; /* backward compatibility */
                if (len > 6)
                        pci_map->priority = val->u.list.vector[i].u.list.vector[6].u.integer;
                if (len > 7)
                        pci_map->target_offset = val->u.list.vector[i].u.list.vector[7].u.integer;
                if (len > 8 && val->u.list.vector[i].u.list.vector[8].kind != Sim_Val_Nil)
                        pci_map->target = val->u.list.vector[i].u.list.vector[8].u.object;
                if (len > 9)
                        pci_map->align_size = val->u.list.vector[i].u.list.vector[9].u.integer;
                if (len > 10)
                        pci_map->reverse_endian = val->u.list.vector[i].u.list.vector[10].u.integer;

                ht_update_int(pci->map_table, reg, pci_map);
        }
        return Sim_Set_Ok;
}


static attr_value_t
get_rom(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;

        if (pci->rom) {
                return SIM_make_attr_list(3,
                                          SIM_make_attr_object(pci->rom),
                                          SIM_make_attr_integer(pci->rom_size),
                                          SIM_make_attr_integer(pci->rom_func));
        } else {
                return SIM_make_attr_nil();
        }
}


static set_error_t
set_rom(void *dummy, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
	pci_device_t *pci = (pci_device_t *)obj->object_data;
        int header_type = pci->config_registers[PCI_HEADER_TYPE] & 0x7f;
        int reg;

        if (!SIM_get_interface(val->u.list.vector[0].u.object, ROM_INTERFACE)) {
                SIM_frontend_exception(SimExc_General, "Object does not implement the ROM interface\n");
                return Sim_Set_Interface_Not_Found;
        }
        if (val->u.list.vector[1].u.integer <= 0) {
                SIM_frontend_exception(SimExc_General, "Illegal size of ROM mapping\n");
                return Sim_Set_Illegal_Value;
        }
        pci->rom = val->u.list.vector[0].u.object;
        pci->rom_size = val->u.list.vector[1].u.integer;
        pci->rom_func = val->u.list.vector[2].u.integer;

        if (header_type == PCI_TYPE_0_HEADER)
                reg = PCI_EXPANSION_ROM_BASE;
        else if (header_type == PCI_TYPE_1_HEADER)
                reg = PCI_BRIDGE_EXPANSION_ROM_BASE;
        else
                ASSERT(0);

        PCI_handle_mapping32(pci,
                             reg, Sim_Addr_Space_Memory,
                             pci->rom_size, pci->rom_func, 0,
                             0,
                             pci->rom, 0, 0);
        return Sim_Set_Ok;
}


#undef  STR
#define STRX(x) #x
#define STR(x) STRX(x)


/* <add-fun id="pci device api">
   <short>register generic PCI device attributes</short>
   Registers the generic PCI device attributes, and performs some
   early initialization. The <fun>PCI_register_device_attributes</fun>
   function should be called as early as possible, typically from the
   module's <fun>init_local</fun> function. The first argument is the
   configuration class for the PCI device. The following arguments are
   optional functions with callbacks for events on the PCI bus. They
   should only be supplied by devices that respond to Interrupt
   Acknowledge Cycles, listens to Special Cycle data, listens to the
   system error line (SERR#), or receives peer-to-peer interrupts.
   </add-fun>
*/
void
PCI_register_device_attributes(
        conf_class_t *pci_class,
        int (*interrupt_ack)(conf_object_t *obj),
        void (*special_cycle)(conf_object_t *obj, uint32 value),
        void (*system_error)(conf_object_t *obj),
        void (*interrupt_raised)(conf_object_t *obj, int pin),
        void (*interrupt_lowered)(conf_object_t *obj, int pin))
{
	pci_device_interface_t *interface1;
	io_memory_interface_t *interface2;
#if defined(PCI_EXPRESS)
        pci_express_interface_t *pcieif;
#endif   /* PCI_EXPRESS */

	interface1 = MM_ZALLOC(1, pci_device_interface_t);
	interface1->interrupt_acknowledge = interrupt_ack;
        interface1->special_cycle = special_cycle;
	interface1->system_error = system_error;
	interface1->interrupt_raised = interrupt_raised;
	interface1->interrupt_lowered = interrupt_lowered;
	interface1->bus_reset = pci_device_bus_reset_callback;
	SIM_register_interface(pci_class, PCI_DEVICE_INTERFACE, interface1);

#if defined(PCI_EXPRESS)
        pcieif = MM_ZALLOC(1, pci_express_interface_t);
        SIM_register_interface(pci_class, PCI_EXPRESS_INTERFACE, pcieif);
#endif   /* PCI_EXPRESS */
        
	interface2 = MM_ZALLOC(1, io_memory_interface_t);
        interface2->operation = pci_device_operation_callback;
	SIM_register_interface(pci_class, IO_MEMORY_INTERFACE, interface2);
        
	SIM_register_typed_attribute(
                pci_class, "pci_bus",
                pci_device_get_pci_bus, NULL,
                pci_device_set_pci_bus, NULL,
                Sim_Attr_Optional,
                "o|n", NULL,
                "The PCI bus this device is connected to, "
                "implementing the <tt>pci-bus</tt> interface.");

	SIM_register_typed_attribute(pci_class, "interrupt_pin",
                                     pci_device_get_interrupt_pin, NULL,
                                     pci_device_set_interrupt_pin, NULL,
                                     Sim_Attr_Optional,
                                     "[iiii]", NULL,
                                     "State of the interrupt pin.");

	SIM_register_typed_attribute(pci_class, "config-registers",
                                     pci_device_get_config_registers, NULL,
                                     pci_device_set_config_registers, NULL,
                                     (attr_attr_t)(Sim_Attr_Optional | Sim_Attr_Integer_Indexed),
                                     "[i{" STR(CONFIGURATION_SPACE_REGS) "}]", "i",
                                     "The 64 PCI configuration registers, each "
                                     "32 bits in size.");

	SIM_register_typed_attribute(pci_class, "write_masks",
                                     pci_device_get_write_masks, NULL,
                                     pci_device_set_write_masks, NULL,
                                     Sim_Attr_Optional,
                                     "[[ii]*]", NULL,
                                     "Write masks for all registered configuration "
                                     "registers. The format for each entry is "
                                     "(offset, mask).");
        
	SIM_register_typed_attribute(pci_class, "mappings",
                                     get_mappings, NULL,
                                     set_mappings, NULL,
                                     Sim_Attr_Optional,
                                     "[[i{5:8}]|[iiiiiiiio|nii]*]", NULL,
                                     "List of all current PCI IO and memory mappings.");

	SIM_register_typed_attribute(pci_class, "expansion-rom",
                                     get_rom, NULL,
                                     set_rom, NULL,
                                     Sim_Attr_Optional,
                                     "[oii]", NULL,
                                     "ROM object, map size, and map function number for "
                                     "the Expansion ROM.");

	SIM_register_typed_attribute(pci_class, "config_register_info",
                                     pci_device_get_register_info, NULL,
                                     0, NULL,
                                     Sim_Attr_Pseudo,
                                     "[[isii]*]", NULL,
                                     "Register info for all registered configuration "
                                     "registers. The format for each entry is "
                                     "(offset, name, size, write-mask).");
}
