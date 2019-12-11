/*
  pci-bridge.c - Base class for generic PCI-to-PCI bridge

  Copyright 2001-2007 Virtutech AB
  
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
#include <stdarg.h>
#include <string.h>

#include <simics/api.h>

#include <simics/alloc.h>
#include <simics/utils.h>

#include <simics/devs/pci.h>

#define PCI_DEVICE_PRIVATE
#include "../pci-device/pci-device.h"

#define DOWNSTREAM_CONF 0
#define DOWNSTREAM_IO   1
#define DOWNSTREAM_MEM  2
#define DOWNSTREAM_PREF 3

#define UPSTREAM_IO_1    4
#define UPSTREAM_IO_2    5

#define UPSTREAM_MEM_1   6
#define UPSTREAM_MEM_2   7
#define UPSTREAM_MEM_3   8

#define DOWNSTREAM_MEM_VGA  9
#define DOWNSTREAM_IO_VGA   10

static void
get_bus_info(pci_device_t *pci)
{
        attr_value_t scval, sival, smval, pcval, pival, pmval;

        /* lookup config, io and memory spaces for our pci busses */
        if (pci->pci_bus) {
                pcval = SIM_get_attribute(pci->pci_bus, "conf_space");
                pmval = SIM_get_attribute(pci->pci_bus, "memory_space");
                pival = SIM_get_attribute(pci->pci_bus, "io_space");
                if ((pcval.kind != Sim_Val_Object)
                    || (pmval.kind != Sim_Val_Object)
                    || (pival.kind != Sim_Val_Object)) {
                        SIM_frontend_exception(
                                SimExc_General,
                                "Illegal primary bus in pci-bridge device");
                        return;
                }
        }

        scval = SIM_get_attribute(pci->secondary_bus, "conf_space");
        smval = SIM_get_attribute(pci->secondary_bus, "memory_space");
        sival = SIM_get_attribute(pci->secondary_bus, "io_space");
        if ((scval.kind != Sim_Val_Object)
            || (smval.kind != Sim_Val_Object)
            || (sival.kind != Sim_Val_Object)) {
                SIM_frontend_exception(
                        SimExc_General,
                        "Illegal secondary bus set in pci-bridge device");
                return;
        }

        if (pci->pci_bus) {
                pci->pci_bus_cfg_space = pcval.u.object;
                pci->pci_bus_mem_space = pmval.u.object;
                pci->pci_bus_io_space  = pival.u.object;
        }
        pci->secondary_bus_cfg_space = scval.u.object;
        pci->secondary_bus_mem_space = smval.u.object;
        pci->secondary_bus_io_space  = sival.u.object;
}

static void
configuration_loaded_hap(void *_obj)
{
        pci_device_t *pci = (pci_device_t *)_obj;

        SIM_hap_delete_callback("Core_Configuration_Loaded",
                                (obj_hap_func_t)configuration_loaded_hap, pci);
        get_bus_info(pci);
}

static void
remap_secondary_config(pci_device_t *pci)
{
        map_info_t map;
        int sec, sub;

        if (pci->pci_bus) {
                pci->pci_bus_interface.remove_map(
                        pci->pci_bus, &pci->log->obj,
                        Sim_Addr_Space_Conf, DOWNSTREAM_CONF);
        }

        sec = PCI_read_config_register(pci, PCI_SECONDARY_BUS_NUMBER);
        sub = PCI_read_config_register(pci, PCI_SUBORDINATE_BUS_NUMBER);

        if (sub < sec)
                return;

        /* tell secondary bus about new number */
        pci->secondary_bus_interface.set_bus_number(pci->secondary_bus, sec);

        memset(&map, 0, sizeof(map));
#if defined(PCI_EXPRESS)
        map.base = sec << 20;
        map.start = sec << 20;
        map.length = (1 << 20) * (sub - sec + 1);
#else   /* !PCI_EXPRESS */
	map.base = sec << 16;
	map.start = sec << 16;
        map.length = (1 << 16) * (sub - sec + 1);
#endif  /* !PCI_EXPRESS */
        map.function = DOWNSTREAM_CONF;

        if (pci->pci_bus) {
                pci->pci_bus_interface.add_map(
                        pci->pci_bus, &pci->log->obj,
                        Sim_Addr_Space_Conf,
                        pci->secondary_bus_cfg_space, map);
        }
}


