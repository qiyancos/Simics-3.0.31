/*
 * simics/arch/sparc.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_ARCH_SPARC_API_H
#define _SIMICS_ARCH_SPARC_API_H

#ifndef TURBO_SIMICS

#if defined(TARGET_SPARC_V9)
/*
 * SPARC V9 architecture defined ASIs
 */
#define ASI_NUCLEUS                         (0x04)
#define ASI_NUCLEUS_LITTLE                  (0x0c)
#define ASI_AS_IF_USER_PRIMARY              (0x10)
#define ASI_AS_IF_USER_SECONDARY            (0x11)
#define ASI_AS_IF_USER_PRIMARY_LITTLE       (0x18)
#define ASI_AS_IF_USER_SECONDARY_LITTLE     (0x19)
#define ASI_PRIMARY                         (0x80)
#define ASI_SECONDARY                       (0x81)
#define ASI_PRIMARY_NOFAULT                 (0x82)
#define ASI_SECONDARY_NOFAULT               (0x83)
#define ASI_PRIMARY_LITTLE                  (0x88)
#define ASI_SECONDARY_LITTLE                (0x89)
#define ASI_PRIMARY_NOFAULT_LITTLE          (0x8a)
#define ASI_SECONDARY_NOFAULT_LITTLE        (0x8b)
#endif /* TARGET_SPARC_V9 */

#if defined(TARGET_ULTRA)
/*
 * Ultra ASIs
 */
#define ASI_PHYS_USE_EC                     (0x14)
#define ASI_PHYS_BYPASS_EC_WITH_EBIT        (0x15)
#define ASI_PHYS_USE_EC_LITTLE              (0x1c)
#define ASI_PHYS_BYPASS_EC_WITH_EBIT_LITTLE (0x1d)

/* Atomic quad load ASIs. Can only be used with ldda */
#define ASI_NUCLEUS_QUAD_LDD                (0x24)
#define ASI_NUCLEUS_QUAD_LDD_L              (0x2c)

#if defined(TARGET_NIAGARA)
#define ASI_SCRATCHPAD                       0x20
#define ASI_MMU_CONTEXTID                    0x21

#define ASI_QUEUE                            0x25

#define ASI_QUAD_LDD_REAL                    0x26
#define ASI_QUAD_LDD_REAL_L                  0x2e

#define ASI_DMMU_CTXT_ZERO_TSB_BASE_PS0      0x31
#define ASI_DMMU_CTXT_ZERO_TSB_BASE_PS1      0x32
#define ASI_DMMU_CTXT_ZERO_CONFIG            0x33
#define ASI_IMMU_CTXT_ZERO_TSB_BASE_PS0      0x35
#define ASI_IMMU_CTXT_ZERO_TSB_BASE_PS1      0x36
#define ASI_IMMU_CTXT_ZERO_CONFIG            0x37
#define ASI_DMMU_CTXT_NONZERO_TSB_BASE_PS0   0x39
#define ASI_DMMU_CTXT_NONZERO_TSB_BASE_PS1   0x3a
#define ASI_DMMU_CTXT_NONZERO_CONFIG         0x3b
#define ASI_IMMU_CTXT_NONZERO_TSB_BASE_PS0   0x3d
#define ASI_IMMU_CTXT_NONZERO_TSB_BASE_PS1   0x3e
#define ASI_IMMU_CTXT_NONZERO_CONFIG         0x3f
#define ASI_STREAM_MA                        0x40
#define ASI_SPARC_BIST                       0x42
#define ASI_ERROR_INJECT_REG                 0x43
#define ASI_STM_CTL_REG                      0x44

#define ASI_HV_SCRATCHPAD                    0x4f
#define ASI_TLB_INVALIDATE_ALL               0x60

#define ASI_AIUP_BLK_INIT_QUAD_LDD           0x22
#define ASI_AIUS_BLK_INIT_QUAD_LDD           0x23
#define ASI_NUCL_BLK_INIT_QUAD_LDD           0x27
#define ASI_AIUP_BLK_INIT_QUAD_LDD_L         0x2a
#define ASI_AIUS_BLK_INIT_QUAD_LDD_L         0x2b
#define ASI_NUCL_BLK_INIT_QUAD_LDD_L         0x2f
#define ASI_PRIM_BLK_INIT_QUAD_LDD           0xe2
#define ASI_SCND_BLK_INIT_QUAD_LDD           0xe3
#define ASI_PRIM_BLK_INIT_QUAD_LDD_L         0xea
#define ASI_SCND_BLK_INIT_QUAD_LDD_L         0xeb
#endif   /* TARGET_NIAGARA */

#if defined(ULTRA_HAS_LDD_PHYS)
#define ASI_QUAD_LDD_PHYS                   (0x34)
#define ASI_QUAD_LDD_PHYS_L                 (0x3c)
#endif /* ULTRA_HAS_LDD_PHYS */

#if defined(TARGET_ULTRAIII) || defined(TARGET_ULTRAIV)
#define ASI_PCACHE_DATA_STATUS              (0x30) /* NI in Simics */
#define ASI_PCACHE_DATA                     (0x31) /* NI in Simics */
#define ASI_PCACHE_TAG                      (0x32) /* NI in Simics */
#define ASI_PCACHE_SNOOP_TAG                (0x33) /* NI in Simics */

#define ASI_SRAM_FAST_INIT                  (0x40)

#define ASI_WCACHE_VALID_BITS               (0x38) /* NI in Simics */
#define ASI_WCACHE_DATA                     (0x39) /* NI in Simics */
#define ASI_WCACHE_TAG                      (0x3a) /* NI in Simics */
#define ASI_WCACHE_SNOOP_TAG                (0x3b) /* NI in Simics */

#define ASI_DCACHE_INVALIDATE               (0x42) /* NI in Simics */
#define ASI_DCACHE_UTAG                     (0x43) /* NI in Simics */
#define ASI_DCACHE_SNOOP_TAG                (0x44) /* NI in Simics */
#endif /* TARGET_ULTRAIII || TARGET_ULTRAIV */

#if defined(TARGET_NIAGARA)
#define ASI_INSTRUCTION_BREAKPOINT           0x42
#define ASI_LSU_CONTROL_REG                  0x45
#endif   /* TARGET_NIAGARA */

#if defined(TARGET_ULTRAI) || defined(TARGET_ULTRAII)
#define ASI_LSU_CONTROL_REG                 (0x45)
#endif
#if defined(TARGET_ULTRAIII) || defined(TARGET_ULTRAIV)
#define ASI_DCU_CONTROL_REG                 (0x45)
#endif

#define ASI_DCACHE_DATA                     (0x46)
#define ASI_DCACHE_TAG                      (0x47)

#define ASI_INTR_DISPATCH_STATUS 	    (0x48)

#if defined(ULTRA_HAS_UPA_CONFIG)
#define ASI_UPA_CONFIG			    (0x4a)
#endif

