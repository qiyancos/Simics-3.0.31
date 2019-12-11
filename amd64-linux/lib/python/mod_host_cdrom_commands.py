from cli import *

def del_host_cdrom_cmd(obj):
    name = obj.name
    try:
        SIM_delete_object(obj)
        print "Host CD-ROM object '%s' deleted." % name
    except Exception, msg:
        print "Failed deleting host CD-ROM object '%s': %s" % (name, msg)

new_command("delete", del_host_cdrom_cmd,
            args  = [],
            type = ["CD-ROM"],
	    namespace = "host-cdrom",
            short = "delete an unused host-cdrom object",
            doc = """
Delete an unused host-cdrom object with the name <i>object-name</i>.
""", filename="/mp/simics-3.0/src/extensions/host-cdrom/commands.py", linenumber="11")
