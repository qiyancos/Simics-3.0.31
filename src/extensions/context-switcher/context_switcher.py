
## context_switcher.py - changes current context depending on target process

##  Copyright 2005-2007 Virtutech AB
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

# MODULE: context-switcher
# CLASS: context-switcher
class_name = "context-switcher"

Core_Trackee_Active = "Core_Trackee_Active"
Core_Trackee_Exec = "Core_Trackee_Exec"

from sim_core import *
import os.path
import re

# Return a function that tests if an object implements the interface
# iface.
def implements_interface(iface):
    def iface_test(obj):
        try:
            SIM_get_interface(obj, iface)
            return 1
        except SimExc_Lookup:
            return 0
    return iface_test

tracker_iface = "tracker"
tracker_unix_iface = "tracker_unix"

object_is_tracker = implements_interface(tracker_iface)
object_is_tracker_unix = implements_interface(tracker_unix_iface)

class switcher_instance:
    def __init__(self, obj):
        obj.object_data = self
        self.obj = obj
        self.tracker = None
        self.tracker_active = False
        self.contexts = {}
        self.exec_watch = {}
        self.default_context = {}
        self.hap_handles = []
    def get_context(self, cpu, tid):
        try:
            return self.contexts[tid]
        except KeyError:
            try:
                return self.default_context[cpu]
            except KeyError:
                return VT_get_primary_context()

def new_instance(parse_obj):
    obj = VT_alloc_log_object(parse_obj)
    switcher_instance(obj)
    return obj

def finalize_instance(obj):
    pass

# Hap handler for the Core_Trackee_Active hap triggered by the
# tracker.
def trackee_active_hap(switch_obj, track_obj, tid, cpu, active):
    if active:
        SIM_log_message(switch_obj, 3, 0, Sim_Log_Info,
                        "Trackee %d active on %s." % (tid, cpu.name))
        cpu.current_context = switch_obj.object_data.get_context(cpu, tid)

# Hap handler for the Core_Trackee_Exec hap triggered by UNIX process
# trackers.
def trackee_exec_hap(switch_obj, track_obj, tid, cpu, bin):
    SIM_log_message(switch_obj, 3, 0, Sim_Log_Info,
                    "Trackee %d executed '%s' on %s." % (tid, bin, cpu.name))
    for b in (bin, re.sub(r'.*/', "", bin)):
        try:
            ctx, cnt = switch_obj.object_data.exec_watch[b]
            switch_obj.object_data.contexts[tid] = ctx
            SIM_log_message(
                switch_obj, 1, 0, Sim_Log_Info,
                ("Context %s is now following trackee %d,"
                 + " since it executed '%s'.") % (ctx.name, tid, bin))
            if cnt != None:
                cnt -= 1
                if cnt > 0:
                    switch_obj.object_data.exec_watch[b] = (ctx, cnt)
                else:
                    del switch_obj.object_data.exec_watch[b]
            return
        except KeyError:
            pass # not watching for this binary

# Update hap handlers, current context and stuff when the switcher
# object's attributes have been changed.
def update(switch_obj):
    switcher = switch_obj.object_data
    tracker = switcher.tracker

    # Remove any old hap handlers.
    for hap, handle in switcher.hap_handles:
        SIM_hap_delete_callback_id(hap, handle)
    switcher.hap_handles = []

    # Install new hap handlers.
    if tracker != None:
        switcher.hap_handles.append((
            Core_Trackee_Active,
            SIM_hap_add_callback_obj(Core_Trackee_Active, tracker, 0,
                                     trackee_active_hap, switch_obj)))
        if len(switcher.exec_watch) > 0:
            switcher.hap_handles.append((
                Core_Trackee_Exec,
                SIM_hap_add_callback_obj(Core_Trackee_Exec, tracker, 0,
                                         trackee_exec_hap, switch_obj)))

    # Update current context for all processors.
    if tracker != None:
        for cpu in tracker.iface.tracker.processor_list(tracker):
            tid = tracker.iface.tracker.active_trackee(tracker, cpu)
            cpu.current_context = switch_obj.object_data.get_context(cpu, tid)

    # Activate or deactivate the process tracker if necessary.
    should_be_active = tracker != None and (len(switcher.contexts) > 0
                                            or len(switcher.exec_watch) > 0)
    if tracker != None:
        if switcher.tracker_active:
            if not should_be_active:
                tracker.iface.tracker.deactivate(tracker)
        else:
            if should_be_active:
                tracker.iface.tracker.activate(tracker)
    switcher.tracker_active = should_be_active

