from cli import *

def del_file_cdrom_cmd(obj):
    name = obj.name
    try:
        SIM_delete_object(obj)
        print "File CD-ROM object '%s' deleted." % name
    except Exception, msg:
        print "Failed deleting file CD-ROM object '%s': %s" % (name, msg)

new_command("delete", del_file_cdrom_cmd,
            args  = [],
            type = ["CD-ROM"],
	    namespace = "file-cdrom",
            short = "delete an unused file-cdrom object",
            doc = """
Delete an unused file-cdrom object with the name <i>object-name</i>.
""", filename="/mp/simics-3.0/src/extensions/file-cdrom/commands.py", linenumber="11")
