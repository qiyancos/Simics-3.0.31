// -*- mode: c; c-basic-offset: 4 -*-

dml 0.9;

bitslice-syntax: le;

log-group Register_Read;
log-group Register_Write;

constant false = (1 == 0);
constant true = (0 == 0);

verbatim void *NULL;

typedef int attr_kind_t;
verbatim attr_kind_t Sim_Val_Nil;
verbatim attr_kind_t Sim_Val_Integer;
verbatim attr_kind_t Sim_Val_List;
verbatim attr_kind_t Sim_Val_Invalid;
verbatim attr_kind_t Sim_Val_String;
verbatim attr_kind_t Sim_Val_Object;
verbatim attr_kind_t Sim_Val_Floating;
verbatim attr_kind_t Sim_Val_Data;

typedef int set_error_t;
verbatim set_error_t Sim_Set_Ok;
verbatim set_error_t Sim_Set_Illegal_Value;
verbatim set_error_t Sim_Set_Interface_Not_Found;

verbatim SIM_alloc_attr_list;
verbatim SIM_clear_exception;
verbatim SIM_get_interface;
verbatim SIM_get_mem_op_value_be;
verbatim SIM_get_mem_op_value_le;
verbatim SIM_log_error;
verbatim SIM_log_info;
verbatim SIM_log_undefined;
verbatim SIM_log_spec_violation;
verbatim SIM_log_target_error;
verbatim SIM_log_unimplemented;
verbatim SIM_make_attr_data;
verbatim SIM_make_attr_floating;
verbatim SIM_make_attr_integer;
verbatim SIM_make_attr_invalid;
verbatim SIM_make_attr_list;
verbatim SIM_make_attr_nil;
verbatim SIM_make_attr_object;
verbatim SIM_make_attr_string;
verbatim SIM_mem_op_is_read;
verbatim SIM_set_mem_op_value_be;
verbatim SIM_set_mem_op_value_le;
verbatim SIM_step_clean;
verbatim SIM_step_next_occurrence;
verbatim SIM_step_post;
verbatim SIM_time_clean;
verbatim SIM_time_next_occurrence;
verbatim SIM_time_post;
verbatim SIM_time_post_cycle;

verbatim VT_time_post;
verbatim VT_time_post_cycle;

verbatim VINIT;
verbatim VGET;
verbatim VADD;
verbatim VLAST;

verbatim UNALIGNED_STORE_BE16;
verbatim UNALIGNED_STORE_BE32;
verbatim UNALIGNED_STORE_BE64;
verbatim UNALIGNED_LOAD_BE16;
verbatim UNALIGNED_LOAD_BE32;
verbatim UNALIGNED_LOAD_BE64;

typedef int8 char;
typedef int32 int;
typedef int exception_type_t;

typedef int64 integer_t;
typedef int64 uinteger_t;

typedef struct {
    int kind;
    struct {
        int64 integer;
        double floating;
        char *string;
        conf_object_t *object;
        struct {
            integer_t size;
            attr_value_t *vector;
        } list;
        struct {
            integer_t size;
            uint8 *data;
        } data;
    } u;
} attr_value_t;

typedef struct {
    char *name;
    uint1 configured;
    conf_object_t *queue;
} conf_object_t;

typedef struct {
    int log_level;
} log_object_t;

typedef uint64 physical_address_t;
typedef uint64 logical_address_t;

// These are actually enums
typedef int mem_op_type_t;
typedef int ini_type_t;
typedef int arc_type_t;
typedef int addr_space_t;

typedef struct {} page_t;
typedef struct {} stall_id_t;

typedef struct {
    logical_address_t   logical_address;
    physical_address_t  physical_address;
    uint32              size;
    mem_op_type_t       type;
    uint1               atomic;
    uint1               inquiry;
    uint1               speculative;
    uint1               ignore;
    uint1               may_stall;
    uint1               ma_no_reissue;
    uint1               reissue;
    uint1               block_STC;
    uint1               use_page_cache;
    uint1               inverse_endian;
    uint2               page_cross;
    uint1               use_iostc;
    uint1               iostc_blocked;
    ini_type_t          ini_type;
    conf_object_t      *ini_ptr;
    int                 id;
    exception_type_t    exception;
    void               *user_ptr;
    char               *real_address;
    int                space_count;
    page_t             *page;
    physical_address_t  source_physical_address;
    arc_type_t          arc_type;
    int                 allocation_size;
    stall_id_t          stall_id;
} generic_transaction_t;

