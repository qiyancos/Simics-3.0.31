import sys
import string
import re
import os
import thread
import types

from sim_core import *
import conf

try:
    import pwd
    _use_pwd = 1
except:
    _use_pwd = 0

# os.altsep is, contrary to documentation, always None
if sys.platform == 'win32':
    _altsep = "/"
else:
    _altsep = None

if 'posix' in sys.builtin_module_names:
    _case_sensitive_files = 1
else:
    _case_sensitive_files = 0

# Redirect python output
class simics_stdout_class:
    def write(self, str):
        VT_write(str, 0)
    def flush(self):
        SIM_flush()

stderr = sys.stderr
sys.stdout = sys.stderr = simics_stdout_class()

# OBSOLETE
ask_for_expander = "expander"
ask_for_description = "description"

_terminal_width = 80
_terminal_height = 24

def terminal_width():
    return _terminal_width

def terminal_height():
    return _terminal_height

def define_float_re():
    dec = r'(\d*\.\d+|\d+\.)([eE][+-]?\d+)?'
    # Python can't parse hex floating-points on Solaris, bug #2868
    # hex = r'0[xX]([\da-fA-F]*\.[\da-fA-F]+|[\da-fA-F]+\.?)[pP][+-]?\d+'
    # return re.compile(r'[+-]?(' + dec + '|' + hex + ')')
    return re.compile(r'[+-]?(' + dec + ')')

whitespace = string.whitespace
whitespace = whitespace.replace('\n', '')
letters = string.ascii_letters
alnum_tab = string.ascii_letters + string.digits + "\a" + "."
re_match = re.match
float_regexp = define_float_re()

deprecated_warned = {}

#
# Routines for converting numbers to strings and back again, with
# settable radix
#
_radix_idx = {2 : 0, 8 : 1, 10 : 2, 16 : 3}

def set_output_radix(rad, group = 0, do_change = 1):
    if rad != 2 and rad != 8 and rad != 10 and rad != 16:
        raise ValueError, "The radix must be either 2, 8, 10, or 16."
    if group < 0:
        raise ValueError, "The digit grouping must be >= 0."
    if do_change:
        conf.prefs.output_radix = rad
    og = conf.prefs.output_grouping
    og[_radix_idx[rad]] = group
    conf.prefs.output_grouping = og
    
def get_output_radix():
    return conf.prefs.output_radix

def get_output_group(radix = -1):
    if radix < 0:
        radix = get_output_radix()
    return conf.prefs.output_grouping[_radix_idx[radix]]

#
# Return a tuple (sign, abs) where sign is either the empty string or
# the string "-" for negative val's. abs is the absolute value of val.
#
def de_sign(val, radix = -1):

    if radix < 0:
        radix = get_output_radix()

    if val < 0:
        if val > -0x8000000000000000 and radix != 10:
            val = val + 0x10000000000000000
            return ("", val)
        return ("-", -val)
    return ("", val)

def number_group(prefix, str, group):
    if group == 0:
        return str
    n = len(str)
    while 1:
        n -= group
        if n <= 0:
            break
        str = str[:n] + '_' + str[n:]

    if prefix:
        while n < 0:
            n += 1
            str = '0' + str
    return str

def number_to_binary(val):
    res = ""
    
    while val > 0:
        if val & 1:
            res = "1" + res
        else:
            res = "0" + res
        val = val >> 1

    return res

# <add-fun id="simics api python">
# <short>return a ready-to-print representation of a number</short>
# <namespace>cli</namespace>
#
# Return a ready-to-print representation of the number <param>val</param>
# in a given base (<param>radix</param>)
# or the current base by default&mdash;following the current settings for
# number representation.
#
# <di name="RETURN VALUE">A string representing the number.</di>
# </add-fun>
def number_str(val, radix = -1):
    if radix < 0:
        radix = get_output_radix()
    prefix = ''
    
    (sign, val) = de_sign(val, radix)

    if val == 0:
        res = "0"
    elif radix == 2:
        res = number_to_binary(val)
        prefix = '0b'
    elif radix == 8:
        res = "%o" % val
        prefix = "0o"
    elif radix == 16:
        res = "%x" % val
        prefix = "0x"
    else:
        res = "%d" % val
    if res[-1] == 'L':
        res = res[:-1]

    return sign + prefix + number_group(prefix, res, get_output_group(radix))

class CliException(Exception):
    def value(self):
        if self.args:
            (val,) = self.args
            return val
        else:
            return '[Exception without args]'
class CliError(CliException): pass
class CliTabComplete(CliException): pass
class CliSyntaxError(CliException): pass
class CliTypeError(CliException): pass
class CliParseError(CliException): pass
class CliParseErrorInDocText(CliException): pass
class CliErrorInPolyToSpec(CliException): pass
class CliArgNameError(CliException): pass
class CliOutOfArgs(CliException): pass
class CliAmbiguousCommand(CliException): pass

#
# Reads a number in base base from string text
# returns number and parsed chars in a tuple
# valid is valid characters for base
# Throws cliSyntaxError exception
#
def get_base_integer(text, base, valid, type):
    num = 0l
    len = 0
    for c in text:
        if c == '_':
            len += 1
            continue
        pos = string.find(valid, c)
        if pos == -1:
            if c not in whitespace and c in alnum_tab:
                raise CliSyntaxError, ("illegal character '"
                                       + c +"' in " + type + " number")
            break
        len = len + 1
        num = num * base + pos
    if len == 0:
        raise CliTypeError, "empty " + type + " integer"
    return (num, len)

#
# Reads an integer from text in some supported base.
# Supported bases are 2, 8, 10 and 16 and each base has
# a special prefix. "0b" for binary, "0o" for octal and
# "0x" for hexadecimal. Decimal numbers has no prefix.
# Throws cliSyntaxError exception.
#
def get_integer(text):
    len = 0
    if text == "":
        raise CliTypeError, "empty integer"
    if text[:2] == "0x":
        base = 16
        valid = "0123456789abcdef"
        type = "hexadecimal"
        len = 2
    elif text[:2] == "0b":
        base = 2
        valid = "01"
        type = "binary"
        len = 2
    elif text[:2] == "0o":
        base = 8
        valid = "01234567"
        type = "octal"
        len = 2
    elif text[0] in "0123456789":
        base = 10
        valid = "0123456789"
        type = "decimal"
    else:
        raise CliTypeError, "Unknown integer type"

    (num, pos) = get_base_integer(string.lower(text[len:]), base, valid, type)
    return (num, len + pos)

def iff(exp, a, b):
    if exp:
        return a
    else:
        return b

# Check if alias
def isalias(cmd, name):
    return name in get_alias(cmd)


#
# <add id="cli argument types">
# <name>str_t</name>
# Accepts any one word or quoted string.
# </add>
#
def str_t(tokens):
    if istoken(tokens[0], "str"):
        return (tokens[0][1], 1)
    elif istoken(tokens[0], "int"):
        return (str(tokens[0][1]), 1)
    raise CliTypeError, "not a string"

#
# <add id="cli argument types">
# <name>int_t</name>
# Accepts any integer (regardless of size).
# </add>
#
def int_t(tokens):
    if istoken(tokens[0], "int"):
        return (tokens[0][1], 1)
    raise CliTypeError, "not an integer"

#
# <add id="cli argument types">
# <name>range_t(min, max, desc, positive = 0)</name>
# Returns an argument which accepts any integers <i>x</i>, such that
# <math><i>min</i> &lt;= <i>x</i> &lt;= <i>max</i></math>. <i>desc</i>
# is the string returned as a description of the argument.
#
# If <i>positive</i> is true, any negative values will be "cast" into
# positive ones using the formula <math><i>max</i> + <i>v</i> +
# 1</math>, where <i>v</i> is the negative value.
# </add>
#
def range_t(min, max, desc, positive = 0):
    def __range_t(tokens):
        if tokens == ask_for_description:
            return desc
        if tokens == ask_for_expander:
            return None
        if not istoken(tokens[0], "int"):
            raise CliTypeError, "not an integer"
        val = tokens[0][1]
        if val < min or val > max:
            val %= (max + 1)
        if positive and val < 0:
            return (max + val + 1, 1)
        return (val, 1)
    return __range_t

__int64_max  = 0x7fffffffffffffff
__uint64_max = 0xffffffffffffffff
__int64_min  = -__int64_max - 1
__int32_max  = 0x7fffffff
__int32_min  = -__int32_max - 1
__uint32_max = 0xffffffff
#
# <add id="cli argument types">
# <name>int64_t</name>
# Accepts any integer that fits in 64 bits (signed or unsigned). The
# value passed to the command function is the value cast to unsigned.
# </add>
#
int64_t = range_t(__int64_min, __uint64_max, "a 64-bit integer", positive = 1)

#
# <add id="cli argument types">
# <name>sint64_t</name>
# Accepts any signed integer that fits in 64 bits.
# </add>
#
sint64_t = range_t(__int64_min, __int64_max, "a 64-bit signed integer")

#
# <add id="cli argument types">
# <name>uint64_t</name>
# Accepts any unsigned integer that fits in 64 bits.
# </add>
#
uint64_t = range_t(0L, __uint64_max, "a 64-bit unsigned integer")

#
# <add id="cli argument types">
# <name>int32_t</name>
# Accepts any integer that fits in 32 bits (signed or unsigned). The
# value passed to the command function is cast into an unsigned value.
# </add>
#
int32_t = range_t(__int32_min, __uint32_max, "a 32-bit integer", positive = 1)

#
# <add id="cli argument types">
# <name>sint32_t</name>
# Accepts any signed integer that fits in 32 bits.
# </add>
#
sint32_t = range_t(__int32_min, __int32_max, "a 32-bit signed integer")

#
# <add id="cli argument types">
# <name>uint32_t</name>
# Accepts any unsigned integer that fits in 32 bits.
# </add>
#
uint32_t = range_t(0L, __uint32_max, "a 32-bit unsigned integer")

#
# <add id="cli argument types">
# <name>integer_t</name>
# Accepts any integer that fits in 64 bits (signed or
# unsigned). Corresponds to the Simics API's integer_t.
# </add>
#
integer_t = int64_t

#
# <add id="cli argument types">
# <name>float_t</name>
# Accepts floating-point numbers.
# </add>
#
def float_t(tokens):
    t = tokens[0]
    if istoken(t, "float"):
        return (t[1], 1)
    elif istoken(t, "int"):
        return (float(t[1]), 1)
    else:
        raise CliTypeError, "not a float"

def float_arg(tokens):
    float_t(tokens)

#
# FLAG (this should never be called)
#
def flag(tokens):
    if istoken(tokens[0], "flag"):
        return (1,1)
    else:
        raise CliTypeError

def flag_t(tokens):
    if istoken(tokens[0], "flag"):
        return (1,1)
    else:
        raise CliTypeError

#
# <add id="cli argument types">
# <name>addr_t</name>
# Accepts a target machine address, optionally with an address space
# prefix, such as <tt>v:</tt> for virtual addresses or <tt>p:</tt> for
# physical.
# </add>
#
def addr_t(tokens):
    if istoken(tokens[0], "addr"):
        if istoken(tokens[1], "int"):
            addr = tokens[1][1]
            if addr < 0:
                raise CliTypeError, "addresses cannot be negative"
            elif addr > __uint64_max:
                raise CliTypeError, "addresses must fit in 64 bit integers"
            return ((tokens[0][1], addr), 2)
        else:
            raise CliSyntaxError, "address had prefix but no number"
    elif istoken(tokens[0], "int"):
        addr = tokens[0][1]
        if addr < 0:
            raise CliTypeError, "addresses cannot be negative"
        elif addr > __uint64_max:
            addr &= 0xffffffffffffffff
        return (("", addr), 1)
    else:
        raise CliTypeError, "not an address"

def addr(tokens):
    return addr_t(tokens)

# <add id="cli argument types">
# <name>filename_t(dirs = 0, exist = 0, simpath = 0)</name>
# Generator function for filename arguments. If the <i>dirs</i>
# argument is zero (which is default), no directories will be
# accepted. The <i>exist</i> flag, when set, forces the file to
# actually exist. If <i>simpath</i> is true, files will be checked for
# existence using <tt>SIM_lookup_file()</tt>, searching the Simics
# search path. <i>simpath</i> implies <i>exist</i>. On Windows, if Cygwin path
# conversion is performed (see <tt>SIM_native_path()</tt> for details), the
# filename will be converted to host native format.
# </add>
def filename_t(dirs = 0, exist = 0, simpath = 0, keep_simics_ref = 0):
    if simpath:
        exist = 1
    def __filename_t(tokens):
        if tokens == ask_for_expander:
            return __file_expander

        if tokens == ask_for_description:
            if exist:
                if not dirs:
                    s = "an existing file"
                else:
                    s = "an existing file or directory"
            else:
                if not dirs:
                    s = "a filename"
                else:
                    s = "a file or directory"
            if simpath:
                return s + " (in the Simics search path)"
            return s

        if not istoken(tokens[0], "str"):
            raise CliTypeError, "not a valid filename"

        filename = tokens[0][1]
        filename = os.path.expanduser(filename)
        if not keep_simics_ref:
            filename = filename.replace('%simics%', conf.sim.simics_base)
        filename = filename.replace('%script%', conf.sim.script_dir)
        if simpath:
            filename = SIM_lookup_file(filename)
            found = filename != None
        else:
            found = os.path.exists(SIM_native_path(filename))
        if exist and not found:
            raise CliTypeError, "file not found"
        if not dirs and found and os.path.isdir(filename):
            raise CliTypeError, "illegal directory"
        return (filename, 1)
    return __filename_t

