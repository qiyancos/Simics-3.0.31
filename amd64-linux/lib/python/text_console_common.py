# Common functions for the text-console modules

from cli import *

# may only be called from script branch
def wait_for_string(obj, str):
    obj.break_string = str
    # get break id at once
    break_id = obj.break_string_id[str]
    wait_for_obj_hap("Xterm_Break_String", obj, break_id)
    obj.unbreak_id = break_id
