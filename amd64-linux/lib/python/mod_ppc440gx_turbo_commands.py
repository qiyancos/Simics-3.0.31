import ppc_commands

ppc_model = 'ppc440gx'

funcs = {}
ppc_commands.setup_local_functions(ppc_model, funcs)
class_funcs = { ppc_model: funcs }

ppc_commands.enable_generic_ppc_commands(ppc_model)
ppc_commands.enable_4xx_tlb_commands(ppc_model)
ppc_commands.enable_440_tlb_commands(ppc_model)
