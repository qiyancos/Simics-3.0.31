
##  Copyright 2004-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.

import copy
from sim_core import *
from cli import *
from configuration import *

# This is the generic flash-memory support provided by Simics
# The following flash memories are pre-configured:
# * Intel 28FxxxC3x   (advanced boot block flash)
# * Intel 28FxxxJ3    (strataflash)
# * Intel 28FxxxJ3A   (strataflash)
# * Intel 28FxxxP30x  (strataflash)
# * Intel 28F160S3
# * Intel 28F320S3
# * Am29F040B
# * Am29F016D
# * Am29SL160CT
# * Am29LV64xD  (and all L/H versions)
# * Am29LV640MH
# * Am29LV160MB
# * SG29GL064M
# * Am29DL323B
# * Am29DL323G_
# * MBM29LV650UE
# * Amd S29GLxxxN
# * AT49BV001A
# * Am29DL163D

# To add other flash configuration, edit the flash_description table to fill in
# the correct values for the flash you want to simulate. Add also a finish
# function that will parse the product name to complete the information. You
# can use the default function if no more configuration is needed.

# You can then use the add_flash_memory() function to add a flash memory in a
# standard python-based Simics configuration, or use the flash_create_memory()
# function that will simply return a list of objects to add to your own
# configuration

# The following commands are supported for Intel flash:
# - CFI support (if any)
# - read identifier mode (including block locking status)
# - read/clear status register
# - write buffer
# - word program
# - block erase
# - simple locking scheme (strataflash) / advanced locking scheme

# The following commands are supported for AMD flash:
# - CFI support (if any)
# - autoselect mode (including protect verify)
# - program
# - sector erase
# - unlock bypass/program/reset (not tested properly)

########################################################
# EDIT TO ADD A NEW FLASH TYPE --- Flash Configuration #
########################################################

#
# Default completion function
#
# finish(product_no, config) -> (config_updated, size of one flash chip, in bytes)
def finish_default(product_no, config):
    size = sum(config["unit-size"]) # compute total size
    return (config, size)

#
# Completion function for:
# Intel 28F800C3T
#          160  B
#          320  
#          640
#
# finish(product_no, config) -> (config_updated, size of one flash chip, in bytes)
def finish_config_28F___C3_(product_no, config):
    # set size-dependent parameters
    if   product_no[3:6] == "800":      # 8Mbit, Bottom
        device_geometry_definition = [0x14, 0x01, 0x00, 0x00, 0x00, 0x02, 0x07, 0x00, 0x20, 0x00, 0x0E, 0x00, 0x00, 0x01]
        device_id = 0x88C1
        big_blocks = 15
    elif product_no[3:6] == "160":      # 16Mbit, Bottom
        device_geometry_definition = [0x15, 0x01, 0x00, 0x00, 0x00, 0x02, 0x07, 0x00, 0x20, 0x00, 0x1E, 0x00, 0x00, 0x01]
        device_id = 0x88C3
        big_blocks = 31
    elif product_no[3:6] == "320":      # 32Mbit, Bottom
        device_geometry_definition = [0x16, 0x01, 0x00, 0x00, 0x00, 0x02, 0x07, 0x00, 0x20, 0x00, 0x3E, 0x00, 0x00, 0x01]
        device_id = 0x88C5
        big_blocks = 63
    elif product_no[3:6] == "640":      # 64Mbit, Bottom
        device_geometry_definition = [0x17, 0x01, 0x00, 0x00, 0x00, 0x02, 0x07, 0x00, 0x20, 0x00, 0x7E, 0x00, 0x00, 0x01]
        device_id = 0x88CD
        big_blocks = 127
    else:
        return "The product no (" + product_no + ") should contain a valid size (800, 160, 320 or 640), not '" + product_no[3:6] + "'"

    # size
    size = 1 << device_geometry_definition[0]

    # check what where the boot block is
    if   product_no[8] == "T":
        boot_block = "top"
    elif product_no[8] == "B":
        boot_block = "bottom"
    else:
        return "The product no (" + product_no + ") should end with T (for top) or B (for bottom), not '" + product_no[8] + "'"

    # cfi_query
    for i in range(0x27, 0x2D):
        config["cfi-query"][i] = device_geometry_definition[i - 0x27]
    if boot_block == "bottom":
        # bottom blocking is already configured
        for i in range(0x2D, 0x35):
            config["cfi-query"][i] = device_geometry_definition[i - 0x27]
    else:
        # top blocking is inverted
        for i in range(0x2D, 0x31):
            config["cfi-query"][i] = device_geometry_definition[i - 0x27 + 4]
        for i in range(0x31, 0x35):
            config["cfi-query"][i] = device_geometry_definition[i - 0x27 - 4]

    # device-id
    if boot_block == "top":
        config['device-id'] = device_id - 1
    else:
        config['device-id'] = device_id

    # unit_size
    if boot_block == "top":
        config['unit-size'] = [0x10000 for i in range(big_blocks)] + [0x2000 for i in range(8)]
    else:
        config['unit-size'] = [0x2000 for i in range(8)] +  [0x10000 for i in range(big_blocks)]
    return (config, size)

