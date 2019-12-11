/*
 * simics/devs/dma.h
 *
  Copyright 1998-2007 Virtutech AB
  
  This file is part of the Virtutech Simics, which is distributed
  under the Virtutech Simics Software License Agreement.
 *
 */

#ifndef _SIMICS_DEVS_DMA_H
#define _SIMICS_DEVS_DMA_H

/*
  Common dma definitions. All dma devices implements this interface.

  The existing dma devices don't implement all of the
  functions. Some don't have DMA_READ_DATA_ADDR,
  DMA_WRITE_DATA_ADDR and DMA_ENABLE_CALL.
   
  Some may not support DMA_SET_INTERRUPT and DMA_CLR_INTERRUPT.
 */

/* DMA Interface
 * Parameters:
 * 1 the dma device
 * 2 the number of the dma channel (0 if device has only one)
 * 3 pointer to data buffer
 * size of transaction
 * + The addr versions have an extra parameter, (number 2) that is
 *   the address where data is read/written
 * + The dma_transfer_time_t has the following parameters:
 *   dma-device, dma-channel, transfer-len
 */

#define COMMON_DMA_INTERFACE "common-dma"

typedef int (*dma_read_data_t)(conf_object_t *, int, char *, int);
typedef int (*dma_write_data_t)(conf_object_t *, int, char *, int);
typedef int (*dma_read_data_addr_t)(conf_object_t *, logical_address_t, int, char *, int);
typedef int (*dma_write_data_addr_t)(conf_object_t *, logical_address_t, int, char *, int);
typedef simtime_t (*dma_transfer_time_t)(conf_object_t *, int, int);

/* Interrupt Interface */
typedef void (*dma_set_interrupt_t)(conf_object_t *);
typedef void (*dma_clr_interrupt_t)(conf_object_t *);
typedef void (*dma_enable_call_t)(conf_object_t *, conf_object_t *);

typedef struct {
        dma_read_data_t read_data;
        dma_write_data_t write_data;
        dma_read_data_addr_t read_data_addr;
        dma_write_data_addr_t write_data_addr;
        dma_transfer_time_t transfer_time;
        dma_set_interrupt_t set_interrupt;
        dma_clr_interrupt_t clr_interrupt;
        dma_enable_call_t enable_call;
} common_dma_interface_t;

#endif /* _SIMICS_DEVS_DMA_H */
