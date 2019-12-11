# support for config objects in Python

import sim_core

all_object_names = []

def new_object(dummy, obj):
    import conf
    setattr(conf, obj.name, obj)
    all_object_names.append(obj.name)

def del_object(dummy, obj, obj_name):
    import conf
    try:
        delattr(conf, obj_name)
        all_object_names.remove(obj_name)
    except:
        print "Failed removing %s from global object list" % obj_name

# put it in a try to get documentation working
try:
    sim_core.SIM_hap_add_callback("Core_Conf_Object_Create", new_object, None)
    sim_core.SIM_hap_add_callback("Core_Conf_Object_Delete", del_object, None)
except NameError:
    pass

# Fill the namespace with existing objects (probably only the sim object)
for obj in sim_core.SIM_all_objects():
    new_object(None, obj)

# Remove our variables from the module namespace
del obj, sim_core, new_object, del_object
