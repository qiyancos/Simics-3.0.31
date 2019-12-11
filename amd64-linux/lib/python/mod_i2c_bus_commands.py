import sim_commands

def get_info(obj):
    try:
        devices = obj.i2c_devices
    except:
        devices = "None"
    else:
        devices.sort()
        devices = ", ".join(map(lambda x: ("%s (0x%x)" % (x[0], x[1])), devices))
    return [(None,
             [ ('I2C devices', devices) ]
             )]

def get_status(obj):
    slave = obj.current_slave
    if not slave:
        slave = '<none>'
    state = [ 'idle', 'master transmit', 'master receive',
              'slave transmit', 'slave receive' ][obj.current_state]
    return [(None,
             [ ('Current slave', slave),
               ('Current state', state)
               ]
             ) ]

sim_commands.new_info_command("i2c-bus", get_info)
sim_commands.new_status_command("i2c-bus", get_status)