static void
map_downstream(pci_device_t *pci, addr_space_t space, uint64 base, uint64 length, int function)
{
        conf_object_t *tgt;
        map_info_t info;

        memset(&info, 0, sizeof(map_info_t));
        info.base = base;
        info.start = base;
        info.length = length;
        info.function = function;
        switch (function) {
        case DOWNSTREAM_IO:
                info.priority = pci->io_down_priority;
                info.align_size = pci->io_down_align_size;
                info.reverse_endian = pci->io_down_endian;
                break;
        case DOWNSTREAM_MEM:
                info.priority = pci->mem_down_priority;
                info.align_size = pci->mem_down_align_size;
                info.reverse_endian = pci->mem_down_endian;
                break;
        case DOWNSTREAM_PREF:
                info.priority = pci->pref_down_priority;
                info.align_size = pci->pref_down_align_size;
                info.reverse_endian = pci->pref_down_endian;
                break;
        case DOWNSTREAM_IO_VGA:
                info.priority = pci->io_down_priority;
                info.align_size = pci->io_down_align_size;
                info.reverse_endian = pci->io_down_endian;
                break;
        case DOWNSTREAM_MEM_VGA:
                info.priority = pci->mem_down_priority;
                info.align_size = pci->mem_down_align_size;
                info.reverse_endian = pci->mem_down_endian;
                break;
        default:
                ASSERT(0);
        }

        if (space == Sim_Addr_Space_IO)
                tgt = pci->secondary_bus_io_space;
        else
                tgt = pci->secondary_bus_mem_space;

        if (pci->pci_bus) {
                pci->pci_bus_interface.add_map(pci->pci_bus, &pci->log->obj,
                                               space, tgt, info);
        }

        SIM_log_info(2, pci->log, pci->log_group,
                     "New downstream %s space mapping (function %d): base = 0x%x, length = 0x%x",
                     space == Sim_Addr_Space_IO ? "I/O" : "memory",                     
                     info.function, (uint32)info.start, (uint32)info.length);
}


static void
map_upstream(pci_device_t *pci, addr_space_t space, uint64 base, uint64 length, int function)
{
        conf_object_t *tgt;
        map_info_t info;

        memset(&info, 0, sizeof(map_info_t));
        info.base = base;
        info.start = base;
        info.length = length;
        info.function = function;

        switch (function) {
        case UPSTREAM_IO_1:
        case UPSTREAM_IO_2:
                info.priority = pci->io_up_priority;
                info.align_size = pci->io_up_align_size;
                info.reverse_endian = pci->io_up_endian;
                break;
        case UPSTREAM_MEM_1:
        case UPSTREAM_MEM_2:
        case UPSTREAM_MEM_3:
                info.priority = pci->mem_up_priority;
                info.align_size = pci->mem_up_align_size;
                info.reverse_endian = pci->mem_up_endian;
                break;
        default:
                ASSERT(0);
        }

        if (space == Sim_Addr_Space_IO)
                tgt = pci->pci_bus_io_space;
        else
                tgt = pci->pci_bus_mem_space;

        pci->secondary_bus_interface.add_map(pci->secondary_bus, &pci->log->obj,
                                             space, tgt, info);

        SIM_log_info(2, pci->log, pci->log_group,
                     "New upstream %s space mapping (function %d): base = 0x%llx, length = 0x%llx",
                     space == Sim_Addr_Space_IO ? "I/O" : "memory",
                     function, base, length);
}


