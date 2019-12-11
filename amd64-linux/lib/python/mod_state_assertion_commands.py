from cli import *
from sim_commands import conf_object_expander
import os
import sys

try:
    temp_filename = "/tmp/state-assertion-" + os.environ['USER'] + ".gz"
except:
    temp_filename = "/tmp/state-assertion.gz"

def get_sa_name(name):
    if not name:
            name = "sa0"
            seq = 0
            try:
                while 1:
                    SIM_get_object(name)
                    seq = seq + 1
                    name = "sa%d" % seq
            except:
                pass
    return name

compr_strings = ["guess", "none", "bz2", "gz"]

def compr_expander(string):
    return get_completions(string, compr_strings)

def get_sa_compr(compression):
    if compression == "guess":
        return 0
    elif compression == "no" or compression == "none":
        return 1
    elif compression == "bz2":
        return 2
    elif compression == "gz":
        return 3
    else:
        print "Unknown compression: %s" % compression
        return 0

def get_compr_from_filename(file):
    if (file[-3:] == ".gz"):
        return 3
    elif (file[-4:] == ".bz2"):
        return 2
    else:
        return 1

def state_assertion_cf_common(file, compression, name, align, postev):
    name = get_sa_name(name)

    compr_nb = get_sa_compr(compression)
    if (compr_nb == 0):
        compr_nb = get_compr_from_filename(file)
    sa = SIM_new_object("state-assertion", name)
    print "Creating file '%s' with compression '%s'"%(file, compr_strings[compr_nb])
    sa.create = [file, compr_nb, "", -1, align, postev]
    return sa

# create a new assertion object
def state_assertion_create_file(file, compression, name, align, postev):
    sa = state_assertion_cf_common(file, compression, name, align, postev)
    print sa.name, "created. You probably want to add some objects or memory space now with 'add' and 'add-mem-lis', then run 'start' to begin the assertion process."

new_command("state-assertion-create-file", state_assertion_create_file,
            [arg(filename_t(), "file"),
             arg(str_t, "compression", "?", "guess", expander = compr_expander),
             arg(str_t, "name", "?", ""),
             arg(int_t, "align", "?", 8L),
             arg(int_t, "post_events", "?", 1L)],
            type = "state-assertion commands",
            short = "record a state assertion file",
            doc = """
            This command creates a state assertion file.<br/>
            - <i>file</i> is the name of the file to be created<br/>
            - <i>compression</i> is the compression used (none, bz2, gz)<br/>
            - <i>name</i> is the name of the object to be created. Default is saX where X is a number.
            - <i>align</i> is the alignment of the structures inside the file. It can be useful to set it so that objects saving their state are sure to get correctly aligned structures. Default is 8 which is sufficient for most hosts.
            - <i>post_events</i> tells state-assertion to post events by itself for recording and comparing. Default is true.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="66")

# connect a server to drive a state-assertion
def state_assertion_connect(server, port, compression, align, postev, name):
    name = get_sa_name(name)

    compr_nb = get_sa_compr(compression)
    # no way to guess here, so we just patch
    if (compr_nb == 0):
        compr_nb = 1
    sa = SIM_new_object("state-assertion", name)
    sa.create = ["", compr_nb, server, port, align, postev]
    print name, "connected. You probably want to add some objects or memory space now with 'add' and 'add-mem-lis', then run 'start' to begin the assertion process."
    return sa

new_command("state-assertion-connect", state_assertion_connect,
            [arg(str_t, "server", "?", "localhost"),
             arg(int_t, "port", "?", 6666L),
             arg(str_t, "compression", "?", "none", expander = compr_expander),
             arg(int_t, "align", "?", 8L),
             arg(int_t, "post_events", "?", 1L),
             arg(str_t, "name", "?", "")],
            type = "state-assertion commands",
            short = "connect to a state-assertion receiver",
            doc = """
            This command connects to a state-assertion receiver so that all data
            gathered during the state recording will be sent over to the
            receiver.<br/>
            - <i>server</i> receiver host waiting for the connection<br/>
            - <i>port</i> port number on which the receiver is waiting for a connection<br/>
            - <i>compression</i> is the compression used (none, bz2, gz)<br/>
            - <i>name</i> is the name of the object to be created. Default is saX where X is a number.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="96")