#
# <add id="cli argument types">
# <name>obj_t(desc, kind = None)</name>
# Returns an argument which accepts any object.
#
# <i>desc</i> is the string returned as a description of the
# argument.  <i>kind</i> can be used to limit the accepted objects to
# only allow objects of a certain kind.  This parameter can either be
# a class name that the object should be an instance of, or the name
# of an interface that the object must implement.
# </add>
#
def obj_t(desc, kind = None):
    def __obj_t(tokens):
        if tokens == ask_for_expander:
            return object_expander(kind)

        if tokens == ask_for_description:
            return desc

        if not istoken(tokens[0], "str"):
            raise CliTypeError, "not a valid object"

        objname = tokens[0][1]
        try:
            obj = SIM_get_object(objname)
        except:
            raise CliTypeError, "not an object"
        if kind and not instance_of(obj, kind):
            raise CliTypeError, "wrong object type"
        return (obj, 1)
    return __obj_t

# <add id="cli argument types">
# <name>string_set_t(strings)</name>
#
# Accepts only strings from the given set. <i>strings</i> can be any
# iterable, such as a tuple, list, or set, in which case the return
# value is the exact string the user gave; or a dictionary mapping
# acceptable user input strings to return values.
#
# The optional parameter <arg>visible</arg> is a list of strings. If
# given, only strings in this list will be suggested by the expander.
#
# </add>
def string_set_t(strings, visible = None):
    if not 'iterkeys' in dir(strings):
        # strings is not a dictionary; make it one
        strings = dict((x, x) for x in strings)
    if visible == None:
        exp_strs = strings.keys()
    else:
        exp_strs = [x for x in visible if x in strings]
    def exp(s):
        return get_completions(s, sorted(exp_strs))
    def __string_set_t(tokens):
        if tokens == ask_for_expander:
            return exp
        elif tokens == ask_for_description:
            return '|'.join(sorted(exp_strs))
        else:
            s, pos = str_t(tokens)
            try:
                s = strings[s]
                return (s, pos)
            except KeyError:
                raise CliTypeError, 'illegal value'
    return __string_set_t

# <add id="cli argument types">
# <name>bool_t(true_str, false_str)</name>
#
#
# Accepts only the two strings <i>true_str</i> and <i>false_str</i>,
# the strings "TRUE" and "FALSE", and boolean values (that is, the
# strings "0" and "1"). It passes True or False to the command
# function depending on which string (or value) was given.
#
# Both arguments are optional; if not given, TRUE, FALSE, 1, and 0
# will still be recognized.
#
# </add>
def bool_t(true_str = 'TRUE', false_str = 'FALSE'):
    return string_set_t({true_str: True, false_str: False,
                         '1': True, '0': False, 'TRUE': True, 'FALSE': False,
                         'True': True, 'False': False},
                        visible = [true_str, false_str])

#
# COMMANDS
#

def print_commands(cmd_list):
    max_len = 0
    for cmd in cmd_list:
        if type(cmd) == type([]):
            name = cmd[0]
        else:
            name = cmd["name"]
        if len(name) > max_len:
            max_len = len(name)

    for cmd in cmd_list:
        if type(cmd) == type([]):
            name = cmd[0]
            cmd = cmd[1]
        else:
            name = cmd["name"]
            
        if cmd["short"]:
            line = cmd["short"]
        else:
            mo = re_match(r'(.*(\.|\n))', cmd["doc"])
            if mo:
                if mo.group(1)[-1] == "\n":
                    line = mo.group(1)[:-1] + "..."
                else:
                    line = mo.group(1)[:-1]
            else:
                line = ""
        print_word_wrap(line,
                        " " + name + " " * (max_len - len(name)) + " - ",
                        " " * (max_len + 4))

def get_categories(cmd):
    if type(cmd["type"]) == type(""):
        return [string.replace(cmd["type"], " ", "-")]
    else:
        return [string.replace(ct, " ", "-") for ct in cmd["type"]]

def get_command_categories():
    d = {}
    for cmd in simics_commands():
        cats = get_categories(cmd)
        for c in cats:
            d[c] = None

    l = d.keys()
    l.sort()
    return l

def hex_str(val, size = 0):
    if size:
        return "%0*x" % (size, val)
    else:
        return "%x" % val

#
# -------------------- helper functions --------------------
#

current_proc = None

def get_frontend_current_processor(data, o, idx):
    return current_proc

def set_frontend_current_processor(data, o, cpu, idx):
    if not SIM_object_is_processor(cpu):
        return Sim_Set_Illegal_Value
    set_current_processor(cpu)
    return Sim_Set_Ok

SIM_register_typed_attribute("sim", "frontend_current_processor",
                             get_frontend_current_processor, 0,
                             set_frontend_current_processor, 0,
                             Sim_Attr_Optional,
                             "o", None,
                             "Current frontend processor")

def set_current_processor(cpu):
    global current_proc

    prev_cpu = current_proc
    current_proc = cpu

    # Send a PSELECT message if we changed CPU
    if VT_remote_control() and prev_cpu != cpu:
        VT_send_control_msg(['pselect', 0, cpu.name])

def current_processor():
    global current_proc
    if not current_proc:
        try:
            current_proc = SIM_proc_no_2_ptr(0)
        except:
            raise CliError, ("This command requires a processor to"
                               + " be defined.")
    return current_proc

# asserts that we have at least one CPU defined
def assert_cpu():
    current_processor()

# Return the current CPU, or the CPU named 'cpu_name'.  If 'kind' is
# given, also check that the CPU is of the right kind.  The 'kind'
# parameter should be a tuple ("type", "description"), where "type"
# can be used in a call to instance_of().
def get_cpu(cpu_name = "", kind = None):
    if not cpu_name:
        obj = current_processor()
    else:
        try:
            obj = SIM_get_object(cpu_name)
        except:
            raise CliError, "There is no processor called " + cpu_name + "."
    if not SIM_object_is_processor(obj):
        raise CliError, "Object '%s' is not a processor" % cpu_name
    if kind and not instance_of(obj, kind[0]):
        raise CliError, "This command requires %s" % kind[1]
    return ( obj, obj.name )

# collect all cpu names
def all_cpus():
    if not SIM_initial_configuration_ok():
        return []

    cl = []
    for o in SIM_all_objects():
        if SIM_object_is_processor(o):
            cl.append(o.name)
    return cl

def cpu_expander(comp):
    return get_completions(comp, all_cpus())

# generic expanders:
#
#  object_expander(kind) returns an expander for objects of the
#   given class or with a given interface

def all_instances_of(cl):
    if cl == None:
        return [obj.name for obj in SIM_all_objects()]
    return [ obj.name for obj in SIM_all_objects()
             if instance_of(obj, cl) ]

# <add-fun id="simics api python">
# <short>Standard expander for an object argument</short>
# <namespace>cli</namespace>
#
# For command writing: standard expander that can be use to provide
# argument completion on all objects of a given class or matching a
# given interface (<param>kind</param>).
#
# For example, to expand a string with the list of processor available
# in the machine, you would write:
# <pre>
# arg(str_t, "cpu", expander =  object_expander("processor"))
# </pre>
#
# To expand a string to all <class>gcache</class> objects:
# <pre>
# arg(str_t, "cache", expander = object_expander("gcache"))
# </pre>
#
# </add-fun>
def object_expander(kind):
    return lambda string: get_completions(string, all_instances_of(kind))

def pr(text):
    sys.stdout.write(text)
    sys.stdout.softspace = 0

term = os.environ.get("TERM", "")[:2] in ["vt", "xt"]
format_type = "term"

def set_default_format(format):
    global format_type
    old = format_type
    format_type = format
    return old

def bold_start():
    if format_type == "term":
        return iff(term, "\033[1m", "")
    else:
        return "<b>"

def bold_end():
    if format_type == "term":
        return iff(term, "\033[m", "")
    else:
        return "</b>"

def bold(str):
    return bold_start() + str + bold_end()

def italic_start():
    if format_type == "term":
        return iff(term, "\033[4m", "")
    else:
        return "<i>"

def italic_end():
    if format_type == "term":
        return iff(term, "\033[m", "")
    else:
        return "</i>"

def italic(str):
    return italic_start() + str + italic_end()

term_bold_active = term_italic_active = 0

def term_stop_font(pr_func):
    if term:
        pr_func("\033[m")

def term_start_font(pr_func):
    global term_bold_active, term_italic_active
    if term:
        pr_func("\033[m")
        if term_bold_active:
            pr_func(bold_start())
        if term_italic_active:
            pr_func(italic_start())

def term_set_italic(pr_func, on):
    global term_italic_active
    if term_italic_active == on:
        return
    term_italic_active = on
    if on:
        pr_func(italic_start())
    else:
        if format_type == "term":
            term_stop_font(pr_func)
            term_start_font(pr_func)
        else:
            pr_func(italic_end())

def term_set_bold(pr_func, on):
    global term_bold_active
    if term_bold_active == on:
        return
    term_bold_active = on
    if on:
        pr_func(bold_start())
    else:
        if format_type == "term":
            term_stop_font(pr_func)
            term_start_font(pr_func)
        else:
            pr_func(bold_end())

def formatEncode(str, ftype):
    if (ftype == "jdocu") or (ftype == "html"):
        res_str = ''
        for c in str:
            if c == '<':
                res_str = res_str + '&lt;'
            elif c == '>':
                res_str = res_str + '&gt;'
            elif c == '&':
                res_str = res_str + '&amp;'
            else:
                res_str = res_str + c
        return res_str
    else:
        return str


def get_synopsis(cmd, max_len = 0, format = 0, ftype = None):
    global format_type
    if ftype:
        prev_format_type = format_type
        format_type = ftype
    else:
        prev_format_type = None
        
    buf = ""
    i = 0

    if max_len == 0:
        max_len = len(cmd["name"])

    seen_quest_and = 0 # in an ?& list

    command_name = iff(format,
                       bold_start() + formatEncode(cmd["name"], format_type)
                       + bold_end(),
                       cmd["name"])

    for arg in cmd["args"]:
        if i == cmd["infix"]:
            buf = buf + command_name + " "*(1+max_len-len(cmd["name"]))
        if arg["doc"]:
            name = arg["doc"]
        elif arg["name"]:
            if type(arg["name"]) == type((1,1)):
                name = "("
                for j in range(len(arg["name"])):
                    if arg["handler"][j] == flag_t:
                        name = name + arg["name"][j] + "|"
                    elif (arg["handler"][j] == str
                          or arg["handler"][j] == str_t):
                        name = (name
                                + iff(format, italic_start(), "")
                                + '"' + arg["name"][j]
                                + '"' + iff(format, italic_end(), "") + "|")
                    else:
                        name = (name
                                + iff(format, italic_start(), "")
                                + arg["name"][j]
                                + iff(format, italic_end(), "") + "|")
                name = name[:-1] + ")"
            else:
                name = arg["name"]
        else:
            name = "arg" + str(i+1)


        if arg["handler"] != flag_t and type(arg["handler"]) != type((1,1)):
            if arg["handler"] == str or arg["handler"] == str_t:
                name = iff(format, italic('"'+name+'"'), '"'+name+'"')
            else:
                name = iff(format, italic(name), name)


        if arg["handler"] == flag_t:
            buf = buf + "[" + name + "]"
        elif arg["spec"] == "?":
            buf = buf + "[" + name + "]"
        elif arg["spec"] == "+":
            buf = buf + name + " ..."
        elif arg["spec"] == "*":
            buf = buf + "[ " + name + " ... ]"
        elif arg["spec"] == "?&" and not seen_quest_and:
            buf = buf + "[ " + name
            seen_quest_and = 1
        else:
            buf = buf + name

        if arg["spec"] != "?&" and seen_quest_and:
            buf = buf + " ]"
            seen_quest_and = 0

        buf = buf + " "

        i = i + 1

    if seen_quest_and:
        buf = buf + "]"
        seen_quest_and = 0

    # restore the format if necessary
    if prev_format_type:
        format_type = prev_format_type

    if not buf:
        return command_name
    else:
        return buf

def get_alias(cmd):
    return cmd["alias"]

#
# --- TERM ---
#