static void
remap_io(pci_device_t *pci)
{
        uint32 base, limit;
        uint64 highest = pci->forward_io32 ? 0xffffffff : 0xffff;
        int upstream = 1;

        /* remove previous mappings */
        if (pci->pci_bus) {
                pci->pci_bus_interface.remove_map(pci->pci_bus, &pci->log->obj,
                                                  Sim_Addr_Space_IO, DOWNSTREAM_IO);
                pci->pci_bus_interface.remove_map(pci->pci_bus, &pci->log->obj,
                                                  Sim_Addr_Space_IO, DOWNSTREAM_IO_VGA);
        }
        pci->secondary_bus_interface.remove_map(pci->secondary_bus, &pci->log->obj,
                                                Sim_Addr_Space_IO, UPSTREAM_IO_1);
        pci->secondary_bus_interface.remove_map(pci->secondary_bus, &pci->log->obj,
                                                Sim_Addr_Space_IO, UPSTREAM_IO_2);

        /* check if I/O mappings are enabled */
        if (!(PCI_read_config_register(pci, PCI_COMMAND) & 1))
                return;

        base  = (PCI_read_config_register(pci, PCI_IO_BASE) & ~0xf) << 8;
        limit = (PCI_read_config_register(pci, PCI_IO_LIMIT) << 8) | 0xfff;

        if (pci->forward_io32) {
                base  |= PCI_read_config_register(pci, PCI_IO_BASE_UPPER_16) << 16;
                limit |= PCI_read_config_register(pci, PCI_IO_LIMIT_UPPER_16) << 16;
        }

        /* only upstream if master enable set */
        if (!(PCI_read_config_register(pci, PCI_COMMAND) & 4))
                upstream = 0;

        if (limit < base) {
                /* no downstream forwarding */

                if (!upstream)
                        return;

                map_upstream(pci, Sim_Addr_Space_IO,
                             0, highest + 1,
                             UPSTREAM_IO_1);

        } else {
                if ((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) >> 2) & 1) {
                        uint32 base_map;
                        for (base_map = base; base_map < limit; base_map += 1024) {
                                map_downstream(pci, Sim_Addr_Space_IO,
                                               base_map, 256,
                                               DOWNSTREAM_IO);
                        }
                } else {
                        map_downstream(pci, Sim_Addr_Space_IO,
                                       base, limit - base + 1, 
                                       DOWNSTREAM_IO);
                }

                if ((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) >> 3) & 1) {
                        uint32 base_k;
                        for (base_k = 0; base_k < 64; base_k++) {
                                uint32 start_1 = 1024 * base_k + 0x3b0;
                                uint32 end_1 = 1024 * base_k + 0x3bb;
                                uint32 start_2 = 1024 * base_k + 0x3c0;
                                uint32 end_2 = 1024 * base_k + 0x3df;
                                if (((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) >> 2) & 1) || start_1 < base || start_1 > limit) {
                                        map_downstream(pci, Sim_Addr_Space_IO, start_1, end_1 - start_1 + 1, DOWNSTREAM_IO_VGA);
                                        map_downstream(pci, Sim_Addr_Space_IO, start_2, end_2 - start_2 + 1, DOWNSTREAM_IO_VGA);
                                }
                        }
                }

                if (!upstream)
                        return;

                /* First upstream from 0 to base - 1.
                   Be careful to avoid VGA mappings. */
                if ((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) >> 3) & 1) {
                        uint32 base_map;
                        int prev_merge_valid = 0;
                        for (base_map = 0; base_map < base; base_map += 1024) {
                                if (prev_merge_valid) {
                                        map_upstream(pci, Sim_Addr_Space_IO,
                                                     base_map - 1024 + 0x3df + 1,
                                                     1024 - 0x3df - 1 + 0x3b0,
                                                     UPSTREAM_IO_1);
                                } else {
                                        map_upstream(pci, Sim_Addr_Space_IO,
                                                     base_map, 0x3b0,
                                                     UPSTREAM_IO_1);
                                }
                                map_upstream(pci, Sim_Addr_Space_IO,
                                             base_map + 0x3bb + 1, 0x3c0 - 0x3bb - 1,
                                             UPSTREAM_IO_1);
                                prev_merge_valid = 1;
                        }
                        if (prev_merge_valid) {
                                map_upstream(pci, Sim_Addr_Space_IO,
                                             base_map - 1024 + 0x3df + 1, 1024 - 0x3df - 1,
                                             UPSTREAM_IO_1);
                        }
                } else if (base > 0) {
                        map_upstream(pci, Sim_Addr_Space_IO,
                                     0, base - 1,
                                     UPSTREAM_IO_1);
                }

                /* Upstream map parts not send downstream when ISA decoding enabled. */
                if ((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) >> 2) & 1) {
                        uint32 base_map;
                        for (base_map = base; base_map < limit; base_map += 1024) {
                                map_upstream(pci, Sim_Addr_Space_IO,
                                             base_map + 256, 1024 - 256,
                                             UPSTREAM_IO_1);
                        }
                }

                /* Second upstream from limit to highest address.
                   Remember to avoid VGA mappings. */
                if ((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) >> 3) & 1) {
                        uint32 base_map;
                        int prev_merge_valid = 0;
                        for (base_map = limit + 1; base_map < highest; base_map += 1024) {
                                if (prev_merge_valid) {
                                        map_upstream(pci, Sim_Addr_Space_IO,
                                                     base_map - 1024 + 0x3df + 1,
                                                     1024 - 0x3df - 1 + 0x3b0,
                                                     UPSTREAM_IO_2);
                                } else {
                                        map_upstream(pci, Sim_Addr_Space_IO,
                                                     base_map, 0x3b0,
                                                     UPSTREAM_IO_2);
                                }
                                map_upstream(pci, Sim_Addr_Space_IO,
                                             base_map + 0x3bb + 1, 0x3c0 - 0x3bb - 1,
                                             UPSTREAM_IO_2);
                                prev_merge_valid = 1;
                        }
                        if (prev_merge_valid) {
                                map_upstream(pci, Sim_Addr_Space_IO,
                                             base_map - 1024 + 0x3df + 1, 1024 - 0x3df - 1,
                                             UPSTREAM_IO_2);
                        }
                } else if (limit < highest) {
                        map_upstream(pci, Sim_Addr_Space_IO,
                                     limit + 1, highest - limit,
                                     UPSTREAM_IO_2);
                }
        }
}

typedef struct {
        uint64 base;
        uint64 limit;
} map_pair_t;

static int
map_pair_cmp(const void *a, const void *b)
{
        map_pair_t *a_val, *b_val;
        a_val = (map_pair_t *)a;
        b_val = (map_pair_t *)b;
        if (a_val->base < b_val->base)
                return -1;
        else if (a_val->base > b_val->base)
                return 1;
        else
                return 0;
}

