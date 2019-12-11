from sim_commands import *

def get_info(obj):
    return [ (None,
              [ ("Memory object", obj.memory)])]

dma_type = ('verify', 'write', 'read', 'illegal')
dma_mode = ('demand', 'single', 'block', 'cascade')

def get_counter_status(obj, i, j):
    return [("Masked", iff(obj.mask[i][j], "yes", "no")),
            ("Page Address", "0x%x" % obj.page_addr[i][j]),
            ("Base Address", "0x%x" % obj.base_addr[i][j]),
            ("Current Address", "0x%x" % obj.current_addr[i][j]),
            ("Base Count", "0x%x" % obj.base_count[i][j]),
            ("Current Count", "0x%x" % obj.current_count[i][j]),
            ("Direction", iff(obj.dec_address[i][j], "down", "up")),
            ("Reset at TC", iff(obj.auto_init[i][j], "yes", "no")),
            ("DMA Type", dma_type[obj.dma_type[i][j]]),
            ("DMA Mode", dma_mode[obj.dma_mode[i][j]]),
            ("Request Reg", obj.request[i][j]),
            ("Terminal Count", obj.tc[i][j])]

def get_status(obj):
    stat = []
    for i in (0, 1):
        stat += [("Controller %d" % i,
                  [("Enabled", iff(obj.disabled[i], "no", "yes")),
                   ("Flip-Flop", obj.flip_flop[i]),
                   ("Page Size", "0x%x" % obj.page_size[i])])]
    for i in (0, 1):
        for j in range(4):
            stat += [("Controller %d Channel %d" % (i, j),
                      get_counter_status(obj, i, j))]
    return stat
                
new_info_command('i8237x2', get_info)
new_status_command('i8237x2', get_status)