#if defined(ULTRA_HAS_SAFARI_CONFIG)
#define ASI_SAFARI_CONFIG		    (0x4a)
#endif

#if defined(ULTRA_HAS_EEE)
#define ASI_ESTATE_ERROR_EN_REG             (0x4b)
#endif

#if defined(ULTRA_HAS_AFAR_AFSR)
#define ASI_ASYNC_FAULT_STATUS              (0x4c)
#define ASI_ASYNC_FAULT_ADDRESS             (0x4d)
#endif

#if defined(TARGET_ULTRAI) || defined(TARGET_ULTRAII) || defined(TARGET_ULTRAIII) || defined(TARGET_ULTRAIV)
#define ASI_ECACHE_TAG                      (0x4e)
#endif

#define ASI_IMMU                            (0x50)
#define ASI_IMMU_TSB_8KB_PTR_REG            (0x51)
#define ASI_IMMU_TSB_64KB_PTR_REG           (0x52)

#if defined(ULTRA_HAS_SERIAL)
#define ASI_SERIAL_ID                       (0x53)
#endif

#define ASI_ITLB_DATA_IN_REG                (0x54)
#define ASI_ITLB_DATA_ACCESS_REG            (0x55)
#define ASI_ITLB_TAG_READ_REG               (0x56)
#define ASI_IMMU_DEMAP                      (0x57)

#define ASI_DMMU                            (0x58)
#define ASI_DMMU_TSB_8KB_PTR_REG            (0x59)
#define ASI_DMMU_TSB_64KB_PTR_REG           (0x5a)
#define ASI_DMMU_TSB_DIRECT_PTR_REG         (0x5b)
#define ASI_DTLB_DATA_IN_REG                (0x5c)
#define ASI_DTLB_DATA_ACCESS_REG            (0x5d)
#define ASI_DTLB_TAG_READ_REG               (0x5e)
#define ASI_DMMU_DEMAP                      (0x5f)

#define ASI_ICACHE_INSTR                    (0x66)
#define ASI_ICACHE_TAG                      (0x67)

#if defined(TARGET_ULTRAIII) || defined(TARGET_ULTRAIV)
#define ASI_IMMU_SNOOP_TAG                  (0x68) /* NI in Simics */
#endif

#if defined(TARGET_ULTRAI) || defined(TARGET_ULTRAII)
#define ASI_ICACHE_PRE_DECODE               (0x6e)
#define ASI_ICACHE_NEXT_FIELD               (0x6f) /* NI in Simics */
#endif
#if defined(TARGET_ULTRAIII) || defined(TARGET_ULTRAIV)
#define ASI_BRANCH_PREDICTION_ARRAY         (0x6f) /* NI in Simics */
#endif

#if defined(TARGET_NIAGARA)
#define ASI_BLK_AIUP                         0x16
#define ASI_BLK_AIUS                         0x17
#else/* !TARGET_NIAGARA */
#define ASI_BLK_AIUP                         0x70
#define ASI_BLK_AIUS                         0x71
#endif /* !TARGET_NIAGARA */

#if defined(TARGET_ULTRAIII) || defined(TARGET_ULTRAIV)
#define ASI_MCU_CTRL_REG                    (0x72) /* NI in Simics */
#if defined(TARGET_ULTRAIV)
#define ASI_ECACHE_CFG_TIMING_CTRL           0x73
#endif   /* TARGET_ULTRAIV */
#define ASI_ECACHE_DATA                     (0x74) /* NI in Simics */
#define ASI_ECACHE_CTRL                     (0x75) /* NI in Simics */
#endif /* TARGET_ULTRAIII || TARGET_ULTRAIV */

#if defined(TARGET_NIAGARA)
#define ASI_INTR_RECEIVE                     0x72
#define ASI_UDB_INTR_W                       0x73
#define ASI_UDB_INTR_R                       0x74
#else
#define ASI_INTR_RECEIVE		     0x49
#define ASI_UDB_INTR_W 			     0x77
#define ASI_UDB_INTR_R 			     0x7f
#endif

#define ASI_ECACHE_W                        (0x76)


#if defined(TARGET_NIAGARA)
#define ASI_BLK_AIUPL                        0x1e
#define ASI_BLK_AIUSL                        0x1f
#else/* !TARGET_NIAGARA */
#define ASI_BLK_AIUPL                        0x78
#define ASI_BLK_AIUSL                        0x79
#endif /* !TARGET_NIAGARA */

#define ASI_ECACHE_R                        (0x7e)

#define ASI_PST8_P                          (0xc0)
#define ASI_PST8_S                          (0xc1)
#define ASI_PST16_P                         (0xc2)
#define ASI_PST16_S                         (0xc3)
#define ASI_PST32_P                         (0xc4)
#define ASI_PST32_S                         (0xc5)
#define ASI_PST8_PL                         (0xc8)
#define ASI_PST8_SL                         (0xc9)
#define ASI_PST16_PL                        (0xca)
#define ASI_PST16_SL                        (0xcb)
#define ASI_PST32_PL                        (0xcc)
#define ASI_PST32_SL                        (0xcd)

#define ASI_FL8_P                           (0xd0)
#define ASI_FL8_S                           (0xd1)
#define ASI_FL16_P                          (0xd2)
#define ASI_FL16_S                          (0xd3)
#define ASI_FL8_PL                          (0xd8)
#define ASI_FL8_SL                          (0xd9)
#define ASI_FL16_PL                         (0xda)
#define ASI_FL16_SL                         (0xdb)

#define ASI_BLK_COMMIT_P                    (0xe0)
#define ASI_BLK_COMMIT_S                    (0xe1)

#define ASI_BLK_P                           (0xf0)
#define ASI_BLK_S                           (0xf1)
#define ASI_BLK_PL                          (0xf8)
#define ASI_BLK_SL                          (0xf9)

#define IMPLICIT_D_ASI_CURRENT()  (IMPLICIT_D_ASI(current_processor))
#define IMPLICIT_I_ASI_CURRENT()  (IMPLICIT_I_ASI(current_processor))

#define IMPLICIT_D_ASI(cpu)     (REG_TL_R(cpu) ? (REG_PSTATE_CLE_R(cpu) ? ASI_NUCLEUS_LITTLE : ASI_NUCLEUS) \
                                               : (REG_PSTATE_CLE_R(cpu) ? ASI_PRIMARY_LITTLE : ASI_PRIMARY))

#define IMPLICIT_I_ASI(cpu)     (REG_TL_R(cpu) ? ASI_NUCLEUS : ASI_PRIMARY)

#endif /* TARGET_ULTRA */