#
# Completion function for:
# Intel 28F160S3
#          320
#
#
# finish(product_no, config) -> (config_updated, size of one flash chip, in bytes)
def finish_config_28F___S3 (product_no, config):
    # set size-dependendt parameters
    if   product_no[3:6] == "160":       # 16Mbit
        device_geometry_definition = [0x15, 0x02, 0x00, 0x05, 0x00, 0x01, 0x1f, 0x00, 0x00, 0x01]
        config['device-id'] = 0xd0
        blocks = 32
    elif product_no[3:6] == "320":       # 32Mbit
        device_geometry_definition = [0x16, 0x02, 0x00, 0x05, 0x00, 0x01, 0x3f, 0x00, 0x00, 0x01]
        config['device-id'] = 0xd4
        blocks = 64
    else:
        return "The product no (" + product_no + ") should contain a valid size (160 or 320), not '" + product_no[3:6] + "'"

    # size
    size = 1 << device_geometry_definition[0]

    # cfi_query
    for i in range(0x27, 0x31):
        config["cfi-query"][i] = device_geometry_definition[i - 0x27]
    config['unit-size'] = [0x10000 for i in range(blocks)]
    return (config, size)

#
# Completion function for:
# Intel 28F320J3A
#          640  
#          128
#
# finish(product_no, config) -> (config_updated, size of one flash chip, in bytes)
def finish_config_28F___J3A(product_no, config):
    # set size-dependent parameters
    if   product_no[3:6] == "320":      # 32Mbit
        device_geometry_definition = [0x16, 0x02, 0x00, 0x05, 0x00, 0x01, 0x1F, 0x00, 0x00, 0x02]
        config['device-id'] = 0x0016
        blocks = 32
    elif product_no[3:6] == "640":      # 64Mbit
        device_geometry_definition = [0x17, 0x02, 0x00, 0x05, 0x00, 0x01, 0x3F, 0x00, 0x00, 0x02]
        config['device-id'] = 0x0017
        blocks = 64
    elif product_no[3:6] == "128":      # 128Mbit
        device_geometry_definition = [0x18, 0x02, 0x00, 0x05, 0x00, 0x01, 0x7F, 0x00, 0x00, 0x02]
        config['device-id'] = 0x0018
        blocks = 128
    else:
        return "The product no (" + product_no + ") should contain a valid size (320, 640 or 128), not '" + product_no[3:6] + "'"

    # size
    size = 1 << device_geometry_definition[0]

    # cfi_query
    for i in range(0x27, 0x31):
        config["cfi-query"][i] = device_geometry_definition[i - 0x27]
    config['unit-size'] = [0x20000 for i in range(blocks)]
    return (config, size)

#
# Completion function for:
# Intel 28F320J3
#          640  
#          128  
#          256
#
# finish(product_no, config) -> (config_updated, size of one flash chip, in bytes)
def finish_config_28F___J3(product_no, config):
    # set size-dependent parameters
    if product_no[3:6] == "320":      # 32Mbit
        device_geometry_definition = [0x16, 0x02, 0x00, 0x05, 0x00, 0x01, 0x1F, 0x00, 0x00, 0x02]
        config['device-id'] = 0x0016
        blocks = 32
    elif product_no[3:6] == "640":      # 64Mbit
        device_geometry_definition = [0x17, 0x02, 0x00, 0x05, 0x00, 0x01, 0x3F, 0x00, 0x00, 0x02]
        config['device-id'] = 0x0017
        blocks = 64
    elif product_no[3:6] == "128":      # 128Mbit
        device_geometry_definition = [0x18, 0x02, 0x00, 0x05, 0x00, 0x01, 0x7F, 0x00, 0x00, 0x02]
        config['device-id'] = 0x0018
        blocks = 128
    elif product_no[3:6] == "256":      # 256Mbit
        device_geometry_definition = [0x19, 0x02, 0x00, 0x05, 0x00, 0x01, 0xFF, 0x00, 0x00, 0x02]
        config['device-id'] = 0x001D
        blocks = 256
    else:
        return "The product no (" + product_no + ") should contain a valid size (320, 640, 128 or 256), not '" + product_no[3:6] + "'"

    # size
    size = 1 << device_geometry_definition[0]

    # cfi_query
    for i in range(0x27, 0x31):
        config["cfi-query"][i] = device_geometry_definition[i - 0x27]
    config['unit-size'] = [0x20000 for i in range(blocks)]
    return (config, size)

