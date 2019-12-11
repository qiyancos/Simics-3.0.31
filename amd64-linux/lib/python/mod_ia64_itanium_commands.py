import ia64_commands

funcs = { 'print_disassemble_line':
          ia64_commands.local_print_disassemble_line,
          'pregs':
          ia64_commands.local_pregs,
          'diff_regs':
          ia64_commands.local_diff_regs }

class_funcs = { 'ia64-itanium': funcs }
