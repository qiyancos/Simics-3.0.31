import alpha_commands

funcs = { 'print_disassemble_line':
          alpha_commands.local_print_disassemble_line,
          'pregs':
          alpha_commands.local_pregs }

class_funcs = { 'alpha-ev5': funcs }