/* macro defining table of ASI properties */
#define ASI_INFO_DEFINITION(table)                                              \
do {                                                                            \
	int i;                                                                  \
	table[ASI_NUCLEUS] =                                                    \
                Sim_ASI_Translating | Sim_ASI_Nucleus | Sim_ASI_Prefetch        \
                | Sim_ASI_Atomic;                                               \
	table[ASI_NUCLEUS_LITTLE] =                                             \
		Sim_ASI_Translating | Sim_ASI_Nucleus                           \
		| Sim_ASI_Little_Endian | Sim_ASI_Prefetch | Sim_ASI_Atomic;    \
	table[ASI_AS_IF_USER_PRIMARY] =                                         \
		Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Primary      \
                | Sim_ASI_Prefetch | Sim_ASI_Atomic;                            \
	table[ASI_AS_IF_USER_SECONDARY] =                                       \
		Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Secondary    \
                | Sim_ASI_Prefetch | Sim_ASI_Atomic;                            \
	table[ASI_AS_IF_USER_PRIMARY_LITTLE] =                                  \
		Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Primary      \
		| Sim_ASI_Prefetch | Sim_ASI_Little_Endian | Sim_ASI_Atomic;    \
	table[ASI_AS_IF_USER_SECONDARY_LITTLE] =                                \
		Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Secondary    \
		| Sim_ASI_Prefetch | Sim_ASI_Little_Endian | Sim_ASI_Atomic;    \
	table[ASI_PRIMARY] =                                                    \
                Sim_ASI_Translating | Sim_ASI_Primary | Sim_ASI_Prefetch        \
                | Sim_ASI_Atomic;                                               \
	table[ASI_SECONDARY] =                                                  \
                Sim_ASI_Translating | Sim_ASI_Secondary | Sim_ASI_Prefetch      \
                | Sim_ASI_Atomic;                                               \
	table[ASI_PRIMARY_NOFAULT] =                                            \
		Sim_ASI_Translating | Sim_ASI_Primary | Sim_ASI_Prefetch        \
                | Sim_ASI_Non_Fault;                                            \
	table[ASI_SECONDARY_NOFAULT] =                                          \
		Sim_ASI_Translating | Sim_ASI_Secondary | Sim_ASI_Prefetch      \
                | Sim_ASI_Non_Fault;                                            \
	table[ASI_PRIMARY_LITTLE] =                                             \
		Sim_ASI_Translating | Sim_ASI_Primary | Sim_ASI_Prefetch        \
		| Sim_ASI_Little_Endian | Sim_ASI_Atomic;                       \
	table[ASI_SECONDARY_LITTLE] =                                           \
		Sim_ASI_Translating | Sim_ASI_Secondary	| Sim_ASI_Prefetch      \
		| Sim_ASI_Little_Endian | Sim_ASI_Atomic;                       \
	table[ASI_PRIMARY_NOFAULT_LITTLE] =                                     \
		Sim_ASI_Translating | Sim_ASI_Primary | Sim_ASI_Prefetch        \
                | Sim_ASI_Non_Fault | Sim_ASI_Little_Endian;                    \
	table[ASI_SECONDARY_NOFAULT_LITTLE] =                                   \
		Sim_ASI_Translating | Sim_ASI_Secondary | Sim_ASI_Prefetch      \
                | Sim_ASI_Non_Fault | Sim_ASI_Little_Endian;                    \
	ASI_INFO_DEFINITION_ULTRA(table);                                       \
	for(i = 0; i < 0x80; i++)                                               \
		table[i] |= Sim_ASI_Restricted;                                 \
} while(0)

#if defined(TARGET_ULTRA)
#define ASI_INFO_DEFINITION_ULTRA(table)                                                        \
do {                                                                                            \
	table[ASI_PHYS_USE_EC] = Sim_ASI_Bypass | Sim_ASI_Atomic;                               \
	table[ASI_PHYS_BYPASS_EC_WITH_EBIT] =                                                   \
		Sim_ASI_Bypass | Sim_ASI_Side_Effects                                           \
		| Sim_ASI_Non_Cachable;                                                         \
	table[ASI_PHYS_USE_EC_LITTLE] =                                                         \
		Sim_ASI_Bypass | Sim_ASI_Little_Endian | Sim_ASI_Atomic;                        \
	table[ASI_PHYS_BYPASS_EC_WITH_EBIT_LITTLE] =                                            \
		Sim_ASI_Bypass | Sim_ASI_Side_Effects | Sim_ASI_Non_Cachable                    \
		| Sim_ASI_Little_Endian;                                                        \
	table[ASI_NUCLEUS_QUAD_LDD] =                                                           \
                Sim_ASI_Translating | Sim_ASI_Nucleus | Sim_ASI_Quad_Ldd;                       \
	table[ASI_NUCLEUS_QUAD_LDD_L] =                                                         \
		Sim_ASI_Translating | Sim_ASI_Nucleus                                           \
                | Sim_ASI_Quad_Ldd  | Sim_ASI_Little_Endian;                                    \
	table[ASI_BLK_AIUP] =                                                                   \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_As_If_User                        \
		| Sim_ASI_Primary;                                                              \
	table[ASI_BLK_AIUS] =                                                                   \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_As_If_User                        \
		| Sim_ASI_Secondary;                                                            \
	table[ASI_BLK_AIUPL] =                                                                  \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_As_If_User                        \
		| Sim_ASI_Primary | Sim_ASI_Little_Endian;                                      \
	table[ASI_BLK_AIUSL] =                                                                  \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_As_If_User                        \
		| Sim_ASI_Secondary | Sim_ASI_Little_Endian;                                    \
        ASI_INFO_DEFINITION_ULTRA_HAS_PARTIAL_STORE(table);                                     \
        ASI_INFO_DEFINITION_ULTRA_HAS_SHORT_FP(table);                                          \
        ASI_INFO_DEFINITION_ULTRA_HAS_BLOCK_COMMIT(table);                                      \
	table[ASI_BLK_P] =                                                                      \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_Primary;                          \
	table[ASI_BLK_S] =                                                                      \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_Secondary;                        \
	table[ASI_BLK_PL] =                                                                     \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_Primary                           \
		| Sim_ASI_Little_Endian;                                                        \
	table[ASI_BLK_SL] =                                                                     \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_Secondary                         \
		| Sim_ASI_Little_Endian;                                                        \
	ASI_INFO_DEFINITION_ULTRA_HAS_LDD_PHYS(table);                                          \
} while(0)
#else  /* not TARGET_ULTRA */
#define ASI_INFO_DEFINITION_ULTRA(table)
#endif /* not TARGET_ULTRA */

