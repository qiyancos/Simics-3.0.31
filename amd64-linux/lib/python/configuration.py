from sim_core import *
from cli import *
# some old scripts expects get_next_cpu_number in this module
from components import get_next_cpu_number

def canon_name(name, is_substring = 0, check_valid = 1):
    name = name.replace("__", "_") # obsolete
    name = name.replace("-", "_")

    if not check_valid:
        return name
    
    if not is_substring:
        if not name[:1].isalpha():
            raise Exception, "Illegal attribute name: '%s'" % name

    for n in range(len(name)):
        # Allow $ for components
        if not name[n] in "_$" and not name[n].isalnum():
            raise Exception, "Illegal attribute name: '%s'" % name

    return name

def OBJECT(name, objclass, **attrs):
    name = canon_name(name)
    a = []
    for k in attrs.keys():
        a.append([canon_name(k), attrs[k]])
    return [name, objclass] + a

def get_attribute(config, objname, attrname):
    objname = canon_name(objname)
    attrname = canon_name(attrname)
    
    for obj in config:
        if obj[0] == objname:
            for attr in obj[2:]:
                if attr[0] == attrname:
                    return attr[1]
            raise Exception, ("Attribute '%s' not found in object '%s'"
                              % (attrname, objname))
    raise Exception, "Object '%s' not found" % objname

def set_attribute(config, objname, attrname, new_value):
    objname = canon_name(objname)
    attrname = canon_name(attrname)
    for obj in config:
        if obj[0] == objname:
            for attr in obj[2:]:
                if attr[0] == attrname:
                    attr[1] = new_value
                    return
            obj.append([attrname, new_value])
            return
    raise Exception, "Object '%s' not found" % objname

def remove_attribute(config, objname, attrname):
    objname = canon_name(objname)
    attrname = canon_name(attrname)
    for obj in config:
        if obj[0] == objname:
            for n in range(2, len(obj)):
                if obj[n][0] == attrname:
                    obj.pop(n)
                    return
            return
    raise Exception, "Object '%s' not found" % objname

# Return list of object names for given class name. An empty list is
# returned if no objects were found.
def class_objects(config, classname):
    return [x[0] for x in config if x[1] == classname]

# Return 1 if given attribute name exists in given object name.
def has_attribute(config, objname, attrname):
    objname = canon_name(objname)
    attrname = canon_name(attrname)
    
    for obj in config:
        if obj[0] == objname:
            for attr in obj[2:]:
                if attr[0] == attrname:
                    return 1
            return 0
    return 0

def object_exists(config, objname):
    objname = canon_name(objname)
    for obj in config:
        if obj[0] == objname:
            return 1
    return 0

def object_substr_exists(config, obj_substr):
    for obj in config:
        if obj[0][:len(obj_substr)] == obj_substr:
            return 1
    return 0

# local
def write_attr_value(file, val):
    if isinstance(val, type(1)) or isinstance(val, type(1L)):
        file.write("0x%x" % val)
    elif isinstance(val, type(1)) or isinstance(val, type(1.0)):
        file.write("%f" % val)
    elif isinstance(val, type("abc")):
        file.write('"%s"' % val)
    elif isinstance(val, type([])):
        file.write("(")
        for i in range(0, len(val)):
            write_attr_value(file, val[i])
            if i != len(val) - 1:
                file.write(", ")
        file.write(")")
    elif isinstance(val, OBJ):
          file.write(canon_name(val.__conf_object_attribute__))
    elif val == None:
        file.write("Nil")
    else:
        raise Exception, "Unimplemented attribute type: " + repr(val)
                
def write_configuration(conf, file):
    file = open(file, "w")
    for i in conf:
        file.write("OBJECT %s TYPE %s {\n" % (i[0], i[1]))
        for j in i[2:]:
            file.write("\t%s: " % j[0])
            write_attr_value(file, j[1])
            file.write("\n")
        file.write("}\n")
    file.close()