def format_command(cmd):
    # first see if the command should be documented with
    # another command

    global format_type
    format_type = "term"

    if cmd["doc_with"]:
        cmd = simics_commands_dict(cmd["doc_with"])

    indent = 3
    width = terminal_width() - 1

    # find all commands that will doc with this one
    doc_with = []
    for c in simics_commands():
        if c["doc_with"] == cmd["name"] or c == cmd:
            doc_with.append(c)

    pr(bold("\nNAME\n"))

    text = cmd["name"]
    aliases = []
    max_len = 0
    cmd_len = 0
    for c in doc_with:
        if c != cmd:
            text = text + ", " + c["name"]
        if len(c["name"]) > cmd_len:
            cmd_len = len(c["name"])
        a = get_alias(c)
        aliases = aliases + a
        if len(c["name"]) > max_len:
            max_len = len(c["name"])

    if cmd["group_short"]:
        text += " - " + cmd["group_short"] + "\n"
    elif cmd["short"]:
        text += " - " + cmd["short"] + "\n"
    else:
        text += "\n"

    pr(" "*indent)
    format_print(string_jdocu(text), indent, width)

    pr(bold("\nSYNOPSIS\n"))

    for c in doc_with:
        pr(" "*indent + get_synopsis(c, 0, 1) + "\n") # max_len <-> 0

    seen = []
    if aliases:
        pr(bold("\nALIAS"))
        if len(aliases) > 1:
            pr(bold("ES"))
        pr("\n")
        for c in doc_with:
            seen = []
            pr(" "*indent)
            text = ""
            alist = get_alias(c)
            if not alist:
                continue
            i = 0
            if len(doc_with) > 1:
                fmt = "%%-%ds  " % cmd_len
                pr(fmt % c["name"])
            for a in alist:
                if a in seen:
                    continue
                seen.append(a)
                if i > 0:
                    text += ", "
                text += bold(a)
                i = i + 1
            text += "\n"
            format_print(text, indent, width)

    text = string.strip(cmd["doc"])

    if text:
        pr(bold("\nDESCRIPTION\n") + " "*indent)
        format_print(text, indent, width)

    for di in cmd["doc_items"]:
        pr("\n" + bold(di[0]) + "\n" + " "*indent)
        format_print(di[1], indent, width)

    pr("\n")

def check_line_wrap(pr_func, col, end, width, indent):
    if col + end > width:
        col = indent + end
        if format_type == "term" and (term_bold_active or term_italic_active):
            term_stop_font(pr_func)
        pr_func("\n" + " "*indent)
        if format_type == "term" and (term_bold_active or term_italic_active):
            term_start_font(pr_func)
    else:
        col = col + end
    return col

def generic_format_print(pr_func, text, indent, width):
    col = indent
    while(text):

        # look for line break (two or more blank lines)
        mo = re_match(r"[ \t\r\f\v]*\n[ \t\r\f\v]*\n\s*", text)
        if mo:
            pr_func("\n" + " "*indent)
            text = text[mo.end():]
            col = indent
            continue

        mo = re_match(r"\s+", text)
        if mo:
            text = text[mo.end():]
            if col > indent:
                pr_func(" ")
                col = col + 1
            continue

        # break line
        mo = re_match(r"<br/?>", text)
        if mo:
            pr_func("\n" + " "*indent)
            text = text[mo.end():]
            col = indent
            continue

        # eat format strings
        if text[0] == "<":
            # italic
            mo = re_match(r"<(/?)(i|file|var|cite)>", text)
            if mo:
                col = check_line_wrap(pr_func, col, 1, width, indent)
                term_set_italic(pr_func, mo.group(1) == '')
                text = text[mo.end():]
                continue

            # bold
            mo = re_match(r"<(/?)(b|tt|em|class|module|cmd|arg|param|fun|type|obj|iface)>", text)
            if mo:
                col = check_line_wrap(pr_func, col, 1, width, indent)
                term_set_bold(pr_func, mo.group(1) == '')
                text = text[mo.end():]
                continue

            # normal
            mo = re_match(r"<(/?)(math|attr)>", text)
            if mo:
                text = text[mo.end():]
                continue

            # match all other tags
            mo = re_match(r"(<[^<]*>)", text)
            text = text[mo.end():]
            col = check_line_wrap(pr_func, col, mo.end(), width, indent)
            # do not print the tags once matched, just skip them
            continue

        mo = re_match(r"&([a-z]+);", text)
        if mo:
            col = check_line_wrap(pr_func, col, 1, width, indent)
            entities = {'lt':  '<',
                        'gt':  '>',
                        'amp': '&',
                        'ndash' : '-',
                        'mdash' : '---',
                        'dquot' : '"',
                        'logor' : '||',
                        'rarr'  : '->',
                        'times' : 'x',
                        'nbsp'  : ' '
                        }
            ent = mo.group(1)
            pr_func(entities.get(ent, "&" + ent + ";"))
            text = text[mo.end():]
            continue

        mo = re_match(r"([^&<\s]*)", text)
        if mo:
            text = text[mo.end():]
            col = check_line_wrap(pr_func, col, mo.end(), width, indent)
            pr_func(mo.group(1))
            continue

        raise CliParseErrorInDocText

def format_print(text, indent, width):
    generic_format_print(pr, text, indent, width)

def collect_string(s):
    global ret_str
    ret_str += s

def get_format_string(text, indent, width):
    global ret_str, format_type
    ret_str = ''
    old_format_type = format_type
    format_type = "html"
    generic_format_print(collect_string, text, indent, width)
    format_type = old_format_type
    return ret_str

#
# --- jDOCU ---
#

def string_jdocu(str):
    res = ""
    for s in str:
        if s == "&":
            res = res + "&amp;"
        elif s == "<":
            res = res + "&lt;"
        elif s == ">":
            res = res + "&gt;"
        else:
            res = res + s
    return res

def command_name_category(n):
    l = len(n)
    if l == 0:
        return 0
    for i in range(l):
        if n[i] in letters:
            return 2
    return 1
    
def command_name_sort(a, b):
    ca = command_name_category(a)
    cb = command_name_category(b)

    if ca != cb:
        return ca - cb

    if a < b:
        return -1
    if a == b:
        return 0
    return 1
    
def one_c_type(c):
    if c == "n":
        return "void "
    if c == "i":
        return "int "
    if c == "I":
        return "integer_t "
    if c == "e":
        return "exception_type_t "
    if c == "o":
        return "lang_void *"
    if c == "s":
        return "char *"
    if c == "m":
        return "memory_transaction_t *"
    if c == "c":
        return "conf_object_t *"
    if c == "v":
        return "void *"
    return "&lt;unknown type %s&gt;" % c

def hap_c_arguments(str, argnames, width = 60, indent = 0, breakline = "\n"):
    res = " " * indent + one_c_type(str[0]) + "(*)("
    indent = len(res)
    str = str[1:]
    if str == "":
        res = res + "void"
    else:
        col = indent
        while str != "":
            this = one_c_type(str[0]) + argnames[0]
            if col > indent and col + len(this) > width - 2:
                res = res + breakline + " " * indent
                col = indent
            res = res + this
            col = col + len(this)
            str = str[1:]
            argnames = argnames[1:]
            if str != "":
                res = res + ", "
                col = col + 2
    return res + ");"
    
#
# --- HTML ---
#

ignore_tags = ["<i>", "</i>", "<b>", "</b>", "<em>", "</em>", "<tt>", "</tt>"]

def ignore_tag(text):
    try:
        for tag in ignore_tags:
            f = 1
            for i in range(len(tag)):
                if tag[i] != text[i]:
                    f = 0
                    break
            if f:
                return len(tag)
        return 0
    except IndexError:
        return 0

def cmd_cmp(a, b):
    if a["name"] < b["name"]:
        return -1
    elif a["name"] == b["name"]:
        return 0
    else:
        return 1

_format_html_paragraph_matcher = re.compile(r"[ \t\r\f\v]*\n[ \t\r\f\v]*\n\s*").match
_format_jdocu_br_matcher = re.compile(r"<br/?>").match

def format_html(text):
    t = ""
    while(text):
        # look for line break (two or more blank lines)
        mo = _format_html_paragraph_matcher(text)
        if mo:
            t = t + "<br><br>\n"
            text = text[mo.end():]
            continue

        # break line
        mo = _format_jdocu_br_matcher(text)
        if mo:
            text = text[mo.end():]
            t = t + "<br>\n"
            continue

        if text[0] == "<":
            l = ignore_tag(text)
            if l:
                t = t + text[:l]
                text = text[l:]
            else:
                text = text[1:]
                t = t + "&lt;"
            continue

        if text[0] == ">":
            text = text[1:]
            t = t + "&gt;"
            continue

        if text[0] == "&":
            text = text[1:]
            t = t + "&amp;"
            continue

        mo = re_match(r"([^\n<>]+)", text)
        if mo:
            text = text[mo.end():]
            t = t + mo.group(1)
            continue

        t = t + text[0]
        text = text[1:]
    return t

def write_doc_item(file, name, text):
    file.write("<dt><b>%s</b></dt>\n<dd>" % name)
    file.write(format_html(text))
    file.write("</dd>\n")

def format_commands_as_html(name):
    global format_type

    oformat = format_type
    
    format_type = "html"

    file = open(name, "w")
    file.write("<html>\n")
    file.write("<head>\n")
    file.write("<title>Simics commands</title>\n")
    file.write("</head>\n")
    file.write("<body>\n")

    file.write("<h1>List of commands</h1><br>\n")
    for cmd in simics_commands():
        file.write("<a href=\"#" + iff(cmd["doc_with"],
                                       cmd["doc_with"],
                                       cmd["name"])
                   + "\">" + format_html(cmd["name"]) + "</a><br>\n")
    file.write("<hr WIDTH=\"100%\">\n")

    for cmd in simics_commands():
        if cmd["doc_with"]:
            continue

        file.write("<a name=\"" + cmd["name"] + "\">\n")
        file.write("<dl>\n")
        # find all commands that will doc with this one
        doc_with = []
        for c in simics_commands():
            if c["doc_with"] == cmd["name"]:
                doc_with.append(c)

        doc_with.sort(cmd_cmp)

        text = cmd["name"]

        aliases = get_alias(cmd)
        for c in doc_with:
            text = text + ", " + c["name"]
            aliases = aliases + get_alias(c)

        if cmd["group_short"]:
            text = text + " - " + cmd["group_short"]
        elif cmd["short"]:
            text = text + " - " + cmd["short"]

        write_doc_item(file, "NAME", text)

        text = "<tt>" + get_synopsis(cmd, 0, 1)
        for c in doc_with:
            text = text + "<br>\n" + get_synopsis(c, 0, 1)
        text = text + "</tt>"

        write_doc_item(file, "SYNOPSIS", text)

        write_doc_item(file, "DESCRIPTION", cmd["doc"])

        for di in cmd["doc_items"]:
            write_doc_item(file, di[0], di[1])
        file.write("</dl>\n")

        file.write("<hr WIDTH=\"100%\">\n")
    file.write("<body>\n")
    file.write("</html>\n")
    file.close()

    format_type = oformat

def commands_text(file = "commands.txt"):
    file = open(file, "w")
    file.write("COMMANDS - for spell-checking\n\n")

    for cmd in simics_commands():
        if cmd["doc_with"]:
            continue
        file.write("Command - %s\n\n" % cmd["name"])
        file.write(cmd["doc"])
        file.write("\n\n")

    file.close()

internals_on = 0
simics_cmds = []
simics_cmds_dict = {}
simics_args = {}

def simics_commands(internal = None):
    if internal == None:                                   
        internal = internals_on
    return filter(lambda cmd: iff(cmd["internal"], internal, 1),
                  simics_cmds)        

def simics_command_exists(key):
    return iff(simics_cmds_dict.get(key), 1, 0)    
    

def simics_commands_dict(key):
    cmd = simics_cmds_dict.get(key)
    if not cmd or not cmd["internal"]:
        return cmd

    if internals_on:
        return cmd
    else:
        return None

def internals():
    global internals_on
    internals_on = 1
    print "Activating access to internal Simics commands."
    print "These are subject to change and may be removed from future"
    print "versions of Simics."

def internals_off():
    global internals_on
    internals_on = 0

# ---------------- front end vars -----------------

_last_cli_repeat  = 0      # 0: no repeat, 1: repeat-cmd-line, 2: repeat-fun
_last_cli_cmdline = ""     # what was the exact command-line
_last_cli_hap = 0          # if a hap cancels the previous command or not

try:
    var_hap = SIM_hap_add_type("CLI_Variable_Write",
                               "s", "variable value",
                               None,
                               "Triggered when a CLI variable is written", 0)
except Exception, msg:
    print "Failed installing CLI_Variable_Write hap: %s" % msg

