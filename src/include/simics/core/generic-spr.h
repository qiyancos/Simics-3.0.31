/*
  Copyright 2006-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 */

#ifndef __SIMICS_CORE_GENERIC_SPR_H__
#define __SIMICS_CORE_GENERIC_SPR_H__

/* <add-type id="gen_spr_access_type_t def"></add-type> */
typedef enum {
        /* Access from a mfspr/mtspr instruction */
        Sim_Gen_Spr_Instruction_Access,

        /* Access through attribute */
        Sim_Gen_Spr_Attribute_Access,

        /* Access through int_register interface */
        Sim_Gen_Spr_Int_Register_Access,

        /* For compatibility with former PPC-only implementation */
        Sim_PPC_Spr_Instruction_Access  = Sim_Gen_Spr_Instruction_Access,
        Sim_PPC_Spr_Attribute_Access    = Sim_Gen_Spr_Attribute_Access,
        Sim_PPC_Spr_Int_Register_Access = Sim_Gen_Spr_Int_Register_Access
} gen_spr_access_type_t;

/* <add-type id="gen_spr_ret_t def"></add-type> */
typedef enum {
        Sim_Gen_Spr_Ok,        /* SPR access was OK */
        Sim_Gen_Spr_Illegal,   /* SPR access should trigger illegal insn exc */
        Sim_Gen_Spr_Privilege, /* SPR access should trigger privilege exc */
        
        /* For compatibility with former PPC-only implementation */
        Sim_PPC_Spr_Ok        = Sim_Gen_Spr_Ok,
        Sim_PPC_Spr_Illegal   = Sim_Gen_Spr_Illegal,
        Sim_PPC_Spr_Privilege = Sim_Gen_Spr_Privilege
} gen_spr_ret_t;

#ifndef TURBO_SIMICS
/* <add-type id="gen_spr_user_getter_func_t type"></add-type> */
typedef gen_spr_ret_t (*gen_spr_user_getter_func_t)
        (conf_object_t *cpu,
         integer_t spr_number,
         gen_spr_access_type_t type,
         lang_void *user_data);

/* <add-type id="gen_spr_user_setter_func_t type"></add-type> */
typedef gen_spr_ret_t (*gen_spr_user_setter_func_t)
        (conf_object_t *cpu,
         integer_t spr_number,
         uinteger_t value,
         gen_spr_access_type_t type,
         lang_void *user_data);
#endif  /* !TURBO_SIMICS */

#endif  /* !__SIMICS_CORE_GENERIC_SPR_H__ */
