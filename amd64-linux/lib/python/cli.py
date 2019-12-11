# interface module, re-exporting stuff from cli_impl.py

# see programming guide for list of supported symbols

from cli_impl import \
terminal_width, terminal_height, \
set_output_radix, get_output_radix, get_output_group, \
number_str, \
iff, \
str_t, int_t, range_t, float_t, flag_t, addr_t, filename_t, obj_t, \
string_set_t, bool_t, \
get_command_categories, get_synopsis, \
hex_str, \
set_current_processor, current_processor, \
assert_cpu, get_cpu, cpu_expander, object_expander, \
pr, \
bold, \
italic, \
format_print, \
hap_c_arguments, \
format_commands_as_html, \
simics_commands, \
internals, internals_off, \
getenv, setenv, \
new_command, \
arg, \
instance_of, \
run, \
get_completions, \
eval_cli_line, \
wait_for_hap, wait_for_hap_idx, wait_for_hap_range, \
wait_for_obj_hap, \
start_branch, \
print_info, \
print_columns, enable_columns, disable_columns, \
print_wrap_code, \
eval_cli_expr, \
watch_expr, \
proto_cmd_complete, \
proto_cmd_pselect, \
proto_cmd_run, \
proto_cmd_run_with_async_reply, \
proto_cmd_single_step, \
proto_cmd_get_object_info, \
proto_cmd_get_object_status, \
get_last_loaded_module, \
get_available_object_name, \
simics_command_exists, \
int64_t, sint64_t, uint64_t, int32_t, sint32_t, uint32_t, integer_t, \
simenv, get_current_locals, \
Just_Right, Just_Center, Just_Left, \
get_component_object, \
collect_completions, \
set_screen_size, \
get_format_string, \
set_default_format, \
stderr, \
run_command, quiet_run_command, \
CliError

# A lot of modules import * from cli and expect the simics API to follow,
# so we include this for compatibility for now. Let's hope we can remove it
# later.
from sim_core import *

# They also expect other imports to follow
import conf