class simenv_class(object):

    def __init__(self, parent):
        object.__setattr__(self, '__variables__', {})
        object.__setattr__(self, '__parent__', parent)
    
    def get_all_variables(self):
        all = self.__variables__.copy()
        if self.__parent__:
            all.update(self.__parent__.get_all_variables())
        return all

    def set_variable_value(self, name, value, local):
        if local:
            self.__variables__[name] = value
        else:
            self.__setattr__(name, value)

    def set_variable_value_idx(self, name, value, local, idx):
        if local:
            if (not self.__variables__.has_key(name)
                or type(self.__variables__[name]) != dict):
                self.__variables__[name] = {}
            self.__variables__[name][idx] = value
        elif self.__parent__ == None:
            if (not self.__variables__.has_key(name)
                or type(self.__variables__[name]) != dict):
                self.__variables__[name] = {}
            self.__variables__[name][idx] = value
            try:
                SIM_hap_occurred_always(var_hap, None, 0, [name])
            except:
                pass
        else:
            self.__parent__.set_variable_value_idx(name, value, 0, idx)

    def remove_variable(self, name):
        if self.__variables__.has_key(name):
            del self.__variables__[name]
        elif self.__parent__:
            return self.__parent__.remove_variable(name)

    def __getattr__(self, name):
        if self.__variables__.has_key(name):
            return self.__variables__[name]
        elif self.__parent__:
            return getattr(self.__parent__, name)
        else:
            return None

    def __setattr__(self, name, value):
        if self.__variables__.has_key(name) or self.__parent__ == None:
            try:
                SIM_hap_occurred_always(var_hap, None, 0, [name])
            except:
                pass
            self.__variables__[name] = value
        else:
            setattr(self.__parent__, name, value)

global_simenv = simenv_class(None)

def getenv(data, o, idx):
    if type(idx) != type(''):
        return None
    return getattr(global_simenv, idx)

def setenv(data, o, val, idx):
    if type(idx) != type(''):
        return Sim_Set_Need_String

    setattr(global_simenv, idx, str(val))
    return Sim_Set_Ok

SIM_register_typed_attribute("sim", "env",
                             getenv, 0, setenv, 0,
                             Sim_Attr_Pseudo | Sim_Attr_String_Indexed,
                             None, "a",
                             "get/set simics environment variable")

# -------------------------------------------------

# If name is not None, return name, or None if it's already taken. If
# name is None, return "stemN" for the lowest integer N such that the
# name "stemN" isn't taken.
def new_object_name(name, stem):
    def name_taken(name):
        try:
            SIM_get_object(name)
            return True
        except:
            return False
    if name != None and name_taken(name):
        return None
    count = 0
    while name == None:
        name = "%s%d" % (stem, count)
        if name_taken(name):
            name = None
            count += 1
    return name

def command_sort_category(n):
    l = len(n)
    if l == 0:
        return 0
    for i in range(l):
        if n[i] in letters:
            return 2
    return 1
    
def command_sorts_before(a, b):
    ca = command_sort_category(a)
    cb = command_sort_category(b)

    if ca != cb:
        return ca < cb

    return a < b

# defines a new argument type
def new_argtype(fun, name, doc = ""):
    simics_args[fun] = { "name":name, "fun":fun, "doc":doc }

_type = type

# <add-fun id="simics api python">
# <short>define a new CLI command</short>
# <namespace>cli</namespace>
#
# Define a new CLI command.
# A complete explanation of <fun>new_command()</fun>
# is available in the <cite>Simics Programming Guide</cite>.
# </add-fun>
def new_command(name, fun, args = [], doc = "", type = "misc commands",
                pri = 0, infix = 0, left = 1,
                short = "", group_short = "", alias = [], doc_with = "",
                check_args = 2,
                doc_items = [], see_also = [], namespace = "",
                method = "", namespace_copy = (), internal = 0,
                filename = "", linenumber = "", module = "",
                object = None, repeat = None, deprecated = None):

    # if infix operator do not check superfluous arguments since they are often
    # used in expressions. can be overridden by setting check_args to 1
    if infix == 1 and check_args == 2:
        check_args = 0

    if alias == "":
        alias = []

    if _type(alias) == _type(""):
        alias = [alias]

    if namespace:
        meth = name
        name = "<"+namespace+">."+name
    else:
        meth = ""

    # Fixes the "help sfmmu0.i-probe" bug.
    if doc_with and not simics_cmds_dict.has_key(doc_with):
        print "*** The doc_with-field in command", name,
        print "points to non-existing command", doc_with

        doc_with_ns = "<"+namespace+">."+doc_with
        if simics_cmds_dict.has_key(doc_with_ns):
            print "    (this seems like a missing namespace-prefix."
            print "     Using doc-with=\"%s\" instead)" % (doc_with_ns)
            doc_with = doc_with_ns

    err = "*** Error when defining command '" + name + "': "

    # check to see if command name already exists
    redefine = 0
    try:
        try_cmd = simics_cmds_dict[name]
        # the command exist, check if it's the same
        if (try_cmd["filename"] == filename
            and try_cmd["linenumber"] == linenumber):
            print err + "redefining the same command"
            redefine = 1
        else:
            # complain, but add the command anyway
            print err + "two different commands have the same name."
    except:
        pass

    # check to see if alias already exists
    for a in alias:
        try:
            if namespace:
                a = "<"+namespace+">." + a
            try_cmd = simics_cmds_dict[a]
            # the command exist, check if it's the same
            if (try_cmd["filename"] == filename
                and try_cmd["linenumber"] == linenumber):
                if not redefine:
                    print err + "redefining the same alias"
            else:
                # complain, but add the command anyway
                print err + "the '%s' alias is already used as a command." % a
        except:
            pass

    if type == "internal commands":
        internal = 1

    cmd = { "name" : name, "fun" : fun, "pri" : pri, "infix" : infix,
            "left" : left, "doc" : doc, "type" : type, "short" : short,
            "group_short" : group_short, "args" : args, "alias" : alias,
            "doc_with" : doc_with, "check_args" : check_args,
            "doc_items" : doc_items, "see_also" : see_also,
            "namespace" : namespace, "method" : meth,
            "namespace_copy" : (), "internal" : internal,
            "filename" : filename, "linenumber" : linenumber,
            "object" : None,
            "repeat" :  repeat, "deprecated" : deprecated }

    # hack around the fact that python-frontend is not included in core
    curr_module = VT_get_current_loading_module()
    if curr_module == "python-frontend":
        cmd["module"] = ""
    else:
        cmd["module"] = curr_module

    inserted = 0
    for i in range(len(simics_cmds)):
        if command_sorts_before(name, simics_cmds[i]["name"]):
            simics_cmds[i:i] = [cmd]
            inserted = 1
            break

    if not inserted:
        simics_cmds.append(cmd)

    simics_cmds_dict[name] = cmd
    if not namespace and alias:
        for a in alias:
            simics_cmds_dict[a] = cmd

    # check the doc_list
    for d in doc_items:
        if _type(d) == _type((0,0)):
            if len(d) == 2:
                if _type(d[0]) == _type("") and _type(d[1]) == _type(""):
                    continue
        print err + "Illformed doc_items"
        break

    # check the arguments
    arg_names = []
    for arg in args:
        if arg["handler"] == flag_t:
            if not arg["name"]:
                print err + "flag argument must have a name"
            if arg["name"][0] != "-":
                print err + "flag name must begin with -"
        # poly
        if _type(arg["handler"]) == _type((0,0)):

            if arg["name"]:
                if _type(arg["name"]) != _type((0,0)):
                    print err,
                    print "name must be a tuple of names to match the handler"
                if len(arg["handler"]) != len(arg["name"]):
                    print err,
                    print "handler and name must be a tuple of equal length"
                arg_names = arg_names + list(arg["name"])
            if arg["expander"]:
                if _type(arg["expander"]) != _type((0,0)):
                    print err,
                    print "expander must be a tuple of functions to match the",
                    print "handler"
                if len(arg["handler"]) != len(arg["expander"]):
                    print err,
                    print "handler and expander must be a tuple of equal",
                    print "length"

            for i in range(len(arg["handler"])):
                if not arg["expander"] or not arg["expander"][i]:
                    try:
                        exp = arg["handler"][i](ask_for_expander)
                        if not arg["expander"]:
                            arg["expander"] = [None] * len(arg["handler"])
                        arg["expander"][i] = exp
                    except:
                        pass

            # convert the expander back to a tuple if the code above converted
            # it to a list of expanders
            if _type(arg["expander"]) == _type([]):
                arg["expander"] = tuple(arg["expander"])

            for t in arg["handler"]:
                _check_handler(err, t)
        else:
            _check_handler(err, arg["handler"])

            if arg["handler"] == int:
                arg["handler"] = int_t
            elif arg["handler"] == str:
                arg["handler"] = str_t

            if (arg["handler"] == int_t and arg["default"]
                and _type(arg["default"]) != _type(0L)
                and _type(arg["default"]) != _type(0)):
                print err,
                print "int_t args must have default values of type int"
            if (arg["handler"] == str_t and arg["default"]
                and _type(arg["default"]) != _type("")):
                print err + "str_t args not string as default value"
            if arg["name"]:
                arg_names.append(arg["name"])

    i = 0
    for a in arg_names:
        if a in arg_names[i+1:]:
            print err + "argument names must be unique"
        i = i + 1

    if namespace_copy:

        nsc = copy_dict(cmd)
        nsc["fun"] = namespace_copy[1]
        if doc:
            nsc["doc"] = ""
            nsc["doc_with"] = name
        nsc["args"] = args[1:]
        nsc["alias"] = alias
        nsc["namespace"] = namespace_copy[0]
        apply(new_command, (), nsc)

def _check_handler(err, t):
    if t == int:
        print err + "int arg type is obsolete, use int_t instead."

    if t == str:
        print err + "str arg type is obsolete, use str_t instead."

    if t == flag:
        print err + "flag arg type is obsolete, use flag_t instead."

    if t == addr:
        print err + "addr arg type is obsolete, use addr_t instead."

    if t == float_arg:
        print err + "float_arg type is obsolete, use float_t instead."


_is_filename_completion = 0
show_tab_complete_dirs = False

def __file_expander(txt):
    global _is_filename_completion
    _is_filename_completion = 1
    VT_filename_completion()
    orig_txt = txt
    if txt and txt[0] == "~":
        pos = txt.find(os.sep, 1)
        if _altsep:
            altpos = txt.find(_altsep, 1)
            if altpos != -1 and altpos < pos:
                pos = altpos
            
        try:
            if pos < 0:                 # no dirseparator after ~
                user = txt[1:]
                if _use_pwd:
                    users = pwd.getpwall()
                else:
                    users = []
                if os.getenv('HOME'):
                    users = users + [['']]
                res = []
                for u in users:
                    if len(u[0]) >= len(user) and u[0][:len(user)] == user:
                        res.append('~' + u[0])
                return res
            else:
                user = txt[1:pos]

            if not user:
                home = os.getenv('HOME')
            else:
                # getpwnam()[5] is the user's home directory
                home = pwd.getpwnam(user)[5]
            txt = home + txt[pos:]
        except Exception, msg:
            pass

    pos = txt.rfind(os.sep)
    if _altsep is not None:
        altpos = txt.rfind(_altsep, 1)
        if altpos != -1 and altpos > pos:
            pos = altpos

    if pos < 0:
        dirname = os.curdir
        filename = txt
    else:
        dirname = txt[:pos]
        filename = txt[pos + 1:]

    dirname += os.sep

    try:
        files = []
        for f in os.listdir(dirname):
            if len(filename) > len(f):
                continue
            if _case_sensitive_files:
                if f[:len(filename)] != filename:
                    continue
            else:
                if string.lower(f[:len(filename)]) != string.lower(filename):
                    continue
            files.append(f)
    except Exception, msg:
        return []

    if filename:
        path = orig_txt[:-len(filename)]
    else:
    	path = orig_txt
    res = map(lambda f: path + f, files)
    if show_tab_complete_dirs:
        res = map(lambda f: iff(os.path.isdir(f), f + os.sep, f), res)
    return res

# <add-fun id="simics api python">
# <short>define a command argument</short>
# <namespace>cli</namespace>
#
# Define a CLI command argument when using <fun>new_command()</fun>.
# A complete explanation of <fun>new_command()</fun> and <fun>arg()</fun>
# is available in the <cite>Simics Programming Guide</cite>.
#
# </add-fun>
def arg(handler, name = "", spec = "1", default = None, data = None,
        doc = "", expander = None, pars = [], is_a = None):
    if spec == "":
        spec = "1"
    if handler == flag_t:
        spec = "?"
        default = 0
    if expander == None:
        try:
            expander = handler(ask_for_expander)
        except:
            expander = None
    return { "handler":handler, "name":name, "default":default, "data":data,
             "spec":spec, "doc":doc, "expander":expander, "pars":pars,
             "is_a": is_a }

new_argtype(int_t,  "integer")
new_argtype(str_t,  "string")
new_argtype(flag_t, "flag")
new_argtype(addr_t, "address")
new_argtype(float_t, "float")
new_argtype(integer_t, "64-bit integer")

def istoken(token, tokentype, val = None):
    if tokentype == "str":
        if token[0] in [ "strval", "str" ]:
            if val:
                return val == token[1]
            return 1
        else:
            return 0

    if token[0] == tokentype:
        return 1
    else:
        return 0

def quiettoken(token):
    return len(token) > 2 and token[2]

def istabcomplete(token):
    if istoken(token, "str") and len(token[1]) and token[1][-1] == "\a":
        return 1
    else:
        return 0

