import types
import sys
from sim_core import *
import sim
import traceback

parent_map = {}

def object_sort_func(a, b):
    return cmp(a.name, b.name)

# The mo_ prefix below stands for "marshalled object", and
# See the marshal_object() function.

def is_component(obj):
    if "component" in dir(obj.iface):
        return 1
    else:
        return 0

def is_toplevel(obj):
    if is_component(obj) and obj.top_level:
        return 1
    else:
        return 0

# Returns the name of a marshalled object
def mo_get_name(marshalled_object):
    for field, value in marshalled_object:
        if field == "name":
            return value
    else:
        raise Exception("marshalled object has no name!")

# Test function; checks if a marshalled objects is a top-level component
def mo_is_toplevel(marshalled_object):
    if not mo_is_component(marshalled_object):
        return False
    
    for field, value in marshalled_object:
        if field == "is_toplevel" and value != 0:
            return True
    else:
        return False

# Test function; checks if a marshalled objects is a component
def mo_is_component(marshalled_object):
    for field, value in marshalled_object:
        if field == "is_component" and value != 0:
            return True
    else:
        return False

def marshal_connection(conn):
    connector, obj, other_end = conn
    return [ connector, obj.name, other_end ]

def marshal_dictionary(d):
    return [ [ k, d[k] ] for k in d.keys() ]

# Connectors is a dictionary of dictionaries
def marshal_connectors(connectors):
    return [ [ k, marshal_dictionary(connectors[k]) ] for k in connectors.keys() ]

def marshal_object(obj):
    if obj is None:
        raise Exception("obj is None in marshal_object()")

    try:
        top_component = obj.top_component.name
    except:
        top_component = ""

    if is_component(obj):
            
        marshalled_object = [ [ 'name', obj.name ],
                              [ 'is_component', 1 ],
                              [ 'classname', obj.classname ],
                              [ 'is_toplevel', is_toplevel(obj) ],
                              [ 'top_component', top_component ],
                              [ 'tooltip', obj.classname ],
                              [ 'object_list',
                                [ confobj.name for confobj in
                                  get_object_list(obj) ]],
                              [ 'connectors',
                                marshal_connectors(obj.connectors) ],
                              [ 'connections',
                                [ marshal_connection(conn)
                                  for conn in obj.connections ]]
                              ]
    else:
        marshalled_object = [ [ 'name', obj.name ],
                              [ 'is_component', 0 ],
                              [ 'classname', obj.classname ],
                              [ 'is_toplevel', 0 ],
                              [ 'top_component', top_component ],
                              [ 'tooltip', obj.classname ] ]

    return marshalled_object


def mo_attr_get_name(marshalled_attr):
    for field, value in marshalled_attr:
        if field == "name":
            return value
    else:
        raise Exception("marshalled attribute has no name")

def marshal_attribute(obj, attr):
    flags = SIM_get_attribute_attributes(obj.classname, attr)
    return [ [ 'name', attr ],
             [ 'flags', flags ] ]

def print_marshalled_object(mobj):
    for attr, val in mobj:
        print attr, "=", val

# Return a list of all the conf-objects belonging to a component
def get_object_list(obj):
    if not is_component(obj):
        return []
    else:
        object_list = filter(None, obj.object_list.values())
        object_list.sort(object_sort_func)
        return object_list

# Return a list of the object's up-connectors
def get_up_connectors(obj):
    if not is_component(obj):
        return []
    else:
        connectors = []
        for name, value in obj.connectors.iteritems():
            if value['direction'] == "up":
                connectors.append(name)
        
        return connectors
                 
# Return a list of the object's down-connectors
def get_down_connectors(obj):
    if not is_component(obj):
        return []
    else:
        connectors = []
        for name, value in obj.connectors.iteritems():
            if value['direction'] == "down":
                connectors.append(name)
        
        return connectors

# Return a list of the object's any-connectors
def get_any_connectors(obj):
    if not is_component(obj):
        return []
    else:
        connectors = []
        for name, value in obj.connectors.iteritems():
            if value['direction'] == "any":
                connectors.append(name)
        
        return connectors

def get_connection_name(conn):
    return conn[0]

def get_connection_object(conn):
    return conn[1]

def get_connection_other_end(conn):
    return conn[2]

# Return a list of those objects which are connected via up-connectors
def get_up_connections(obj):
    if not is_component(obj):
        return []
    else:
        up_connectors = get_up_connectors(obj)
        return [ conn for conn in obj.connections
                 if get_connection_name(conn) in up_connectors ]

# Return a list of those objects which are connected via down-connectors
def get_down_connections(obj):
    if not is_component(obj):
        return []
    else:
        down_connectors = get_down_connectors(obj)
        return [ conn for conn in obj.connections
                 if get_connection_name(conn) in down_connectors ]

# Return a list of those objects which are connected via any-connectors
def get_any_connections(obj):
    if not is_component(obj):
        return []
    else:
        any_connectors = get_any_connectors(obj)
        return [ conn for conn in obj.connections
                 if get_connection_name(conn) in any_connectors ]