#if defined(ULTRA_HAS_PARTIAL_STORE)
#define ASI_INFO_DEFINITION_ULTRA_HAS_PARTIAL_STORE(table)                                      \
do {                                                                                            \
	table[ASI_PST8_P] = Sim_ASI_Translating | Sim_ASI_Primary;                              \
	table[ASI_PST8_S] = Sim_ASI_Translating | Sim_ASI_Secondary;                            \
	table[ASI_PST16_P] = Sim_ASI_Translating | Sim_ASI_Primary;                             \
	table[ASI_PST16_S] = Sim_ASI_Translating | Sim_ASI_Secondary;                           \
	table[ASI_PST32_P] = Sim_ASI_Translating | Sim_ASI_Primary;                             \
	table[ASI_PST32_S] = Sim_ASI_Translating | Sim_ASI_Secondary;                           \
	table[ASI_PST8_PL] =                                                                    \
		Sim_ASI_Translating | Sim_ASI_Primary                                           \
		| Sim_ASI_Little_Endian;                                                        \
	table[ASI_PST8_SL] =                                                                    \
		Sim_ASI_Translating | Sim_ASI_Secondary                                         \
		| Sim_ASI_Little_Endian;                                                        \
	table[ASI_PST16_PL] =                                                                   \
		Sim_ASI_Translating | Sim_ASI_Primary                                           \
		| Sim_ASI_Little_Endian;                                                        \
	table[ASI_PST16_SL] =                                                                   \
		Sim_ASI_Translating | Sim_ASI_Secondary                                         \
		| Sim_ASI_Little_Endian;                                                        \
	table[ASI_PST32_PL] =                                                                   \
		Sim_ASI_Translating | Sim_ASI_Primary                                           \
		| Sim_ASI_Little_Endian;                                                        \
	table[ASI_PST32_SL] =                                                                   \
		Sim_ASI_Translating | Sim_ASI_Secondary                                         \
		| Sim_ASI_Little_Endian;                                                        \
} while (0)
#else    /* ULTRA_HAS_PARTIAL_STORE */
#define ASI_INFO_DEFINITION_ULTRA_HAS_PARTIAL_STORE(table)
#endif   /* ULTRA_HAS_PARTIAL_STORE */

#if defined(ULTRA_HAS_SHORT_FP)
#define ASI_INFO_DEFINITION_ULTRA_HAS_SHORT_FP(table)                                           \
do {                                                                                            \
	table[ASI_FL8_P] = Sim_ASI_Translating | Sim_ASI_Primary | Sim_ASI_Short_FP;            \
	table[ASI_FL8_S] = Sim_ASI_Translating | Sim_ASI_Secondary | Sim_ASI_Short_FP;          \
	table[ASI_FL16_P] = Sim_ASI_Translating | Sim_ASI_Primary  | Sim_ASI_Short_FP;          \
	table[ASI_FL16_S] = Sim_ASI_Translating | Sim_ASI_Secondary  | Sim_ASI_Short_FP;        \
	table[ASI_FL8_PL] =                                                                     \
		Sim_ASI_Translating | Sim_ASI_Primary                                           \
		| Sim_ASI_Little_Endian | Sim_ASI_Short_FP;                                     \
	table[ASI_FL8_SL] =                                                                     \
		Sim_ASI_Translating | Sim_ASI_Secondary                                         \
		| Sim_ASI_Little_Endian | Sim_ASI_Short_FP;                                     \
	table[ASI_FL16_PL] =                                                                    \
		Sim_ASI_Translating | Sim_ASI_Primary                                           \
		| Sim_ASI_Little_Endian | Sim_ASI_Short_FP;                                     \
	table[ASI_FL16_SL] =                                                                    \
		Sim_ASI_Translating | Sim_ASI_Secondary                                         \
		| Sim_ASI_Little_Endian | Sim_ASI_Short_FP;                                     \
} while(0)
#else    /* ULTRA_HAS_SHORT_FP */
#define ASI_INFO_DEFINITION_ULTRA_HAS_SHORT_FP(table)
#endif   /* ULTRA_HAS_SHORT_FP */

#if defined(ULTRA_HAS_BLOCK_COMMIT)
#define ASI_INFO_DEFINITION_ULTRA_HAS_BLOCK_COMMIT(table)                                       \
do {                                                                                            \
	table[ASI_BLK_COMMIT_P] =                                                               \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_Primary | Sim_ASI_Commit;         \
	table[ASI_BLK_COMMIT_S] =                                                               \
		Sim_ASI_Translating | Sim_ASI_Block | Sim_ASI_Secondary | Sim_ASI_Commit;       \
} while(0)
#else    /* ULTRA_HAS_BLOCK_COMMIT */
#define ASI_INFO_DEFINITION_ULTRA_HAS_BLOCK_COMMIT(table)
#endif   /* ULTRA_HAS_BLOCK_COMMIT */

#if defined(ULTRA_HAS_LDD_PHYS)
#define ASI_INFO_DEFINITION_ULTRA_HAS_LDD_PHYS(table)			                        \
do {									                        \
	table[ASI_QUAD_LDD_PHYS] = Sim_ASI_Bypass | Sim_ASI_Quad_Ldd;	                        \
	table[ASI_QUAD_LDD_PHYS_L] = Sim_ASI_Bypass | Sim_ASI_Quad_Ldd | Sim_ASI_Little_Endian; \
} while(0)
#else  /* not ULTRA_HAS_LDD_PHYS */
#define ASI_INFO_DEFINITION_ULTRA_HAS_LDD_PHYS(table)
#endif /* not ULTRA_HAS_LDD_PHYS */


#if defined(TARGET_NIAGARA)
#define ASI_INFO_DEFINITION_NIAGARA(table)                                      \
do {                                                                            \
        table[ASI_QUAD_LDD_REAL]    = Sim_ASI_Bypass | Sim_ASI_Quad_Ldd;        \
        table[ASI_QUAD_LDD_REAL_L]  =                                           \
                Sim_ASI_Bypass | Sim_ASI_Quad_Ldd                               \
                | Sim_ASI_Little_Endian;                                        \
        table[ASI_AIUP_BLK_INIT_QUAD_LDD]  =                                    \
                Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Primary      \
                | Sim_ASI_Quad_Ldd;                                             \
        table[ASI_AIUS_BLK_INIT_QUAD_LDD]   =                                   \
                Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Secondary    \
                | Sim_ASI_Quad_Ldd;                                             \
        table[ASI_NUCL_BLK_INIT_QUAD_LDD]   =                                   \
                Sim_ASI_Translating | Sim_ASI_Nucleus | Sim_ASI_Quad_Ldd;       \
        table[ASI_AIUP_BLK_INIT_QUAD_LDD_L] =                                   \
                Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Primary      \
                | Sim_ASI_Quad_Ldd | Sim_ASI_Little_Endian;                     \
        table[ASI_AIUS_BLK_INIT_QUAD_LDD_L] =                                   \
                Sim_ASI_Translating | Sim_ASI_As_If_User | Sim_ASI_Secondary    \
                | Sim_ASI_Quad_Ldd | Sim_ASI_Little_Endian;                     \
        table[ASI_NUCL_BLK_INIT_QUAD_LDD_L] =                                   \
		Sim_ASI_Translating | Sim_ASI_Nucleus                           \
                | Sim_ASI_Quad_Ldd  | Sim_ASI_Little_Endian;                    \
        table[ASI_PRIM_BLK_INIT_QUAD_LDD]   =                                   \
                Sim_ASI_Translating | Sim_ASI_Primary | Sim_ASI_Quad_Ldd;       \
        table[ASI_SCND_BLK_INIT_QUAD_LDD]   =                                   \
                Sim_ASI_Translating | Sim_ASI_Secondary | Sim_ASI_Quad_Ldd;     \
        table[ASI_PRIM_BLK_INIT_QUAD_LDD_L] =                                   \
                Sim_ASI_Translating | Sim_ASI_Primary | Sim_ASI_Quad_Ldd        \
                | Sim_ASI_Little_Endian;                                        \
        table[ASI_SCND_BLK_INIT_QUAD_LDD_L] =                                   \
                Sim_ASI_Translating | Sim_ASI_Secondary | Sim_ASI_Quad_Ldd      \
                | Sim_ASI_Little_Endian;                                        \
} while (0)
#endif /* TARGET_NIAGARA */