#local
def rename_obj_in_list(attr_list, old_name, new_name):
    for i in range(0, len(attr_list)):
        if isinstance(attr_list[i], type([])):
            rename_obj_in_list(attr_list[i], old_name, new_name)
        elif (type(attr_list[i]) == type('')
              and canon_name(attr_list[i], check_valid = 0) == old_name):
            attr_list[i] = new_name
        elif (isinstance(attr_list[i], OBJ)
              and canon_name(attr_list[i].__conf_object_attribute__, check_valid = 0) == old_name):
            attr_list[i] = OBJ(new_name)

def rename_object(conf, old_name, new_name):
    old_name = canon_name(old_name)
    new_name = canon_name(new_name)
    
    for i in conf:
        if canon_name(i[0]) == old_name:
            i[0] = new_name
        for j in range(2, len(i)):
            if isinstance(i[j], type([])):
                rename_obj_in_list(i[j], old_name, new_name)
            elif (type(i[j]) == type('')
                  and canon_name(i[j], check_valid = 0) == old_name):
                i[j] = new_name
            elif (isinstance(i[j], OBJ)
                  and canon_name(i[j].__conf_object_attribute__, check_valid = 0) == old_name):
                i[j] = OBJ(new_name)

def delete_object(config, objname):
    objname = canon_name(objname)
    for obj in config:
        if obj[0] == objname:
            config.remove(obj)
    return 0

def set_configuration(object_list):
    sims = []
    for obj in object_list:
        if obj[0] == "sim":
            sims.append(obj)
    # move attributes of all sim objects to the first one
    if len(sims) > 1:
        for obj in sims[1:]:
            for attr in range(2, len(obj)):
                set_attribute(object_list, "sim", obj[attr][0], obj[attr][1])
            object_list.remove(obj)
    try:
        SIM_set_configuration(object_list)
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

def configuration_error(msg):
    print
    print "Configuration error:"
    print
    print msg
    print
    SIM_command_has_problem()
    if VT_remote_control():
        VT_send_control_msg(['startup-failure', 0, str(msg)])

def get_conf_object_name(conf_obj):
    if "__conf_object_attribute__" in dir(conf_obj):
        return conf_obj.__conf_object_attribute__
    elif type(conf_obj) == type(""):
        print "Warning: get_conf_object_name() called with string: %s" % conf_obj
        return conf_obj
    else:
        print "Error, get_conf_object_name requires an object"
        return ""

class OBJ:
    def __init__(self, name):
        self.__conf_object_attribute__ = name
    def __repr__(self):
        return "OBJ('%s')" % self.__conf_object_attribute__

class DATA:
    def __init__(self, size, filename, offset):
        self.__data_attribute__ = (size, filename, offset)
    def __repr__(self):
        return "DATA(0x%x, '%s', 0x%x)" % self.__data_attribute__

class FLOAT:
    def __init__(self, float_string):
        self.__float_attribute__ = float_string
    def __repr__(self):
        return "FLOAT('%s\')" % self.__float_attribute__

def convert_attr(objs, attr):
    if type(attr) == type([]):
        for a in range(len(attr)):
            attr[a] = convert_attr(objs, attr[a])
    elif isinstance(attr, OBJ):
        name = attr.__conf_object_attribute__.replace('-', '_')
        if not objs.has_key(name):
            raise 'ERROR: Reference to unknown object: %s' % name
        attr = objs[name]
    return attr

# used by e.g. load-persistent-state
def convert_to_pre_objects(old_objs, obj_type = pre_conf_object):
    objs = {}
    for oo in old_objs:
        objs[oo[0]] = obj_type(oo[0], oo[1])
    for oo in old_objs:
        o = objs[oo[0]]
        for a in oo[2:]:
            attr = convert_attr(objs, a[1])
            exec "o.%s = attr" % a[0]
        objs[oo[0]] = o
    return objs