static void
remap_memory(pci_device_t *pci)
{
        uint64 mem_base, mem_limit, pref_base, pref_limit;
        uint64 highest64 = UINT64_C(0xffffffffffffffff);
        uint64 highest32 = 0xffffffff;
        uint64 highest = pci->forward_prefetchable64 ? highest64 : highest32;
        map_pair_t map_pair[3];
        int num_mappings = 0;

        /* remove previous mappings */
        if (pci->pci_bus) {
                pci->pci_bus_interface.remove_map(pci->pci_bus, &pci->log->obj,
                                                  Sim_Addr_Space_Memory, DOWNSTREAM_PREF);
                pci->pci_bus_interface.remove_map(pci->pci_bus, &pci->log->obj,
                                                  Sim_Addr_Space_Memory, DOWNSTREAM_MEM);
                pci->pci_bus_interface.remove_map(pci->pci_bus, &pci->log->obj,
                                                  Sim_Addr_Space_Memory, DOWNSTREAM_MEM_VGA);
        }
        pci->secondary_bus_interface.remove_map(pci->secondary_bus, &pci->log->obj,
                                                Sim_Addr_Space_Memory, UPSTREAM_MEM_1);
        pci->secondary_bus_interface.remove_map(pci->secondary_bus, &pci->log->obj,
                                                Sim_Addr_Space_Memory, UPSTREAM_MEM_2);
        pci->secondary_bus_interface.remove_map(pci->secondary_bus, &pci->log->obj,
                                                Sim_Addr_Space_Memory, UPSTREAM_MEM_3);

        /* check if memory mappings are enabled */
        if (!(PCI_read_config_register(pci, PCI_COMMAND) & 2))
                return;

        mem_base  = PCI_read_config_register(pci, PCI_MEMORY_BASE) << 16;
        mem_limit = (PCI_read_config_register(pci, PCI_MEMORY_LIMIT) << 16) | 0xfffff;

        pref_base  = (PCI_read_config_register(pci, PCI_PREFETCHABLE_MEMORY_BASE) & ~0xf) << 16;
        pref_limit = (PCI_read_config_register(pci, PCI_PREFETCHABLE_MEMORY_LIMIT) << 16) | 0xfffff;

        if (pci->forward_prefetchable64) {
                pref_base  |= (uint64)PCI_read_config_register(pci, PCI_PREFETCHABLE_BASE_UPPER_32) << 32;
                pref_limit |= (uint64)PCI_read_config_register(pci, PCI_PREFETCHABLE_LIMIT_UPPER_32) << 32;
        }

        if ((mem_limit >= mem_base) && pci->forward_mem) {

                map_downstream(pci, Sim_Addr_Space_Memory,
                               mem_base, mem_limit - mem_base + 1,
                               DOWNSTREAM_MEM);

                map_pair[num_mappings].base = mem_base;
                map_pair[num_mappings].limit = mem_limit;
                num_mappings++;
        }

        if ((pref_limit >= pref_base) && pci->forward_prefetchable) {

                map_downstream(pci, Sim_Addr_Space_Memory,
                               pref_base, pref_limit - pref_base + 1,
                               DOWNSTREAM_PREF);

                map_pair[num_mappings].base = pref_base;
                map_pair[num_mappings].limit = pref_limit;
                num_mappings++;
        }

        if ((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) >> 3) & 1) {
                map_downstream(pci, Sim_Addr_Space_Memory, 0xa0000, 0xbffff - 0xa0000 + 1, DOWNSTREAM_MEM_VGA);
                map_pair[num_mappings].base = 0xa0000;
                map_pair[num_mappings].limit = 0xbffff;
                num_mappings++;
        }

        if (num_mappings == 0) {
                /* fake mapping since we can't map one 64-bit length */
                map_pair[num_mappings].base = highest32 + 1;
                map_pair[num_mappings].limit = highest32;
                num_mappings++;
        }

        ASSERT(num_mappings <= 3);

        if (!pci->forward_prefetchable && !pci->forward_mem)
                return;
        
        /* now create upstream mappings in the holes */

        /* only upstream if master enable set */
        if (!(PCI_read_config_register(pci, PCI_COMMAND) & 4))
                return;

        qsort(map_pair, num_mappings, sizeof(map_pair_t), map_pair_cmp);

        int i;
        uint64 prev_end = 0;
        for (i = 0; i < num_mappings; i++) {
                if (prev_end < map_pair[i].base)
                        map_upstream(pci, Sim_Addr_Space_Memory,
                                     prev_end, map_pair[i].base - prev_end,
                                     UPSTREAM_MEM_1);
                prev_end = map_pair[i].limit + 1;
        }
        if (prev_end < highest) {
                map_upstream(pci, Sim_Addr_Space_Memory,
                             prev_end, highest - prev_end + 1,
                             UPSTREAM_MEM_2);
        }
}