def has_up_connections(obj):
    return get_up_connections(obj) != []

def has_down_connections(obj):
    return get_down_connections(obj) != []

def has_any_connections(obj):
    return get_any_connectors(obj) != []


# Return True/False indicating if object a has an up-connection to b
def is_upwards_connected(a, b):
    return b in get_up_connections(a)

# Return True/False indicating if object a has a down-connection to b
def is_downwards_connected(a, b):
    return b in get_down_connections(a)

# Return True/False indicating if object a has an any-connection to b
def is_any_connected(a, b):
    return b in get_any_connections(a)
    

class ProtocolCommand:
    def execute(self, msg):
        """Execute a protocol command, and return the reply."""
        pass

    def handle_command(self, msg):
        """Execute a protocol command, and send the reply back to the
        client."""

        try:
            cmd = msg[0]
            id = msg[1]
            
            reply = self.execute(msg)
            VT_send_control_msg(["reply", id, reply])
            
        except Exception, e:
            traceback.print_exc(None, sys.stderr)
            sys.stderr.write("%s when executing CLP command %s: %s\n" % \
                             (e.__class__, msg, e))
            

class GetObjectsCommand(ProtocolCommand):
    def execute(self, msg):
        objects = sim.objects.values()
        objects.sort(object_sort_func)
        return [ marshal_object(obj) for obj in objects]

class GetAttributesCommand(ProtocolCommand):
    def execute(self, msg):
        _, _, name = msg
        obj = sim.objects[name]
        return [ marshal_attribute(obj, attr) for attr, _, _, _ in obj.attributes ]

class GetDescriptionCommand(ProtocolCommand):
    def execute(self, msg):
        _, _, objectname = msg
        obj = SIM_get_object(objectname)
        classinfo = VT_get_class_info(obj.class_data, 0, 0)
        descr = classinfo[0]

        def marshal_attribute_info(attrinfo):
            name, rw, attrattr, descr, type, indextype = attrinfo
            return [["name", name],
                    ["rw", rw],
                    ["attr", attrattr],
                    ["descr", descr],
                    ["type", type],
                    ["indextype", indextype ]]
                    
        return [descr, [marshal_attribute_info(ai) for ai in \
                        VT_get_all_attributes(obj.class_data, 0, 0) ]]
        
commands = {
    "clp-get-objects" : GetObjectsCommand(),
    "clp-get-attributes" : GetAttributesCommand(),
    "clp-get-descriptions": GetDescriptionCommand(),
    }

             
def dispatch_clp_commands(msg):
    try: 
        cmdname = msg[0]
        commands[cmdname].handle_command(msg)
    except Exception, e:
        traceback.print_exc(None, sys.stderr)
        sys.stderr.write("%s when dispatching CLP command %s: %s\n" % \
                         (e.__class__, msg, e))


# Test functions

failures = []

def test_command(cmd, msg, validator, silent = False):
    global failures
    
    try:
        if not silent:
            print
        print "Testing %s(%s)" % (cmd, msg)
        reply = commands[cmd].execute(msg)
        if not silent:
            print "Validating reply: %s" % (reply)
        result = validator(reply)
        if not result:
            failures += ["%s(%s): validator func %s failed" % (cmd, msg, validator)]
            return False
        else:
            return True
        
    except Exception, e:
        print "Command invocation threw exception:", e
        if not silent:
            traceback.print_exc(file = sys.stderr)
        failures += ["%s(%s): got exception: %s" % (cmd, msg, e)]

    return False
    

def test(silent = False):

    # There is not very much to test at the moment; just make sure the commands
    # don't crash or something.

    def get_objects_validator(reply):
        global failures
        return True

    test_command("clp-get-objects", None,
                 get_objects_validator,
                 silent = silent)

    # object-tests
    for obj in sim.objects.values():
        def get_attributes_validator(reply):
            global failures
            return True

        test_command("clp-get-attributes", [None, 0, obj.name],
                     get_attributes_validator, silent = silent)


    if len(failures) > 0:
        print
        print "There where %d failures:" % len(failures)
        print "=" * 60
        for f in failures:
            print f
    else:
        print
        print "All tests succeeded!"
        print
        
    return len(failures)

        
def on_conf_object_create(_, obj):
    VT_send_control_msg(['clp-object-created', 0, marshal_object(obj)])

SIM_hap_add_callback("Core_Conf_Object_Create", on_conf_object_create, None)

def print_components():
    for comp in [ obj for obj in sim.objects.values() if is_component(obj) ]:
        print
        print comp.name
        print '=' * 80
        
        connector_names = comp.connectors.keys()
        connector_names.sort()
        for conn_name in connector_names:
            connector = comp.connectors[conn_name]
            print "connector    %-15s %-20s %-20s" % (conn_name,
                                                    connector['direction'],
                                                    connector['type'])
            
        print '-' * 80
        for connector, object, other_end in comp.connections:
            print "connection   %-15s %-50s %-10s" % (connector, object, other_end)

        print
