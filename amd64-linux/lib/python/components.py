from cli import *
from sim_core import *
import sim_commands
import re, string
import sim

# TODO: 0-pad connectors for proper sorting

writing_template = False

next_cpu_number = 0
def get_next_cpu_number():
    global next_cpu_number
    tmp = next_cpu_number
    next_cpu_number += 1
    return tmp

def mac_as_list(str):
    try:
        return map(lambda x:int(x, 16), str.split(':'))
    except:
        return []

def mac_from_list(lst):
    try:
        return string.join(map(lambda x: "%02x" % x, lst), ":")
    except:
        return []

def ip_as_list(str):
    try:
        return map(lambda x:int(x), str.split('.'))
    except:
        return []

def ip_from_list(lst):
    try:
        return string.join(map(lambda x: "%d" % x, lst), ".")
    except:
        return []

def convert_name(name, par_str, seq_str):
    name = name.replace('$', seq_str)
    while '(' in name:
        m = re.match('.*?(\(.*?\))', name)
        if not m:
            raise Exception, 'Illegal object name, no matching ) found'
        osub = m.group(1)
        nsub = osub.replace('x', par_str).replace('(', '').replace(')', '')
        try:
            nsub = str(eval(nsub))
        except:
            pass
        name = name.replace(osub, nsub)
    return name

next_nbr = {}

def next_sequence(name):
    # the name is not quaranteed to be unique since the user may create
    # an object with the same name before this one is instantiated, but
    # we avoid the most common collisions here, and handle the rest when
    # the setting the configuration.

    if not next_nbr.has_key(name):
        next_nbr[name] = [0]
    next = next_nbr[name].pop(0)

    while 1:
        unique_name = name + `next`
        if not unique_name in map(lambda x: x.name, SIM_all_objects()):
            break
        next += 1

    if len(next_nbr[name]) == 0:
        next_nbr[name] = [next + 1]
    return next

object_prefix = ''

class pre_obj(pre_conf_object):
    'Generate pre_conf_object with unique name'

    def __init__(self, object_name, class_name):
        object_name = object_prefix + object_name
        pre_conf_object.__init__(self, object_name, class_name)
        self.__sequence_name__ = str(next_sequence(object_name))
        self.__proto_name__ = object_name
        self.__convert_name__('0')

    def __convert_name__(self, parent_name):
        self.name = convert_name(self.__proto_name__,
                                 parent_name,
                                 self.__sequence_name__)

    def rename(self, new_name):
        self.__proto_name__ = new_name
        self.__convert_name__('0')        

class pre_obj_noprefix(pre_obj):
    'Generate pre_conf_object with unique name, no prefix added'

    def __init__(self, object_name, class_name):
        pre_conf_object.__init__(self, object_name, class_name)
        self.__sequence_name__ = str(next_sequence(object_name))
        self.__proto_name__ = object_name
        self.__convert_name__('0')

class object_list(object):
    pass

# map Simics class name to Python class
class_list = {}

def get_component(conf_obj):
    return conf_obj.object_data

def get_class(class_name):
    return class_list[class_name]