# Completion function for:
# Intel P30 strataflash
#
def finish_config_28F___P30_(product_no, config):
    # Add intel specific extended query data
    config['cfi-query'] += [0x00] * (0x10a - len(config['cfi-query']))
    config['cfi-query'] += [0x50, 0x52,              # 0x10a
                            0x49, 0x31, 0x34, 0xe6,  # 0x10c
                            0x01, 0x00, 0x00, 0x01,  # 0x110
                            0x03, 0x00, 0x18, 0x90,  # 0x114
                            0x02, 0x80, 0x00, 0x03,  # 0x118
                            0x03, 0x89, 0x00, 0x00,  # 0x11c
                            0x00, 0x00, 0x00, 0x00,  # 0x120
                            0x10, 0x00, 0x04, 0x03,  # 0x124
                            0x04, 0x01, 0x02, 0x03,  # 0x128
                            0x07, 0x01, 0x24, 0x00,  # 0x12c
                            0x01, 0x00, 0x11, 0x00,  # 0x130
                            0x00, 0x02, None, None,  # 0x134
                            None, None, 0x64, 0x00,  # 0x138
                            0x02, 0x03, 0x00, 0x80,  # 0x13c
                            0x00, 0x00, 0x00, 0x80,  # 0x140
                            None, None, None, None,  # 0x144
                            0x64, 0x00, 0x02, 0x03,  # 0x148
                            0x00, 0x80, 0x00, 0x00,  # 0x14c
                            0x00, 0x80, 0xff, 0xff,  # 0x150
                            0xff, 0xff, 0xff]        # 0x154

    # Where is the boot block?
    if product_no[-1] == "T":
        boot_block = "top"
    elif product_no[-1] == "B":
        boot_block = "bottom"
    else:
        return ("The product no (" + product_no + ") should end with TQ0/T00 "
                "(for top) or BQ0/B00 (for bottom), not '"
                + product_no[-3] + "'")

    # Chip size?
    if product_no[3:6] == "640":       # 64 Mbit
        blocks = 64
        config['device-id'] = iff(boot_block == "bottom", 0x881a, 0x8817)

        device_geometry = [0x17, 0x01, 0x00, 0x06, 0x00, 0x02]
        if boot_block == "bottom":
            device_geometry += [0x03, 0x00, 0x80, 0x00, 0x3e, 0x00, 0x00, 0x02]
        else:
            device_geometry += [0x3e, 0x00, 0x00, 0x02, 0x03, 0x00, 0x80, 0x00]
        device_geometry += [0x00, 0x00, 0x00, 0x00]

        if boot_block == "bottom":
            config['cfi-query'][0x136:0x13a] = [0x03, 0x00, 0x80, 0x00]
            config['cfi-query'][0x144:0x148] = [0x3e, 0x00, 0x00, 0x02]
        else:
            config['cfi-query'][0x136:0x13a] = [0x3e, 0x00, 0x00, 0x02]
            config['cfi-query'][0x144:0x148] = [0x03, 0x00, 0x80, 0x00]

    elif product_no[3:6] == "128":     # 128 Mbit
        blocks = 128
        config['device-id'] = iff(boot_block == "bottom", 0x881b, 0x8818)

        device_geometry = [0x18, 0x01, 0x00, 0x06, 0x00, 0x02]
        if boot_block == "bottom":
            device_geometry += [0x03, 0x00, 0x80, 0x00, 0x7e, 0x00, 0x00, 0x02]
        else:
            device_geometry += [0x7e, 0x00, 0x00, 0x02, 0x03, 0x00, 0x80, 0x00]
        device_geometry += [0x00, 0x00, 0x00, 0x00]

        if boot_block == "bottom":
            config['cfi-query'][0x136:0x13a] = [0x03, 0x00, 0x80, 0x00]
            config['cfi-query'][0x144:0x148] = [0x7e, 0x00, 0x00, 0x02]
        else:
            config['cfi-query'][0x136:0x13a] = [0x7e, 0x00, 0x00, 0x02]
            config['cfi-query'][0x144:0x148] = [0x03, 0x00, 0x80, 0x00]

    elif product_no[3:6] == "256":     # 256 Mbit
        blocks = 256
        config['device-id'] = iff(boot_block == "bottom", 0x891c, 0x8919)

        device_geometry = [0x19, 0x01, 0x00, 0x06, 0x00, 0x02]
        if boot_block == "bottom":
            device_geometry += [0x03, 0x00, 0x80, 0x00, 0xfe, 0x00, 0x00, 0x02]
        else:
            device_geometry += [0xfe, 0x00, 0x00, 0x02, 0x03, 0x00, 0x80, 0x00]
        device_geometry += [0x00, 0x00, 0x00, 0x00]

        if boot_block == "bottom":
            config['cfi-query'][0x136:0x13a] = [0x03, 0x00, 0x00, 0x80]
            config['cfi-query'][0x144:0x148] = [0xfe, 0x00, 0x00, 0x02]
        else:
            config['cfi-query'][0x136:0x13a] = [0xfe, 0x00, 0x00, 0x02]
            config['cfi-query'][0x144:0x148] = [0x03, 0x00, 0x00, 0x80]
    else:
        return ("The product no (" + product_no + ") should contain a valid "
                "size specification (640/128/256), not '"
                + product_no[3:6] + "'")

    size = 1 << device_geometry[0]
    for i in range(0x27, 0x39):
        config['cfi-query'][i] = device_geometry[i - 0x27]

    if boot_block == "top":
        config['unit-size'] = [0x20000] * (blocks - 1) + [0x8000] * 4
    else:
        config['unit-size'] = [0x8000] * 4 + [0x20000] * (blocks - 1)
    return (config, size)

