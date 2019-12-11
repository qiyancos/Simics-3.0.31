
##  Copyright 2001-2007 Virtutech AB

#
# serial.py
#
# add host serial connection
#
# Magnus Christensson
#

#
# Example usage:
# > @add_serial(conf.cpu0, conf.com1, "COM1", 19200)
#

def create_name(base):
	i = 0
	try:
		while 1:
			SIM_get_object("%s%d" % (base, i))
			i = i + 1
	except SimExc_General:
		return "%s%d" % (base, i)

def add_serial(queue_obj, serial_port, host_device, host_baudrate):
	# Create objects
	bridge_class = SIM_get_class("host-serial")
	bridge_name = create_name("com_host_bridge")
	bridge_obj = SIM_new_object(bridge_class, bridge_name)

	# Initialize bridge
	SIM_set_attribute(bridge_obj, "target_device", serial_port)
	SIM_set_attribute(bridge_obj, "queue", queue_obj)
	SIM_set_attribute(bridge_obj, "host_device", host_device)
	SIM_set_attribute(bridge_obj, "host_baudrate", host_baudrate)

	# Inform serial port
	serial_port.console = bridge_obj