static void
bridge_type1_configuration_register_write(pci_device_t *pci, uint32 offset, uint32 size, uint32 value)
{
	switch (offset) {
        case PCI_COMMAND:
                PCI_write_sized_config_register(pci, offset, value, size);
                if (pci->forward_io)
                        remap_io(pci);
                remap_memory(pci);
                /* handle enable/disable of other base addresses */
                common_configuration_register_write(pci, offset, size, value);
                break;

        case PCI_SECONDARY_BUS_NUMBER:
        case PCI_SUBORDINATE_BUS_NUMBER:
                PCI_write_sized_config_register(pci, offset, value, size);
                remap_secondary_config(pci);
                break;

	case PCI_SECONDARY_STATUS: {
                uint16 status = PCI_read_sized_config_register(pci, offset, size);
                value &= 0xf800; // only bit 15-11 writable
                /* bits set in value clears the corresponding ones in status */
                value = (status & (value ^ status)) | (status & 0x7ff);
                PCI_write_sized_config_register(pci, offset, value, size);
                break;
        }

        case PCI_IO_BASE:
        case PCI_IO_LIMIT:
                /* see comment for PCI_MEMORY_BASE */
                PCI_write_sized_config_register(pci, offset, value, size);
                if (pci->forward_io)
                        remap_io(pci);
                break;

        case PCI_MEMORY_BASE:
        case PCI_MEMORY_LIMIT:
                /* If disabled, we shouldn't really update the register, but
                   our AGP bridge isn't currently a real bridge. The reason is
                   missing VGA handling in our PCI code. Since there are almost
                   no bridges that doesn't have forwarding based on
                   MEMORY_BASE, this hack is probably ok. */
                PCI_write_sized_config_register(pci, offset, value, size);
                if (pci->forward_mem)
                        remap_memory(pci);
                break;

        case PCI_PREFETCHABLE_MEMORY_BASE:
        case PCI_PREFETCHABLE_MEMORY_LIMIT:
                if (pci->forward_prefetchable) {
                        PCI_write_sized_config_register(pci, offset, value, size);
                        remap_memory(pci);
                }
                break;

        case PCI_PREFETCHABLE_BASE_UPPER_32:
        case PCI_PREFETCHABLE_LIMIT_UPPER_32:
                if (pci->forward_prefetchable64) {
                        PCI_write_sized_config_register(pci, offset, value, size);
                        remap_memory(pci);
                }
                break;

        case PCI_IO_BASE_UPPER_16:
        case PCI_IO_LIMIT_UPPER_16:
                if (pci->forward_io32) {
                        PCI_write_sized_config_register(pci, offset, value, size);
                        remap_io(pci);
                }
                break;

        case PCI_BRIDGE_EXPANSION_ROM_BASE:
                base_address_write(pci, offset, value);
                break;

        case PCI_BRIDGE_CONTROL:
                if (value & (1 << 6)) {
                        SIM_log_info(2, pci->log, pci->log_group,
                                     "Reset of secondary bus");

                        /* clear secondary status, and reset the secondary bus */
                        PCI_write_config_register(pci, PCI_SECONDARY_STATUS,
                                                  PCI_read_config_register(pci,
                                                                           PCI_SECONDARY_STATUS)
                                                  & 0x7ff);
                        pci->secondary_bus_interface.bus_reset(pci->secondary_bus);
                        /* reset-bit should be cleared explicitly */
                }
                PCI_write_sized_config_register(pci, offset, value, size);
                remap_io(pci);
                remap_memory(pci);
                break;

        default:
                common_configuration_register_write(pci, offset, size, value);
        }
}


static void
bridge_type1_reset(pci_device_t *pci)
{
        base_address_write(pci, PCI_BASE_ADDRESS_0, 0);
        base_address_write(pci, PCI_BASE_ADDRESS_1, 0);
        base_address_write(pci, PCI_BRIDGE_EXPANSION_ROM_BASE, 0);

        PCI_write_config_register(pci, PCI_PRIMARY_BUS_NUMBER, 0);
        PCI_write_config_register(pci, PCI_SECONDARY_BUS_NUMBER, 0);
        PCI_write_config_register(pci, PCI_SUBORDINATE_BUS_NUMBER, 0);

        PCI_write_config_register(pci, PCI_SECONDARY_LATENCY_TIMER, 0);

        PCI_write_config_register(pci, PCI_IO_BASE,
                                  PCI_read_config_register(pci, PCI_IO_BASE) & 0xf0);
        PCI_write_config_register(pci, PCI_IO_LIMIT,
                                  PCI_read_config_register(pci, PCI_IO_LIMIT) & 0xf0);

        PCI_write_config_register(pci, PCI_MEMORY_BASE,
                                  PCI_read_config_register(pci, PCI_MEMORY_BASE) & 0xfff0);
        PCI_write_config_register(pci, PCI_MEMORY_LIMIT,
                                  PCI_read_config_register(pci, PCI_MEMORY_LIMIT) & 0xfff0);

        PCI_write_config_register(pci, PCI_PREFETCHABLE_MEMORY_BASE,
                                  PCI_read_config_register(pci, PCI_PREFETCHABLE_MEMORY_BASE)
                                  & 0xfff0);
        PCI_write_config_register(pci, PCI_PREFETCHABLE_MEMORY_LIMIT,
                                  PCI_read_config_register(pci, PCI_PREFETCHABLE_MEMORY_LIMIT)
                                  & 0xfff0);

        PCI_write_config_register(pci, PCI_IO_BASE_UPPER_16, 0);
        PCI_write_config_register(pci, PCI_IO_LIMIT_UPPER_16, 0);
        PCI_write_config_register(pci, PCI_PREFETCHABLE_BASE_UPPER_32, 0);
        PCI_write_config_register(pci, PCI_PREFETCHABLE_LIMIT_UPPER_32, 0);

        /* remove mappings */
        remap_io(pci);
        remap_memory(pci);

        PCI_write_config_register(pci, PCI_SECONDARY_STATUS,
                                  PCI_read_config_register(pci,
                                                           PCI_SECONDARY_STATUS) & 0x7ff);

        PCI_write_config_register(pci, PCI_BRIDGE_CONTROL, 0);

        /* send reset to secondary bus */
        pci->secondary_bus_interface.bus_reset(pci->secondary_bus);
}