typedef struct {
    physical_address_t  base;
    physical_address_t  start;
    physical_address_t  length;
    int                 function;
    uint8               priority;
    int                 align_size;
    int                 reverse_endian;
} map_info_t;

template device {
    // structural info
    parameter objtype = "device";
    parameter parent                    auto;
    parameter dev                       = $this;
    parameter bank                      = undefined;
    parameter banks                     auto;

    // automatic parameters
    parameter name                      auto;
    parameter obj                       auto;
    parameter logobj                    auto;
    parameter qname                     = undefined;
    parameter classname                 default $name;

    // register defaults
    parameter documentation             default undefined;
    parameter register-size             default undefined;
    parameter byte-order                default "little-endian";

    method init() default { 
        foreach bank in ($banks)
            call bank.init;
    }
    method post_init() default { inline $finalize; }
    method finalize() default { }
    method hard-reset() default {
        foreach bank in ($banks)
            call bank.hard-reset;
    }
    method soft-reset() default {
        foreach bank in ($banks)
            call bank.soft-reset;
    }
}

template bank {
    is node;

    // structural info
    parameter objtype = "bank";
    parameter parent                    auto;
    parameter bank                      = $this;
    parameter mapped-registers          auto;
    parameter unmapped-registers        auto;

    // optional parameters
    parameter documentation             default undefined;
    parameter function                  default undefined;
    parameter overlapping               default false;
    parameter partial                   default false;

    // register defaults
    parameter signed                    default false;
    parameter allocate                  default true;
    parameter register-size             default $dev.register-size;
    parameter byte-order                default $dev.byte-order;

    method init() default { }

    method hard-reset default {
        foreach reg in ($mapped-registers)
            inline reg.hard-reset-register;
        foreach reg in ($unmapped-registers)
            inline reg.hard-reset-register;
    }

    method soft-reset default {
        foreach reg in ($mapped-registers)
            inline reg.soft-reset-register;
        foreach reg in ($unmapped-registers)
            inline reg.soft-reset-register;
    }

    method access(generic_transaction_t *memop, uint32 offset, uint32 size) default {
        if (size > 8) {
            log error (0) "Oversized access to %s", defined $name ? $name : "device";
            fail;
        }
        if (SIM_mem_op_is_read(memop) != 0) {
            inline $read-access-memop(memop, offset, size);
        } else {
            local uint64 writeval;
            inline $get-write-value(memop) -> (writeval);
            inline $write-access-memop(memop, offset, size, writeval);
        }
    }

    method get-write-value(generic_transaction_t *memop) -> (uint64 writeval) default {
        if (!defined $byte-order)
            error;
	writeval = ($byte-order == "little-endian"
		    ? SIM_get_mem_op_value_le(memop)
		    : SIM_get_mem_op_value_be(memop));
    }

    method set-read-value(generic_transaction_t *memop, uint64 value) default {
        if (!defined $byte-order)
            error;
	else if ($byte-order == "little-endian")
	    SIM_set_mem_op_value_le(memop, value);
	else
	    SIM_set_mem_op_value_be(memop, value);
    }

    method read-access-memop(generic_transaction_t *memop, uint32 offset, uint32 size) default {
	local bool success = 0;
	local uint64 value = 0;
        call $read-access(memop, offset, size) -> (success, value);
	if (!success) {
	    inline $miss-read-access(offset, size) -> (success, value);
	}
	if (!success) {
	    inline $miss-access(memop, offset, size);
	} else {
	    inline $finalize-read-access(memop, value);
	}
    }

    method finalize-read-access(generic_transaction_t *memop, uint64 val) default {
	inline $set-read-value(memop, val);
    }

    method read-access(generic_transaction_t *memop, uint32 offset, uint32 size) -> (bool success, uint64 value) default {
        inline $access2(memop, offset, size, true, undefined) -> (success, value);
    }

    method read(generic_transaction_t *memop, uint32 offset, uint32 size) -> (uint64 readvalue) default {
	local bool success; // will be ignored
        call $read-access(memop, offset, size) -> (success, readvalue);
    }

    method miss-read-access(uint32 offset, uint32 size) -> (bool success, uint64 value) default {
	success = false;
    }

    method write-access-memop(generic_transaction_t *memop, uint32 offset, uint32 size, uint64 value) default {
	local bool success = 0;
	call $write-access(memop, offset, size, value) -> (success);
	if (!success) {
	    inline $miss-write-access(offset, size, value) -> (success);
	}
	if (!success) {
	    inline $miss-access(memop, offset, size);
	} else {
	    inline $finalize-write-access(memop, value);
	}
    }

    method finalize-write-access(generic_transaction_t *memop, uint64 val) default {
	// do nothing
    }

    method write-access(generic_transaction_t *memop, uint32 offset, uint32 size, uint64 value) -> (bool success) default {
        inline $access2(memop, offset, size, false, value) -> (success, undefined);
    }

    method write(generic_transaction_t *memop, uint32 offset, uint32 size, uint64 writevalue) default {
	local bool success; // will be ignored
        call $write-access(memop, offset, size, writevalue) -> (success);
    }

    method miss-write-access(uint32 offset, uint32 size, uint64 value) -> (bool success) default {
	success = false;
    }

    // This is called with a constant 'isread'
    method access2(memop, offset, size, isread, writevalue) -> (success, readvalue) default {
	success = true;
        if (isread) {
            readvalue = 0;
        }

        if ($partial && $overlapping) {
            // overlapping allowed
            // partial allowed

            local uint8 lsb;
            local uint8 bitcount;

            // value_lsb is where the next register is to be placed in
            // opvalue
            local int value_lsb;
            if (!defined $byte-order)
                error;
            if ($byte-order == "little-endian")
                value_lsb = 0;
            else
                value_lsb = size * 8;

            foreach reg in ($mapped-registers) {

                if (reg.size == 1 && offset == reg.offset) {
                    // Access the register
                    if ($byte-order == "big-endian")
                        value_lsb = value_lsb - 8;

                    if (isread)
                        call reg.read-access(memop, 8, 0)
                            -> (readvalue[value_lsb + 7:value_lsb]);
                    else
                        call reg.write-access(memop, 8, 0, writevalue[value_lsb + 7:value_lsb]);

                    if (size == 1)
                        exit;

                    size = size - 1;
                    offset = offset + 1;

                    if ($byte-order == "little-endian")
                        value_lsb = value_lsb + 8;
                }
                if (reg.size != 1 && offset >= reg.offset && offset < (reg.offset + reg.size)) {
                    local typeof(offset) top;

                    top = offset + size;
                    if (top > reg.offset + reg.size)
                        top = reg.offset + reg.size;
                    bitcount = (top - offset) * 8;

                    // The accessed bits in the register
                    if ($byte-order == "little-endian") {
                        lsb = (offset - reg.offset) * 8;
                    } else {
                        lsb = (reg.offset + reg.size - top) * 8;
                        value_lsb = value_lsb - bitcount;
                    }

                    // Access the register
                    if (isread)
                        call reg.read-access(memop, lsb + bitcount, lsb)
                            -> (readvalue[value_lsb + (bitcount - 1):value_lsb]);
                    else
                        call reg.write-access(memop, lsb + bitcount, lsb,
                                                writevalue[value_lsb + (bitcount - 1):value_lsb]);

                    // This assumes that $mapped-registers is sorted
                    size = size - (top - offset);
                    offset = top;

                    if ($byte-order == "little-endian")
                        value_lsb = value_lsb + bitcount;

                    if (size == 0)
                        exit;
                }
            }
        } else if ($partial && !$overlapping) {
            // overlapping not allowed
            // partial allowed

            local uint8 lsb;
            local uint8 bitcount;

            foreach reg in ($mapped-registers) {

                if (reg.size == 1 && offset == reg.offset && size == 1) {
                    // Access the register
                    if (isread)
                        call reg.read-access(memop, 8, 0) -> (readvalue);
                    else
                        call reg.write-access(memop, 8, 0, writevalue);

                    exit;
                }
                if (reg.size != 1 && offset >= reg.offset && offset + size <= (reg.offset + reg.size)) {

                    bitcount = size * 8;

                    // The accessed bits in the register
                    if ($byte-order == "little-endian")
                        lsb = (offset - reg.offset) * 8;
                    else
                        lsb = (reg.offset + reg.size - (offset + size)) * 8;

                    // Access the register
                    if (isread)
                        call reg.read-access(memop, lsb + bitcount, lsb) -> (readvalue);
                    else
                        call reg.write-access(memop, lsb + bitcount, lsb, writevalue);

                    exit;
                }
            }
        } else if (!$partial && $overlapping) {
            // overlapping allowed
            // partial not allowed

            // value_lsb is where the next register is to be placed in
            // opvalue
            local int value_lsb;
            if (!defined $byte-order)
                error;
            if ($byte-order == "little-endian")
                value_lsb = 0;
            else
                value_lsb = size * 8;

            foreach reg in ($mapped-registers) {
                if (offset == reg.offset && size >= reg.size) {

                    if ($byte-order == "big-endian")
                        value_lsb = value_lsb - reg.size * 8;

                    if (isread)
                        call reg.read-access(memop, reg.bitsize, 0)
                            -> (readvalue[value_lsb + reg.size*8 - 1 : value_lsb]);
                    else
                        call reg.write-access(memop, reg.bitsize, 0,
                                                writevalue[value_lsb + reg.size*8 - 1 : value_lsb]);

                    size = size - reg.size;
                    if (size == 0) {
                        exit;
                    } else {
                        offset = offset + reg.size;

                        if ($byte-order == "little-endian")
                            value_lsb = value_lsb + reg.size * 8;
                    }
                }
            }
        } else if (!$partial && !$overlapping) {
            // overlapping not allowed
            // partial not allowed
            foreach reg in ($mapped-registers) {
                if (offset == reg.offset && size == reg.size) {
                    if (isread)
                        call reg.read-access(memop, reg.bitsize, 0) -> (readvalue);
                    else
                        call reg.write-access(memop, reg.bitsize, 0, writevalue);
                    exit;
                }
            }
        } else {
            error;
        }
	if (!$overlapping || size > 0) {
	    size = size; // suppress unused-variable warnings
	    success = false;
	}
    }

    parameter miss-bank default undefined;
    parameter miss-bank-offset default 0;

    // miss-access must take over responsibility for updating the memop!
    method miss-access(memop, offset, size) default {
        if (defined $name)
            log info 4 (0) "Missed in bank %s", $name;
        else
            log info 4 (0) "Missed in anonymous bank";
        if (defined $miss-bank) {
            call $miss-bank.access(memop, offset + $miss-bank-offset, size);
        } else {
            inline $log-miss(memop, offset, size);
            fail;
        }
    }

    method log-miss(memop, offset, size) {
        if (SIM_mem_op_is_read(memop) != 0)
            log spec-violation 1 (Register_Read)
                "%d byte %sread access at offset %#x%s outside registers or misaligned access",
                size, memop->inquiry ? "inquiry " : "",
                offset, defined $name ? " in "+$name : "";
        else
            log spec-violation 1 (Register_Write)
                "%d byte %swrite access at offset %#x%s outside registers or misaligned access",
                size, memop->inquiry ? "inquiry " : "",
                offset, defined $name ? " in "+$name : "";
    }

    method get(offset, size) -> (uint64 value) default {
        local int32 diff;
        value = 0;
        if (size > 8)
            fail;
        foreach reg in ($mapped-registers) {
            if ((offset + size > reg.offset) &&
                (offset < reg.offset + reg.size))
            {
                local uint64 val;
                inline reg.get -> (val);

                // Truncate end if the last bits are not included
                diff = (offset + size) - (reg.offset + reg.size);
                if (diff < 0)
                    val = val[reg.bitsize + diff * 8 - 1 : 0];

                // Shift value if the offsets don't match
                if (reg.offset > 0 && offset < reg.offset) {
                    val = val << ((reg.offset - offset) * 8);
                } else if (offset > reg.offset) {
                    val = val >> ((offset - reg.offset) * 8);
                }
                value = value | val;
            }
        }
    }

    method set(offset, size, value) default {
        local int32 diff;
        if (size > 8)
            fail;
        foreach reg in ($mapped-registers) {
            if ((offset + size > reg.offset) &&
                (offset < reg.offset + reg.size))
            {
                // Assume that we can do a reg.set(reg.get()) without side effects
                local typeof(reg) oldval;
                local typeof(value) val = value;
                local uint8 vallsb;
                local uint8 valmsb;
                local uint8 reglsb;
                local uint8 regmsb;

                inline reg.get -> (oldval);

                // Adjust msb
                diff = (offset + size) - (reg.offset + reg.size);

                if (diff > 0)
                    valmsb = (size - diff) * 8;
                else
                    valmsb = size * 8;

                if (diff < 0)
                    regmsb = (reg.size + diff) * 8;
                else
                    regmsb = reg.size * 8;

                // Adjust lsb
                diff = offset - reg.offset;

                if (diff < 0)
                    vallsb = (-diff) * 8;
                else
                    vallsb = 0;

                if (diff > 0)
                    reglsb = diff * 8;
                else
                    reglsb = 0;

                oldval[regmsb:reglsb] = value[valmsb:vallsb];
                inline reg.set(oldval);
            }
        }
    }
}