/*
   <add id="arch_register_id_t def">
   <insert id="v9_register_id type"/>
   </add>

   <add id="arch_register_id_t desc">
   For SPARC the enum <type>v9_register_id_t</type> can be used to refer to
   the different registers.
   The following macros also exists to generate the register id for
   integer and floating point registers:

   <smaller>
   <insert id="reg_id_macros"/>
   </smaller>
   </add>
*/

/* <add-type id="v9_register_id type"><ndx>v9_register_id_t</ndx>
   </add-type> */
typedef enum {
        V9_Reg_Id_R0   = 0,
        /* R1 - R31 */
        V9_Reg_Id_F0   = 32,
        /* F1 - F63 */
        V9_Reg_Id_FCC0 = 96,
        V9_Reg_Id_FCC1 = 97,
        V9_Reg_Id_FCC2 = 98,
        V9_Reg_Id_FCC3 = 99,
        V9_Reg_Id_CC   = 100,
        V9_Reg_Id_PC   = 101,
        V9_Reg_Id_NPC  = 102,
        V9_Reg_Id_AEXC = 103, /* part of fsr */
        V9_Reg_Id_CEXC = 104, /* part of fsr */
        V9_Reg_Id_FTT  = 105, /* part of fsr */
        V9_Reg_Id_DUDL = 106, /* part of fprs */
        V9_Reg_Id_FEF  = 107, /* part of fprs */
        V9_Reg_Id_Y    = 108,
        V9_Reg_Id_GSR  = 109,
        V9_Reg_Id_CANSAVE = 110,
        V9_Reg_Id_CANRESTORE = 111,
        V9_Reg_Id_OTHERWIN = 112,
        V9_Reg_Id_CLEANWIN = 113,
        V9_Reg_Id_CWP  = 114,
        V9_Reg_Id_ASI  = 115,

        V9_Reg_Id_Not_Used  = 124,
        V9_Reg_Id_Sync = 125
} v9_register_id_t;

/* <add id="reg_id_macros">
   <insert-until text="// JDOCU INSERT-UNTIL V9_REG_ID"/>
   </add> */
#define V9_REG_ID_RN(n)   (V9_Reg_Id_R0+(n))
#define V9_REG_ID_FN(n)   (V9_Reg_Id_F0+(n))
#define V9_REG_ID_FCCN(n) (V9_Reg_Id_FCC0+(n))
// JDOCU INSERT-UNTIL V9_REG_ID

#endif /* TURBO_SIMICS */

/* <add-type id="sparc sparc_access_type_t"></add-type> */
typedef enum {
        V9_Access_Normal,
        V9_Access_Normal_FP,
        V9_Access_Double_FP, /* ldd/std */
        V9_Access_Short_FP,
        V9_Access_FSR,
        V9_Access_Atomic,
        V9_Access_Atomic_Load,
        V9_Access_Prefetch,
        V9_Access_Partial_Store,
        V9_Access_Ldd_Std_1,
        V9_Access_Ldd_Std_2,
        V9_Access_Block,
        V9_Access_Internal1
} sparc_access_type_t;

#ifndef TURBO_SIMICS

/* <add id="simics arch api types">
   <name index="true">v9_memory_transaction_t</name>
   <doc>
   <doc-item name="NAME">v9_memory_transaction_t</doc-item>
   <doc-item name="SYNOPSIS">
   <smaller>
   <insert id="v9_memory_transaction_t def"/>
   </smaller>
   </doc-item>
   <doc-item name="DESCRIPTION">

   This is the Sparc specific memory transaction data structure.
   The generic data is stored in the <var>s</var> field.

   The <var>cache_virtual</var> bit is set if this memory transaction
   corresponds to a TLB entry that has the <const>CV</const> (cache
   virtual) bit set. Conversely, the <var>cache_physical</var> bit
   corresponds to the TLB entry's <const>CP</const> (cache physical)
   bit and the <var>side_effect</var> bit corresponds to the
   <const>E</const> bit.

   The <var>priv</var> bit is cleared if the memory transaction 
   comes from one of the <const>USER</const> ASI's.

   The <var>red</var> bit is set if the memory transaction was
   generated by a CPU which has the <const>RED</const> bit in the
   <const>%pstate</const> register set.

   SPARC-V9 uses an address space identifier (ASI) to qualify memory
   access instructions. This is stored in the <var>address_space</var>
   field; it will be set to <const>ASI_PRIMARY</const> for "normal"
   memory transactions.

   The <var>prefetch_fcn</var> field is only set for memory
   transactions of type <const>Sim_Trans_Prefetch</const>, for which
   it contains the <const>fcn</const> field of the prefetch
   instruction.

   The <var>access_type</var> field describes the type of the
   access, as defined in the <type>sparc_access_type_t</type> enum.
   <ndx>sparc_access_type_t</ndx> For example if a load is for a
   floating point register or a standard integer one.

   </doc-item>
   </doc>
   </add> 
*/

/* <add-type id="v9_memory_transaction_t def"></add-type> */
typedef struct v9_memory_transaction {
        generic_transaction_t s;
        unsigned              cache_virtual:1;
        unsigned              cache_physical:1;
        unsigned              side_effect:1;
        unsigned              priv:1;
        unsigned              red:1;
        unsigned              hpriv:1;
        unsigned              henb:1;
        uint8                 address_space;
        uint8                 prefetch_fcn;
        sparc_access_type_t   access_type;

        /* if non-zero, the id needed to calculate the program counter */
        intptr_t turbo_miss_id;
} v9_memory_transaction_t; 

typedef struct mmu_error_info {
        conf_object_t *mmu_obj;
        conf_object_t *cpu_obj;
        exception_type_t ex;
        uint64 addr;
        int ft;
        int asi;
        read_or_write_t r_or_w;
        data_or_instr_t d_or_i;
        int atomic;
        int tl;
        int priv;
} mmu_error_info_t;

/* <add-type id="mmu_interface_t">
   <fun>logical_to_physical()</fun> should fill in the
   <var>physical_address</var> field (and other address fields when
   appropriate) in the memory transaction if the transaction is
   valid. Side effects such as modifying dirty or access bits should
   only take place if the inquiry bit in the transaction is clear.
   The set_error function can return a new exception to override the
   one set by the Simics core. The overriding exception is only used
   for memory accesses.
   </add-type> */