def state_assertion_of_common(file, compression, name, postev):
    name = get_sa_name(name)

    compr_nb = get_sa_compr(compression)
    if (compr_nb == 0):
        compr_nb = get_compr_from_filename(file)
    sa = SIM_new_object("state-assertion", name)
    print "Opening file '%s' with compression '%s'"%(file, compr_strings[compr_nb])
    sa.open = [file, compr_nb, -1, postev]
    return sa

# open a state assertion file
def state_assertion_open_file(file, compression, name, postev):
    sa = state_assertion_of_common(file, compression, name, postev)
    print sa.name, "opened. You should run 'start' to begin the assertion process."

new_command("state-assertion-open-file", state_assertion_open_file,
            [arg(filename_t(exist = 1), "file"),
             arg(str_t, "compression", "?",  "guess", expander = compr_expander),
             arg(str_t, "name", "?", ""),
             arg(int_t, "post_events", "?", 1L)],
            type = "state-assertion commands",
            short = "open a state assertion file for comparing",
            doc = """
            Open a state assertion file to compare it to the current execution.<br/>
            - <i>name</i> is the name of the object. A default name in saX is provided if none is given.<br/>
            - <i>file</i> is the name of the state assertion file<br/>
            - <i>compression</i> is the compression used on the file (none, bz2, gz)
            - <i>post_events</i>
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="131")

def state_assertion_open_server(port, compression, name, postev):
    name = get_sa_name(name)

    compr_nb = get_sa_compr(compression)
    if compr_nb == 0:
        compr_nb = 1
    sa = SIM_new_object("state-assertion", name)
    sa.open = ["", compr_nb, port, postev]
    print name, "connected. You should run start to begin the assertion process."

new_command("state-assertion-receive", state_assertion_open_server,
            [arg(int_t, "port", "?", 6666L),
             arg(str_t, "compression", "?",  "none", expander = compr_expander),
             arg(str_t, "name", "?", ""),
             arg(int_t, "post_events", "?", 1L)],
            type = "state-assertion commands",
            short = "wait for a connection from a state assertion sender",
            doc = """
            Wait for a connection (state-assertion-connect) from a sender. The data received from the sender will be compared against the current execution.<br/>
            - <i>port</i> indicates where simics should wait for the connection<br/>
            - <i>compression</i> is the compression used on the file (none, bz2, gz)
            - <i>name</i> is the name of the object. A default name in saX is provided if none is given.<br/>
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="156")

# add an conf object for assertion
def state_assertion_add_cmd(sa, obj, steps, type, attr):
    sa.add = [obj, steps, type, attr];

new_command("add", state_assertion_add_cmd,
            [arg(str_t, "object-name", expander = conf_object_expander),
             arg(int_t, "steps"),
             arg(int_t, "type", "?", 1),
             arg(str_t, "attribute", "?", "")],
            type = "state-assertion commands",
            short = "add an object to be asserted",
            namespace = "state-assertion",
            doc = """
            Add an object to a state assertion file so its state will be recorded.<br/>
            - <i>obj</i> is the name of the object to be added.<br/>
            - <i>steps</i> is the number of steps between each save.<br/>
            - <i>type</i> is the type of state saved in the file (for devices that provide several, the most complete state is saved by default). IA64 cpus have two states, 1 is system-level, 2 is user-level (without CR, PSR, RR)<br/>
            - <i>attribute</i> is the attribute to save. If specified, the save_state interface is not used and the attribute is saved instead. This is useful for object having no save_state interface.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="174")

# add an conf object for assertion
def state_assertion_add_mem_lis_cmd(sa, memory_space):
    sa.addmemlis = [memory_space]

new_command("add-mem-lis", state_assertion_add_mem_lis_cmd,
            [arg(str_t, "memory_space")],
            type = "state-assertion commands",
            short = "add a memory listener on the specified memory space",
            namespace = "state-assertion",
            doc = """
            Add a memory listener to a memory space so that all memory transactions will be recorded in the file.<br/>
            - <i>memory_space</i> is the name of the memory space  to listen to.<br/>
            - <i>-o</i> allows state-assertion to take over an existing memory hierarchy.<br/>
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="194")