/* <add-fun id="pci device api">
   <short>default handling of unclaimed accesses</short>
   If no callback is installed to handle accesses to unmapped addresses
   for type 1 devices, then this function is called. It set the master
   abort flag in the <tt>Secondary Status</tt> register, and return a
   value with all ones. Master abort mode 1, where a target abort on the
   primary bus is signalled instead, is currently not implemented.
   </add-fun>
*/
exception_type_t
PCI_bridge_default_access_not_taken(
        conf_object_t *obj,
        conf_object_t *src_space, conf_object_t *dst_space,
        exception_type_t ex,
        generic_transaction_t *mem_op,
        map_info_t mapinfo)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        unsigned int i;

        if (PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) & (1 << 5)) {
                // TODO: signal target-abort instead of master-abort!
        }

        /* set received master-abort flag */
        PCI_write_config_register(pci, PCI_SECONDARY_STATUS,
                                  PCI_read_config_register(pci, PCI_SECONDARY_STATUS)
                                  | (1 << 13));

        /* return all 1s */
        if (SIM_mem_op_is_read(mem_op)) {
                for (i = 0; i < mem_op->size; i++)
                        mem_op->real_address[i] = 0xff;
        }

        return Sim_PE_No_Exception;
}


/* <add-fun id="pci device api">
   <short>default system error handling for bridges</short>
   If no callback is installed to handle system errors for type 1 devices,
   then this function is called. It will set the system error received bit
   in the <tt>Secondary Status</tt> register, and signal system error on
   the primary bus.
   </add-fun>
*/
void
PCI_bridge_default_system_error(conf_object_t *obj)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;

        /* set received system-error flag */
        PCI_write_config_register(pci, PCI_SECONDARY_STATUS,
                                  PCI_read_config_register(pci, PCI_SECONDARY_STATUS)
                                  | (1 << 14));

        /* send the system error on the primary bus if SERR# Enable set */
        if ((PCI_read_config_register(pci, PCI_BRIDGE_CONTROL) & (1 << 1))
            &&  (PCI_read_config_register(pci, PCI_COMMAND) & (1 << 8)))
                PCI_system_error(pci);
}


/* <add-fun id="pci device api">
   <short>default handling of secondary interrupts</short>
   Performs the default handling of raised interrupts received on
   the secondary PCI bus that should be routed to the primary bus.
   The interrupt line is changed in the following way:
   <tt>pin = (pin + device) % 4</tt>. It is possible to override
   this function using <fun>PCI_bridge_init</fun>.
   </add-fun>
*/
static void
PCI_bridge_default_interrupt_raised(conf_object_t *obj, 
                                    conf_object_t *irq_obj,
                                    int dev, int pin)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;

        ASSERT(pin < 4);
        PCI_raise_interrupt_pin(pci, (pin + dev) % 4);
}


/* <add-fun id="pci device api">
   <short>default handling of secondary interrupts</short>
   Performs the default handling of lowered interrupts on the
   secondary PCI bus that should be routed to the primary bus.
   The interrupt line is changed in the following way:
   <tt>pin = (pin + device) % 4</tt>. It is possible to override
   this function using <fun>PCI_bridge_init</fun>.
   </add-fun>
*/
static void
PCI_bridge_default_interrupt_lowered(conf_object_t *obj, 
                                     conf_object_t *irq_obj,
                                     int dev, int pin)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;

        ASSERT(pin < 4);
        PCI_lower_interrupt_pin(pci, (pin + dev) % 4);
}



