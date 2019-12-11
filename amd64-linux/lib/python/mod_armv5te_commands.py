import arm_commands

funcs = { 'print_disassemble_line':
          arm_commands.local_print_disassemble_line,
          'pregs':
          arm_commands.local_pregs,
          'diff_regs':
          arm_commands.arm_diff_regs,
          'get_pending_exception_string':
          arm_commands.local_pending_exception }

class_funcs = { 'armv5te': funcs }