#
# Completion function for:
# Am29DL323GB
# Am29DL323GT
#
# finish(product_no, config) -> (config_updated, size of one flash chip, in bytes)
def finish_config_Am29DL323G_(product_no, config):
    # check what where the boot block is
    if   product_no[-1] == "T":
        boot_block = "top"
    elif product_no[-1] == "B":
        boot_block = "bottom"
    else:
        return "The product no (" + product_no + ") should end with T (for top) or B (for bottom), not '" + product_no[-1] + "'"

    if boot_block == "top":
        config['device-id'] = 0x2250
        config['unit-size'] = [0x10000]*63 + [0x2000]*8
        config["cfi-query"][0x4f] = 0x03
    else:
        config['device-id'] = 0x2253
        config['unit-size'] = [0x2000]*8 + [0x10000]*63
        config["cfi-query"][0x4f] = 0x02

    return finish_default(product_no, config)

#
# Completion function for:
# S29GL128N
# S29GL256N
# S29GL512N
#
def finish_config_S29GL___N(product_no, config):
    # check size
    if   product_no[5:8] == "128":
        size = 128
    elif product_no[5:8] == "256":
        size = 256
    elif product_no[5:8] == "512":
        size = 512
    else:
        return "The product no (" + product_no + ") is not supported. Only 128,256 or 512 Mbit are supported."

    config['unit-size'] = [128*1024]*size
    if size == 128:
        config["cfi-query"][0x27] = 0x18
        config["cfi-query"][0x2d] = 0x7f
        config["cfi-query"][0x2e] = 0x00
    elif size == 256:
        config["cfi-query"][0x27] = 0x19
        config["cfi-query"][0x2d] = 0xff
        config["cfi-query"][0x2e] = 0x00
    else:
        config["cfi-query"][0x27] = 0x1a
        config["cfi-query"][0x2d] = 0xff
        config["cfi-query"][0x2e] = 0x01

    # not sure on this one
    config["cfi-query"][0x4f] = 0x04  # bottom WP protect
    #config["cfi-query"][0x4f] = 0x05  # top WP protect

    return finish_default(product_no, config)


#
# list of completion functions
#
complete_functions = {
    "28F___C3_" : finish_config_28F___C3_,
    "28F___J3A" : finish_config_28F___J3A,
    "28F___J3"  : finish_config_28F___J3,
    "28F___S3"  : finish_config_28F___S3,
    "28F___P30_" : finish_config_28F___P30_,
    "82802-8"   : finish_default,
    "Am29F040B" : finish_default,
    "Am29F016D" : finish_default,
    "Am29SL160CT": finish_default,
    "Am29LV640MH": finish_default,
    "Am29LV64_D": finish_default,
    "Am29LV160MB": finish_default,
    "SG29GL064M": finish_default,
    "Am29DL323B": finish_default,
    "Am29DL323G_": finish_config_Am29DL323G_,
    "MBM29LV650UE": finish_default,
    "S29GL___N": finish_config_S29GL___N,
    "AT49BV001A": finish_default,
    "AT49BV001AT": finish_default,
    "Am29DL163D": finish_default,
    }

