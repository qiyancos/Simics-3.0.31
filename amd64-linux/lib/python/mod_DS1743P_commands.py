from string import *
from cli import *

#
# -------------------- set-date-time --------------------
#

def set_date_time_cmd(obj, year, month, mday, hour, minute, second):
    try:
	if year < 1990 or year >= 2038:
		print "Year %d out of range." % year
		return
	if month <= 0 or month > 12:
		print "Month %d out of range [1, 12]." % month
		return
	if mday <= 0 or mday > 31:
		print "Mday %d out of range." % mday
		return
	if hour < 0 or hour >= 24:
		print "Hour %d out of range [0, 23]." % hour
		return
	if minute < 0 or minute >= 60:
		print "Minute %d out of range [0, 59]." % minute
		return
	if second < 0 or second >= 60:
		print "Second %d out of range [0, 59]." % second
		return
	SIM_set_attribute(obj, "year", year)
	SIM_set_attribute(obj, "month", month)
	SIM_set_attribute(obj, "mday", mday)
	SIM_set_attribute(obj, "hour", hour)
	SIM_set_attribute(obj, "minute", minute)
	SIM_set_attribute(obj, "second", second)

    except Exception, y:
	print "Error setting time in DS1743P device: %s" % y

new_command("set-date-time", set_date_time_cmd,
            [arg(int_t, "year"), arg(int_t, "month"), arg(int_t, "mday"), arg(int_t, "hour"), arg(int_t, "minute"), arg(int_t, "second")],
            alias = "",
            type  = "DS1743P" + " commands",
            short = "set date and time",
	    namespace = "DS1743P",
            doc = """
Set the date and time of the realtime clock. Both month and mday start at one.
Year should be in the full four-digit format. The cmos-init command must be issued
before this command (unless the simulation was started from a checkpoint).
""", filename="/mp/simics-3.0/src/devices/DS1743P/commands.py", linenumber="38")


#
# -------------------- get-date-time --------------------
#

def get_date_time_cmd(obj):
    print "Time: %04d-%02d-%02d %02d:%02d:%02d" % (
               SIM_get_attribute(obj, "year"),
               SIM_get_attribute(obj, "month"),
               SIM_get_attribute(obj, "mday"),
               SIM_get_attribute(obj, "hour"),
               SIM_get_attribute(obj, "minute"),
               SIM_get_attribute(obj, "second"))

new_command("get-date-time", get_date_time_cmd,
            [],
            alias = "",
            type  = "DS1743P" + " commands",
            short = "get date and time",
	    namespace = "DS1743P",
            doc = """
Return the date and time of the realtime clock.<br/>
""", filename="/mp/simics-3.0/src/devices/DS1743P/commands.py", linenumber="64")