class component_object(object):
    # default class variables
    connectors = {}
    # description, class_name
    
    def __init__(self, parse_obj):
        obj = VT_alloc_log_object(parse_obj)
        obj.object_data = self
        self.connections = []
        self.conf = {}
        if not 'top_level' in dir(self):
            self.top_level = False
        self.top_component = None
        self.instantiated = False
        # component_queue is only used to override automatic assignment
        self.component_queue = None
        # queue is temporary and only used to assign obj.queue
        self.queue = None
        self.obj = obj
        self.connector_info = {}
        self.o = object_list()
        self.object_prefix = object_prefix
        self.connection_checked = {}
        if self.top_level:
            self.components = []

    def finalize_instance(self):
        if not self.instantiated:
            # if already instantiated, this is from a checkpoint
            self.add_objects()
        # set the component attribute in all objects
        for obj in self.o.__dict__.values():
            if isinstance(obj, list):
                for o in obj:
                    if o:
                        o.component = self.obj
            else:
                obj.component = self.obj
        self.add_connector_info()
        # check that there is connector_info for all connectors    
        for cnt in self.connectors:
            try:
                self.connector_info[cnt]
            except:
                print ("Missing 'connector_info' for %s:%s"
                       % (self.classname, cnt))

    def delete_instance(self):
        all = []
        for obj in self.o.__dict__.values():
            if isinstance(obj, list):
                all += [o for o in obj if o]
            else:
                all.append(obj)
        for o in all:
            try:
                name = o.name
                SIM_delete_object(o)
            except Exception, msg:
                print "Failed deleting object '%s': %s" % (name, msg)
        return 0

    def get_object_names(self):
        names = []
        for obj in self.o.__dict__.items():
            if isinstance(obj[1], list):
                for idx in range(len(obj[1])):
                    names += [obj[0] + "[%d]" % idx]
                pass
            else:
                names += [obj[0]]
        return names

    def instantiation_done(self):
        # subclass may override this function
        for obj in self.get_object_names():
            if eval('self.o.%s' % obj) == None:
                continue
            exec "self.o.%s = SIM_get_object(self.o.%s.name)" % (obj, obj)
        if self.component_queue:
            self.component_queue = SIM_get_object(self.component_queue.name)
            self.obj.queue = self.component_queue
        else:
            self.obj.queue = self.queue
        # convert pre-obj references in connector-info
        for cnt in self.connector_info:
            val = self.connector_info[cnt]
            if isinstance(val, list):
                for c in range(len(val)):
                    if isinstance(val[c], pre_obj):
                        val[c] = SIM_get_object(val[c].name)
            else: # tuple
                for t in range(len(val)):
                    for c in range(len(val[t])):
                        if isinstance(val[t][c], pre_obj):
                            val[t][c] = SIM_get_object(val[t][c].name)
        self.instantiated = True
    
    def add_objects(self):
        # subclass should override this function
        # NOTE: Note called after loading a checkpoint!
        pass

    def add_connector_info(self):
        print ("Warning: %s does not have any add_connector_info() function"
               % self.obj.name)

    def get_objects(self):
        objs = {}
        for obj in self.get_object_names():
            objs[obj] = eval('self.o.%s' % obj)
        return objs

    def rename_component_objects(self, parent_string):
        for obj in self.get_object_names():
            obj = eval('self.o.%s' % obj)
            if not obj:
                continue
            obj.__convert_name__(parent_string)

    @classmethod
    def get_connectors(self, idx):
        return self.connectors

    def get_connections(self, idx):
        return self.connections

    def set_connections(self, val, idx):
        if self.instantiated:
            # TODO: also check removed connections
            added = [x[0] for x in val if x[0] not in
                     [y[0] for y in self.connections]]
            for cnt in added:
                if not self.connectors[cnt]['hotplug']:
                    SIM_attribute_error("Cannot change non-hotplug connection "
                                        "for instantiated component.")
                    return Sim_Set_Illegal_Value
        self.connections = val
        return Sim_Set_Ok

    def get_object_prefix(self, idx):
        if writing_template:
            return None
        return self.object_prefix

    def set_object_prefix(self, val, idx):
        self.object_prefix = val
        return Sim_Set_Ok

    def get_object_list(self, idx):
        if writing_template:
            return None
        if self.instantiated:
            return self.get_objects()
        else:
            return {}

    def set_object_list(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        for obj in val.items():
            try:
                exec "self.o.%s = obj[1]" % obj[0]
            except:
                # resize list
                try:
                    lst, idx = re.match('(\w+)\[(\d+)\]', obj[0]).group(1,2)
                    exec ("self.o.%s.extend([None] * (%s + 1 -len(self.o.%s)))"
                          % (lst, idx, lst))
                    exec "self.o.%s = obj[1]" % obj[0]
                except Exception, msg:
                    print "Warning: Failed adding '%s' to object list" % obj[0]
        return Sim_Set_Ok

    def get_top_level(self, idx):
        if writing_template:
            # only save 'top-level' in template if different from class default
            if self.top_level != type(self).top_level:
                return self.top_level
            else:
                return None
        return self.top_level

    def set_top_level(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        if (len([x for x in self.connectors.values()
                 if x['direction'] == 'up']) > 0
            and val == True):
            SIM_attribute_error("A top-level component can not have up "
                                "connectors.")
            return Sim_Set_Illegal_Value
        self.top_level = val
        return Sim_Set_Ok

    def get_components(self, idx):
        if writing_template:
            return None
        return self.components

    def set_components(self, val, idx):
        if self.instantiated:
            return Sim_Set_Illegal_Value
        self.components = val
        return Sim_Set_Ok

    def get_cpu_list(self, idx):
        if writing_template:
            return None
        return self.get_processors()

    def set_cpu_list(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        elif hasattr(self, 'set_processors'):
            try:
                self.set_processors(val)
            except Exception, msg:
                SIM_attribute_error(str(msg))
                return Sim_Set_Illegal_Value
        return Sim_Set_Ok

    def get_top_component(self, idx):
        if writing_template:
            return None
        return self.top_component

    def set_top_component(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.top_component = val
        return Sim_Set_Ok

    def get_instantiated(self, idx):
        if writing_template:
            return None
        return self.instantiated

    def set_instantiated(self, val, idx):
        if self.obj.configured:
            return Sim_Set_Illegal_Value
        self.instantiated = val
        return Sim_Set_Ok

def wrap_get_class_attribute(arg, conf_class, idx):
    return arg(idx)

def wrap_get_attribute(arg, obj, idx):
    return arg(get_component(obj), idx)

def wrap_get_ckpt_attribute(arg, obj, idx):
    ret = arg(get_component(obj), idx)
    if writing_template:
        # do not save checkpoint attributes in template
        return None
    return ret

def wrap_set_attribute(arg, obj, val, idx):
    return arg(get_component(obj), val, idx)

def component_new_instance(parse_obj, python_class):
    return get_class(python_class.classname)(parse_obj).obj

def component_finalize_instance(obj):
    get_component(obj).finalize_instance()

def component_delete_instance(obj):
    return get_component(obj).delete_instance()

def connection_used(obj, cnt):
    cnts = [x for x in obj.connections if x[0] == cnt]
    if len(cnts) and not obj.connectors[cnt]['multi']:
        return True
    else:
        return False

def component_basename(cmp_class):
    return get_class(cmp_class).basename

# returns true if two components are connected
def components_connected(src_obj, dst_obj):
    return iff(len([x for x in src_obj.connections if x[1] == dst_obj]), 1, 0)

def connect_error(src, dst, msg):
    print "Cannot connect '%s' to '%s'. %s" % (src, dst, msg)
    SIM_command_has_problem()

def valid_connector(src_cmp, dst_cmp, src_cnt, dst_cnt):
    try:
        src_cmp.connector_info[src_cnt]
        return True
    except:
        connect_error(src_cmp.obj.name, dst_cmp.obj.name,
                      "The '%s' component does not have any '%s' "
                      "connector." % (src_cmp.obj.name, src_cnt))
        return False

def same_connectors(src_cmp, dst_cmp, src_cnt, dst_cnt):
    if (src_cmp.connectors[src_cnt]['type']
        != dst_cmp.connectors[dst_cnt]['type']):
        connect_error(
            src_cmp.obj.name, dst_cmp.obj.name,
            "The '%s' and '%s' connectors are of different types. ('%s' and "
            "'%s')" % (src_cnt, dst_cnt,
                       src_cmp.connectors[src_cnt]['type'],
                       dst_cmp.connectors[dst_cnt]['type']))    
        return False
    else:
        return True

def find_connectors(src_cmp, dst_cmp, src_cnt, dst_cnt, first):
    cnt_type = None
    if src_cnt:
        if not valid_connector(src_cmp, dst_cmp, src_cnt, dst_cnt):
            return (None, None)
        cnt_type = src_cmp.connectors[src_cnt]['type']
    if dst_cnt:
        if not valid_connector(dst_cmp, src_cmp, dst_cnt, src_cnt):
            return (None, None)
        cnt_type = dst_cmp.connectors[dst_cnt]['type']
    if not cnt_type:
        # find connector type found in both components
        possible = []
        for c in src_cmp.connectors:
            if not connection_used(src_cmp.obj, c):
                possible += [(c, x) for x in dst_cmp.connectors
                             if (dst_cmp.connectors[x]['type']
                                 == src_cmp.connectors[c]['type']
                                 and not connection_used(dst_cmp.obj, x))]
        if len(possible) == 0:
            connect_error(src_cmp.obj.name, dst_cmp.obj.name,
                          "No matching connectors found.")            
            return (None, None)
        elif len(possible) > 1 and not first:
            connect_error(src_cmp.obj.name, dst_cmp.obj.name,
                          "More than one matching connector pair.")
            return (None, None)
        possible.sort()
        possible = possible[0:1]
        src_cnt, dst_cnt = possible[0]
    else:
        if src_cnt:
            possible = [x for x in dst_cmp.connectors
                        if (dst_cmp.connectors[x]['type'] == cnt_type
                            and not connection_used(dst_cmp.obj, x))]
        else:
            possible = [x for x in src_cmp.connectors
                        if (src_cmp.connectors[x]['type'] == cnt_type
                            and not connection_used(src_cmp.obj, x))]
    if len(possible) == 0:
        connect_error(src_cmp.obj.name, dst_cmp.obj.name,
                      "The '%s' component does not have any connector of the "
                      "type '%s'." % (iff(src_cnt,
                                          dst_cmp.obj.name,
                                          src_cmp.obj.name), cnt_type))
        return (None, None)
    elif len(possible) > 1 and not first:        
        connect_error(src_cmp.obj.name, dst_cmp.obj.name,
                      "More that one connector of the type %s." % cnt_type)
        return (None, None)
    possible.sort()
    possible = possible[0:1]
    return (iff(src_cnt, src_cnt, possible[0]),
            iff(dst_cnt, dst_cnt, possible[0]))

def connector_expander(string, obj):
    return get_completions(string, [x for x in obj.connectors
                                    if not connection_used(obj, x)])

def disconnect_expander(string, obj):
    return get_completions(string, [x for x in obj.connectors
                                    if connection_used(obj, x)])

def connect_cmd(src_obj, src_cnt, dst_obj, dst_cnt, first = False):
    # allow component only
    if dst_obj == None:
        if src_cnt == None:
            print "No destination component specified."
            SIM_command_has_problem()
            return
        try:
            dst_obj = SIM_get_object(src_cnt)
            SIM_get_interface(dst_obj, 'component')
        except:
            SIM_command_has_problem()
            print "Unknown component '%s'" % src_cnt
            return
        src_cnt = None

    src_cmp = get_component(src_obj)
    dst_cmp = get_component(dst_obj)

    # src_cnt and dst_cnt are optional
    if src_cnt == None or dst_cnt == None:
        src_cnt, dst_cnt = find_connectors(src_cmp, dst_cmp,
                                           src_cnt, dst_cnt, first)
        if src_cnt == None:
            return
    if not valid_connector(src_cmp, dst_cmp, src_cnt, dst_cnt):
        return
    if not valid_connector(dst_cmp, src_cmp, dst_cnt, src_cnt):
        return
    if not same_connectors(src_cmp, dst_cmp, src_cnt, dst_cnt):
        return
    try:
        if connection_used(src_obj, src_cnt):
            raise Exception, ("The '%s' connector of the '%s' component is "
                              "already in use." % (src_cnt, src_obj.name))
        if connection_used(dst_obj, dst_cnt):
            raise Exception, ("The '%s' connector of the '%s' component is "
                              "already in use." % (dst_cnt, dst_obj.name))
    except Exception, msg:
        return connect_error(src_obj.name, dst_obj.name, msg)

    if src_obj.instantiated != dst_obj.instantiated:
        return connect_error(src_obj.name, dst_obj.name,
                             "Both components must be non-instantiated or "
                             "instantiated.")
    if src_obj.instantiated and src_obj.connectors[src_cnt]['hotplug'] == 0:
        return connect_error(src_obj.name, dst_obj.name,
                             "The '%s' connector of the '%s' component "
                             "does not support hot-plugging."
                             % (src_cnt, src_obj.name))
    if dst_obj.instantiated and dst_obj.connectors[dst_cnt]['hotplug'] == 0:
        return connect_error(src_obj.name, dst_obj.name,
                             "The '%s' connector of the '%s' component "
                             "does not support hot-plugging."
                             % (dst_cnt, dst_obj.name))

    # if connector has a check function, call it
    type = src_cmp.connectors[src_cnt]['type']
    if hasattr(src_cmp, 'check_%s' % type.replace('-', '_')):
        if isinstance(dst_cmp.connector_info[dst_cnt], tuple):
            info = dst_cmp.connector_info[dst_cnt][1]
        else:
            info = dst_cmp.connector_info[dst_cnt]
        try:
            f = eval('src_cmp.check_%s' % type.replace('-', '_'))
            arg = [src_cnt] + info
            f(*arg)
        except Exception, msg:
            return connect_error(src_obj.name, dst_obj.name, msg)
    if hasattr(dst_cmp, 'check_%s' % type.replace('-', '_')):
        if isinstance(src_cmp.connector_info[src_cnt], tuple):
            info = src_cmp.connector_info[src_cnt][1]
        else:
            info = src_cmp.connector_info[src_cnt]
        try:
            f = eval('dst_cmp.check_%s' % type.replace('-', '_'))
            arg = [dst_cnt] + info
            f(*arg)
        except Exception, msg:
            return connect_error(src_obj.name, dst_obj.name, msg)
    # update connections attribute
    cnts = src_obj.connections
    cnts += [[src_cnt, dst_obj, dst_cnt]]
    src_obj.connections = cnts
    cnts = dst_obj.connections
    cnts += [[dst_cnt, src_obj, src_cnt]]
    dst_obj.connections = cnts

    # connecting already instantiated components at once
    if src_obj.instantiated:
        finalize_connection(src_cmp, src_cnt, dst_cmp, dst_cnt)
        finalize_connection(dst_cmp, dst_cnt, src_cmp, src_cnt)
        # add new top-component and queue attribute
        for (cmp, cnt) in ((src_cmp, src_cnt), (dst_cmp, dst_cnt)):
            if cmp == src_cmp:
                o_cmp, o_cnt = (dst_cmp, dst_cnt)
            else:
                o_cmp, o_cnt = (src_cmp, src_cnt)
            if ((cmp.connectors[cnt]['direction'] == 'up'
                 or (cmp.connectors[cnt]['direction'] == 'any'
                     and o_cmp.connectors[o_cnt]['direction'] == 'down'))
                and o_cmp.top_component):
                if not cmp.top_component:
                    set_top_component(cmp, o_cmp.top_component)
                    set_queue(cmp,
                              get_component(o_cmp.top_component).get_clock())

def disconnect_cmd(src_obj,  src_cnt, dst_obj, dst_cnt, quiet = False):
    src_cmp = get_component(src_obj)

    # check if src_cnt is connector, or a component-name
    if src_cnt and dst_obj == None:
        try:
            info = src_cmp.connectors[src_cnt]
        except:
            try:
                dst_obj = SIM_get_object(src_cnt)
                src_cnt = None
            except:
                pass

    # if no src_cnt, look for single existing connection
    # or single connection with dst_obj if specified
    if not src_cnt:
        if dst_obj:
            cnts = [x for x in src_obj.connections if x[1] == dst_obj]
        else:
            cnts = [x for x in src_obj.connections]
        if len(cnts) == 0:
            if dst_obj:
                print "No connection with %s exists." % dst_obj.name
            else:
                print "No connections exist."
            SIM_command_has_problem()
            return
        elif len(cnts) > 1:
            if dst_obj:
                print ("More than one connection with %s, please specify "
                       "one." % dst_obj.name)
            else:
                print "More than one connection exist, please specify one."
            SIM_command_has_problem()
            return
        src_cnt = cnts[0][0]
        dst_obj = cnts[0][1]
    try:
        info = src_cmp.connectors[src_cnt]
    except:
        print ("The '%s' component does not have any '%s' connector."
               % (src_obj.name, src_cnt))
        SIM_command_has_problem()
        return
    if info['hotplug'] != True:
        print ("Cannot disconnect '%s' connector that does not support "
               "hotplugging." % src_cnt)
        SIM_command_has_problem()
        return
    cnts = [x for x in src_obj.connections if x[0] == src_cnt]
    if len(cnts) == 0:
        print "The '%s' connector is empty." % src_cnt
        SIM_command_has_problem()
        return
    if dst_obj:
        cnts = [x for x in src_obj.connections if x[1] == dst_obj]
        if len(cnts) == 0:
            print ("The '%s' connector is not connected to the '%s' component."
                   % (src_cnt, dst_obj))
            SIM_command_has_problem()
            return
    if dst_cnt:
        cnts = [x for x in src_obj.connections if x[2] == dst_cnt]
        if len(cnts) == 0:
            print ("The '%s' connector is not connected to a '%s' connector."
                   % (src_cnt, dst_cnt))
            SIM_command_has_problem()
            return
    if len(cnts) > 1:
        print ("The '%s' connector has multiple connections. Specify "
               "destination object and/or connector." % src_obj.name)
        SIM_command_has_problem()
        return
    cnt = cnts[0]
    if not dst_obj:
        dst_obj = cnt[1]
    dst_cmp = get_component(dst_obj)
    if not dst_cnt:
        dst_cnt = cnt[2]

    # update connections attribute
    cnts = src_obj.connections
    cnts.remove([src_cnt, dst_obj, dst_cnt])
    src_obj.connections = cnts
    cnts = dst_obj.connections
    cnts.remove([dst_cnt, src_obj, src_cnt])
    dst_obj.connections = cnts

    # connecting already instantiated components at once
    if src_obj.instantiated:
        destroy_connection(src_cmp, src_cnt, src_cmp.connectors[src_cnt],
                           dst_cmp, dst_cnt)
        destroy_connection(dst_cmp, dst_cnt, dst_cmp.connectors[dst_cnt],
                           src_cmp, src_cnt)
        for (cmp, cnt) in ((src_cmp, src_cnt), (dst_cmp, dst_cnt)):
            if cmp == src_cmp:
                o_cmp, o_cnt = (dst_cmp, dst_cnt)
            else:
                o_cmp, o_cnt = (src_cmp, src_cnt)
            # possibly remove top-component
            if ((cmp.connectors[cnt]['direction'] == 'up'
                 or (cmp.connectors[cnt]['direction'] == 'any'
                     and o_cmp.connectors[o_cnt]['direction'] == 'down'))
                and cmp.top_component == o_cmp.top_component):
                #
                set_new_top_component(cmp, cnt)
    if not quiet:
        print "Disconnected %s:%s from %s:%s" % (src_obj.name, src_cnt,
                                                 dst_obj.name, dst_cnt)

def set_new_top_component(cmp, cnt):
    remove_top_component(cmp)
    # Find a new top-component from other up connector
    for up_cnt in cmp.connectors:
        for c in [x for x in cmp.connections if x[0] == up_cnt]:
            if ((cmp.connectors[up_cnt]['direction'] == 'up'
                 or (cmp.connectors[up_cnt]['direction'] == 'any'
                     and c[1].connectors[c[2]]['direction'] == 'down'))
                and c[1].top_component):
                set_top_component(cmp, c[1].top_component)
                set_queue(cmp,
                          get_component(c[1].top_component).get_clock())
                return

def finalize_connection(src_cmp, src_nm, dst_cmp, dst_nm):
    src_cnt = src_cmp.connectors[src_nm]
    f = eval(('dst_cmp.connect_%s' % src_cnt['type']).replace('-', '_'))
    if isinstance(src_cmp.connector_info[src_nm], tuple):
        arg = [dst_nm] + src_cmp.connector_info[src_nm][0]
    else:
        arg = [dst_nm] + src_cmp.connector_info[src_nm]
    try:
        f(*arg)
    except Exception, msg:
        import traceback
        traceback.print_exc()
        raise CliError("Connect function for '%s' in '%s' returned an error: "
                       "%s." % (src_cnt['type'], dst_cmp.obj.name, msg))

def destroy_connection(src_cmp, src_nm, src_cnt, dst_cmp, dst_nm):
    f = eval(('dst_cmp.disconnect_%s' % src_cnt['type']).replace('-', '_'))
    try:
        f(dst_nm)
    except Exception, msg:
        import traceback
        traceback.print_exc()
        raise CliError("Disconnect function for '%s' in '%s' returned an "
                       "error: %s." % (src_cnt['type'], dst_cmp.obj.name, msg))

def call_connect_cb(cb, src_cmp, src_cnt, dst_cmp, dst_cnt):
    if dst_cmp.connection_checked.get((dst_cnt, src_cmp.obj, src_cnt), 0):
        # already called
        return
    dst_cmp.connection_checked[(dst_cnt, src_cmp.obj, src_cnt)] = 1
    if cb:
        cb(src_cmp, src_cnt, dst_cmp, dst_cnt)

# do not call directly
def component_iterate(cmp, cmp_cb, cnt_cb, first):
    if not first:
        # the first component may have empty up connectors, since this function
        # can start iterating anywhere in the hierarchy
        used_up = []
        for cnt in [x for x in cmp.connectors.items()
                    if x[1]['direction'] == 'up']:
            used_up += [x for x in cmp.connections if x[0] == cnt[0]]

        for cnt in used_up:
            if cmp.connection_checked.get(tuple(cnt), 0) == 0:
                # not all used up connectors initialized yet
                return

    if cmp_cb:
        cmp_cb(cmp)

    # look for incorrectly empty connectors
    reqs = [x for x in cmp.connectors.items() if x[1]['empty_ok'] == 0]
    for req in reqs:
        cnts = [x for x in cmp.connections if x[0] == req[0]]
        if len(cnts) == 0:
            raise Exception, ("The '%s' connector in '%s' can not be empty."
                              % (req[0], cmp.obj.name))

    # always follow connectors going down
    for cnt in [x for x in cmp.connectors.items()
                if x[1]['direction'] == 'down']:
        for c in [x for x in cmp.connections if x[0] == cnt[0]]:
            call_connect_cb(cnt_cb, cmp, cnt[0], get_component(c[1]), c[2])
    # use a set() to make sure we only call each component once
    cmps = []
    for cnt in [x for x in cmp.connectors.items()
                if x[1]['direction'] == 'down']:
        cmps += [x[1] for x in cmp.connections if x[0] == cnt[0]]
    for c in set(cmps):
        component_iterate(get_component(c), cmp_cb, cnt_cb, False)

    # follow 'any' connectors that go down
    for cnt in [x for x in cmp.connectors.items()
                if x[1]['direction'] == 'any']:
        for c in [x for x in cmp.connections if x[0] == cnt[0]]:
            other_cnt = c[1].connectors[c[2]]
            if other_cnt['direction'] == 'up':
                call_connect_cb(cnt_cb, cmp, cnt[0], get_component(c[1]), c[2])
    cmps = []
    for cnt in [x for x in cmp.connectors.items()
                if x[1]['direction'] == 'any']:
        for c in [x for x in cmp.connections if x[0] == cnt[0]]:
            other_cnt = c[1].connectors[c[2]]
            if (other_cnt['direction'] == 'up'
                and (c[1].top_component == None
                     or cmp.top_component == None   # None when removing top
                     or (c[1].top_component == cmp.top_component))):
                cmps.append(c[1])
    for c in set(cmps):
        component_iterate(get_component(c), cmp_cb, cnt_cb, False)

    # do the up connections
    for cnt in [x for x in cmp.connectors.items()
                if x[1]['direction'] == 'up']:
        for c in [x for x in cmp.connections if x[0] == cnt[0]]:
            call_connect_cb(cnt_cb, cmp, cnt[0], get_component(c[1]), c[2])

    # do up connections on any connectors
    for cnt in [x for x in cmp.connectors.items()
                if x[1]['direction'] == 'any']:
        for c in [x for x in cmp.connections if x[0] == cnt[0]]:
            other_cnt = c[1].connectors[c[2]]
            if other_cnt['direction'] == 'down':
                call_connect_cb(cnt_cb, cmp, cnt[0], get_component(c[1]), c[2])

def traverse_components(cmp, cmp_cb, cnt_cb):
    # clear iterator helper dictionary first
    for x in sim.interfaces['component'].objects.values():
        get_component(x).connection_checked = {}
    component_iterate(cmp, cmp_cb, cnt_cb, True)

def find_all_processors(top_cmp):
    """Find all processors in components reachable from the given top
    component (not including processors in the top component itself).
    Return a list with the processors sorted by their processor
    number."""
    processors = set()
    def add_processors(cmp):
        if cmp == top_cmp:
            return
        try:
            processors.update(cmp.get_processors())
        except AttributeError:
            pass # component has no get_processors() method
    def foo(src_cmp, src_nm, dst_cmp, dst_nm):
        print ("src_cmp = %s, src_nm = %s, dst_cmp = %s, dst_nm = %s"
               % (src_cmp, src_nm, dst_cmp, dst_nm))
    def cmp_processors(cpu0, cpu1):
        return cmp(SIM_get_processor_number(cpu0),
                   SIM_get_processor_number(cpu1))
    traverse_components(top_cmp, add_processors, None)
    return list(sorted(processors, cmp = cmp_processors))

def set_recorder(objs):
    # look for an existing recorder, or create a new one
    rec = [x for x in SIM_all_objects() if x.classname == 'recorder']
    if len(rec):
        new_rec = rec[0]
    else:
        rec = [x for x in objs if x.classname == 'recorder']
        if len(rec):
            new_rec = rec[0]
        else:
            new_rec = SIM_create_object('recorder', 'rec0', [])

    ro = [x for x in objs if 'recorder' in sim.classes[x.classname].attributes]
    for o in ro:
        try:
            o.recorder
        except:
            o.recorder = new_rec

def is_standalone(obj):
    # returns true if component may be standalone, not that it actually is
    for i in obj.connectors.values():
        if not i['empty_ok']:
            return 0
    return 1

def set_top_component_cb(x, top):
    if not x.top_component:
        x.top_component = top
        get_component(top).components += [x.obj]

def set_top_component(cmp, top_cmp):
    traverse_components(cmp,  lambda x: set_top_component_cb(x, top_cmp), None)

def remove_top_component_cb(x):
    if x.top_component:
        get_component(x.top_component).components.remove(x.obj)
        x.top_component = None

def remove_top_component(cmp):
    traverse_components(cmp, remove_top_component_cb, None)

some_queue = None

def set_queue_cb(cmp, queue):
    global some_queue
    if cmp.component_queue:
        queue = cmp.component_queue
    if cmp.instantiated:
        cmp.obj.queue = queue
    else:
        cmp.queue = queue
    if not some_queue:
        some_queue = queue
    for o in [x for x in cmp.get_objects().values() if x]:
        if hasattr(o, 'queue') and o.queue:
            pass
        elif o.classname in sim.interfaces['clock'].classes:
            o.queue = o
        else:
            o.queue = queue

def set_queue(cmp, queue):
    traverse_components(cmp, lambda x: set_queue_cb(x, queue), None)

def instantiate_cmd(verbose, cmps):
    if len(cmps) == 0:
        # find all non-instantiated top-level and standalone components
        cmps = [x for x in sim.interfaces['component'].objects.values()
                if not x.instantiated and x.top_level == True]
        alone = [x for x in sim.interfaces['component'].objects.values()
                 if (not x.instantiated and x.top_level == False
                     and is_standalone(x))]
    else:
        alone = []
        ill = ([x for x in cmps
                if not x in sim.interfaces['component'].objects.values()])
        if len(ill):
            print "'%s' is not a component." % ill[0].name
            SIM_command_has_problem()
            return
        ill = [x for x in cmps if x.top_level == False]
        for i in ill[:]:
            # allow stand-alone components to be instantiated
            if is_standalone(i):
                alone.append(i)
                ill.remove(i)
                cmps.remove(i)

        if len(ill):
            print ("'%s' is not a top-level or stand-alone component." %
                   ill[0].name)
            SIM_command_has_problem()
            return

        ill = [x for x in cmps if x.instantiated]
        if len(ill):
            print "Component '%s' is already instantiated." % ill[0].name
            SIM_command_has_problem()
            return

    if len(cmps) == 0 and len(alone) == 0:
        print "No top-level or stand-alone components to instantiate."
        SIM_command_has_problem()
        return

    # cmps only contains top-level components below this point

    all = []
    try:
        for cmp in cmps:
            set_top_component(get_component(cmp), cmp)
        for cmp in cmps:
            traverse_components(get_component(cmp),
                                None, finalize_connection)
            all += map(lambda x: get_component(x),
                       [x for x in cmp.components if not x.instantiated])
    except Exception, msg:
        print "Failed to instantiate components. ", msg
        SIM_command_has_problem()
        return

    # check for alone components if not already in list
    for x in alone[:]:
        if get_component(x) in all:
            alone.remove(x)

    try:
        for cmp in alone:
            # call traverse_components to trigger connections
            traverse_components(get_component(cmp),
                                None, finalize_connection)
            all += [get_component(cmp)]
    except Exception, msg:
        print "Failed to instantiate components. ", msg
        SIM_command_has_problem()
        return

    objs = {}
    for cmp in all:
        for o in cmp.get_objects().values():
            if not o:
                continue
            if o in objs.values():
                # may happen for cross-domain objects, such as links
                continue
            # shouldn't happen often...
            if objs.has_key(o.name) or o.name in sim.objects.keys():
                # a sequence number for the base-name has already been assigned
                # add this as _<number>
                o.rename(o.name + '_$')
                if objs.has_key(o.name) or o.name in sim.objects.keys():
                    raise Exception, ("Failed giving duplicate object a "
                                      "unique name: %s" % o.name)
            objs[o.name] = o

    # make sure all modules are loaded (info in sim namespace)
    # and check that class exist at the same time
    try:
        for o in objs.values():
            SIM_get_class(o.classname)
    except:
        print ("The object '%s' is of unknown class '%s'."
               % (o.name, o.classname))
        SIM_command_has_problem()
        return

    # set recorder if not already set
    set_recorder(objs.values())

    try:
        clocks = sim.interfaces['clock'].classes.keys()
    except Exception, msg:
        print "No clocks defined, cannot set configuration."
        SIM_command_has_problem()
        return

    for cmp in cmps:
        set_queue(get_component(cmp), get_component(cmp).get_clock())
    for cmp in alone:
        # non top-level, assign a dummy queue until inserted into hierarchy
        queue = SIM_next_queue(None)
        if not queue:
            # if instantiating a non top-level on the first instantation try
            # using a queue from the not yet set configuration
            queue = some_queue
        if queue:
            set_queue(get_component(cmp), queue) 

    try:
        SIM_add_configuration(objs, None)
    except Exception, msg:
        print 'Failed setting configuration: ', msg
        SIM_command_has_problem()
        return
    for cmp in all:
        if verbose:
            print "Instantiating:", cmp.obj.name
        cmp.instantiation_done()

def list_cmd(component, short):
    cmps = sim.interfaces['component'].objects.values()
    if component:
        if not component.top_level:
            print '%s is not a top-level component.' % component.name
            SIM_command_has_problem()
            return
        cmps = [x for x in cmps if x.top_component == component]
    for cmp in cmps:
        if cmp.top_component:
            top = cmp.top_component.name
        else:
            top = "none"
        str = '%-28s - %-22s (top: %s)' % (cmp.name, cmp.classname, top)
        print str,
        if not cmp.instantiated:
            print '- not instantiated'
        else:
            print
        if short:
            continue
        print '-' * len(str)
        for cnt in sorted(cmp.connectors.keys()):
            val = cmp.connectors[cnt]
            print "   %-15s %-20s %-8s" % (cnt, val['type'], val['direction']),
            other = [x for x in cmp.connections if x[0] == cnt]
            if len(other) == 0:
                print'<empty>'
                continue
            space = ''
            for oth in other:
                print '%s%s:%s' % (space, oth[1].name, oth[2])
                space = ' ' * 49
        print

def set_prefix_cmd(prefix):
    global object_prefix
    if prefix and not re.match("[a-zA-Z][\w-]*", prefix):
        print "%r is not a valid class name prefix." % prefix
        SIM_command_has_problem()
        return
    object_prefix = prefix

def get_prefix_cmd():
    return object_prefix

def build_create_function(f, cls, args, num):
    arg = sep = ''
    for i in range(num):
        arg += sep + 'x%d' % i
        sep = ', '
    # That we have to use locals() as globals is probably a python bug.
    return eval('lambda %s: f(cls, args%s%s)' % (arg, sep, arg), locals())


def add_component(cls, attrs, x):
    ccls = get_class(cls)
    try:
        base = ccls.basename
    except:
        print 'Component class %s has no base name.' % cls
        base = 'component'
    name = iff(x[0], x[0], get_available_object_name(object_prefix
                                                     + base + '_cmp'))
    obj = pre_conf_object(name, cls)
    for i in range(1, len(attrs)):
        if x[i] != None:
            exec('obj.%s = %s' % (attrs[i], repr(x[i])))
    try:
        SIM_add_configuration({attrs[0] : obj}, None)
    except Exception, msg:
        print 'Failed creating component: ', msg
        SIM_command_has_problem()
        return None
    return name

def create_component_cmd(cls, attrs, *x):
    name = add_component(cls, attrs, x)
    if not name:
        return
    if SIM_is_interactive():
        print "Created non-instantiated '%s' component '%s'." % (cls, name)
    return (name,)

def new_component_cmd(cls, attrs, *x):
    name = add_component(cls, attrs, x)
    if not name:
        return
    instantiate_cmd(False, [SIM_get_object(name)])
    if SIM_is_interactive():
        print "Created instantiated '%s' component '%s'." % (cls, name)
    return (name,)

def object_list_expander(string, comp):
    return get_completions(string, comp.object_list)

def get_object_cmd(comp, obj_name):
    try:
        return eval('get_component(comp).o.%s.name' % obj_name)
    except:
        print 'Component %s contains no object %s' % (comp.name, obj_name)
        SIM_command_has_problem()
        return None

def get_info(obj):
    cnt = []
    for c in sorted(obj.connectors.items()):
        descr = "%-20s %-4s" % (c[1]['type'], c[1]['direction'])
        if c[1]['hotplug']:
            descr += "  hotplug"
        cnt.append((c[0], descr))
    return [("Implementing objects",
             sorted(obj.object_list.items())),
            ("Connectors", cnt)]

def get_status(obj, attributes):
    attrs = []
    for a in attributes:
        attrs.append((a[0], SIM_get_attribute(obj, a[0])))
    status = []
    if len(attrs):
        status += [("Attributes", sorted(attrs))]
    status += [("Connections",
                sorted(map(lambda x: (x[0], x[1].name), obj.connections)))]
    return status

def register_component_class(python_class,
                             attributes, checkpoint_attributes = [],
                             top_level = False):
    class_list[python_class.classname] = python_class
    class_data = class_data_t()
    class_data.new_instance = lambda x: component_new_instance(x, python_class)
    class_data.finalize_instance = component_finalize_instance
    class_data.delete_instance = component_delete_instance
    class_data.description = python_class.description
    if python_class.classname == 'component':
        class_data.parent = 'log-object'
    elif (python_class.classname == 'top-component'
          or top_level == False):
        class_data.parent = 'component'
    else:
        class_data.parent = 'top-component'
    SIM_register_class(python_class.classname, class_data)
    VT_revexec_ignore_class(python_class.classname)
    
    comp_iface = component_interface_t()
    SIM_register_interface(python_class.classname, 'component', comp_iface)

    SIM_register_typed_class_attribute(
        python_class.classname, 'connectors',
        wrap_get_class_attribute, python_class.get_connectors,
        None, None,
        Sim_Attr_Pseudo,
        'D', None,
        'Dictionary of dictionaries with connectors defined by this component '
        'class, indexed by name. Each connector contains the name of the '
        'connector "type", a "direction" ("up", "down" or "any"), a flag '
        'indicating if the connector can be "empty", another flag that is '
        'set if the connector is "hotplug" capable, and finally a flag that '
        'is TRUE if muliple connections to this connector is allowed.')

    SIM_register_typed_attribute(
        python_class.classname, 'object_list',
        wrap_get_attribute, python_class.get_object_list,
        wrap_set_attribute, python_class.set_object_list,
        Sim_Attr_Optional,
        'D', None,
        'Dictionary with objects that the component consists of.')

    SIM_register_typed_attribute(
        python_class.classname, 'object_prefix',
        wrap_get_attribute, python_class.get_object_prefix,
        wrap_set_attribute, python_class.set_object_prefix,
        Sim_Attr_Optional,
        's', None,
        'Object prefix string used by the component. The prefix is typically '
        'set by the <cmd>set-component-prefix</cmd> command before the '
        'component is created.')

    SIM_register_typed_attribute(
        python_class.classname, 'connections',
        wrap_get_attribute, python_class.get_connections,
        wrap_set_attribute, python_class.set_connections,
        Sim_Attr_Optional,
        '[[sos]*]', None,
        'List of connections for the component. The format is a list of '
        'lists, each containing the name of the connector, the connected '
        'component, and the name of the connector on the other component.')

    python_class.top_level = top_level
    if top_level:
        SIM_register_typed_attribute(
            python_class.classname, 'components',
            wrap_get_attribute, python_class.get_components,
            wrap_set_attribute, python_class.set_components,
            Sim_Attr_Optional,
            '[o*]', None,
            'List of components below the the top-level component. This '
            'attribute is not valid until the object has been instantiated.')

        SIM_register_typed_attribute(
            python_class.classname, 'cpu_list',
            wrap_get_attribute, python_class.get_cpu_list,
            wrap_set_attribute, python_class.set_cpu_list,
            Sim_Attr_Optional,
            '[o*]', None,
            'List of all processors below the the top-level component. This '
            'attribute is not valid until the object has been instantiated.')

    SIM_register_typed_attribute(
        python_class.classname, 'top_level',
        wrap_get_attribute, python_class.get_top_level,
        wrap_set_attribute, python_class.set_top_level,
        Sim_Attr_Optional,
        'b', None,
        'Set to TRUE for top-level components, i.e. the root of a hierarchy.')

    SIM_register_typed_attribute(
        python_class.classname, 'top_component',
        wrap_get_attribute, python_class.get_top_component,
        wrap_set_attribute, python_class.set_top_component,
        Sim_Attr_Optional,
        'o', None,
        'The top level component. Attribute is not valid until the component '
        'has been instantiated.')

    SIM_register_typed_attribute(
        python_class.classname, 'instantiated',
        wrap_get_attribute, python_class.get_instantiated,
        wrap_set_attribute, python_class.set_instantiated,
        Sim_Attr_Optional,
        'b', None,
        'Set to TRUE if the component has been instantiated.')

    args_str = "[arg(str_t, 'name', '?')"
    for attr in attributes + checkpoint_attributes:
        #
        # We mark checkpoint attributes as internal, and do not create any
        # command argument for them. When we add template handling, the
        # checkpoint attributes should not be included!
        #
        checkpoint_attribute = attr in checkpoint_attributes
        template_attribute = len(attr) > 4 and attr[4]

        if eval('\"set_%s\" in dir(python_class)' % attr[0]):
            set_function = wrap_set_attribute
            set_arg = eval('python_class.set_%s' % attr[0])
        else:
            # read-only attribute
            set_function = None
            set_arg = None

        flag = attr[1] & Sim_Attr_Flag_Mask

        if checkpoint_attribute:
            if flag == Sim_Attr_Required:
                raise Exception, "Cannot have required checkpoint-attribute."
            attr[1] |= Sim_Attr_Internal

        SIM_register_typed_attribute(
            python_class.classname, attr[0],
            iff (checkpoint_attribute and not template_attribute,
                 wrap_get_ckpt_attribute, wrap_get_attribute),
            eval('python_class.get_%s' % attr[0]),
            set_function, set_arg,
            attr[1],
            attr[2], None,
            attr[3])

        if flag == Sim_Attr_Pseudo or checkpoint_attribute:
            # do not add command arguments
            continue
        
        arg_str = 'arg('
        if attr[2] == 'i' or attr[2] == 'b':
            arg_str += 'int_t, '
        elif attr[2] == 's':
            arg_str += 'str_t, '
        elif attr[2] == 'f':
            arg_str += 'float_t, '
        else:
            raise Exception, "Unsupported attribute type %s." % attr[2]
        arg_str += "'%s'" % attr[0]
        if flag == Sim_Attr_Required:
            pass
        elif flag == Sim_Attr_Optional:
            arg_str += ", '?'"
        else:
            raise Exception, "Unsupported attribute flag %s." % attr[1]
        args_str += ', ' + arg_str + ')'
    args_str += ']'
    attr_list = ['name'] + [x[0] for x in attributes
                            if x[1] & Sim_Attr_Flag_Mask != Sim_Attr_Pseudo]
    
    for c in python_class.connectors:
        name = python_class.connectors[c]['type'].replace('-', '_')
        if not hasattr(python_class, 'connect_%s' % name):
            raise Exception, ("Missing connect function for %s:%s"
                              % (python_class.classname, name))
        if python_class.connectors[c]['hotplug']:
            if not python_class.connectors[c]['empty_ok']:
                raise Exception, ("Hotplug connector %s:%s must be 'empty_ok'."
                                  % (python_class.classname, name))
            if not hasattr(python_class, 'disconnect_%s' % name):
                raise Exception, ("Missing disconnect function for %s:%s"
                                  % (python_class.classname, name))
        
    if not python_class.classname in ['component', 'top-component']:
        new_command('create-%s' % python_class.classname,
                    build_create_function(create_component_cmd,
                                          python_class.classname,
                                          attr_list, len(attr_list)),
                    eval(args_str),
                    type = ["Components"],
                    short = ('create a non-instantiated %s'
                             % python_class.classname),
                    doc = ('Creates a non-instantiated component of the class '
                           '"%s". If <param>name</param> is not specified, '
                           'the component will get a class-specific default '
                           'name. The other arguments correspond to class '
                           'attributes.' %  python_class.classname), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1368")
        add_new = not len([x for x in python_class.connectors.values()
                           if x['empty_ok'] == False])
        if add_new:
            new_command('new-%s' % python_class.classname,
                        build_create_function(new_component_cmd,
                                              python_class.classname,
                                              attr_list, len(attr_list)),
                        eval(args_str),
                        type = ["Components"],
                        short = ('create an instantiated %s'
                                 % python_class.classname),
                        see_also = ['create-%s' % python_class.classname],
                        doc = ('Creates an instantiated component of the '
                               'class "%s". If <param>name</param> is not '
                               'specified, the component will get a '
                               'class-specific default name. The other '
                               'arguments correspond to class attributes.'
                               % python_class.classname), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1384")

    sim_commands.new_info_command(python_class.classname, get_info)
    sim_commands.new_status_command(python_class.classname,
                                    lambda x: get_status(x, attributes))

class component_component(component_object):
    classname = 'component'
    description = 'Base component class, should not be instantiated.'
    
class top_component_component(component_object):
    classname = 'top-component'
    description = 'Base top-level component class, should not be instantiated.'

register_component_class(component_component, [])
register_component_class(top_component_component, [], top_level = True)

new_command('get-component-object', get_object_cmd,
            [arg(str_t, 'object', expander = object_list_expander)],
            short = 'get named object from components',
            namespace = 'component',
            type = ["Components"],
            doc = ('Get the configuration object with name <var>object</var> '
                   'from the component. The objects that a component '
                   'consists of are listed in the <i>object_list</i> '
                   'attribute.'), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1415")

common_connector_docs = (
    'If only a single connector pair on the two components have maching '
    'types, then the connector arguments to the command can be left out. '
    'Similarly it is possible to give a connector name for only one of the '
    'components if there is a single matching connector on the other '
    'component. '
    'The <param>-f</param> flag tells the command to use the first unused '
    'connector (in alphabetic order) if several ones match.')

new_command('connect', connect_cmd,
            [arg(str_t, 'connector', '?', None, expander = connector_expander),
             arg(obj_t('component', 'component'), 'component', '?', None),
             arg(str_t, 'dst-connector', '?', None),
             arg(flag_t, '-f')],
            short = 'connect components',
            namespace = 'component',
            type = ["Components"],
            doc = ('Connects the <i>connector</i> of this component to the '
                   '<i>dst-connector</i> connector of <i>component</i>. '
                   + common_connector_docs), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1434")

new_command('disconnect', disconnect_cmd,
            [arg(str_t, 'connector', '?', None,
                 expander = disconnect_expander),
             arg(obj_t('component', 'component'), 'component', '?', None),
             arg(str_t, 'dst-connector', '?', None)],
            short = 'disconnect component connector',
            namespace = 'component',
            type = ["Components"],
            doc = ('Disconnects the <i>connector</i> from another component '
                   'connector. Connectors can only be disconnected if they '
                   'support hotplugging.'), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1446")

new_command('connect-components', connect_cmd,
            [arg(obj_t('component', 'component'), 'src-component'),
             arg(str_t, 'src-connector', '?', None),
             arg(obj_t('component', 'component'), 'component', '?', None),
             arg(str_t, 'dst-connector', '?', None),
             arg(flag_t, '-f')],
            short = 'connect components',
            type = ["Components"],
            doc = ('Creates a connection between the connectors '
                   '<i>src-connector</i> and <i>dst-connector</i> of the '
                   '<i>src-component</i> and <i>dst-component</i> components. '
                   + common_connector_docs), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1458")

def save_template(filename):
    global writing_template
    writing_template = True
    obj_list = sim.interfaces['component'].objects.values()
    try:
        VT_write_configuration_objects(filename, obj_list)
    except Exception, msg:
        SIM_command_has_problem()
        print "Failed writing component template to file: ", msg
        writing_template = False
        return
    print "Writing component template '%s'." % filename
    writing_template = False

new_command('save-component-template', save_template,
            [arg(filename_t(), 'file')],
            type  = ['Configuration'],
            short = 'save a component configuration template',
            see_also = ['read-configuration', 'write-configuration',
                        'list-components'],
            doc = """
Save a configuration file with only component objects and their connection
information. This template corresponds to an empty machine configuration,
without any software setup. The saved component template can be loaded into
Simics using the <cmd>read-configuration</cmd> command, producing a collection
of non-instantiated components.
""", filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1485")

def import_cmd(module):
    SIM_load_module(module)

def build_import_function(f, module):
    return lambda: f(module)

def register_components(module):
    new_command('import-%s' % module,
                build_import_function(import_cmd, module),
                [],
                short = 'import a component collection',
                type = ["Components"],
                doc = ('Imports all components from the "%s" collection.'
                       % module), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1506")

new_command('instantiate-components', instantiate_cmd,
            [arg(flag_t, '-v'),
             arg(obj_t('component', 'component'), 'component', '*')],
            short = 'instantiate components',
            type = ["Components"],
            doc = ('Instantiates non-instantiated components. '
                   'With no argument, all top-level components are collected '
                   'and instantiated along with all components below '
                   'them. If one or more components are specified as '
                   'arguments, only these and the components below them are '
                   'instantiated. <arg>-v</arg> will make the command '
                   'print the name of the instantiated components.'), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1514")

new_command('list-components', list_cmd,
            [arg(obj_t('component', 'component'), 'component', '?'),
             arg(flag_t, '-s')],
            short = 'list components',
            type = ["Components"],
            doc = ('List existing components with their names, types and '
                   'and connectors. For each connector the destination '
                   'component and connector is printed. If a top-level '
                   '<i>component</i> is specified, only components below it '
                   'in the hierarchy are listed. The -s flags can be used to '
                   'get a short list.'), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1527")

new_command('set-component-prefix', set_prefix_cmd,
            [arg(str_t, 'prefix')],
            short = 'set a prefix for all component names',
            type = ['Components'],
            see_also = ['get-component-prefix'],
            doc = ('Sets a string prefix that will be added to the names of '
                   'all component objects that are created after the '
                   'invocation of this command.'), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1539")

new_command('get-component-prefix', get_prefix_cmd,
            [],
            short = 'get current component name prefix',
            type = ['Components'],
            see_also = ['set-component-prefix'],
            doc = ('Get the current component name prefix.'), filename="/mp/simics-3.0/src/core/common/components.py", linenumber="1548")
