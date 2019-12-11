from sim_core import *

# TODO: wrap haps

# used to remove conf.<obj> object without dereferencing it
class obj_entry:
    def __init__(self, classname, obj):
        self.classname = classname
        self.obj = obj

obj_info = {}

class container(object):
    def __init__(self, classname):
        self.name = classname

class attr_container(object):
    def __init__(self, name):
        self.__class_name = name
    def __setattr__(self, name, val):
        if name[0] == "_":
            self.__dict__[name] = val
        else:
            SIM_set_class_attribute(self.__class_name, name, val)
    def __getattribute__(self, name):
        if name[0] == "_":
            return object.__getattribute__(self, name)
        else:
            return SIM_get_class_attribute(self.__class_name, name)

def add_class_info(class_name):
    classes[class_name] = container(class_name)
    classes[class_name].classattrs = attr_container(class_name)
    classes[class_name].attributes = []
    classes[class_name].objects = {}
    classes[class_name].interfaces = {}
    attrs = VT_get_attributes(class_name)
    for a in attrs:
        aa = SIM_get_attribute_attributes(class_name, a)
        if aa & Sim_Attr_Class:
            classes[class_name].classattrs.__dict__[a] = 0
        else:
            classes[class_name].attributes.append(a)
    ifaces = (VT_get_interfaces(class_name)
              + [x[0] for x in VT_get_port_interfaces(class_name)])
    for i in ifaces:
        if not interfaces.has_key(i):
            interfaces[i] = container(i)
            interfaces[i].name = i
            interfaces[i].classes = {}
            interfaces[i].objects = {}
        interfaces[i].classes[class_name] = classes[class_name]
        try:
            classes[class_name].interfaces[i] = SIM_get_class_interface(class_name, i)
        except:
            continue

def canonicalize_name(name):
    name = name.replace("-", "_")
    name = name.replace("+", "__")
    return name

def wrap_classes():
    global unhandled_classes
    for c in unhandled_classes:
        add_class_info(c)
    unhandled_classes = []

unhandled_classes = list(SIM_all_classes())

def new_object(arg, obj):
    if len(unhandled_classes):
        wrap_classes()
    classes[obj.classname].objects[obj.name] = obj
    for i in classes[obj.classname].interfaces:
        interfaces[i].objects[obj.name] = obj
    objects[obj.name] = obj
    obj_info[obj.name] = obj_entry(obj.classname, obj)

def del_object(arg, null_obj, name):
    # do not dereference obj!
    cl = obj_info[name].classname
    obj = obj_info[name].obj
    del classes[cl].objects[name]
    for i in classes[cl].interfaces:
        del interfaces[i].objects[name]
    del objects[name]
    del obj_info[name]

def new_class(arg, obj, name):
    unhandled_classes.append(name)

def del_class(arg, obj, name):
    if name in unhandled_classes:
        unhandled_classes.remove(name)
    else:
        del classes[name]

def module_loaded(arg, obj, name):
    wrap_classes()

SIM_hap_add_callback("Core_Module_Loaded", module_loaded, None)
SIM_hap_add_callback("Core_Conf_Class_Register", new_class, None)
SIM_hap_add_callback("Core_Conf_Class_Unregister", del_class, None)
SIM_hap_add_callback("Core_Conf_Object_Create", new_object, None)
SIM_hap_add_callback("Core_Conf_Object_Delete", del_object, None)

classes = {}
interfaces = {}
objects = {}