/* <add-fun id="pci device api">
   <short>Initialize generic PCI bridge device</short>
   Initializes a generic PCI-to-PCI (type 1) device. This function should
   be called directly after <fun>PCI_device_init</fun>. The <arg>system_error</arg>
   callback can be set to receive system errors on the secondary bus. If none
   is given, the <fun>PCI_bridge_default_system_error</fun> function is used as
   default. Similarly for the <arg>access_not_taken</arg> argument, that defaults
   to <fun>PCI_bridge_default_access_not_taken</fun>. The <arg>interrupt_raised</arg>
   and <arg>interrupt_lowered</arg> functions can be used to override
   <fun>PCI_bridge_default_interrupt_raised</fun> and
   <fun>PCI_bridge_default_interrupt_lowered</fun>. The next arguments specify what
   kind of transactions that the bridge supports. 16-bit I/O, 32-bit I/O operations,
   memory, prefetchable memory and 64-bit prefetchable memory operations.
   </add-fun>
*/
void
PCI_bridge_init(pci_device_t *pci,
                void (*system_error)(conf_object_t *obj),
                exception_type_t (*access_not_taken)(
                        conf_object_t *obj,
                        conf_object_t *src_space,
                        conf_object_t *dst_space,
                        exception_type_t ex,
                        generic_transaction_t *mem_op,
                        map_info_t mapinfo),
                void (*interrupt_raised)(
                        conf_object_t *obj, 
                        conf_object_t *dev_obj,
                        int device, int pin),
                void (*interrupt_lowered)(
                        conf_object_t *obj, 
                        conf_object_t *dev_obj,
                        int device, int pin),
                int forward_io, int forward_io32,
                int forward_mem,
                int forward_prefetchable, 
                int forward_prefetchable64)
{
        ASSERT(forward_io >= forward_io32);
        ASSERT(forward_prefetchable >= forward_prefetchable64);

        pci->forward_io = forward_io;
        pci->forward_io32 = forward_io32;
        pci->forward_mem = forward_mem;
        pci->forward_prefetchable = forward_prefetchable;
        pci->forward_prefetchable64 = forward_prefetchable64;

        /* PCI-to-PCI bridge */
        PCI_write_config_register(pci, PCI_CLASS_CODE, 0x060400);
        PCI_write_config_register(pci, PCI_HEADER_TYPE, 1);

        if (system_error)
                pci->system_error = system_error;
        else
                pci->system_error = PCI_bridge_default_system_error;

        if (access_not_taken)
                pci->access_not_taken = access_not_taken;
        else
                pci->access_not_taken = PCI_bridge_default_access_not_taken;

        if (interrupt_raised)
                pci->interrupt_raised = interrupt_raised;
        else
                pci->interrupt_raised = PCI_bridge_default_interrupt_raised;

        if (interrupt_lowered)
                pci->interrupt_lowered = interrupt_lowered;
        else
                pci->interrupt_lowered = PCI_bridge_default_interrupt_lowered;

        /* set 32-bit capable flag */
        if (forward_io32) {
                PCI_write_config_register(pci, PCI_IO_BASE, 1);
                PCI_write_config_register(pci, PCI_IO_LIMIT, 1);
        }

        /* set 64-bit capable flag */
        if (forward_prefetchable64) {
                PCI_write_config_register(pci, PCI_PREFETCHABLE_MEMORY_BASE, 1);
                PCI_write_config_register(pci, PCI_PREFETCHABLE_MEMORY_LIMIT, 1);
        }

        SIM_hap_add_callback("Core_Configuration_Loaded",
                             (obj_hap_func_t)configuration_loaded_hap, pci);

        type1_configuration_register_write =  bridge_type1_configuration_register_write;
        type1_reset = bridge_type1_reset;
        get_bridge_bus_info = get_bus_info;
}


/* <add-fun id="pci device api">
   <short>Set optional memory mapping attributes</short>
   Configures the bridge's memory mappings. The priority,
   align_size boundary and a reverse-endian flag can be set for
   each mapping. These values are described in the <tt>map</tt>
   attribute of the <tt>memory-space</tt> class. Default is 0
   for all values. The mappings that can be modified are IO
   downstream, memory downstream, prefetchable memory downstream,
   IO upstream and memory upstream.
   </add-fun>
*/
void
PCI_bridge_map_setup(
        pci_device_t *pci,
        int io_down_priority, int io_down_align_size, int io_down_endian,
        int mem_down_priority, int mem_down_align_size, int mem_down_endian,
        int pref_down_priority, int pref_down_align_size, int pref_down_endian,
        int io_up_priority, int io_up_align_size, int io_up_endian,
        int mem_up_priority, int mem_up_align_size, int mem_up_endian)
{
        pci->io_down_priority = io_down_priority;
        pci->io_down_align_size = io_down_align_size;
        pci->io_down_endian = io_down_endian;

        pci->mem_down_priority = mem_down_priority;
        pci->mem_down_align_size = mem_down_align_size;
        pci->mem_down_endian = mem_down_endian;

        pci->pref_down_priority = pref_down_priority;
        pci->pref_down_align_size = pref_down_align_size;
        pci->pref_down_endian = pref_down_endian;

        pci->io_up_priority = io_up_priority;
        pci->io_up_align_size = io_up_align_size;
        pci->io_up_endian = io_up_endian;

        pci->mem_up_priority = mem_up_priority;
        pci->mem_up_align_size = mem_up_align_size;
        pci->mem_up_endian = mem_up_endian;
}
                    

static void
received_system_error(conf_object_t *obj)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        pci->system_error(obj);
}

static exception_type_t
received_access_not_taken(conf_object_t *obj,
                          conf_object_t *src_space, conf_object_t *dst_space,
                          exception_type_t ex,
                          generic_transaction_t *mem_op,
                          map_info_t mapinfo)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        return pci->access_not_taken(obj, src_space, dst_space, ex, mem_op, mapinfo);
}


static void
received_interrupt_raised(conf_object_t *obj, conf_object_t *irq_obj, int dev, int pin)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        pci->interrupt_raised(obj, irq_obj, dev, pin);
}


static void
received_interrupt_lowered(conf_object_t *obj, conf_object_t *irq_obj, int dev, int pin)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        pci->interrupt_lowered(obj, irq_obj, dev, pin);
}