#
# static description of flash memory chips
#
flash_descriptions = {
    "28F___C3_" : {
        "cfi-query" : [0x89, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x03, # 0x10
                       0x00, 0x35, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0xB4, 0xC6, 0x05, # 0x1C
                       0x00, 0x0A, 0x00, 0x04, # 0x20
                       0x00, 0x03, 0x00, None, # 0x24
                       None, None, None, None, # 0x28
                       None, None, None, None, # 0x2C
                       None, None, None, None, # 0x30
                       None,                   # 0x34
                       0x50, 0x52, 0x49, 0x31, # 0x35 Extended Query
                       0x30, 0x66, 0x00, 0x00, # 0x39
                       0x00, 0x01, 0x03, 0x00, # 0x3D
                       0x33, 0xC0, 0x01, 0x80, # 0x41
                       0x00, 0x03, 0x03],      # 0x45
        "device-id" : None,
        "manufacturer-id" : 0x0089,     # intel
        "max-chip-width" : 16,          # 16-bits chips
        "unit-size" : None,
        "intel_write_buffer" : 0,       # no write-buffer in C3
        "intel_protection_program" : 1,
        "intel_configuration" : 1,
        "intel_lock" : 2                # advanced locking
        },

    "28F___P30_" : {
        "cfi-query" : [0x89, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0c
                       0x51, 0x52, 0x59, 0x01, # 0x10
                       0x00, 0x0a, 0x01, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x17, # 0x18
                       0x20, 0x85, 0x95, 0x08, # 0x1c
                       0x09, 0x0a, 0x00, 0x01, # 0x20
                       0x01, 0x02, 0x00, None, # 0x24
                       0x01, 0x00, 0x06, 0x00, # 0x28
                       # Device geometry - filled in by complete function
                       None, None, None, None, # 0x2c
                       None, None, None, None, # 0x30
                       None, None, None, None, # 0x34
                       None],
        "device-id" : None,
        "manufacturer-id" : 0x0089,            # Intel
        "max-chip-width" : 16,
        "unit-size" : None,

        # TODO: verify these
        "intel_write_buffer" : 1,
        "intel_protection_program" : 1,
        "intel_configuration" : 1,
        "intel_lock" : 2                       # Advanced locking
        },

    "28F___S3" : {
         "cfi-query" : [0xb0, 0x00, 0x00, 0x00, # 0x00  Sharp Manufacturer ID
                        0x00, 0x00, 0x00, 0x00, # 0x04  
                        0x00, 0x00, 0x00, 0x00, # 0x08
                        0x00, 0x00, 0x00, 0x00, # 0x0C
                        0x51, 0x52, 0x59, 0x01, # 0x10
                        0x00, 0x31, 0x00, 0x00, # 0x14 0x15 is Pointer to Extended Query
                        0x00, 0x00, 0x00, 0x27, # 0x18
                        0x55, 0x27, 0x55, 0x03, # 0x1C
                        0x06, 0x0A, 0x0f, 0x04, # 0x20
                        0x04, 0x04, 0x04, None, # 0x24
                        None, None, None, None, # 0x28
                        None, None, None, None, # 0x2C
                        None,
                        0x50, 0x52, 0x49, 0x31, # 0x31 Extended Query
                        0x30, 0x0f, 0x00, 0x00, # 0x35 
                        0x00, 0x01, 0x03, 0x00, # 0x39
                        0x50, 0x50],            # 0x3D
         "device-id" : None,                    # 
         "manufacturer-id" : 0x00b0,            # Sharp Manufacturer ID is verbatim from Intel docs.
         "max-chip-width" : 16,          # 16-bits chips
         "unit-size" : None,
         "intel_write_buffer" : 1,       
         "intel_protection_program" : 0, # No protection command on S3
         "intel_configuration" : 1,
         "intel_lock" : 1                # Simple locking
         },

    "28F___J3A" : {
        "cfi-query" : [0x89, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x01, # 0x10
                       0x00, 0x31, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x07, # 0x1C
                       0x07, 0x0A, 0x00, 0x04, # 0x20
                       0x04, 0x04, 0x00, None, # 0x24
                       None, None, None, None, # 0x28
                       None, None, None, None, # 0x2C
                       None, 
                       0x50, 0x52, 0x49, 0x31, # 0x31 Extended Query
                       0x31, 0x0A, 0x00, 0x00, # 0x35
                       0x00, 0x01, 0x01, 0x00, # 0x39
                       0x33, 0x00, 0x01, 0x00, # 0x3D
                       0x03, 0x00],            # 0x41
        "device-id" : None,
        "manufacturer-id" : 0x0089,     # intel
        "max-chip-width" : 16,          # 16-bits chips
        "unit-size" : None,
        "intel_write_buffer" : 1,
        "intel_protection_program" : 1,
        "intel_configuration" : 1,
        "intel_lock" : 1                # simple locking
        },

    "28F___J3" : {
        "cfi-query" : [0x89, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x01, # 0x10
                       0x00, 0x31, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x08, # 0x1C
                       0x08, 0x0A, 0x00, 0x04, # 0x20
                       0x04, 0x04, 0x00, None, # 0x24
                       None, None, None, None, # 0x28
                       None, None, None, None, # 0x2C
                       None, 
                       0x50, 0x52, 0x49, 0x31, # 0x31 Extended Query
                       0x31, 0x0A, 0x00, 0x00, # 0x35
                       0x00, 0x01, 0x01, 0x00, # 0x39
                       0x33, 0x00, 0x01, 0x80, # 0x3D
                       0x00, 0x03, 0x03, 0x03, # 0x41
                       0x00],                  # 0x45
        "device-id" : None,
        "manufacturer-id" : 0x0089,     # intel
        "max-chip-width" : 16,          # 16-bits chips
        "unit-size" : None,
        "intel_write_buffer" : 1,
        "intel_protection_program" : 1,
        "intel_configuration" : 1,
        "intel_lock" : 1                # simple locking
        },

    "82802-8" : {                       # Intel FWH
        "device-id" : 0xAC,
        "manufacturer-id" : 0x89,       # intel
        "max-chip-width" : 8,
        "unit-size" : [0x10000 for i in range(16)],
        "intel_write_buffer" : 1,
        "intel_lock" : 1,               # simple locking
        "command-set": 0x0001,          # Intel command-set, since no CFI structure
        },

    "Am29F040B" : {
        "device-id" : 0xA4,
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 8,           # 8-bits chips
        "command-set": 0x0002,          # AMD command-set, since no CFI structure
        "unit-size" : [0x10000 for i in range(8)]
        },

    "AT49BV001A" : {
        "device-id" : 0x05,
        "manufacturer-id" : 0x1f,  # Atmel
        "max-chip-width" : 8,
        "command-set" : 0x0002,
        "unit-size" : [ 0x4000, 0x2000, 0x2000, 0x8000, 0x10000 ]
        },

    "AT49BV001AT" : {
        "device-id" : 0x04,
        "manufacturer-id" : 0x1f,  # Atmel
        "max-chip-width" : 8,
        "command-set" : 0x0002,
        "unit-size" : [ 0x10000, 0x8000, 0x2000, 0x2000, 0x4000 ]
        },

    "Am29F016D" : {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x45, # 0x18
                       0x55, 0x00, 0x00, 0x03, # 0x1C
                       0x00, 0x0A, 0x00, 0x05, # 0x20
                       0x00, 0x04, 0x00, 0x15, # 0x24
                       0x00, 0x00, 0x00, 0x00, # 0x28
                       0x01, 0x1F, 0x00, 0x00, # 0x2C
                       0x01, 0x00, 0x00, 0x00, # 0x30
                       0x00, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x31, 0x00, 0x02, 0x04, # 0x44
                       0x01, 0x04, 0x00, 0x00, # 0x48
                       0x00, 0x00, 0x00, 0x00],# 0x4C
        "device-id" : 0xAD,
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 8,           # 8-bits chips
        "unit-size" : [0x10000 for i in range(32)],
        },

    "Am29SL160CT" : {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x18, # 0x18
                       0x22, 0x00, 0x00, 0x04, # 0x1C
                       0x00, 0x0A, 0x00, 0x05, # 0x20
                       0x00, 0x04, 0x00, 0x15, # 0x24
                       0x02, 0x00, 0x00, 0x00, # 0x28
                       0x02, 0x07, 0x00, 0x20, # 0x2C
                       0x00, 0x1E, 0x00, 0x00, # 0x30
                       0x01, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x30, 0x00, 0x02, 0x01, # 0x44
                       0x01, 0x04, 0x00, 0x00, # 0x48
                       0x00, 0x00, 0x00, 0x00],# 0x4C
        "device-id" : 0x22A4,
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 16,           # 16-bits chip
        "unit-size" : [0x10000 for i in range(31)] + [0x2000 for i in range(8)],
        },
     "Am29LV640MH": {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x07, # 0x1C
                       0x07, 0x0A, 0x00, 0x01, # 0x20
                       0x05, 0x04, 0x00, 0x17, # 0x24
                       0x02, 0x00, 0x05, 0x00, # 0x28
                       0x01, 0x7F, 0x00, 0x00, # 0x2C
                       0x01, 0x00, 0x00, 0x00, # 0x30
                       0x00, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x33, 0x08, 0x02, 0x01, # 0x44
                       0x01, 0x04, 0x00, 0x00, # 0x48
                       0x01, 0xB5, 0xC5, 0x05, # 0x4C
                       0x01],                  # 0x50
        "device-id" : [0x227E, 0x220C, 0x2201],
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 16,           # 16-bits chip
        "unit-size" : [0x10000 for i in range(128)],
        },
     "Am29LV64_D": {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x04, # 0x1C
                       0x00, 0x0A, 0x00, 0x05, # 0x20
                       0x00, 0x04, 0x00, 0x17, # 0x24
                       0x01, 0x00, 0x00, 0x00, # 0x28
                       0x01, 0x7F, 0x00, 0x00, # 0x2C
                       0x01, 0x00, 0x00, 0x00, # 0x30
                       0x00, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x33, 0x00, 0x02, 0x04, # 0x44
                       0x01, 0x04, 0x00, 0x00, # 0x48
                       0x00, 0xB5, 0xC5, 0x05], # 0x4C
        "device-id" : 0x22D7,
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 16,           # 16-bits chip
        "unit-size" : [0x10000 for i in range(128)],
        },
    "Am29DL323G_": {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x04, # 0x1C
                       0x00, 0x0A, 0x00, 0x05, # 0x20
                       0x00, 0x04, 0x00, 0x16, # 0x24
                       0x02, 0x00, 0x00, 0x00, # 0x28
                       0x02, 0x07, 0x00, 0x20, # 0x2C
                       0x00, 0x3e, 0x00, 0x00, # 0x30
                       0x01, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x33, 0x04, 0x02, 0x01, # 0x44
                       0x01, 0x04, 0x30, 0x00, # 0x48
                       0x00, 0x85, 0x95, None],# 0x4C
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 16,           # 16-bit chip
        },
    "SG29GL064M": {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x07, # 0x1C
                       0x07, 0x0A, 0x00, 0x01, # 0x20
                       0x05, 0x04, 0x00, 0x17, # 0x24
                       0x02, 0x00, 0x05, 0x00, # 0x28
                       0x01, 0x7F, 0x00, 0x00, # 0x2C
                       0x01, 0x00, 0x00, 0x00, # 0x30
                       0x00, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x33, 0x08, 0x02, 0x01, # 0x44
                       0x01, 0x04, 0x00, 0x00, # 0x48
                       0x01, 0xB5, 0xC5, 0x05, # 0x4C
                       0x01],                  # 0x50
        "device-id" : [0x227E, 0x220C, 0x2201],
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 16,           # 16-bits chip
        "unit-size" : [0x10000 for i in range(128)],
        },
    "Am29LV160MB": {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x07, # 0x1C
                       0x00, 0x0A, 0x00, 0x01, # 0x20
                       0x00, 0x04, 0x00, 0x15, # 0x24
                       0x02, 0x00, 0x00, 0x00, # 0x28
                       0x04, 0x00, 0x00, 0x40, # 0x2C
                       0x00, 0x01, 0x00, 0x20, # 0x30
                       0x00, 0x00, 0x00, 0x80, # 0x34
                       0x00, 0x1E, 0x00, 0x00, # 0x38
                       0x01, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x33, 0x08, 0x02, 0x01, # 0x44
                       0x01, 0x04, 0x00, 0x00, # 0x48
                       0x00],                  # 0x4C
        "device-id" : 0x2249,
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 16,           # 16-bits chip
        "unit-size" : [0x4000, 0x2000, 0x2000, 0x8000] + [0x10000 for i in range(31)],
        },

    "MBM29LV650UE": {
        "cfi-query" : [0x04, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x04, # 0x1C
                       0x00, 0x0A, 0x00, 0x05, # 0x20
                       0x00, 0x04, 0x00, 0x17, # 0x24
                       0x01, 0x00, 0x05, 0x00, # 0x28
                       0x01, 0x7F, 0x00, 0x00, # 0x2C
                       0x01, 0x00, 0x00, 0x00, # 0x30
                       0x00, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x31, 0x01, 0x02, 0x04, # 0x44
                       0x01, 0x04, 0x00, 0x00, # 0x48
                       0x00, 0xB5, 0xC5, 0x05], # 0x4C
        "device-id" : 0x22d7,
        "manufacturer-id" : 0x04,       # Spansion/Fujitsu
        "max-chip-width" : 16,          # 16-bits chip
        "amd_ignore_cmd_address": 1,
        "unit-size" : [0x10000 for i in range(128)],
        },

    "S29GL___N": {
        "cfi-query" : [0x04, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C
                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x07, # 0x1C
                       0x07, 0x0A, 0x00, 0x01, # 0x20
                       0x05, 0x04, 0x00, None, # 0x24
                       0x02, 0x00, 0x05, 0x00, # 0x28
                       0x01, None, None, 0x00, # 0x2C
                       0x02, 0x00, 0x00, 0x00, # 0x30
                       0x00, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x33, 0x10, 0x02, 0x01, # 0x44
                       0x00, 0x08, 0x00, 0x00, # 0x48
                       0x02, 0xB5, 0xC5, None, # 0x4C
                       0x01], # 0x50
        "device-id" : 0x22de,
        "manufacturer-id" : 0x01,
        "max-chip-width" : 16,          # 16-bits chip
        },

      "Am29DL163D" : {
        "cfi-query" : [0x01, 0x00, 0x00, 0x00, # 0x00
                       0x00, 0x00, 0x00, 0x00, # 0x04
                       0x00, 0x00, 0x00, 0x00, # 0x08
                       0x00, 0x00, 0x00, 0x00, # 0x0C

                       0x51, 0x52, 0x59, 0x02, # 0x10
                       0x00, 0x40, 0x00, 0x00, # 0x14
                       0x00, 0x00, 0x00, 0x27, # 0x18
                       0x36, 0x00, 0x00, 0x04, # 0x1C
                       0x00, 0x0A, 0x00, 0x05, # 0x20
                       0x00, 0x04, 0x00, 0x15, # 0x24
                       0x02, 0x00, 0x00, 0x00, # 0x28
                       0x02, 0x07, 0x00, 0x20, # 0x2C
                       0x00, 0x1E, 0x00, 0x00, # 0x30
                       0x01, 0x00, 0x00, 0x00, # 0x34
                       0x00, 0x00, 0x00, 0x00, # 0x38
                       0x00, 0x00, 0x00, 0x00, # 0x3C
                       0x50, 0x52, 0x49, 0x31, # 0x40
                       0x31, 0x00, 0x02, 0x01, # 0x44
                       0x01, 0x04, 0x18, 0x00, # 0x48
                       0x00, 0x85, 0x95, 0x03],# 0x4C
        "device-id" : 0x28,
        "manufacturer-id" : 0x01,       # AMD
        "max-chip-width" : 16,          # 16-bits chip
        "unit-size" : [0x10000 for i in range(31)] + [0x2000 for i in range(8)],
        },
    }