template node {
    parameter parent                    auto;
    parameter dev                       = $parent.dev;
    parameter bank                      default $parent.bank;

    parameter name                      auto;
    parameter desc                      default undefined;
    parameter index                     default undefined;
    parameter indexvar                  default undefined;

    parameter qname                     default
        (defined $parent.qname ? $parent.qname + "." : "")
        +
        (defined $name ? $name : "")
        +
        (defined $index ? "[" + # $index + "]" : "");
}

template group {
    is node;
    parameter objtype = "group";
}

template registerwithfields {
    //method hard-reset() {}
    //method soft-reset() {}
    //method read() -> (value) {}
    //method write(value) {}
}

template register {
    is node;
    is conf-attribute;

    // set this in template for a field to check it's not used for registers
    parameter notinregister = 0;

    // structural info
    parameter objtype = "register";
    parameter fields                    auto;

    // conf-attribute parameter
    parameter attr-type                 = "i";

    // logging parameters
    parameter logging                   default true;
    parameter read-logging              default $logging;
    parameter write-logging             default $logging;

    // required parameters
    parameter size                      default $bank.register-size;
    parameter bitsize                   = $size * 8;

    // optional parameters
    parameter documentation             default undefined;
    parameter offset                    default undefined;

    // Inherited parameters
    parameter signed                    default $bank.signed;
    parameter allocate                  default $bank.allocate;
    parameter byte-order                default $bank.byte-order;

    // Resetting
    parameter hard-reset-value default 0;
    parameter soft-reset-value default $hard-reset-value;

    method hard-reset-register default {
	if ($fields[0].explicit) {
	    foreach field in ($fields)
		inline field.hard-reset;
	} else {
	    // No explicit fields
	    inline $hard-reset;
	}
        inline $after-hard-reset;
    }

    method hard-reset() default {
        if ($allocate)
            $this = $hard-reset-value;
    }

    method after-hard-reset() default {
    }

    method soft-reset-register default {
	if ($fields[0].explicit) {
	    foreach field in ($fields)
		inline field.soft-reset;
	} else {
	    // No explicit fields
	    inline $soft-reset;
	}
        inline $after-soft-reset;
    }

    method soft-reset() default {
        if ($allocate)
            $this = $soft-reset-value;
    }

    method after-soft-reset() default {
    }

    method read() -> (value) default {
        if ($allocate) {
            value = $this;
        } else {
            log unimplemented 1 (Register_Read) "Can't read from %s", $qname;
            fail;
        }
    }

    method write(value) default {
        if ($allocate) {
            $this = value;
        } else {
            log error (Register_Write) "Can't write to %s", $qname;
            fail;
        }
    }

    method set-attribute(attr_value_t value) -> (set_error_t err) {
        try {
            inline $set(value.u.integer);
            inline $after-set;
            err = Sim_Set_Ok;
        } except {
            err = Sim_Set_Illegal_Value;
        }
    }

    method get-attribute -> (attr_value_t value) {
        value.kind = Sim_Val_Integer;
        inline $get -> (value.u.integer);
    }

    method set(value) default {
	if ($fields[0].explicit) {
	    foreach field in ($fields) {
		if ($bitsize == field.bitsize)
		    // Only one field
		    inline field.set(value);
		else
		    inline field.set(value[field.msb:field.lsb]);
	    }
	} else {
	    // No explicit fields
	    if ($allocate) {
		$this = value;
	    } else {
		log error (0) "set() not implemented for register %s", $qname;
		fail;
	    }
	}
    }

    method get() -> (value) default {
	if ($fields[0].explicit) {
	    local typeof($this) fieldval = 0;
	    foreach field in ($fields) {
		if ($bitsize == field.bitsize)
		    // Only one field
		    inline field.get() -> (fieldval);
		else {
		    inline field.get() -> (fieldval[field.msb:field.lsb]);
		}
	    }
	    value = fieldval;
	} else {
	    // No explicit fields
	    if ($allocate) {
		value = $this;
	    } else {
		log error (0) "get() not implemented for register %s", $qname;
		fail;
	    }
        }
    }

    method read-access(generic_transaction_t *memop,
                       uint8 msb1, uint8 lsb) -> (uint64 value) default {
	inline $read-access-main(memop, msb1, lsb) -> (value);
	inline $after-read(memop);
    }

    method read-access-main(memop, msb1, lsb) -> (value) default {
	if (defined msb1) {
	    // Possibly partial register access
	    local typeof($this) fieldval = 0;
	    if ($fields[0].explicit) {
		foreach field in ($fields) {
		    if ($bitsize == field.bitsize) {
			// Only one field
			inline field.read-access() -> (fieldval);
		    } else if ($bitsize == 8 || lsb <= field.msb && msb1 > field.lsb) {
			inline field.read-access() -> (fieldval[field.msb:field.lsb]);
		    }
		}
	    } else {
		// No explicit fields
		inline $read() -> (fieldval);
	    }
	    value = fieldval[msb1 - 1 : lsb];
	} else {
	    // Whole-register access
	    if ($fields[0].explicit) {
		foreach field in ($fields) {
		    if ($bitsize == field.bitsize)
			// Only one field
			inline field.read-access() -> (value);
		    else
			inline field.read-access() -> (value[field.msb:field.lsb]);
		}
	    } else {
		// No explicit fields
		inline $read() -> (value);
	    }
	}
	if ($read-logging)
	    log info 4 (Register_Read) "%s from register %s => %#x",
		memop->inquiry ? "Inquiry read" : "Read",
		$qname, value;
    }

    method write-access(generic_transaction_t *memop,
                        uint8 msb1, uint8 lsb, uint64 value) default {
	inline $write-access-main(memop, msb1, lsb, value);
	inline $after-write(memop);
    }

    method write-access-main(memop, msb1, lsb, value) default {
	if ($write-logging)
	    log info 4 (Register_Write) "%s to register %s <= %#x",
		memop->inquiry ? "Inquiry write" : "Write",
		$qname, value;
	if (defined msb1) {
	    // Possibly partial register access
	    if ($fields[0].explicit) {
		foreach field in ($fields) {
		    if (lsb <= field.msb && (field.lsb == 0 || msb1 > field.lsb)) {
			if (lsb > field.lsb || msb1 - lsb < field.bitsize) {
			    // Partial access
			    local typeof($this) fieldval = 0;
			    if ($bitsize == field.bitsize) {
				// Only one field
				inline field.get -> (fieldval);
				fieldval[msb1 - 1:lsb] = value;
				inline field.write-access(fieldval);
			    } else {
				inline field.get -> (fieldval[field.msb:field.lsb]);
				fieldval[msb1 - 1:lsb] = value;
				inline field.write-access(fieldval[field.msb:field.lsb]);
			    }
			} else {
			    // Whole-field access
			    if ($bitsize == field.bitsize)
				// Only one field
				inline field.write-access(value);
			    else
				inline field.write-access((value << lsb)[field.msb:field.lsb]);
			}
		    }
		}
	    } else {
		// No explicit fields
		if (lsb > 0 || msb1 - lsb < $bitsize) {
		    // Partial access
		    local typeof($this) fieldval = 0;
		    inline $get -> (fieldval);
		    fieldval[msb1 - 1:lsb] = value;
		    inline $write(fieldval);
		} else {
		    // Whole-field access
		    inline $write(value);
		}
	    }
	} else {
	    // Whole-register access
	    if ($fields[0].explicit) {
		foreach field in ($fields) {
		    if ($bitsize == field.bitsize)
			// Only one field
			inline field.write-access(value);
		    else
			inline field.write-access(value[field.msb:field.lsb]);
		}
	    } else {
		// No explicit fields
		inline $write(value);
	    }
	}
    }

    method after-read(memop) default {
        // no default action
    }

    method after-write(memop) default {
        // no default action
    }
}

template field {
    is node;

    // set this in template for a register to check it's not used for fields
    parameter notinfield = 0;

    // structural info
    parameter objtype = "field";
    parameter reg                       = $parent;

    // whether this field was explicitly declared
    parameter explicit                  auto;
    parameter qname                     = ($explicit
                                           ? $parent.qname + "." + $name
                                           : $parent.qname);


    // required parameters
    parameter lsb;
    parameter msb;
    parameter bitsize = $msb - $lsb + 1;

    // optional parameters
    parameter documentation default undefined;

    // Inherited parameters
    parameter signed           default $reg.signed;
    parameter allocate         default $reg.allocate;
    parameter hard-reset-value default $reg.hard-reset-value;
    parameter soft-reset-value default $reg.soft-reset-value;

    method hard-reset() default {
	if ($allocate)
	    $this = $hard-reset-value;
    }

    method soft-reset() default {
	if ($allocate)
	    $this = $soft-reset-value;
    }

    method read() -> (value) default {
	if ($allocate) {
	    value = $this;
	} else {
	    log error (Register_Read) "Can't read from %s", $qname;
	    fail;
	}
    }

    method write(value) default {
        if ($allocate) {
            $this = value;
        } else {
            log error (Register_Write) "Can't write to %s", $qname;
            fail;
        }
    }

    method set(value) default {
        if ($allocate)
            $this = value;
        else {
            log error (0) "set() not implemented for register %s", $qname;
        }
    }

    method get() -> (value) default {
        if ($allocate)
            value = $this;
        else {
            log error (0) "get() not implemented for register %s", $qname;
            value = 0;
        }
    }

    method read-access() -> (value) default {
        inline $read -> (value);
    }

    method write-access(value) default {
        inline $write(value);
    }
}

template connect {
    is node;
    is conf-attribute;
    parameter objtype = "connect";

    parameter documentation default undefined;

    parameter interfaces auto;
    parameter attr-type = $configuration == "required" ? "o" : "o|n";

    method set-attribute(attr_value_t value) -> (set_error_t err) {
        local conf_object_t *obj = value.kind == Sim_Val_Object ? value.u.object : NULL;

        if (obj) {
            foreach iface in ($interfaces) {
                try
                    inline iface.verify(obj);
                except {
                    err = Sim_Set_Interface_Not_Found;
                    exit;
                }
            }
        }

        // Commit the change
        $this = obj;
        foreach iface in ($interfaces)
            inline iface.connect(obj);

        inline $after-set;
        err = Sim_Set_Ok;
    }

    method get-attribute -> (attr_value_t value) {
        value = SIM_make_attr_object($this);
    }
}

template interface {
    is node;
    parameter objtype = "interface";

    parameter required default true;
    parameter c-type default $name + "_interface_t";
    parameter c-name default $name;

    // Check that the interface exists, if required
    method verify(conf_object_t *obj) {
        if ($required && SIM_get_interface(obj, $name) == NULL) {
            SIM_clear_exception();
            log error (0) "The %s object does not implement the required %s interface",
                obj->name, $name;
            fail;
        }
    }

    // Get the interface from another object
    method connect(conf_object_t *obj) {
        if (obj) {
            $this = SIM_get_interface(obj, $name);
            SIM_clear_exception();
        } else
            $this = NULL;
    }
}

template attribute {
    is node;
    is conf-attribute;
    parameter objtype = "attribute";

    parameter documentation             default undefined;
    parameter attr-type                 = $type;

    parameter allocate-type             default undefined;
    parameter type                      default (!defined $allocate-type ? undefined
                                                 : $allocate-type == "string" ? "s"
                                                 : $allocate-type == "uint8" ? "i"
                                                 : $allocate-type == "uint16" ? "i"
                                                 : $allocate-type == "uint32" ? "i"
                                                 : $allocate-type == "uint64" ? "i"
                                                 : $allocate-type == "int8" ? "i"
                                                 : $allocate-type == "int16" ? "i"
                                                 : $allocate-type == "int32" ? "i"
                                                 : $allocate-type == "int64" ? "i"
                                                 : $allocate-type == "bool" ? "i"
                                                 : $allocate-type == "double" ? "f"
                                                 : undefined);

    method get -> (attr_value_t value) default {
        if (!defined $allocate-type)
            value = SIM_make_attr_invalid();
        else if ($type == "i")
            value = SIM_make_attr_integer($this);
        else if ($type == "s")
            value = SIM_make_attr_string($this);
        else if ($type == "f")
            value = SIM_make_attr_floating($this);
        else
            value = SIM_make_attr_invalid();
    }
    method set(attr_value_t value) default {
        if (!defined $allocate-type)
            fail;
        else if ($type == "i")
            $this = value.u.integer; // no check for range
        else if ($type == "s") {
            MM_FREE($this);
            $this = MM_STRDUP(value.u.string);
        } else if ($type == "f")
            $this = value.u.floating;
        else
            fail;
    }

    method set-attribute(attr_value_t value) -> (set_error_t err) {
        err = Sim_Set_Ok;
        try {
            inline $set(value);
            inline $after-set;
        } except
            err = Sim_Set_Illegal_Value;
    }

    method get-attribute -> (attr_value_t value) {
        try
            inline $get -> (value);
        except
            value = SIM_make_attr_invalid();
    }
}

template conf-attribute {
    parameter configuration             default "optional";
    parameter persistent                default false;
    parameter attr-type;

    method after-set default {
    }
}

template event {
    is node;
    parameter objtype = "event";
    parameter parent                    auto;
    parameter name                      auto;

    parameter documentation             default undefined;

    parameter repeat                    default undefined;
    parameter timebase                  default "seconds";

    method describe-event(void *data) -> (char *description) default {
        if (defined $desc)
            description = $desc;
        else
            description = $qname;
    }

    method get-event-info(void *data) -> (attr_value_t info) default {
        info = SIM_make_attr_nil();
    }

    method set-event-info(attr_value_t info) -> (void *data) default {
        if (info.kind != Sim_Val_Nil) {
            log error (0) "Strange event info";
        }
    }

    method post(when, data) {
        if ($timebase == "steps")
            SIM_step_post($dev.obj, when, $this.callback, data);
        else if ($timebase == "cycles")
            SIM_time_post_cycle($dev.obj, when, 0, $this.callback, data);
        else if ($timebase == "seconds")
            SIM_time_post($dev.obj, when, 0, $this.callback, data);
        else if ($timebase == "stacked")
            SIM_stacked_post($dev.obj, $this.callback, data);
        else
            error;
    }

    method post_on_queue(queue, when, data) {
        assert when >= 0;
        if ($timebase == "steps")
            error;              // no VT_step_post implemented yet
        else if ($timebase == "cycles") {
            // log info 1 (0) "Posting on queue %s in %d %s", queue->name, when, $timebase;
            VT_time_post_cycle(queue, $dev.obj, when, 0, $this.callback, data);
        } else if ($timebase == "seconds") {
            // log info 1 (0) "Posting on queue %s in %g %s", queue->name, when, $timebase;
            VT_time_post(queue, $dev.obj, when, 0, $this.callback, data);
        } else
            error;
    }

    method remove(data) {
        if ($timebase == "steps")
            SIM_step_clean($dev.obj, $this.callback, data);
        else if ($timebase == "cycles" || $timebase == "seconds")
            SIM_time_clean($dev.obj, 0, $this.callback, data);
        else
            error;
    }

    export method callback(void *param) {
        if (defined $repeat)
            inline $post($repeat, param);
        try
            inline $event(param);
        except
            log error (0) "Error in %s event", $qname;
    }

    method next(data) -> (when) {
	// next() always returns negative for 'not in queue'
        if ($timebase == "steps")
            when = SIM_step_next_occurrence($dev.obj, $this.callback, data) - 1;
        else if ($timebase == "cycles")
            when = SIM_time_next_occurrence($dev.obj, $this.callback, data) - 1;
        else if($timebase == "seconds") {
            local cycles_t queue_cycles = SIM_time_next_occurrence($dev.obj, $this.callback, data);
            if (queue_cycles == 0)
                when = -1.0;
            else {
                inline $get_queue_frequency();
                when = cast(queue_cycles - 1, double) / cast($queue_frequency, double);
            }
        }
        else
            error;
    }

    method posted(data) -> (truth) {
        if ($timebase == "steps")
            truth = (SIM_step_next_occurrence($dev.obj, $this.callback, data)
                     != 0);
        else
            truth = (SIM_time_next_occurrence($dev.obj, $this.callback, data)
                     != 0);
    }

    method start {
        local next;

        if (!defined $repeat)
            error;

        inline $next(NULL) -> (next);
        if (next == 0)
            inline $post($repeat, NULL);
    }

    method stop {
        if (!defined $repeat)
            error;

        inline $remove(NULL);
    }
}

template implement {
    parameter objtype = "implement";
    parameter parent                    auto;
    parameter name                      auto;
    parameter dev                       = $parent.dev;

    parameter c-type default $name + "_interface_t";
}

template data {
    parameter objtype = "implement";
    parameter parent                    auto;
    parameter name                      auto;
    parameter dev                       = $parent.dev;
}