class_data = class_data_t()
class_data.new_instance = new_instance
class_data.finalize_instance = finalize_instance
class_data.kind = Sim_Class_Kind_Session
class_data.description = """
    This object makes sure that certain context objects are active when
    certain simulated processes are active."""
SIM_register_class(class_name, class_data)

def attr_tracker():
    def get(arg, obj, idx):
        return obj.object_data.tracker
    def set(arg, obj, val, idx):
        if val == None or object_is_tracker(val):
            old = obj.object_data.tracker
            if old != val:
                if old != None and obj.object_data.tracker_active:
                    old.iface.tracker.deactivate(old)
                obj.object_data.tracker = val
                update(obj)
            return Sim_Set_Ok
        else:
            return Sim_Set_Illegal_Type
    SIM_register_typed_attribute(
        class_name, "tracker", get, None, set, None,
        Sim_Attr_Session, "o|n", None,
        "Tracker that keeps track of simulated processes.")
attr_tracker()

def attr_contexts():
    def get(arg, obj, idx):
        c = obj.object_data.contexts
        if idx == None:
            return [[k, v] for k, v in c.iteritems()]
        else:
            return c.get(idx, None)
    def set(arg, obj, val, idx):
        if idx == None:
            c = {}
            for k, v in val:
                c[k] = v
            obj.object_data.contexts = c
        else:
            c = obj.object_data.contexts
            if val == None:
                c.pop(idx, None)
            else:
                c[idx] = val
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "contexts", get, None, set, None,
        Sim_Attr_Session | Sim_Attr_Integer_Indexed, "[[i,o]*]", "o|n",
        """Context to use for each tid. tids that are not mapped to a
        context here use the default context. Mapping a tid to Nil
        deletes any mapping from that tid to a context.""")
attr_contexts()

def attr_default_context():
    def get(arg, obj, idx):
        if idx == None:
            return obj.object_data.default_context.items()
        else:
            return obj.object_data.default_context.get(
                SIM_get_object(idx), None)
    def set(arg, obj, val, idx):
        if idx == None:
            obj.object_data.default_context = {}
            for cpu, ctx in val:
                if type(cpu) == str:
                    cpu = SIM_get_object(cpu)
                obj.object_data.default_context[cpu] = ctx
        else:
            obj.object_data.default_context[SIM_get_object(idx)] = val
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "default_context", get, None, set, None,
        Sim_Attr_Session | Sim_Attr_String_Indexed, "[[o|s,o|n]*]", "o|n",
        """List of (<i>cpu</i>, <i>context</i>) pairs, specifying what
        context to use for a processor when no interesting process is
        active.""")
attr_default_context()

def attr_exec_watch():
    def get(arg, obj, idx):
        c = obj.object_data.exec_watch
        if idx == None:
            return [[bin, ctx, cnt] for bin, (ctx, cnt) in c.iteritems()]
        else:
            return list(c.get(idx, None))
    def set(arg, obj, val, idx):
        if idx == None:
            c = {}
            for bin, ctx_cnt in val:
                try:
                    ctx, cnt = ctx_cnt
                except TypeError:
                    ctx = cnt = None
                if ctx != None and (cnt == None or cnt > 0):
                    c[bin] = (ctx, cnt)
            obj.object_data.exec_watch = c
        else:
            c = obj.object_data.exec_watch
            try:
                ctx, cnt = val
                if cnt == None or cnt > 0:
                    c[idx] = (ctx, cnt)
                else:
                    del c[idx]
            except TypeError:
                c.pop(idx, None)
        update(obj)
        return Sim_Set_Ok
    SIM_register_typed_attribute(
        class_name, "exec_watch", get, None, set, None,
        Sim_Attr_Session | Sim_Attr_String_Indexed,
        "[[s,[o,i|n]|n]*]", "[o,i|n]|n",

        """Watch list for the <tt>exec</tt> syscall. This is a map
        from binary name to context object and a counter. When a
        process calls <tt>exec</tt> with a binary that is in this
        watch list, its pid is mapped to the context in the
        <b>contexts</b> attribute, so that the context will follow
        that process. The counter is decremented; when it reaches
        zero, the mapping is deleted from this watch list. (A Nil
        counter makes the mapping last forever.)

        Mapping a binary name to Nil deletes any mapping from that
        binary to a context.""")

attr_exec_watch()

def ifc_temporal_state():
    def finish_restore(obj, state):
        # Update current context of all processors after Hindsight has
        # restored a saved state.
        update(obj)
    tstate_if = temporal_state_interface_t()
    tstate_if.finish_restore = finish_restore
    SIM_register_interface(class_name, "temporal_state", tstate_if)
ifc_temporal_state()

from cli import *
import sim_commands