# fforward an assertion file
def state_assertion_ff_cmd(sa, obj, steps):
    sa.fforward = [obj, steps];

new_command("fforward", state_assertion_ff_cmd,
            [arg(str_t, "object-name", expander = conf_object_expander),
             arg(int_t, "steps")],
            type = "state-assertion commands",
            short = "fast-forward a state assertion file when comparing",
            namespace = "state-assertion",
            doc = """
            Fast-forward a state assertion file. The contents of the file are ignored until the object <i>obj</i> has skipped <i>steps</i> steps. The simulation is not fast-forwarded. Other objects in the file are fast-forwarded along.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="213")

# start trace assertion
def state_assertion_start_cmd(sa):
    sa.start = 1

new_command("start", state_assertion_start_cmd,
            [],
            type = "state-assertion commands",
            short = "start trace asserting/comparing",
            namespace = "state-assertion",
            doc = """
            Start the recording/comparison.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="227")

# stop trace assertion
def state_assertion_stop_cmd(sa):
    sa.stop = 1

new_command("stop", state_assertion_stop_cmd,
            [],
            type = "state-assertion commands",
            short = "stop trace asserting/comparing and close the file",
            namespace = "state-assertion",
            doc = """
            Stop the recording/comparison, flush the buffers and close the file.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="240")

# stop trace assertion
def state_assertion_info_cmd(sa):
    sa.info = 1

new_command("info", state_assertion_info_cmd,
            [],
            type = "state-assertion commands",
            short = "provide information about the state assertion",
            namespace = "state-assertion",
            doc = """
            Describe the state assertion performed by the current object.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="253")


# stop trace assertion
def state_assertion_status_cmd(sa):
    sa.status = 1

new_command("status", state_assertion_status_cmd,
            [],
            type = "state-assertion commands",
            short = "provide the status of the current state assertion",
            namespace = "state-assertion",
            doc = """
            Describe the status of the state assertion performed by the
            current object.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="267")

# simple record
def state_assertion_record(file, compression, object, steps, type):
    sa = state_assertion_cf_common(file, compression, "", 8, 1)
    state_assertion_add_cmd(sa, object, steps, type, "")
    state_assertion_start_cmd(sa)

new_command("state-assertion-simple-record", state_assertion_record,
            [arg(str_t, "file", "?", temp_filename),
             arg(str_t, "compression", "?",  "guess", expander = compr_expander),
             arg(str_t, "object-name", "?", "cpu0",
                 expander = conf_object_expander),
             arg(int_t, "steps", "?", 1),
             arg(int_t, "type", "?", 1)],            
            type = "state-assertion commands",
            short = "record the state of an object every x steps",
            doc = """
Create a file (by default /tmp/state-assertion-$USER.gz) and save the state
of <i>object</i> every <i>steps</i> steps. You just have to run 'c' afterwards
to begin the recording.<br/> <i>object</i> is the simics object whose state
will be recorded. <i>steps</i> is the number of steps
between each state recording (default is 1).""", filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="283")

# simple assert
def state_assertion_assert(file, compression, post):
    sa = state_assertion_of_common(file, compression, "", post)
    state_assertion_start_cmd(sa)

new_command("state-assertion-simple-assert", state_assertion_assert,
            [arg(filename_t(), "file", "?", temp_filename),
             arg(str_t, "compression", "?",  "guess", expander = compr_expander),
             arg(int_t, "post_event", "?", 1)],
            type = "state-assertion commands",
            short = "assert the file",
            doc = """
            This command asserts the current run against the file. You just have to run 'c' afterwards to begin the assertion process.
            """, filename="/mp/simics-3.0/src/extensions/state-assertion/commands.py", linenumber="304")
