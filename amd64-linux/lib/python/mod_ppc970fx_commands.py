import ppc_commands

ppc_model = 'ppc970fx'

funcs = {}
ppc_commands.setup_local_functions(ppc_model, funcs)
class_funcs = { ppc_model: funcs }

ppc_commands.enable_generic_ppc_commands(ppc_model)
ppc_commands.enable_fpu_commands(ppc_model)
ppc_commands.enable_altivec_commands(ppc_model)
ppc_commands.enable_ppc64_commands(ppc_model)