typedef struct {
        exception_type_t (*logical_to_physical)(conf_object_t *mmu_obj,
                                                v9_memory_transaction_t *);
        int (*get_current_context)(conf_object_t *mmu_obj,
                                   conf_object_t *cpu);
        void (*cpu_reset)(conf_object_t *mmu_obj,
                          conf_object_t *cpu_obj,
                          exception_type_t exc_no);
        exception_type_t (*undefined_asi)(conf_object_t *mmu_obj,
                                          v9_memory_transaction_t *mem_op);
        exception_type_t (*set_error)(conf_object_t *mmu_obj,
                                      conf_object_t *cpu_obj,
                                      exception_type_t ex,
                                      uint64 addr,
                                      int ft,
                                      int address_space,
                                      read_or_write_t r_or_w,
                                      data_or_instr_t d_or_i,
                                      int atomic,
                                      int tl,
                                      int priv);
        void (*set_error_info)(mmu_error_info_t *ei);

        exception_type_t (*asi_0x40_callback)(conf_object_t *cpu,
                                              uint64 addr, uint64 value, int size, int fp);

} mmu_interface_t;


/* <add-type id="sparc asi_info_t"></add-type> */
typedef enum asi_info {
        Sim_ASI_Bypass        = 1 <<  0,
        Sim_ASI_Restricted    = 1 <<  1,
        Sim_ASI_Translating   = 1 <<  2,
        Sim_ASI_Little_Endian = 1 <<  3,
        Sim_ASI_Nucleus       = 1 <<  4,
        Sim_ASI_Primary       = 1 <<  5,
        Sim_ASI_Secondary     = 1 <<  6,
        Sim_ASI_Non_Fault     = 1 <<  7,
        Sim_ASI_As_If_User    = 1 <<  8,
        Sim_ASI_Non_Cachable  = 1 <<  9,
        Sim_ASI_Block         = 1 << 10,
        Sim_ASI_Side_Effects  = 1 << 11,
        Sim_ASI_Commit        = 1 << 12,
        Sim_ASI_HRestricted   = 1 << 13,
        Sim_ASI_Quad_Ldd      = 1 << 14,
        Sim_ASI_Prefetch      = 1 << 15,
        Sim_ASI_Atomic        = 1 << 16,
        Sim_ASI_Short_FP      = 1 << 17,
        Sim_ASI_Sync1         = 1 << 18,
        Sim_ASI_Sync2         = 1 << 19
} asi_info_t;

/* <add id="sparc_v9_interface_t">
   SPARC V9 specific functions.
 
   This interface is implemented by SPARC V9 processors to provide
   various functionality that is specific for this class of processors.

   The <fun>install_default_class_asi_handler</fun> installs a function,
   <param>handler</param>, that is called each time an address is accessed
   in the <param>asi</param> address space a processor of the same class
   that <param>cpu</param> belongs to. This function will override
   the Simics default handling of the selected ASI. The
   <fun>install_user_class_asi_handler</fun> is similar, but is called before
   the default handler. If this function returns <i>Sim_PE_Default_Semantics</i>
   the default handler will be called. A return of <i>Sim_PE_No_Exception</i> will
   override the default handler.

   The function can also return <i>Sim_PE_Ignore_Semantics</i>, this will tell
   Simics not to update the destination register on loads.

   The function <fun>access_asi_handler</fun> allows user access to a specific ASI.
   In no handler is installed, or the ASI is a memory ASI, 'Data_Access_Exception'
   will be returned. The real_address pointer in the memory_transaction struct
   should point to an aligned buffer with big-endian data.
   
   Note that installing and accessing ASI handlers using this interface is
   only supported for non-memory ASIs.

   The <fun>get_asi_info</fun> function is used to query Simics about the
   characteristics of a specified ASI. For example if the ASI is
   translating, refers to a block access, etc. All available
   queries/characteristics are listed in the <type>asi_info_t</type> enum.
   <ndx>asi_info_t</ndx> Several characteristics can be checked at once
   and the function will return a mask of matching ones.

   The <fun>read_window_register</fun> and <fun>write_window_register</fun>
   functions can be used to access registers in any register window. Similarly
   the <fun>read_global_register</fun> and <fun>write_global_register</fun> functions
   provide access to all global registers. The <param>globals</param> argument
   is used to select the set of global registers to read from. The mapping
   between global set and set number can be found in the <i>global_set_name</i>
   attribute in the processor class.

   The register number when accessing windowed registers is 0 - 7 for accesses
   to the current global registers, 8 - 15 for the out registers of the selected
   window, 16 - 23 for the local registers, and 24 - 32 for the in registers.

   There are several functions that can be used to read and write floating point
   register values. The <tt>_i</tt> versions use single-precision (32bit) with
   integer representation, the <tt>_s</tt> versions use single-precision float
   representation, <tt>_x</tt> versions use double-precision (64 bit) integer
   representation, and the <tt>_d</tt> versions use double-precision and double float
   representation. Single-precision registers are numbered 0, 1 to 31 and
   double-precision 0, 2, 62.

   <small>
   <insert-until text="// ADD INTERFACE sparc_v9_interface"/>
   </small>
   </add> */
typedef struct sparc_v9_interface {

        void (*install_default_class_asi_handler)(
                conf_object_t *cpu,
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);
        void (*install_user_class_asi_handler)(
                conf_object_t *cpu,
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);
        void (*remove_default_class_asi_handler)(
                conf_object_t *cpu,
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);
        void (*remove_user_class_asi_handler)(
                conf_object_t *cpu,
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);

        exception_type_t (*access_asi_handler)(conf_object_t *cpu,
                                               v9_memory_transaction_t *mem_op);

        int (*get_asi_info)(conf_object_t *cpu, int asi, asi_info_t info);

        uinteger_t (*read_window_register)(conf_object_t *cpu,
                                           int window, int reg);

        void (*write_window_register)(conf_object_t *cpu,
                                      int window, int reg,
                                      uinteger_t value);

        uinteger_t (*read_global_register)(conf_object_t *cpu,
                                           int globals, int reg);

        void (*write_global_register)(conf_object_t *cpu,
                                      int globals, int reg,
                                      uinteger_t value);

        uint32  (*read_fp_register_i)(conf_object_t *cpu, int reg);
        uint64  (*read_fp_register_x)(conf_object_t *cpu, int reg);
        float   (*read_fp_register_s)(conf_object_t *cpu, int reg);
        double  (*read_fp_register_d)(conf_object_t *cpu, int reg);
        void   (*write_fp_register_i)(conf_object_t *cpu,
                                      int reg, uint32 value);
        void   (*write_fp_register_x)(conf_object_t *cpu,
                                      int reg, uint64 value);
        void   (*write_fp_register_s)(conf_object_t *cpu,
                                      int reg, float value);
        void   (*write_fp_register_d)(conf_object_t *cpu,
                                      int reg, double value);

        /* obsolete installers */
        void (*install_default_asi_handler)(
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);
        void (*install_user_asi_handler)(
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);
        void (*remove_default_asi_handler)(
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);
        void (*remove_user_asi_handler)(
                exception_type_t (*handler)(conf_object_t *,
                                            generic_transaction_t *),
                int asi);
} sparc_v9_interface_t;

