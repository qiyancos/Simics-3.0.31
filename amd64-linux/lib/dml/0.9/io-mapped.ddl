// This module defines the io-memory interface

dml 0.9;

implement io-memory {
    method map(addr_space_t memory_or_io,
               map_info_t info) -> (int status)
    {
        status = 0; // not used

        select bank in ($banks) where (defined bank.function
                                       && info.function == bank.function)
        {
            log info 4 (0) "Mapping %s at %#Px", defined bank.qname ? bank.qname : "bank" , info.base;
        } else {
            log error (0) "Unknown mapping of function %d", info.function;
        }
    }

    method operation(generic_transaction_t *mem_op,
                     map_info_t map_info) -> (exception_type_t ex)
    {
        ex = Sim_PE_No_Exception;
        select bank in ($banks) where (defined bank.function
                                       && map_info.function == bank.function)
        {
            local uint32 offset = (mem_op->physical_address - map_info.base + map_info.start);
            local uint32 size = mem_op->size;
            try
                call bank.access(mem_op, offset, size);
            except
                ex = Sim_PE_IO_Not_Taken;
        } else {
            log error (0) "Unknown access to function %d", map_info.function;
            ex = Sim_PE_IO_Not_Taken;
        }
    }
}

verbatim exception_type_t Sim_PE_No_Exception;
verbatim exception_type_t Sim_PE_Code_Break;
verbatim exception_type_t Sim_PE_Silent_Break;
verbatim exception_type_t Sim_PE_Inquiry_Outside_Memory;
verbatim exception_type_t Sim_PE_Inquiry_Unhandled;
verbatim exception_type_t Sim_PE_IO_Break;
verbatim exception_type_t Sim_PE_IO_Not_Taken;
verbatim exception_type_t Sim_PE_IO_Error;
verbatim exception_type_t Sim_PE_Interrupt_Break;
verbatim exception_type_t Sim_PE_Interrupt_Break_Take_Now;
verbatim exception_type_t Sim_PE_Exception_Break;
verbatim exception_type_t Sim_PE_Hap_Exception_Break;
verbatim exception_type_t Sim_PE_Stall_Cpu;
verbatim exception_type_t Sim_PE_Locked_Memory;
verbatim exception_type_t Sim_PE_Continue;
verbatim exception_type_t Sim_PE_Return_Break;
verbatim exception_type_t Sim_PE_Instruction_Finished;
verbatim exception_type_t Sim_PE_Default_Semantics;
verbatim exception_type_t Sim_PE_Ignore_Semantics;
verbatim exception_type_t Sim_PE_Speculation_Failed;
verbatim exception_type_t Sim_PE_Invalid_Address;
verbatim exception_type_t Sim_PE_MAI_Return;
verbatim exception_type_t Sim_PE_Error;

typedef struct {} map_demap_interface_t;
typedef struct {} memory_space_interface_t;
