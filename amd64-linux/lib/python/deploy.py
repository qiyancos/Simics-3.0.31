import types
import sim_core
import traceback
import sys

def call_module_function(msg):
    try:
        reply = -1

        id = msg[1]
        module = msg[2]
        function = msg[3]

        try:
            exec("import " + module)
        except Exception, e:
            raise Exception("While importing module " + module + ": " + str(e))

        try:
            if not isinstance(eval(module), types.ModuleType):
                raise Exception("There was a variable called \"" + module + \
                    "\", hiding the module with the same name.")
        except NameError:
            raise Exception("The module \"" + module + "\" did not exist.")

        try:
            if not isinstance(eval(module + '.' + function), types.FunctionType):
                raise Exception( \
                    "There is a variable called \"" + function + "\" in module \"" + module + \
                    "\", hiding the specified function with the same name.")
        except NameError:
            raise Exception( \
                "There was no function called called \"" + function + "\" in module \"" + module + \
                "\".")

        reply = eval(module + '.' + function)(*msg[4:])

        sim_core.VT_send_control_msg(["reply", id, reply])
    except Exception, e:
        sim_core.VT_send_control_msg(["exception", id])
        
        traceback.print_exc(None, sys.stdout)

def exec_python(msg):
    try:
        id = msg[1]

        module = msg[2]
        cmd = msg[3]

        if not module == "":
            exec("import " + module)

        exec(cmd)

        sim_core.VT_send_control_msg(["reply", id, 0])
    except Exception, e:
        traceback.print_exc(None, sys.stderr)	
        traceback.print_exc(None, sys.stdout)

        raise e
    