# status command prints dynamic information
def get_status(obj):
    def get_name(obj):
        if obj == None:
            return "none"
        else:
            return obj.name
    def describe_tid(tid):
        tracker = obj.object_data.tracker
        return tracker.iface.tracker.describe_trackee(tracker, tid)
    return [(None,
             [("Tracker", get_name(obj.object_data.tracker))]),
            ("Contexts for specific trackees",
             [(describe_tid(tid), get_name(ctx)) for (tid, ctx)
              in obj.object_data.contexts.iteritems()]),
            ("Contexts for specific binaries",
             [(bin, get_name(ctx)) for (bin, (ctx, count))
              in obj.object_data.exec_watch.iteritems()]),
            ("Default contexts",
             [(cpu.name, get_name(ctx)) for (cpu, ctx)
              in obj.object_data.default_context.iteritems()])]

sim_commands.new_status_command(class_name, get_status)

def get_context(name):
    try:
        ctx = SIM_get_object(name)
    except:
        ctx = SIM_create_object("context", name, [])
    if ctx.classname == "context":
        return ctx
    else:
        raise SimExc_General("'%s' is not a context" % name)

def cmd_track_pid():
    def cmd(obj, pid, ctx, remove):
        tracker = obj.object_data.tracker
        if not object_is_tracker_unix(tracker):
            print "The attached tracker is not a UNIX process tracker."
            return
        tid = tracker.iface.tracker_unix.pid_to_tid(tracker, pid)
        if remove:
            ctx = None
        else:
            if ctx == None:
                ctx = "pid-%d-context" % pid
            try:
                ctx = get_context(ctx)
            except:
                print "An object called '%s' already exists." % ctx
                return
        obj.contexts[tid] = ctx
        if ctx != None:
            print "Context '%s' is now tracking process %d." % (ctx.name, pid)
        else:
            print "No context is now tracking process %d." % pid
    new_command("track-pid", cmd,
                [arg(int_t, "pid"),
                 arg(str_t, "context", spec = "?", default = None,
                     expander = object_expander("context")),
                 arg(flag_t, "-remove")],
                namespace = class_name,
                see_also = ["<%s>.track-bin" % class_name],
                type = ["Symbolic Debugging", "Debugging"],
                short = "track the process with a given pid",
                doc = """

                Causes the given context to be active when a process
                with the given pid is active; if no context is
                specified, a new one will be created for this purpose.

                If the <tt>-remove</tt> flag is given, any existing
                mapping from this pid will be removed.

                This command requires the attached tracker to be a
                UNIX process tracker.

                """)
cmd_track_pid()

def cmd_track_bin():
    def mangle_name(name):
        bname = os.path.basename(name)
        if bname:
            return re.sub(r'[^a-zA-Z0-9_-]', '-', bname)
        else:
            return "track-bin"
    def cmd(obj, bin, ctx, persistent, remove):
        tracker = obj.object_data.tracker
        if not object_is_tracker_unix(tracker):
            print "The attached tracker is not a UNIX process tracker."
            return
        if remove:
            ctx = None
        else:
            if ctx == None:
                ctx = "%s-context" % mangle_name(bin)
            try:
                ctx = get_context(ctx)
            except:
                print "An object called '%s' already exists." % ctx
                return
        if persistent:
            cnt = None
            cnt_str = "all processes"
        else:
            cnt = 1
            cnt_str = "the first process"
        obj.exec_watch[bin] = [ctx, cnt]
        if ctx != None:
            print (("Context '%s' will be tracking %s\n"
                    + "that executes the binary '%s'.")
                   % (ctx.name, cnt_str, bin))
        else:
            print "Not watching for execution of binary '%s'." % bin
    new_command("track-bin", cmd,
                [arg(str_t, "binary"),
                 arg(str_t, "context", spec = "?", default = None,
                     expander = object_expander("context")),
                 arg(flag_t, "-persistent"),
                 arg(flag_t, "-remove")],
                namespace = class_name,
                see_also = ["<%s>.track-pid" % class_name],
                type = ["Symbolic Debugging", "Debugging"],
                short = "track first use of a given binary",
                doc = """

                After this command is given, the first process that
                makes an <tt>exec</tt> syscall with the given binary
                as argument will be associated to the given context
                just as if the <b>track-pid</b> command had been used.
                If no context is specified, a new one will be created.

                If the <tt>-persistent</tt> flag is given, all
                processes &ndash; not just the first &ndash; that
                <tt>exec</tt> the binary will be associated with the
                context.

                If the <tt>-remove</tt> flag is given, any existing
                mapping from this binary will be removed.

                This command requires the attached tracker to be a
                UNIX process tracker.

                """)
cmd_track_bin()