##############################
# End of flash configuration #
##############################

def obj_name(name):
    if len(machine) != 0:
        return machine + name
    else:
        return name

# return 0 if not matching, 1 if matching
def compare_product_no(str1, str2):
    l1 = len(str1)
    l2 = len(str2)
    if l1 != l2:
        return 0
    else:
        for i in range(0,l2):
            if str1[i] != "_" and str1[i] != str2[i]:
                return 0
        return 1
    
def match_product_no(def_list, product_no):
    for p in def_list.keys():
        if compare_product_no(p, product_no):
            return p
    return None


#
# add_flash_memory arguments:
#
# * mandatory arguments
#
#   name:              base name for all objects (flash, ram, image)
#   product_no:        product number, like 28F160C3T
#   interleave:        1,2,4,8
#   bus_width:         8,16,32,64
#   files:             like image file attribute (maybe [])
#   mappings:          [[object, address]*] (maybe [])
#
# * optional arguments:
#   mapping_template   base template to use for mappings, if more values needs
#                      to be filled in
#   ...                attributes set in the generic-flash-memory objects
#
def add_flash_memory(name, product_no, interleave, bus_width, files, mappings,
                     mapping_template = [None, None, 0, 0, None, None],
                     queue = None,
                     accept_inquiries = 0,
                     accept_smaller_reads = 1,
                     accept_smaller_writes = 0,
                     big_endian = 0):

    (list, size) = flash_create_memory(obj_name(name), product_no, interleave,
                                       bus_width, files, queue,
                                       accept_inquiries, accept_smaller_reads,
                                       accept_smaller_writes,
                                       big_endian)
    # add objects to the list
    object_list[machine] += list

    # map the flash where asked to
    for m in mappings:
        map = get_attribute(object_list[machine], obj_name(m[0]), "map")
        # fill the template
        map_entry = mapping_template[:]
        map_entry[0] = m[1]                         # address
        map_entry[1] = OBJ(obj_name(name))          # translator object
        map_entry[4] = size                         # size
        map_entry[5] = OBJ(obj_name(name + "-ram")) # target object
        # set the mapping
        map += [map_entry]
        set_attribute(object_list[machine], obj_name(m[0]), "map", map)