#define SPARC_V9_INTERFACE "sparc-v9"
// ADD INTERFACE sparc_v9_interface

/* <add id="sparc_interrupt_interface_t">
   <ndx>interrupt_ack_t</ndx>
   <ndx>interrupt_cpu_t</ndx>
   <ndx>trap_cpu_t</ndx>

   Interrupt a Sparc Processor.
 
   This interface is implemented by sparc processors to be able to
   receive interrupts or asynchronous traps. The arguments to the
   <fun>interrupt_cpu</fun> the cpu to interrupt (<param>cpu</param>),
   a pointer to the sending object (<param>obj</param>), the mid of
   the sending object (<param>source_mid</param>), the mid of the
   target object (<param>target_mid</param>), and a callback function
   that will be called when it is determined if the CPU can receive the
   interrupt (<param>irq_ack_cb</param>). There is also a data pointer
   (<param>data</param>), pointing to an array of 64-bit integers, and
   a user pointer (<param>callback_data</param>) that is returned by
   the ack callback to the caller. In the callback, the result is
   returned as the argument <param>ack</param>, which is either 0 for
   ACK or 1 for NACK.

   The <fun>trap_cpu</fun> function can be used for disrupting and
   deferred traps. The trap will be inserted after the current
   executing instruction. If Simics is run in out of order execution
   mode, the trap will occur when all instructions in the reorder
   buffer have completed.

   Precise traps can be injected by instructions accessing
   memory. This is done by setting the <var>exception</var> field of a
   <type>generic_transaction_t</type> in the <fun>operate</fun>
   function of a timing model interface. It is thus necessary to
   create a timing model object to be able to inject precise traps.

   <insert-until text="// ADD INTERFACE sparc_interrupt_interface"/>
   </add> */

typedef void (*interrupt_ack_t)(conf_object_t *obj, 
                                conf_object_t *cpu,
                                int cpu_mid,
                                int ack, 
                                lang_void *usr);

typedef void (*interrupt_cpu_t)(conf_object_t *cpu, 
                                conf_object_t *obj,
                                int source_mid,
                                int target_mid,
                                interrupt_ack_t irq_ack_cb, 
                                uint64 *data, 
                                lang_void *usr,
                                int dummy1, int dummy2);

typedef void (*trap_cpu_t)(conf_object_t *cpu,
                           exception_type_t trap_vector);

typedef struct sparc_interrupt_interface {
#if !defined(GULP)
        interrupt_cpu_t interrupt_cpu;
#endif
        trap_cpu_t trap_cpu;
} sparc_interrupt_interface_t;

#define SPARC_INTERRUPT_INTERFACE "sparc-interrupt"
// ADD INTERFACE sparc_interrupt_interface

/* <add id="sparc_irq_bus_interface_t">
   Handle interrupts over a bus.
 
   This interface is implemented by bus devices that are used to
   send interrupts between SPARC processors, and between devices
   and processors.

   <ndx>set_bus_id_t</ndx>
   <ndx>interrupt_by_id_t</ndx>
   <ndx>get_object_by_id_t</ndx>
   <ndx>reset_all_t</ndx>

   <insert-until text="// ADD INTERFACE sparc_irq_bus_interface"/>
   </add> */

typedef int (*set_bus_id_t)(conf_object_t *obj, conf_object_t *src, int id);

typedef void (*interrupt_by_id_t)(conf_object_t *obj,
                                  conf_object_t *src, 
                                  int src_id,
                                  int dst_id,
                                  interrupt_ack_t interrupt_ack,
                                  uint64 *data,
                                  lang_void *usr,
                                  int dummy0,
                                  int dummy1);

typedef conf_object_t *(*get_object_by_id_t)(conf_object_t *obj, int id);

typedef void (*reset_all_t)(conf_object_t *obj, int reset_type);

typedef struct sparc_irq_bus_interface {
        set_bus_id_t set_bus_id;
#if !defined(GULP)
        interrupt_by_id_t interrupt_by_id;
#endif
        get_object_by_id_t get_object_by_id;
        reset_all_t reset_all;
} sparc_irq_bus_interface_t;

#define SPARC_IRQ_BUS_INTERFACE "sparc-irq-bus"
// ADD INTERFACE sparc_irq_bus_interface

/* <add id="sparc_u3_interface_t">
   <ndx>sparc_u3_error_t</ndx>

   This interface contains <nobr>UltraSPARC III</nobr> specific
   functions. Currently, the only one is the <fun>cause_error</fun>
   function, which is used to cause errors. Its arguments are the
   following:

   <var>obj</var> is the CPU to which the error should be reported.

   <var>afsr_status_bit</var> is the number of the bit in the
   Asynchronous Fault Status Register that this error sets, or
   &ndash;1 if none. Valid values are 33 through 53.

   <var>trap</var> is the trap that should be taken (if enabled; see
   below), or &ndash;1 if none. Valid values are
   <const>Instruction_Access_Error</const>,
   <const>Data_Access_Error</const>,
   <const>Corrected_ECC_Error</const>, and
   <const>Fast_ECC_Error</const>.

   <var>estate_error_enable_bit</var> is the number of the bit in the
   E-cache Error Enable Register (<const>ESTATE_ERROR_EN</const>) that
   controls whether the trap in the <var>trap</var> argument should be
   taken (unless it is &ndash;1), or &ndash;1 if none.

   <var>m_synd_priority</var> is the priority level of the MTag ECC
   syndrome data supplied in the <var>m_synd</var> argument, or 0 if
   none. Valid values are 0, 1, and 2.

   <var>m_synd</var> is the 4-bit MTags ECC syndrome data, or 0 if
   none.

   <var>e_synd_priority</var> is the priority level of the system bus
   and E-cache ECC syndrome data supplied in the <var>e_synd</var>
   argument, or 0 if none. Valid values are 0, 1, and 2.

   <var>e_synd</var> is the 9-bit system bus and E-cache ECC syndrome
   data, or 0 if none.

   <var>afar_priority</var> is the priority level of the
   <var>afar</var> argument, or 0 if none. Valid values are 0 through 4.

   <var>afar</var> should contain the address that will be written to
   the Asynchronous Fault Address Register (<const>AFAR</const>),
   given that the <var>afar_priority</var> is high enough.

   <var>set_priv</var> should be non-zero if the
   <const>AFSR.PRIV</const> bit should be set if the
   <const>PSTATE.PRIV</const> bit is set at the time of the error.

   <var>set_me</var> should be non-zero if the <const>AFSR.ME</const>
   bit should be set if the <const>AFSR</const> bit indicated by the
   <var>afsr_status_bit</var> argument already was set.

   <insert-until text="// ADD INTERFACE sparc_u3_interface"/> </add>
*/
typedef void (*sparc_u3_error_t)(conf_object_t *obj,
                                 int afsr_status_bit,
                                 exception_type_t trap,
                                 int estate_error_enable_bit,
                                 int m_synd_priority,
                                 unsigned m_synd,
                                 int e_synd_priority,
                                 unsigned e_synd,
                                 int afar_priority,
                                 uint64 afar,
                                 int set_priv,
                                 int set_me);