def get_arg_description(handler):
    if type(handler) == type((1,1)):
        desc = ""
        for h in handler:
            try:
                tmp = simics_args[h]["name"]
            except KeyError:
                tmp = h(ask_for_description)
            desc = desc + " or " + tmp
        return desc[4:]
    else:
        try:
            return simics_args[handler]["name"]
        except KeyError:
            return handler(ask_for_description)

def find_arg(name, arglist):
    i = 0
    for a in arglist:
        if type(a["name"]) == type((1,1)): # tuple of names
            if name in a["name"]:
                return (a, i)
        elif name == a["name"]:
            return (a, i)
        i = i + 1
    return (None, 0)

def poly_to_spec(arg, spec):
    for i in range(len(arg["name"])):
        if arg["name"][i] == spec:
            arg["name"] = (spec,)
            arg["handler"] = (arg["handler"][i],)
            if arg["expander"]:
                arg["expander"] = arg["expander"][i]
            return arg
    raise CliErrorInPolyToSpec

def call_arg_expander(exp, comp, cmd):
    if cmd["namespace"]:
        try:
            lst = exp(comp, cmd["object"])
        except TypeError:
            lst = exp(comp)
    else:
        lst = exp(comp)
    return lst

def token_string(ts):
    t = ts[0]
    ts = ts[1:]
    if t[0] == "addr":
        return t[1]+':'+token_string(ts)
    elif t[0] in ["str", "strval", "flag"]:
        return t[1]
    elif t[0] == "int" or t[0] == "float":
        return str(t[1])
    else:
        return ""
            
def format_tokens(ts):
    s = []
    for t in ts:
        if t[0] == "str":
            s.append("s"+repr(t[1]))
        elif t[0] in ["int", "float"]:
            s.append(repr(t[1]))
        else:
            s.append(repr(t[0]))
    return string.join(s, " ")

def _arg_interpreter(cmd, arglist, tokens):
    command = cmd["name"]
    used_args = []
    processed_args = 0
    require_next = 0
    pos = -1

    # add argument number to args
    i = 0
    for a in arglist:
        a["num"] = i
        i = i + 1

    dict = {}

    tokenlen = len(tokens)

    # create a return list of equal length as arglist
    retlist = []
    for a in arglist:
        retlist.append(0)

    while arglist:
        if istoken(tokens[0], "void"):
            tokens[0] = ('int', 0)

        if istoken(tokens[0], "str") and istoken(tokens[1], "str", "="):
            # named parameter?
            name = tokens[0][1]
            
            (arg, i) = find_arg(name, arglist)

            if arg:
                used_args.append(arg)
                del arglist[i]
                tokens = tokens[2:]
                retentry = arg["num"]

                if type(arg["name"]) == type((0,0)):
                    arg = poly_to_spec(arg, name)

                # tab completion stuff
                if istabcomplete(tokens[0]):
                    comp = tokens[0][1][:-1]
                    if arg["expander"]:
                        comps = call_arg_expander(arg["expander"], comp, cmd)
                        if comps:
                            raise CliTabComplete, comps
                    if (arg["spec"] == "?"
                        and type(arg["default"]) != type((0,0))):
                        if type(arg["default"]) == type(""):
                            if arg["default"] == "":
                                raise CliTabComplete, []
                            else:
                                raise CliTabComplete, [arg["default"]]
                        elif (type(arg["default"]) == type(1)
                              or type(arg["default"]) == type(1L)):
                            raise CliTabComplete, [str(arg["default"])]
                        else:
                            raise CliTabComplete, []
                        raise CliTabComplete, [str(arg["default"])]
                    raise CliTabComplete, []

                if arg["spec"] == "?":
                    # require argument now when name has been specified
                    arg["spec"] = "1"

            else:
                (arg, i) = find_arg(name, used_args)
                if arg:
                    raise CliArgNameError, ("argument '" + name
                                              + "' used twice in command '"
                                              + command + "'")
                else:
                    raise CliArgNameError, ("unknown argument name '" + name
                                              + "' in '" + command + "'")
        elif istoken(tokens[0], "flag"): #flag?
            flagname = tokens[0][1]

            (arg, i) = find_arg(flagname, arglist)

            if arg:
                used_args.append(arg)
                del arglist[i]
                retentry = arg["num"]
                if type(arg["name"]) == type((0,0)):
                    arg = poly_to_spec(arg, flagname)
            else:
                (arg, i) = find_arg(flagname, used_args)
                if arg:
                    raise CliArgNameError, ("flag '" + flagname
                                              + "' used twice in command '"
                                              + command + "'")
                else:
                    raise CliArgNameError, ("unknown flag '" + flagname
                                              + "' in '" + command + "'")
        else:
            arg = arglist[0]

            # completion stuff
            if istabcomplete(tokens[0]):
                comp = tokens[0][1][:-1]
                comps = []

                for a in arglist:
                    # tuple ? then poly arg
                    if type(a["handler"]) == type((0,0)):
                        for i in range(len(a["handler"])):
                            if comp == a["name"][i][:len(comp)]:
                                comps.append(a["name"][i]
                                             + iff(a["handler"][i] == flag_t,
                                                   "", " ="))
                    else:
                        if a["name"] and comp == a["name"][:len(comp)]:
                            comps.append(a["name"]
                                         + iff(a["handler"] == flag_t,
                                               "", " ="))

                if comps:
                    raise CliTabComplete, comps

                exp = arg["expander"]
                if exp:
                    if type(exp) == type((0,0)):
                        exp = exp[0]
                    comps = call_arg_expander(exp, comp, cmd)
                    if comps:
                        raise CliTabComplete, comps

                if arg["spec"] == "?":
                    arglist = arglist[1:]
                    continue

                raise CliTabComplete, []

            used_args.append(arg)
            arglist = arglist[1:]
            retentry = arg["num"]

        anslist = []
        while 1:
            if istabcomplete(tokens[0]):
                raise CliTabComplete, []

            try:
                # tuple? then it is or beteen entries == polyvalue
                if type(arg["handler"]) == type((1,1)):
                    fail = 1
                    for h in range(len(arg["handler"])):
                        try:
                            (val, pos) = arg["handler"][h](tokens)
                            val = (arg["handler"][h], val, arg["name"][h])
                            fail = 0
                            break
                        except CliTypeError, msg:
                            continue
                    if fail:
                        raise CliTypeError
                else:
                    # call the argtypes handler with rest of tokens
                    (val, pos) = arg["handler"](tokens)
                    # if we have a is_a function test the argument
                    if arg["is_a"]:
                        if not arg["is_a"](val):
                            raise CliTypeError

                processed_args = processed_args + 1
	        tokens = tokens[pos:]
                anslist.append(val)

                # if this is set the next ?& entry must be there
                if arg["spec"] == "?&":
                    require_next = 1
                else:
                    require_next = 0

                if arg["spec"] != "+" and arg["spec"] != "*":
                    break

            except CliTypeError, msg:
                if arg["spec"][0] == "?" and not require_next:
                    # last arg and wrong type
                    if arglist == [] and not istoken(tokens[0], ")"):
                        raise CliOutOfArgs, \
                              ("argument "
                               + str(processed_args+1) + " ("
                               + token_string(tokens)
                               + ") given to '" + command
                               + "' has the wrong type;\n"
                               + get_arg_description(arg["handler"])
                               + " expected.\nSYNOPSIS: "
                               + get_synopsis(cmd, len(command)))
                    else:
                        val = arg["default"]

                    if arg["spec"] == "?&":
                        while arglist:
                            if arglist[0]["spec"] == "?&":
                                del arglist[0]
                            else:
                                break
                    break
                elif arg["spec"] == "+":
                    if anslist == []:
                        raise CliOutOfArgs, \
                              ("out of arguments for command '" + command
                               + "';\nexpecting "
                               + get_arg_description(arg["handler"])
                               + " list.\nSYNOPSIS: "
                               + get_synopsis(cmd, len(command)))
                    else:
                        val = anslist
                        break
                elif arg["spec"] == "*":
                    val = anslist
                    break
                else:
                    if istoken(tokens[0], ")"):
                        raise CliOutOfArgs, \
                              ("argument number "+ str(retentry+1)
                               + " is missing in '"
                               + command + "';\n"
                               + get_arg_description(arg["handler"])
                               + " expected.\n"
                               + "SYNOPSIS: "
                               + get_synopsis(cmd, len(command)))
                    else:
                        raise CliOutOfArgs, \
                              ("argument " + str(processed_args + 1)
                               + " (" + token_string(tokens)
                               + ") given to '" + command
                               + "' has the wrong type;\n"
                               + get_arg_description(arg["handler"])
                               + " expected.\nSYNOPSIS: "
                               + get_synopsis(cmd, len(command)))

        retlist[retentry] = val

    if istabcomplete(tokens[0]):
        raise CliTabComplete, []

    if cmd["check_args"] and not istoken(tokens[0], ')'):
        raise CliParseError, ("too many arguments for command '" + command
                                + "'.\nSYNOPSIS: "
                                + get_synopsis(cmd, len(command)))

    return (retlist, tokenlen - len(tokens))

def get_octal_len(str):
    max_len = min(len(str), 3)
    while max_len:
        try:
            val = int(str[:max_len], 8)
            if val < 0 or val > 255:
                raise Exception
            return max_len
        except Exception, msg:
            max_len -= 1
    return 0

#
# tokenizes the input command line string.
#
#

def str_token(str):
    if str == 'TRUE':
        return ('int', 1)
    elif str == 'FALSE':
        return ('int', 0)
    else:
        return ('str', str)