#
# create a list of objects representing the flash memory
# see above function for parameters
#
def flash_create_memory(name, product_no, interleave, bus_width,
                        files = [],
                        queue = None,
                        accept_inquiries = 0,
                        accept_smaller_reads = 1,
                        accept_smaller_writes = 0,
                        big_endian = 0):

    # find the description
    pn = match_product_no(flash_descriptions, product_no)
    if not pn:
        print "add_flash_memory():"
        print ("  No product were found matching the product number '"
               + product_no + "'")
        print ("  It should be one of the following (with '_' replaced by an "
               "appropriate letter or number):")
        print " ", flash_descriptions.keys()
        return

    config = copy.deepcopy(flash_descriptions[pn])
    ret = complete_functions[pn](product_no, config)

    if type(ret) == type(""):
        print "add_flash_memory():"
        print "  " + ret
        return
    else:
        (config, size) = ret

    # compute the total size
    size *= interleave

    # complete the configuration
    config['interleave'] = interleave
    config['bus_width'] = bus_width
    config['accept_inquiries'] = accept_inquiries
    config['accept_smaller_reads'] = accept_smaller_reads
    config['accept_smaller_writes'] = accept_smaller_writes
    config['big_endian'] = big_endian
    config['storage_ram'] = OBJ(name + "-ram")

    return ([OBJECT(name + "-ram", "ram",
                    image = OBJ(name + "-image"))] +
            iff(queue,
                [OBJECT(name + "-image", "image",
                        queue = OBJ(queue),
                        size = size,
                        files = files)] +
                [OBJECT(name,
                        "generic-flash-memory",
                        queue = OBJ(queue),
                        **config)],

                [OBJECT(name + "-image", "image",
                        size = size,
                        files = files)] +
                [OBJECT(name,
                        "generic-flash-memory",
                        **config)]),
            size)

#
# Return the total size in bytes of the memory occupied by the flash system
# (useful for mappings)
#
def flash_get_size(product_no, interleave):
    pn     = match_product_no(flash_descriptions, product_no)
    config = copy.deepcopy(flash_descriptions[pn])
    ret    = complete_functions[pn](product_no, config)

    if type(ret) == type(""):
        print "add_flash_memory():"
        print "  " + ret
        return
    else:
        (config, size) = ret

    size *= interleave

    return size
