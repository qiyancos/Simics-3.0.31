
##  Copyright 2003-2007 Virtutech AB
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

from sim_core import *
from cli import *
from configuration import *
import socket
import string
import sys

if not "object_list" in dir():  object_list = {}
if not "machine_list" in dir(): machine_list = []
if not "conf_list" in dir():    conf_list = []
if not "machine" in dir():      machine = ""
if not "central_queue" in dir(): central_queue = machine + "cpu0"

if not "configuration_loaded" in dir():
    def configuration_loaded(func):
        if SIM_initial_configuration_ok() != 0:
            print ("The function '%s' cannot be used " +
                   "once a configuration is loaded" % func)
            SIM_command_has_problem()
            return 1
        else:
            return 0
        
if not "get_configuration" in dir():
    def get_configuration():
        all_objs = []
        for mach in machine_list:
            machine = mach
            all_objs += object_list[machine]
        return all_objs

if not "set_machine" in dir():
    def set_machine(mach):
        global machine, conf_list
        machine = mach
        try:
            conf_list = object_list[machine]
        except:
            pass

if not "post_configuration" in dir():
    def post_configuration():
        pass

if not "finish_configuration" in dir():
    def finish_configuration():
        if configuration_loaded("finish_configuration"):
            return
        all_objs = get_configuration()
        try:
            SIM_set_configuration(all_objs)
        except Exception, msg:
            print
            print msg
            print
            print "Failed loading the configuration in Simics. This is probably"
            print "due to some misconfiguration, or that some required file is"
            print "missing. Please check the above output for error messages"
            print
            SIM_command_has_problem()
            if VT_remote_control():
                VT_send_control_msg(['startup-failure', 0, str(msg)])
            return
        post_configuration()

def add_clock():
    global machine_list, machine
    machine_list += [machine]
    object_list[machine] = ([OBJECT(machine + "clock", "clock",
                                    queue = OBJ(machine + "clock"),
                                    freq_mhz = 10)])

import os

def get_username():
    try:
        return os.environ['USER']
    except KeyError:
        return "user"

# the socket_name and socket_mode parameters are unused on windows
def add_central(port = 1909,
                socket_name = ("/tmp/simics-central.%s" % get_username()),
                socket_mode = 0666,
                min_latency = 5000000,
                min_processes = 1):
    if configuration_loaded("add_central"):
        return

    # This is the default frequency.  It is set explicitly to document
    # the assumption.
    freq = 1000000000000

    # This is a compatibility interface, where the min_latency is
    # given in nanoseconds, and is actually only half the real
    # min_latency.  Convert it to the new style.
    min_latency = min_latency * 2000

    if not machine in machine_list:
        machine_list.append(machine)
    try:
        object_list[machine]
    except:
        object_list[machine] = []

    if (object_exists(object_list[machine], "central-server") or
        object_exists(object_list[machine], "central-client")):
        return

    if central_setup == "local":
        # We take "local" to mean standard networking setup, but no central
        return

    if central_setup == "exported":
        if sys.platform == "win32":
            object_list[machine] += [OBJECT("central-server", "central-server",
                                            frequency = freq,
                                            min_latency = min_latency,
                                            tcp_port = port),
                                     OBJECT("central-client", "central-client",
                                            server = OBJ("central-server"))]
        else:
            object_list[machine] += [OBJECT("central-server", "central-server",
                                            frequency = freq,
                                            min_latency = min_latency,
                                            tcp_port = port,
                                            unix_socket = socket_name,
                                            unix_socket_mode = socket_mode),
                                     OBJECT("central-client", "central-client",
                                            server = OBJ("central-server")
                                            #server = socket_name
                                            )]
    elif central_setup == "remote":
        pass
    else:
        print "add_central() not supported yet, ignoring"
        return