typedef struct sparc_u3_interface {
        sparc_u3_error_t cause_error;
} sparc_u3_interface_t;

#define SPARC_U3_INTERFACE "sparc-u3"
// ADD INTERFACE sparc_u3_interface

#if !defined(HAVE_SPARC_EXCEPTION_TYPE)
#define HAVE_SPARC_EXCEPTION_TYPE
/* <add id="simics arch api types">
   <name index="true">v9_exception_type_t</name>
   <doc>
   <doc-item name="NAME">v9_exception_type_t</doc-item>
   <doc-item name="SYNOPSIS"><insert id="v9_exception_type_t def"/></doc-item>
   <doc-item name="DESCRIPTION">
   The <type>v9_exception_type_t</type> lists all hardware
   exceptions defined in the UltraSPARC architecture. This type is
   used in some cases where functions take the generic
   <type>exception_type_t</type>.
   </doc-item>
   </doc>
   </add>

   <add-type id="v9_exception_type_t def">
   </add-type>
*/
typedef enum v9_exception_type {
        Power_On_Reset = 0x001,
        Watchdog_Reset = 0x002,
        Externally_Initiated_Reset = 0x003,
        Software_Initiated_Reset = 0x004,
        Red_State_Exception = 0x005,
        Instruction_Access_Exception = 0x008,
        Instruction_Access_MMU_Miss = 0x009,
        Instruction_Access_Error = 0x00a,
        Illegal_Instruction = 0x010,
        Privileged_Opcode = 0x011,
        Unimplemented_Ldd = 0x012,
        Unimplemented_Std = 0x013,
        Fp_Disabled = 0x020,
        Fp_Exception_Ieee_754 = 0x021,
        Fp_Exception_Other = 0x022,
        Tag_Overflow = 0x023,
        Clean_Window = 0x024,
        Division_By_Zero = 0x028,
        Internal_Processor_Error = 0x029,
        Data_Access_Exception = 0x030,
        Data_Access_MMU_Miss = 0x031,
        Data_Access_Error = 0x032,
        Data_Access_Protection = 0x033,
        Mem_Address_Not_Aligned = 0x034,
        Lddf_Mem_Address_Not_Aligned = 0x035,
        Stdf_Mem_Address_Not_Aligned = 0x036,
        Privileged_Action = 0x037,
        Ldqf_Mem_Address_Not_Aligned = 0x038,
        Stqf_Mem_Address_Not_Aligned = 0x039,

#if defined(TARGET_NIAGARA)
        Instr_Real_Translation_Miss = 0x3e,
        Data_Real_Translation_Miss = 0x3f,
#endif   /* TARGET_NIAGARA */

        Async_Data_Error = 0x040,
        Interrupt_Level_1 = 0x41,
        Interrupt_Level_2 = 0x42,
        Interrupt_Level_3 = 0x43,
        Interrupt_Level_4 = 0x44,
        Interrupt_Level_5 = 0x45,
        Interrupt_Level_6 = 0x46,
        Interrupt_Level_7 = 0x47,
        Interrupt_Level_8 = 0x48,
        Interrupt_Level_9 = 0x49,
        Interrupt_Level_10 = 0x4a,
        Interrupt_Level_11 = 0x4b,
        Interrupt_Level_12 = 0x4c,
        Interrupt_Level_13 = 0x4d,
        Interrupt_Level_14 = 0x4e,
        Interrupt_Level_15 = 0x4f,

#if defined(TARGET_NIAGARA)
        Hstick_Match = 0x5e,
        Trap_Level_Zero = 0x5f,
#endif   /* TARGET_NIAGARA */

        Interrupt_Vector = 0x60,
        PA_Watchpoint = 0x61,
        VA_Watchpoint = 0x62,
        Corrected_ECC_Error = 0x63,
        
        Fast_Instruction_Access_MMU_Miss = 0x64,
        Fast_Data_Access_MMU_Miss = 0x68,
        Fast_Data_Access_Protection = 0x6c,

#if defined(TARGET_NIAGARA)
        Streaming_Interrupt = 0x70,
#else
        Fast_ECC_Error = 0x70,
#endif

#if defined(TARGET_NIAGARA1)
        Modular_Arithmetic_Interrupt = 0x74,
#endif

#if defined(TARGET_NIAGARA)
        Instruction_Breakpoint = 0x76,
        Cpu_Mondo_Trap         = 0x7c,
        Dev_Mondo_Trap         = 0x7d,
        Resumable_Error        = 0x7e,
        Nonresumable_Error     = 0x7f,
#endif   /* TARGET_NIAGARA */

        Spill_0_Normal = 0x080,
        Spill_1_Normal = 0x084,
        Spill_2_Normal = 0x088,
        Spill_3_Normal = 0x08c,
        Spill_4_Normal = 0x090,
        Spill_5_Normal = 0x094,
        Spill_6_Normal = 0x098,
        Spill_7_Normal = 0x09c,
        Spill_0_Other = 0x0a0,
        Spill_1_Other = 0x0a4,
        Spill_2_Other = 0x0a8,
        Spill_3_Other = 0x0ac,
        Spill_4_Other = 0x0b0,
        Spill_5_Other = 0x0b4,
        Spill_6_Other = 0x0b8,
        Spill_7_Other = 0x0bc,
        Fill_0_Normal = 0x0c0,
        Fill_1_Normal = 0x0c4,
        Fill_2_Normal = 0x0c8,
        Fill_3_Normal = 0x0cc,
        Fill_4_Normal = 0x0d0,
        Fill_5_Normal = 0x0d4,
        Fill_6_Normal = 0x0d8,
        Fill_7_Normal = 0x0dc,
        Fill_0_Other = 0x0e0,
        Fill_1_Other = 0x0e4,
        Fill_2_Other = 0x0e8,
        Fill_3_Other = 0x0ec,
        Fill_4_Other = 0x0f0,
        Fill_5_Other = 0x0f4,
        Fill_6_Other = 0x0f8,
        Fill_7_Other = 0x0fc,
        Trap_Instruction = 0x100,
        Last_Real_Exception = 0x200
} v9_exception_type_t;
#endif /* HAVE_SPARC_EXCEPTION_TYPE */

#if defined(TARGET_NIAGARA)
#define INSTRUCTION_BREAKPOINT_VA           0x08
#endif

#endif /* TURBO_SIMICS */

#endif /*  _SIMICS_ARCH_SPARC_API_H */
