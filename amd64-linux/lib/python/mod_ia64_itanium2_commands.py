import ia64_commands

funcs = { 'print_disassemble_line':
          ia64_commands.local_print_disassemble_line,
          'pregs':
          ia64_commands.local_pregs }

class_funcs = { 'ia64-itanium2': funcs }