def add_fc_central():
    # TODO:
    print "add_fc_central() not supported yet, ignoring"
    return
    if configuration_loaded("add_fc_central"):
        return
    if object_exists(object_list[machine], machine + "fc_central"):
        handle_error("Only one fc-central module supported")
        return
    object_list[machine] += ([OBJECT("fc-central", "fc-central",
                                     central = OBJ("central"))])
    modules = get_attribute(object_list[machine], "central", "modules")
    modules += ["fc_central"]
    set_attribute(object_list[machine], "central", "modules", modules)

def add_hulc_central():
    if configuration_loaded("add_hulc_central"):
        return
    if object_exists(object_list[machine], machine + "hulc_central"):
        handle_error("Only one hulc-central module supported")
        return
    object_list[machine] += ([OBJECT("hulc-central", "hulc-central",
                                     central = OBJ("central"))])
    modules = get_attribute(object_list[machine], "central", "modules")
    modules += [OBJ("hulc_central")]
    set_attribute(object_list[machine], "central", "modules", modules)

def add_link_central():
    # TODO:
    print "add_link_central() not supported yet, ignoring"
    return
    if configuration_loaded("add_link_central"):
        return
    if object_exists(object_list[machine], "links"):
        handle_error("Only one link-central module supported")
        return
    object_list[machine] += ([OBJECT("links", "central-links",
                                     central = OBJ("central"))])
    modules = get_attribute(object_list[machine], "central", "modules")
    modules += [OBJ("links")]
    set_attribute(object_list[machine], "central", "modules", modules)

def add_ethernet_net(name = "net0", ip = "10.10.0.0", mask = "255.255.255.0", shared_media = 0):
    try:
        sn_ip = socket.inet_aton(ip)
        # inet_aton is insane on 64-bit host in Python 2.2
        if sys.byteorder == "big":
            sn_ip = sn_ip[-4:-1]
        else:
            sn_ip = sn_ip[0:3]
        sn_ip = socket.inet_ntoa(sn_ip + '\x01')
    except:
        handle_error("Illegal IP address in add_ethernet_net().")
        return
    object_list[machine] += [OBJECT(name, "ethernet-link",
                                    central = iff(object_exists(object_list[machine], "central-client"),
                                                  OBJ("central-client"), None)),
                             OBJECT(name + "_sn", "service-node",
                                    queue = OBJ(central_queue),                                    
                                    routing_table = [[ip, mask, "0.0.0.0", OBJ(name + "_sn_dev")]]),
                             OBJECT(name + "_sn_dev", "service-node-device",
                                    queue = OBJ(central_queue),
                                    link = OBJ(name),
                                    service_node = OBJ(name + "_sn"),
                                    netmask = mask,
                                    ip_address = sn_ip)]

def add_arp(net, ip_addr, eth_addr):
    # Use all service-nodes that we can find. This function is
    # only for bw compatibility anyway.
    sns = []
    for o in object_list[machine]:
        if o[1] == "service-node":
            sns += [o[0]]
    for sn in sns:
        try:
            hosts = get_attribute(object_list[machine], sn, "hosts")
        except:
            hosts = []
        entry = None
        for x in hosts:
            if x[1] == ip_addr:
                entry = x
        if entry:
            entry[0] = eth_addr
        else:
            hosts += [[eth_addr, ip_addr, "unknown", "network.sim"]]
        set_attribute(object_list[machine], sn, "hosts", hosts)

def add_dns(ip, host, domain, ethernet = "ethernet"):
    # Use all service-nodes that we can find. This function is
    # only for bw compatibility anyway.
    sns = []
    for o in object_list[machine]:
        if o[1] == "service-node":
            sns += [o[0]]
    for sn in sns:
        try:
            hosts = get_attribute(object_list[machine], sn, "hosts")
        except:
            hosts = []
        entry = None
        for x in hosts:
            if x[1] == ip:
                entry = x
        if entry:
            entry[1] = ip
            entry[2] = host
            entry[3] = domain
        else:
            hosts += [[None, ip, host, domain]]
        set_attribute(object_list[machine], sn, "hosts", hosts)