def tokenize(text):
    escapes = {'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', 'a': '\a',
               'v': '\v', 'f': '\f', 'e': '\033'}

    # Get commands with no letter characters (except -,/), i.e. +, * etc. These
    # will separate tokens.
    no_letter_cmds = []
    for command in simics_commands():
        if (command["name"] != "-"
            and command["name"] != "/"
            and command["name"] != "["
            and command["name"] != "~"):
            f = 1
            for c in command["name"]:
                if c in letters:
                    f = 0
                    break
            if f:
                no_letter_cmds.append(command["name"])

    # print no_letter_cmds

    # put a sentinel last so that we always end with a white space
    text = " " + text + " "

    tokens = []
    while text != "":

        # look for flag token, i.e. \s+-wordchars\s
        mo = re_match(r"\s+(-[a-zA-Z][a-zA-Z0-9-]*)(?=(\s|\)|;))", text)
        if mo:
            tokens.append(("flag", mo.group(1)))
            text = text[mo.end():]
            continue

        # Eat whites, but not NL
        text = text.lstrip(whitespace)

        if text == "": break

        # look for comments
        if text[0] == "#":
            line_end = text.find('\n')
            if line_end < 0:
                return tokens
            else:
                text = text[line_end:]
                continue

        # command separator
        if text[0] == ";":
            tokens.append((';',))
            text = text[1:]
            continue

        if text[0] == "\n":
            tokens.append(('NL', ))
            text = text[1:]
            continue

        # look for variables, i.e. $wordchars
        mo = re_match(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", text)
        if mo:
            text = text[mo.end():].lstrip(whitespace)
            # keep $ first
            if len(text) and ((text[0] in ('=', '[') and text[:2] != '==')
                              or text[:2] in ('+=', '-=')):
                if (len(tokens)
                    and istoken(tokens[-1], 'str')
                    and tokens[-1][1] == 'local'):
                    tokens[-1] = ("str", '$' + mo.group(0))
                else:
                    tokens.append(("str", mo.group(0)))
            else:
                #tokens.append("(")
                tokens.append(("str", "$",))
                tokens.append(("str", mo.group(1)))
                #tokens.append(")")
            continue

        # look for % (register access)
        mo = re_match(r"\%([a-zA-Z][a-zA-Z0-9_]*)", text)
        if mo:
            realtail = text[mo.end():]
            tail = realtail.lstrip(whitespace)
            if len(tail) and ((tail[0] == '=' and tail[:2] != '==')
                              or tail[:2] in ('+=', '-=')):
                # keep % first
                tokens.append(("str", mo.group(0)))
                text = tail
                continue
            if len(realtail):
                # separate variable from the following text. Special case for
                # - since %a-4 shouldn't be expanded to %a -4, but %a - 4
                if realtail[0] == '-':
                    text = mo.group(0) + ' ' + realtail[0] + ' ' + realtail[1:]
                else:
                    text = mo.group(0) + ' ' + realtail

        # look for address prefix
        mo = re_match(r"(v|p|l|li|ld|cs|ds|es|fs|gs|ss|)\s*:", text)
        if mo:
            tokens.append(("addr", mo.group(1)))
            text = text[mo.end():]
            continue

        # string?
        if text[0] == '"':
            mo = re_match(r'"((\\"|[^"])*)"', text)
            new = ""

            if mo:
                tmp = mo.group(1)
                l = len(tmp)
                if l > 1:
                    i = 0
                    while i < l:
                        if tmp[i] == '\\':
                            i = i + 1
                            if i == l:
                                raise CliSyntaxError, "Unterminated string"

                            if tmp[i] in string.octdigits:
                                oct_len = get_octal_len(tmp[i:])
                                if oct_len:
                                    new += chr(int(tmp[i:i + oct_len], 8))
                                    i += oct_len - 1
                                else:
                                    new += escapes.get(tmp[i], tmp[i])
                            else:
                                new += escapes.get(tmp[i], tmp[i])
                        else:
                            new = new + tmp[i]
                        i = i + 1
                else:
                    new = tmp

                tokens.append(("strval", new))
                text = text[mo.end():]
                continue
            else:
                pos = text.find('\a ')
                if pos < 0:
                    raise CliSyntaxError, "Unterminated string"
                # terminate string on tab-completion
                text = text.replace('\a ', '\a"', 1)
                continue

        # eval python expr -> pass it to eval python command
        mo = re_match(r"`(.*?)`", text)
        if mo:
            # This is translated to "python exp", which is a specially
            # treated prefix operato with high priority 
            tokens.append("(")
            tokens.append(("str", "python"))
            tokens.append(("str", mo.group(1)))
            tokens.append(")")
            text = text[mo.end():]
            continue

        text.strip()
        this_text = text
        found = 0
        for i in range(len(text)):
            if found:
                break
            cmd_len = 0
            for cmd in (no_letter_cmds + [' ']):
                if text[i:i+len(cmd)] == cmd and len(cmd) > cmd_len:
                    this_text = text[:i]
                    cmd_len = len(cmd)
                    found = 1

        if this_text.count('.') > 1:
            possible_number = 0
        else:
            possible_number = 1

        mo = float_regexp.match(text)
        if mo and possible_number and text[mo.end():][:1] != '\a':
            # convert floats to python floats
            tokens.append(("float", float(mo.group(0))))
            text = text[mo.end():]
            continue

        try:
            if text[0] in "0123456789":
                get_integer(text)
            elif text[0] == "-" or text[0] == "~":
                get_integer(text[1:])
            else:
                raise Exception
            is_integer = possible_number
        except:
            is_integer = 0

        if text[0] in '(){}':
            tokens.append((text[0],))
            text = text[1:]
        elif text[0] in "0123456789" and is_integer:
            (num, pos) = get_integer(text)
            text = text[pos:]
            tokens.append(("int", num))
        elif (text[0] == "-" and text[1] != "?" and text[1] != '>' and tokens
              and (istoken(tokens[-1], ")")
                   or istoken(tokens[-1], "var")
                   or istoken(tokens[-1], "int"))):
            text = text[1:]
            tokens.append(("str", "-"))
        elif (text[0] == "/" and tokens
              and (istoken(tokens[-1], ")")
                   or istoken(tokens[-1], "var")
                   or istoken(tokens[-1], "int"))):
            tokens.append(("str", "/"))
            text = text[1:]
        elif text[0] == "-" and is_integer:
            text = text[1:]
            (num, pos) = get_integer(text)
            text = text[pos:]
            tokens.append(("int", -num))
        elif text[0] == "~" and is_integer:
            text = text[1:]
            (num, pos) = get_integer(text)
            text = text[pos:]
            tokens.append(("int", ~num))
        elif text[0] == '[':
            tokens.append(("str", text[0]))
            tokens.append(('(',))
            text = text[1:]
        elif text[0] == ']':
            tokens.append((')',))
            text = text[1:]
        else:
            for i in range(len(text)):
                # look for no-letter-commands in string, they separate tokens
                match = 0
                use_cmd = ''
                for cmd in no_letter_cmds:
                    if text[i:i+len(cmd)] == cmd and len(cmd) > len(use_cmd):
                        match = 1
                        use_cmd = cmd
                cmd = use_cmd
                if match:
                    if i > 0:
                        tokens.append(str_token(text[:i]))
                    tokens.append(("str", text[i:i+len(cmd)]))
                    text = text[i+len(cmd):]
                    break
                elif text[i] in whitespace + "(){}[];":
                    tokens.append(str_token(text[:i]))
                    text = text[i:]
                    break
                elif text[i] == '\n':
                    tokens.append(str_token(text[:i]))
                    tokens.append(('NL', ))
                    text = text[i:].replace('\n', '', 1)
                    break

    return tokens

#python does not provide this function
def copy_dict(dict):
    new = {}
    for key in dict.keys():
        new[key] = dict[key]
    return new

def copy_arg_list(org):
    new = []
    for arg in org:
        new.append(copy_dict(arg))
    return new

def instance_of(object, classname):
    if object.classname == classname:
        return 1
    if classname in dir(object.iface):
        return 1
    if classname == 'conf_object_t' and type(object) == type(conf.sim):
        return 1
    return 0

def get_namespace_commands(prefix):
    pos = prefix.find(".")
    if pos >= 0:
        obj_name = prefix[:pos]
    else:
        l = []
        obj_name = prefix
        # no dot in prefix, add only object names with a trailing dot.
        for o in SIM_all_objects():
            name = o.name
            if not name.startswith(obj_name):
                continue
            l.append(name+".")

        # if there is only one possible object, we continue bellow and expand
        # to every command as well
        if len(l) != 1:
            return l
            
    l = []
    for o in SIM_all_objects():
        name = o.name
        if not name.startswith(obj_name):
            continue
        for cmd in simics_commands():
            if instance_of(o, cmd["namespace"]):
                l.append(name + "."
                         + cmd["name"][cmd["name"].find(".") + 1:])
    return l

def get_conf_objects(prefix):
    l = []
    for o in SIM_all_objects():
        name = o.name
        if not name.startswith(prefix):
            continue
        l.append(name)
    return l

current_locals = global_simenv
pre_branch_locals = global_simenv

def get_current_locals():
    return current_locals

class cli_variable_class(object):
    def __getattr__(self, name):
        return getattr(get_current_locals(), name)

    def __setattr__(self, name, value):
        get_current_locals().set_variable_value(name, value, 0)

simenv = cli_variable_class()

def run_and_report(commands, user_typed = 0):
    global _last_cli_repeat
    msg = None
    command_ok = 0

    try:
        commands()
    except CliSyntaxError, msg:
	msg = "Syntax error: " + str(msg)
    except CliParseError, msg:
 	msg = "Parse error: " + str(msg)
    except (CliArgNameError, CliOutOfArgs), msg:
        msg = "Argument error: " + str(msg)
    except CliAmbiguousCommand, msg:
	pass
    except CliTabComplete, ex:
        # this code is probably never reach during normal Simics usage;
        # normally tab completion goes through either the tab_complete()
        # function or proto_cmd_complete()
        for n in ex.value():
            print "   " + n
    except (CliError, SimExc_Index, SimExc_General), msg:
	pass
    else:
        command_ok = 1


    if msg is not None:
	# "msg" might be a exception instance so it needs to be
        # converted to a string.
	VT_write(str(msg) + "\n", 1)

    if command_ok == 0 and not user_typed:
        _last_cli_repeat = 0

def start_script_branch(f):
    global current_locals, pre_branch_locals
    pre_branch_locals = current_locals
    # a new current_locals will be set when the branch is started
    id = conf.python.iface.python.create_branch(f)
    current_locals = pre_branch_locals
    return id
    
def start_cli_script_branch(tokens):
    return start_script_branch(lambda:
                               run_and_report(lambda:
                                              evaluate_one(tokens, 0)))

def run(text, comp = 0, user_typed = 0, watch_eval_python = 0, no_execute = 0):
    global _last_cli_repeat
    global _last_cli_hap

    tokens = evaluate_one(tokenize(text), user_typed, no_execute)

    if tokens and tokens[0] != None:
        # Ugly hack to get command return value back to GUI frontend
        if watch_eval_python:
            if istoken(tokens[0], "int"):
                raise WatchCommandReturnValue, str(tokens[0][1])

        if user_typed:
            if istoken(tokens[0], "void"):
                pass
            elif quiettoken(tokens[0]):
                pass
            elif istoken(tokens[0], "int"):
                pr(number_str(tokens[0][1]) + "\n")
            else:
                pr(token_string(tokens) + "\n")

    # if there was a hap signaled, then the command should not be repeated
    # at all
    if _last_cli_hap:
        _last_cli_repeat = 0
        _last_cli_hap = 0

class run_command_stdout_class:
    def write(self, str):
        self.run_command_output += str
    def flush(self):
        pass
    def clear(self):
        self.run_command_output = ''
    def get_output(self):
        return self.run_command_output

run_command_stdout = run_command_stdout_class()

# <add-fun id="simics api python">
# <short>Run a CLI command</short>
# <namespace>cli</namespace>
#
# Runs a CLI command, or a CLI expression, as if it has been entered at the
# prompt. Errors are reported using CliError exception, and any return value
# from the command is returned by this function to Python.
#
# Note that the <tt>!</tt> and <tt>@</tt> modifiers are not supported
# when using <fun>run_command()</fun>.
#
# </add-fun>
def run_command(text):
    tokens = evaluate_one(tokenize(text), user_typed = 0)
    if tokens and tokens[0] != None:
        if istoken(tokens[0], "void") or quiettoken(tokens[0]):
            return None
        else:
            return tokens[0][1]
    return None

# <add-fun id="simics api python">
# <short>Run a CLI command and return output</short>
# <namespace>cli</namespace>
#
# Runs a CLI command, or a CLI expression, as if it has been entered at the
# prompt. Errors are reported using CliError exception.
#
# The <fun>quiet_run_command()</fun> is similar to <fun>run_command()</fun>
# but returns a tuple with the command return value as first entry, and the
# text output as the second.
#
# Note that the <tt>!</tt> and <tt>@</tt> modifiers are not supported
# when using <fun>quiet_run_command()</fun>.
#
# </add-fun>
def quiet_run_command(text):
    if sys.stdout == run_command_stdout:
        raise Exception, "quiet_run_command() can not be used recursively" 
    stdout = sys.stdout
    sys.stdout = run_command_stdout
    run_command_stdout.clear()
    try:
        return (run_command(text), run_command_stdout.get_output())
    finally:
        sys.stdout = stdout

def remove_newlines(tokens):
    pushed = []
    for i in range(len(tokens)):
        if istoken(tokens[i], '(') or istoken(tokens[i], '{'):
            pushed += [tokens[i][0]]
        elif istoken(tokens[i], ')'):
            if len(pushed) and pushed[-1] == '(':
                pushed.pop()
            else:
                raise CliSyntaxError, "unbalanced parentheses"
        elif istoken(tokens[i], '}'):
            if pushed[-1] == '{':
                pushed.pop()
            else:
                raise CliSyntaxError, "unbalanced parentheses"
        elif istoken(tokens[i], 'NL'):
            if pushed[-1] == '{':
                tokens[i] = (';',)
    return [x for x in tokens if not istoken(x, 'NL')]

def get_expr_end(tokens, first = '(', separator = None):
    if first == '(':
        last = ')'
    else:
        last = '}'
    par = 0
    pos = 1
    if not istoken(tokens[0], first):
        if not separator:
            return pos
        for i in range(1, len(tokens)):
            if istoken(tokens[i], separator):
                return i
        # TODO: generate error?
        return pos
    for i in range(1, len(tokens)):
        if istoken(tokens[i], first):
            par += 1
        elif istoken(tokens[i], last):
            if par == 0:
                # if () didn't end the expression, look for separator
                if (separator
                    and (len(tokens) > (i + 1))
                    and not istoken(tokens[i + 1], separator)):
                    return i + 1 + get_expr_end(tokens[i + 1:],
                                                None, separator)
                else:
                    return pos + 1
            par -= 1
        pos += 1
    raise CliSyntaxError, "unbalanced parentheses"

def evaluate_one(_tokens, user_typed, no_execute = 0):
    global _last_cli_repeat

    tokens = _tokens[:]

    # use a local copy to keep _last_cli_repeat as it was at the start
    loc_last_cli_repeat = _last_cli_repeat

    global current_locals
    old_locals = current_locals

    # put parentheses around the expression, if not already
    if len(tokens) and istoken(tokens[0], '{'):
        end = get_expr_end(tokens, '{')
        tokens[0] = '('
        tokens[end - 1] = ')'
        current_locals = simenv_class(old_locals)

    if (len(tokens) == 0
        or not istoken(tokens[0], "(")
        or len(tokens) != get_expr_end(tokens)):
        tokens = [("(",)] + tokens + [(")",)]

    object = None

    tokens = remove_newlines(tokens)

    # main eval loop

    while len(tokens) > 1:
        start = 0
        end = -1
        discard_result = 0

        # if is handled here or by the if command
        if (len(tokens) > 3
            and istoken(tokens[1], 'str')
            and tokens[1][1] == 'script-branch'):
            branch_end = get_expr_end(tokens[2:], '{')
            tokens[1:2 + branch_end] = [
                ('int',
                 start_cli_script_branch(tokens[2:2 + branch_end]))]

        elif (len(tokens) > 3
              and istoken(tokens[1], 'str')
              and tokens[1][1] in ('if', 'while')):
            cmpend = 2 + get_expr_end(tokens[2:], '(', '{')
            if len(tokens) > cmpend and tokens[cmpend][0] == '{':
                expend = cmpend + get_expr_end(tokens[cmpend:], '{')
            else:
                raise CliSyntaxError, ("missing { in %s statement"
                                       % tokens[1][1])
            elsend = 0

            cmptok = tokens[2:cmpend]
            exptok = tokens[cmpend:expend]

            check_if = tokens[1][1] == 'if'
            if_pos = 1
            ifexpend = expend

            while (check_if
                   and len(tokens) >= (ifexpend + 2) # minimal is else and ()
                   and istoken(tokens[ifexpend], 'str')
                   and tokens[ifexpend][1] == 'else'):
                if len(tokens) == (ifexpend + 2):
                    raise CliSyntaxError, "empty else statement"
                if tokens[ifexpend + 1][0] == '{':
                    elsend = ifexpend + 1 + get_expr_end(tokens[ifexpend + 1:],
                                                         '{')
                    check_if = False
                    elstok = tokens[expend + 1:elsend]
                else:
                    cmpend = (ifexpend + 2
                              + get_expr_end(tokens[ifexpend + 2:], '(', '{'))
                    if len(tokens) > cmpend and tokens[cmpend][0] == '{':
                        ifexpend = cmpend + get_expr_end(tokens[cmpend:], '{')
                    else:
                        raise CliSyntaxError, ("missing { in %s statement"
                                               % tokens[ifexpend + 1][1])

            if check_if:
                # in case last else was not handled in loop
                elsend = ifexpend
                elstok = tokens[expend + 1:elsend]

            ret = [('void', )]
            res = evaluate_one(cmptok, user_typed, no_execute)
            while len(res[0]) > 1 and (res[0][1] or res[0][1] == ''):
                ret = evaluate_one(exptok, user_typed, no_execute)
                if tokens[1][1] == 'if':
                    break
                res = evaluate_one(cmptok, user_typed, no_execute)

            if elsend:
                if len(res[0]) < 2 or not (res[0][1] or res[0][1] == ''):
                    ret = evaluate_one(elstok, user_typed, no_execute)
            else:
                elsend = expend

            tokens[1:elsend] = ret

        for i in range(1, len(tokens)):
            if istoken(tokens[i], "("):
                start = i
                break
            elif istoken(tokens[i], ";"):
                end = i + 1
                discard_result = 1
                tokens[i:i+1] = ((")",), ("(",))
                if user_typed:
                    _last_cli_repeat = 1
                break

        if start > 0:
            expend = start + get_expr_end(tokens[start:])
            sub = tokens[start:expend]
            del tokens[start:expend]
            rs = evaluate_one(sub, user_typed, no_execute)
            if istoken(rs[0], "void"):
                retval = None
            else:
                retval = rs[0][1]
            if (len(tokens) > start
                and istoken(tokens[start], "str")
                and tokens[start][1][0] == '.'
                # special case for '[' since we drop ']'
                and not (istoken(tokens[start - 1], "str")
                         and tokens[start - 1][1][0] == '[')):
                tokens[start] = (tokens[start][0],
                                 iff(retval, str(retval), '')
                                 + tokens[start][1])
            else:
                tokens[start:start] = rs
            continue
        else:
            if end < 0:
                end = len(tokens)
            sub = tokens[0:end]
            tokens = tokens[end:]
        
        if end == -1:
            raise CliSyntaxError, "unbalanced parentheses"

        if len(sub) == 2:
            tokens == tokens[2:]
            continue

        while 1:
            # now, find command with highest priority, this only
            # applies to non-namespace infix commands

            found = cmd = None
            hi_pri_pos = 0
            hi_pri = -1000000

            for i in range(len(sub)):
                if istoken(sub[i], "str") and not istoken(sub[i], "strval"):
                    cmd = simics_commands_dict(sub[i][1])
                if cmd and ((i == 1 and not cmd["infix"])
                            or cmd["infix"]
                            or cmd["name"] in ["%","~", "python", "$",
                                               "defined"]):
                    if cmd["pri"] > hi_pri:
                        # higher priority operator
                        hi_pri_pos = i
                        hi_pri = cmd["pri"]
                        found = cmd
                    elif cmd == found and cmd["infix"] and not cmd["left"]:
                        # right-associative infix operator
                        hi_pri_pos = i
                        hi_pri = cmd["pri"]
                        found = cmd
            i = hi_pri_pos

            # only allow assignment in position 2, i.e. ( foo = 1 ... )
            # requiered not to mess up with named args
            if found and found["name"] == "=" and i != 2:
                found = None

            # tokenizer handles "$<var> = " as a special case, that we have
            # to workaround if used as attribute name in  "<obj>->$<var> ="
            if (found and found['name'] == '->' and len(sub) > 3
                and istoken(sub[3], 'str') and sub[3][1][0] == '$'):
                sub[3:4] = [('(',), ('str', '$'),
                            ('str', sub[3][1][1:]), (')',)]
                break

            if found and found['name'] in ('->', '['):
                if (len(sub) > (i + 2) and istoken(sub[i + 2], 'str')
                    and sub[i + 2][1] == '='):
                    del sub[i + 2]
                    sub[i + 1:i + 1] = [('flag', '-w')]
                else:
                    sub[i + 2:i + 2] = [('flag', '-r')]
                    sub[i + 3:i + 3] = [('int', 0)]

            # help and appropos are handled special here, this allows 
            # help x->y for example
            if (istoken(sub[i], "str")
                and sub[i][1] in ["help", "h", "man", "apropos", "a"]):
                if (len(sub) > i + 2
                    and istoken(sub[i + 2], 'str')
                    and sub[i + 2][1] == '='):
                    # skip 'arg =' when following help
                    s = e = i + 3
                else:
                    s = e = i + 1
                arg = ''
                while not istoken(sub[e], ')'):
                    if istabcomplete(sub[e]) and len(sub[e][1]) == 1:
                        # do not merge single tab-complete with the string
                        break
                    arg += str(sub[e][1])
                    e += 1
                if arg:
                    sub[s:e] = [('strval', arg)]

            # if no command found, try to find one by prefix, first word within
            # brackets
            if not found:
                if istoken(sub[1], "str") and not istoken(sub[1], "strval"):
                    name = sub[1][1]
                    if len(name) and name[-1] == "\a":
                        name = name[:-1]

                    cmds = []

                    # needed if namespace command and exact match of command
                    exact_match = 0

                    # namespace
                    pos = string.find(name, ".")
                    if pos >= 0:
                        namespace = name[:pos]
                        name = name[pos+1:]
                        try:
                            object = SIM_get_object(namespace)
                        except:
                            raise CliParseError, ("No name space '"
                                                    + namespace + "'")

                        for cmd in simics_commands():
                            if instance_of(object, cmd["namespace"]):
                                if name == cmd["method"][:len(name)]:
                                    cmds.append(namespace + "."
                                                + cmd["method"])
                                    if not exact_match:
                                        found = cmd
                                        if name == cmd["method"]:
                                            exact_match = 1
                                if cmd["alias"]:
                                    for a in cmd["alias"]:
                                        if name == a[:len(name)]:
                                            cmds.append(namespace + "." + a)
                                            if not exact_match:
                                                found = cmd
                                                if name == a:
                                                    exact_match = 1
                    else:
                        for cmd in simics_commands():
                            tmp = get_completions(name,
                                                  [cmd["name"]] + cmd["alias"])
                            if not cmd["namespace"] and tmp:
                                found = cmd
                                cmds = cmds + tmp

                                if (len(tmp) == 1 and tmp[0] == name
                                    and not istabcomplete(sub[1])):
                                    exact_match = 1 	 
                                    break

                        for n in get_namespace_commands(name):
                            if n[:len(name)] == name:
                                cmds.append(n)
                            if n == name and not istabcomplete(sub[1]):
                                exact_match = 1
                                break

                    if len(sub[1][1]) and sub[1][1][-1] == "\a":
                        raise CliTabComplete, cmds

                    if not exact_match:
                        found = 0
                    else:
                        i = 1

            if not found:

                if len(sub) == 3:
                    if istoken(sub[1], "strval") or istoken(sub[1], "int"):
                        break

                if istoken(sub[1], "str"):
                    raise CliError, "unknown command '" + sub[1][1] + "'."

                if istoken(sub[1], "void"):
                    break

                raise CliParseError, "cannot understand that!"

            if (len(sub) > 3
                and istoken(sub[2], 'str') and sub[2][1] == '->'
                and istoken(sub[3], 'str') and sub[3][1][-1] == '\a'):

                # only for tab-completion of obj->attr
                name = sub[1][1]
                attr = sub[3][1][:-1]
                try:
                    object = SIM_get_object(name)
                except:
                    raise CliParseError, ("No name space '" + name + "'")
                attrs = get_completions(attr,
                                        VT_get_attributes(object.classname))
                raise CliTabComplete, map(lambda x: name + '->' + x, attrs)

            if not object and found["namespace"]:
                raise CliError, ("A classname cannot be used as a namespace."
                                   + " An instance name must be used. ")
            del sub[i]
            if found["infix"] and i > found["infix"]:
                i = i - found["infix"]

            # save the object for tab completion stuff
            found["object"] = object

            (args, num) = _arg_interpreter(found,
                                           copy_arg_list(found["args"]),
                                           sub[i:])
            del sub[i:i+num]

            if no_execute:
                sub[i:i] = [("void",)]
                continue

            if user_typed and (loc_last_cli_repeat == 2) and (found["repeat"]):
                retval = apply(found["repeat"],
                               iff(object, [object], []) + args)
                # repeat because another command may have changed that
                _last_cli_repeat = 2
            else:
                if found['deprecated']:
                    global deprecated_warned
                    
                    if not found['fun'] in deprecated_warned.keys():
                        deprecated_warned[found['fun']] = 1
                        print ("Warning: This command is deprecated. "
                               "Use %s instead." % found['deprecated'])
                        print
                        if conf.prefs.fail_on_warnings:
                            SIM_quit(1)

                retval = apply(found["fun"], iff(object, [object], []) + args)
                if user_typed:
                    if found["repeat"]:
                        _last_cli_repeat = 2

            if SIM_command_problem_status():
                raise CliError

            if isinstance(retval, tuple):
                quiet = True
                retval = retval[0]
            else:
                quiet = False

            object = None
            no_break = 0
            if (len(sub[i:])
                and istoken(sub[i], "str")
                and sub[i][1].startswith('.')):
                sub[i] = (sub[i][0], iff(retval, str(retval), "") + sub[i][1])
                if len(sub) == 3:
                    no_break = 1
            elif isinstance(retval, (int, long)):
                sub[i:i] = [("int", retval, quiet)]
            elif isinstance(retval, str):
                sub[i:i] = [("str", retval, quiet)]
            elif isinstance(retval, float):
                sub[i:i] = [("float", retval, quiet)]
            elif isinstance(retval, type(conf.sim)):
                sub[i:i] = [("str", retval.name, quiet)]
            else:
                sub[i:i] = [("void",)]
            if len(sub) <= 3 and not no_break:
                break

        if discard_result:
            continue

        tokens[0:0] = [sub[1]]

    current_locals = old_locals
    if len(tokens):
        return tokens
    else:
        return [('void', )]

def get_completions(comp, list):
    l = []
    for cc in list:
        if cc[:len(comp)] == comp:
            l.append(cc)
    return l

def proto_cmd_complete(req):
    global _is_filename_completion
    _is_filename_completion = 0
    
    cmd, id, text = req
        
    try:
        run(text + "\a", len(text), 0, 0, no_execute = 1)
    except CliTabComplete, ex:
        VT_send_control_msg(['reply', id,
                             _is_filename_completion, ex.value()])
    except:
        VT_send_control_msg(['reply', id,
                             _is_filename_completion, []])

# rlcompleter may not be available everywhere
try:
    import rlcompleter
except ImportError:
    rlcompleter = None

def generic_tab_complete(add_func, text, word, start, end):
    if end > 0 and text[0] == '@':
        if not rlcompleter:
            return
        # Add completion for simple python expressions immediately
        # following the '@' sign, for example @conf.cpu0.<tab>
        obj = rlcompleter.Completer()
        i = 0
        actual = text[1:end]
        while 1:
            try:
                choice = obj.complete(actual, i)
            except StandardError:
                break
            except SimExc_PythonTranslation:
                break
            if not choice:
                break
            if choice.startswith(actual):
                add_func('@' + choice)
            i += 1
        return
    try:
        run(text[:end]+"\a "+text[end:], end, 0, 0, no_execute = 1)
    except CliTabComplete, ex:
        for t in ex.value():
            add_func(t)
    except:
        pass

def tab_complete(arg, obj, text, word, start, end):
    generic_tab_complete(VT_add_completion, text, word, start, end)
    
def collect_completions(text, word, start, end):
    global show_tab_complete_dirs
    all = []
    def collect(t):
        all.append(t)
    show_tab_complete_dirs = True
    generic_tab_complete(collect, text, word, start, end)
    show_tab_complete_dirs = False
    return all

try:
    SIM_hap_add_callback("Python_Tab_Completion", tab_complete, None)
except:
    print "SIM_hap_add_callback() failed.",
    print "This is ok when generating documentation."

def cli_sim_stop_cb(arg, obj, exc, str):
    global _last_cli_hap

    if (exc == SimExc_Break.number):
        _last_cli_hap = 1 # signal a hap for run()

# add the callback to the Core_Simulation_Stopped Hap
if SIM_hap_add_callback("Core_Simulation_Stopped",
                        cli_sim_stop_cb, None) == -1:
    print "Failed to set cli.py callback"

# <add-fun id="simics api python">
# <short>evaluate a CLI command line</short>
# <namespace>cli</namespace>
#
# Evaluate a CLI command line as if it has been entered at the prompt.
# This is useful to re-use existing command code when writing Python scripts.
# Command errors are printed on the console, and not reported back to Python.
# Note that the <tt>!</tt> and <tt>@</tt> modifiers are not supported
# when using <fun>eval_cli_line()</fun>.
#
# </add-fun>
def eval_cli_line(text, user_typed = 0):
    global _last_cli_cmdline
    global _last_cli_cmdrepeat
    global _last_cli_repeat
    global _is_filename_completion

    _is_filename_completion = 0

    if not SIM_is_interactive():
        user_typed = 0

    # if we got a repeat command (empty text) then check and re-use the
    # previous command if running interactively
    if text == "" and user_typed:
        if _last_cli_repeat: # all kind of repeat
            text = _last_cli_cmdrepeat
            VT_logit("cli-repeat-last-command\n") # log in .simics-log
    elif text == "cli-repeat-last-command":
        text = _last_cli_cmdline
        VT_logit("cli-repeat-last-command\n") # log in .simics-log
    else:
        _last_cli_repeat = 0 # cancel repeat

    if text == "":
        return

    _last_cli_cmdline = text
    if user_typed:
        _last_cli_cmdrepeat = text

    run_and_report(lambda: run(text, 0, user_typed), user_typed)

# Support for Script branches

def wait_for_hap_common(arg):
    global current_locals, pre_branch_locals
    branch_locals = current_locals
    try:
        ret = SIM_get_attribute_idx(conf.python, "hap_sleep", arg)
    except:
        # will generate exception if branch was interrupted
        pre_branch_locals = current_locals
        current_locals = branch_locals
        raise SimExc_Break, "Script branch interrupted"
    pre_branch_locals = current_locals
    current_locals = branch_locals
    return ret

def wait_for_hap(hap_name):
    return wait_for_hap_common([hap_name, None])

def wait_for_hap_idx(hap_name, idx):
    return wait_for_hap_common([hap_name, None, idx])

def wait_for_hap_range(hap_name, idx0, idx1):
    return wait_for_hap_common([hap_name, None, idx0, idx1])

def wait_for_obj_hap(hap_name, obj, idx0 = -1, idx1 = -1):
    if obj:
        name = obj.name
    else:
        name = None
    if idx0 == -1:
        return wait_for_hap_common([hap_name, name])
    elif idx1 == -1:
        return wait_for_hap_common([hap_name, name, idx0])
    else:
        return wait_for_hap_common([hap_name, name, idx0, idx1])

import __main__

class unused_arg:
    pass

def start_branch(branch, arg = unused_arg()):
    if isinstance(branch, str):
        print "Warning: calling start_branch() with string is obsolete."
        print "         function: %s" % branch
        if conf.prefs.fail_on_warnings:
            SIM_quit(1)
        name = branch
        try:
            branch = eval("__main__." + name)
        except:
            print "start_branch(): Cannot find function %s" % name
            return
    if isinstance(arg, unused_arg):
        return start_script_branch(branch)
    else:
        return start_script_branch(lambda: branch(arg))

def fmt_value(value):
    if type(value) == type(conf.sim):
        return value.name
    elif type(value) == type([]):
        if value:
            l = [ fmt_value(v) for v in value ]
            return ", ".join(l)
        else:
            return "none"
    elif type(value) == type(None):
        return "none"
    else:
        return str(value)

def print_info(info, key_width = 20):
    fmt = "%%%ds :" % key_width
    for section, data in info:
        print
        if section:
            print "%s:" % section
        for key, value in data:
            print fmt % key, fmt_value(value)


Just_Right = 0
Just_Center = 1
Just_Left = 2

_column_disable = 0

#
# Print data in nicely formatted columns. Data is an array or arrays, where
# each entry in the "outer" array is a data row. Each entry in the inner array
# is a field in a column. Each column has a justification (Just_Right,
# Just_Center, or Just_Left) in the just array, which must have the same number
# of entries as every inner array of data.
#
# If has_title is true, data[0] is considered to contain column titles.
#
# column_space is the number of spaces added between each column.
#
# wrap_space is the text added between any "outer" columns.
#
# The inner arrays can optionally contain one extra element which will be
# printed on a line of its own after the "real" line. If such elements are
# present, column wrappning will never be done.
#
# The outer array can also contain strings, which are automatically converted
# to arrays containing just that element.
#
def print_columns(just, data, has_title = 1, column_space = 2,
                  wrap_space = " | "):
    global _column_disable

    def fix_fields(x):
        def fix_elements(y):
            if type(y) != type(""):
                return "%s" % y
            return y

        if type(x) != type([]):
            x = [ x ]
        return map(fix_elements, x)

    has_title = not not has_title

    data = map(fix_fields, data)

    has_extra = 0

    cols = len(just)

    if data == [] or cols <= has_title:
        return

    widths = [0] * len(data[0])
    for row in data:
        for i in range(0, cols):
            l = len(row[i])
            if l > widths[i]:
                widths[i] = l
        if len(row) > cols:
            has_extra = 1

    rwid = -column_space
    for i in range(0, cols):
        rwid = rwid + widths[i] + column_space

    if rwid <= 0:
        return

    if has_extra or _column_disable:
        columns = 1

    else:
        columns = ((terminal_width() - 1 + len(wrap_space))
                   / (rwid + len(wrap_space)))
        if columns > len(data) - has_title:
            columns = len(data) - has_title
        if columns < 1:
            columns = 1

    fields = len(data)
    if has_title:
        fields = fields + columns - 1

    rows = (fields + columns - 1) / columns

    for row in range(0, rows):
        line = ""
        for col in range(0, columns):
            if row == 0 and has_title:
                field = data[0]
            else:
                if has_title:
                    f = col * (rows - 1) + row
                else:
                    f = col * rows + row
                if f >= len(data):
                    field = [""] * cols
                else:
                    field = data[f]

            if col > 0:
                str = wrap_space
            else:
                str = ""
            for i in range(0, cols):
                if i > 0:
                    str = str + " " * column_space
                spc = widths[i] - len(field[i])
                if just[i] == Just_Right:
                    str = str + " " * spc + field[i]
                elif just[i] == Just_Center:
                    str += " " * (spc / 2) + field[i] + " " * ((spc + 1) / 2)
                else:
                    str += field[i] + " " * spc

            line = line + str
            if len(field) > cols:
                line = line + "\n" + field[cols]

        print line
        if row == 0 and has_title:
            print (("-" * (rwid + len(wrap_space) / 2) + "+" +
                    "-" * ((len(wrap_space) - 1) / 2)) * (columns - 1) +
                   "-" * rwid)

def enable_columns():
    global _column_disable
    if _column_disable > 0:
        _column_disable = _column_disable - 1

def disable_columns():
    global _column_disable
    _column_disable = _column_disable + 1

def _screen_resized(arg, obj, width, height):
    global _terminal_width, _terminal_height
    _terminal_width = width
    _terminal_height = height

SIM_hap_add_callback("Core_Screen_Resized", _screen_resized, None)

def set_screen_size(width, height):
    _screen_resized(None, None, width, height)

def print_simple_wrap_code(line, width):
    spaces = 0
    while spaces < len(line) and line[spaces] == ' ':
        spaces = spaces + 1

    if spaces >= width:
        print line
        return

    words = line.split()
    indent = " " * spaces
    while words:
        rem = width - len(indent) - len(words[0])
        print "%s%s" % (indent, words[0]),
        words = words[1:]
        while words and rem > len(words[0]):
            print words[0],
            rem = rem - len(words[0]) - 1
            words = words[1:]
        print
        indent = " " * spaces + "    "

def print_wrap_code(code, width):
    for line in code.splitlines():
        if len(line) <= width:
            print line
            continue

        print_simple_wrap_code(line, width)

def print_word_wrap(line, first_prefix, indent):
    words = line.split()
    prefix = first_prefix
    while words:
        print "%s%s" % (prefix, words[0]),
        rem = terminal_width() - 1 - len(prefix) - len(words[0])
        words = words[1:]
        while words and len(words[0]) < rem:
            rem = rem - len(words[0]) - 1
            print words[0],
            words = words[1:]
        print
        prefix = indent
        
# watch expression support
class WatchCommandReturnValue(Exception):
    pass

def promote_value(val):
    try:
        return long(str(val))
    except:
        return str(val)

def eval_cli_expr(expr):
    try:
        run(expr, 0, 0, watch_eval_python = 1)
    except WatchCommandReturnValue, msg:
        return promote_value(msg)

    return "?? (CLI command did not return a value)"

def eval_python_expr(expr):
    return promote_value(eval(expr))

def watch_expr(req):
    try:
        cmd, id, type, expr = req
        if type == "python":
            val = eval_python_expr(expr)
        elif type == "cli":
            val = eval_cli_expr(expr)
        else:
            raise Exception, "unknown expression type '%s'" % str(type)

        VT_send_control_msg(['reply', id, 1, val])

    except:
        _, value, _ = sys.exc_info()
        VT_send_control_msg(['reply', id, 0, str(value)])

def proto_cmd_pselect(req):
    # It's an internal error if this fails for some reason. It means that
    # the frontend has tried to set a CPU which doesn't exist.
    if len(req) == 2:
        id = req[1]
    elif len(req) == 3:
        id = req[1]
        cpu = req[2]
        set_current_processor(SIM_get_object(cpu))
    else:
        print "proto_cmd_pselect(): argument error"
        return

    try:
        name = current_processor().name
    except:
        name = ""
        
    VT_send_control_msg(['reply', id, name])


def proto_cmd_run(req):
    _, id = req
    eval_cli_line("run")
    VT_send_control_msg(["reply", id])

def proto_cmd_run_with_async_reply(req):
    _, id = req
    VT_send_control_msg(["reply", id])
    eval_cli_line("run")

def proto_cmd_single_step(req):
    _, id = req
    eval_cli_line("stepi")
    VT_send_control_msg(["reply", id])


def get_info_func_for_object(obj):
    import sim_commands
    return sim_commands.get_obj_funcs(obj)['get_info']

def get_status_func_for_object(obj):
    import sim_commands
    return sim_commands.get_obj_funcs(obj)['get_status']

def detuplify(l):
    if type(l) in [ types.TupleType, types.ListType ]:
        return [ detuplify(e) for e in l ]
    elif type(l) in [ types.StringType,
                      types.IntType,
                      types.BooleanType,
                      types.FloatType,
                      types.LongType ]:
        return l
    elif hasattr(l, "name"):
        return "object:" + l.name
    else:
        return str(l)

def proto_cmd_get_object_info(req):
    _, id, objname = req
    obj = SIM_get_object(objname)
    try:
        info_func = get_info_func_for_object(obj)
        info = detuplify(info_func(obj))
        VT_send_control_msg(["reply", id, info])
    except KeyError, msg:
        # info command not implemented
        VT_send_control_msg(["reply", id, []])

    
def proto_cmd_get_object_status(req):
    _, id, objname = req
    obj = SIM_get_object(objname)
    try:
        status_func = get_status_func_for_object(obj)
        status = detuplify(status_func(obj))
        VT_send_control_msg(["reply", id, status])
    except KeyError, msg:
        # status command not implemented
        VT_send_control_msg(["reply", id, []])
    
# hack to share commands.py (source) files between modules
def get_last_loaded_module():
    return VT_get_last_loaded_module()

# <add-fun id="simics api python">
# <short>return a non-allocated object name</short>
# <namespace>cli</namespace>
#
# Return an object name suitable for creating a new object
# (i.e., that has not been used yet) based on the <param>prefix</param>
# passed as argument.
#
# </add-fun>
def get_available_object_name(prefix):
    """Finds a name that isn't used by any existing object, by adding a number to the
    given prefix.  First prefix0 is tries, then prefix1, etc"""
    i = 0
    while 1:
        try:
            name = prefix + str(i)
            SIM_get_object(name)
        except SimExc_General:
            # This name is unused
            return name
        i += 1

def get_component_object(cmp_obj, obj_name):
    # make sure it is a conf object
    if type(cmp_obj) != type(conf.sim):
        raise Exception, ("First argument to get_component_object() is not a "
                          "conf_object_t")
    cmp = cmp_obj.object_data
    try:
        return eval('cmp.o.%s' % obj_name)
    except:
        raise Exception, "Component does not contain any %s object" % obj_name
