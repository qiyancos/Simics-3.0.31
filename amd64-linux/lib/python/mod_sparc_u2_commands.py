import sparc_v9_commands

funcs = { 'print_disassemble_line':
          sparc_v9_commands.local_print_disassemble_line,
          'pregs':
          sparc_v9_commands.local_pregs,
          'print_pstate_bits':
          sparc_v9_commands.print_pstate_bits,
          'global_set_names':
          sparc_v9_commands.global_set_names,
          'get_pending_exception_string':
          sparc_v9_commands.local_pending_exception }

class_funcs = { 'ultrasparc-ii': funcs }

sparc_v9_commands.register_diff_registers(funcs, "ultrasparc-ii")