static attr_value_t
get_secondary_bus(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        return SIM_make_attr_object(pci->secondary_bus);
}


static set_error_t
set_secondary_bus(void *dummy, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        pci_bus_interface_t *pci_bus_interface;
        io_memory_interface_t *io_memory;
        pci_device_t *pci = (pci_device_t *)obj->object_data;

        if (!(pci_bus_interface =
              (pci_bus_interface_t *)SIM_get_interface(val->u.object, PCI_BUS_INTERFACE)))
                return Sim_Set_Interface_Not_Found;

        if (!(io_memory =
              (io_memory_interface_t *)SIM_get_interface(val->u.object, IO_MEMORY_INTERFACE)))
                return Sim_Set_Interface_Not_Found;

        pci->secondary_bus = val->u.object;
        pci->secondary_bus_interface = *pci_bus_interface;
        pci->secondary_bus_io_memory = *io_memory;
        return Sim_Set_Ok;
}


static attr_value_t
get_mapping_setup(void *dummy, conf_object_t *obj, attr_value_t *idx)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;
        return SIM_make_attr_list(15,
                                  SIM_make_attr_integer(pci->io_down_priority),
                                  SIM_make_attr_integer(pci->io_down_align_size),
                                  SIM_make_attr_integer(pci->io_down_endian),
                                  SIM_make_attr_integer(pci->mem_down_priority),
                                  SIM_make_attr_integer(pci->mem_down_align_size),
                                  SIM_make_attr_integer(pci->mem_down_endian),
                                  SIM_make_attr_integer(pci->pref_down_priority),
                                  SIM_make_attr_integer(pci->pref_down_align_size),
                                  SIM_make_attr_integer(pci->pref_down_endian),
                                  SIM_make_attr_integer(pci->io_up_priority),
                                  SIM_make_attr_integer(pci->io_up_align_size),
                                  SIM_make_attr_integer(pci->io_up_endian),
                                  SIM_make_attr_integer(pci->mem_up_priority),
                                  SIM_make_attr_integer(pci->mem_up_align_size),
                                  SIM_make_attr_integer(pci->mem_up_endian));
}


static set_error_t
set_mapping_setup(void *dummy, conf_object_t *obj, attr_value_t *val, attr_value_t *idx)
{
        pci_device_t *pci = (pci_device_t *)obj->object_data;

        pci->io_down_priority = val->u.list.vector[0].u.integer;
        pci->io_down_align_size = val->u.list.vector[1].u.integer;
        pci->io_down_endian = val->u.list.vector[2].u.integer;
        pci->mem_down_priority = val->u.list.vector[3].u.integer;
        pci->mem_down_align_size = val->u.list.vector[4].u.integer;
        pci->mem_down_endian = val->u.list.vector[5].u.integer;
        pci->pref_down_priority = val->u.list.vector[6].u.integer;
        pci->pref_down_align_size = val->u.list.vector[7].u.integer;
        pci->pref_down_endian = val->u.list.vector[8].u.integer;
        pci->io_up_priority = val->u.list.vector[9].u.integer;
        pci->io_up_align_size = val->u.list.vector[10].u.integer;
        pci->io_up_endian = val->u.list.vector[11].u.integer;
        pci->mem_up_priority = val->u.list.vector[12].u.integer;
        pci->mem_up_align_size = val->u.list.vector[13].u.integer;
        pci->mem_up_endian = val->u.list.vector[14].u.integer;
        return Sim_Set_Ok;
}

/* <add-fun id="pci device api">
   <short>register generic PCI bridge attributes</short>
   Registers the generic PCI bridge device attributes, and performs
   some early initialization. This function should be called directly
   after <fun>PCI_register_device_attributes</fun>.
   </add-fun>   
*/
void
PCI_register_bridge_attributes(conf_class_t *pci_class)
{
        pci_bridge_interface_t *pci_bridge_interface;
        bridge_interface_t *bridge_interface;

        SIM_register_typed_attribute(pci_class, "secondary_bus",
                                     get_secondary_bus, NULL,
                                     set_secondary_bus, NULL,
                                     Sim_Attr_Required,
                                     "o", NULL,
                                     "Secondary (downstream) PCI bus.");

        SIM_register_typed_attribute(pci_class, "mapping_setup",
                                     get_mapping_setup, NULL,
                                     set_mapping_setup, NULL,
                                     Sim_Attr_Optional,
                                     "[i{15}]", NULL,
                                     "Attributes for mappings");

        pci_bridge_interface = MM_ZALLOC(1, pci_bridge_interface_t);
        pci_bridge_interface->system_error = received_system_error;
	pci_bridge_interface->raise_interrupt = received_interrupt_raised;
	pci_bridge_interface->lower_interrupt = received_interrupt_lowered;
        SIM_register_interface(pci_class, PCI_BRIDGE_INTERFACE, pci_bridge_interface);

        bridge_interface = MM_ZALLOC(1, bridge_interface_t);
        bridge_interface->not_taken = received_access_not_taken;
        SIM_register_interface(pci_class, BRIDGE_INTERFACE, bridge_interface);
}
