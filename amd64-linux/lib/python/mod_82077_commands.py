from cli import *
from sim_commands import *
import string, os

disk_types = { "320" : [40,  8, 2],
               "360" : [40,  9, 2],
               "720" : [80,  9, 2],
               "1.2" : [80, 15, 2],
              "1.44" : [80, 18, 2],
              "2.88" : [80, 36, 2]}

def floppy_drive_get_info(obj):
    return ( None )

def floppy_drive_get_status(obj):
    floppy_size = [obj.tracks, obj.sectors_per_track, obj.heads]
    try:
        idx = disk_types.values().index(floppy_size)
        floppy_type = disk_types.keys()[idx]
    except:
        floppy_type = "Unknown"
    
    drive = ("Drive",
             [ ("Busy", obj.drive_busy),
               ("Seek in progress", obj.seek_in_progress),
               ("Disk changed", obj.disk_changed),
               ("Motor", iff(obj.motor_on, "on", "off")),
               ("Data rate", obj.data_rate),
               ("Current head", obj.cur_head),
               ("Current sector", obj.cur_sector) ] )
    if obj.image:
        floppy = ("Floppy",
                  [ ("Floppy type", floppy_type),
                    ("Write protect", obj.write_protect),
                    ("Tracks", obj.tracks),
                    ("Sectors per track", obj.sectors_per_track),
                    ("Heads", obj.heads),
                    ("Image object", obj.image.name) ] )
    else:
        floppy = ("Floppy",
                  [ ("No floppy", "") ])
    return [ drive, floppy ]


new_info_command('floppy-drive', floppy_drive_get_info)
new_status_command('floppy-drive', floppy_drive_get_status)


def i82077_get_info(obj):
    drive_list = join([d.name for d in obj.drives])
    if drive_list == '':
        drive_list = 'None'

    return [ (None,
              [ ("IRQ device", obj.irq_dev),
                ("IRQ number", obj.irq_level),
                ("DMA device", obj.dma_dev),
                ("DMA channel", obj.dma_channel),
                ("Drives", drive_list) ] ) ]
                
def i82077_get_status(obj):
    return [ (None,
              [ ("Enabled", iff(obj.enabled, "yes", "no")),
                ("DMA enabled", iff(obj.dma_enabled, "yes", "no")),
                ("FIFO enabled", iff(obj.fifo_enabled, "yes", "no")),
                ("Poll enabled", iff(obj.poll_enabled, "yes", "no")),
                ("State", ["idle", "command", "execute", "result"][obj.state]),
                ("Step rate", obj.step_rate),
                ("Selected drive", obj.drive_select),
                ("Command busy", obj.command_busy),
                ("Poll change", obj.poll_change),
                ("Current command", "0x%x" % obj.cmd_id),
                ("Implied seek", obj.implied_seek),
                ("ST0 register", obj.st0),
                ("ST1 register", obj.st1),
                ("ST2 register", obj.st2) ] ) ]


new_info_command('i82077', i82077_get_info)
new_status_command('i82077', i82077_get_status)

#
# -------------------- insert-floppy --------------------
#

floppy_count = 0

def insert_floppy_cmd(obj, drive, floppy_file, rw, size):
    global floppy_count
    drive = string.upper(drive)
    if not drive in ('A', 'B'):
        print "Incorrect drive-letter, use one of A and B"
        SIM_command_has_problem()
        return
    try:
        if drive == 'A' and len(obj.drives) < 1:
            raise Exception
        elif len(obj.drives) < 2:
            raise Exception
    except:
        print ("No drive '%s' connected to controller %s. "
               "Cannot insert floppy." % (drive, obj.name))
        SIM_command_has_problem()
        return
    try:
        disk_size = disk_types[size]
    except:
        print "Unknown disk size %s." % size
        SIM_command_has_problem()
        return
    if drive == 'A':
        fd = obj.drives[0]
    else:
        fd = obj.drives[1]
    if fd.image:
        print "Floppy already inserted into drive %s." % drive
        SIM_command_has_problem()
        return
    fd.disk_changed = 1
    fd.tracks = disk_size[0]
    fd.sectors_per_track = disk_size[1]
    fd.heads = disk_size[2]
    # simply replace the old image object
    # make sure we use a unique name (e.g. after a checkpoint)
    unique = 0
    while not unique:
        image_name = 'fd_image_%s_%d' % (drive, floppy_count)
        floppy_count += 1
        try:
            SIM_get_object(image_name)
        except:
            unique = 1
    im_size = disk_size[0] * disk_size[1] * disk_size[2] * 512
    SIM_create_object('image', image_name,
                      [['queue', SIM_current_processor()],
                       ['size', im_size]])
    fd.image = SIM_get_object(image_name)
    filesize = os.stat(floppy_file)[6]
    if filesize == 0:
        filesize = fd.image.size
        print "Image %s reported zero size, assuming special file." % (
            floppy_file)
    rw_str = iff(rw == 1, 'rw', 'ro')
    fd.image.files = [[floppy_file, rw_str, 0, filesize]]
    print "Floppy inserted in drive '%s:'. (File %s)." % (drive, floppy_file)
    if size != '1.44':
        print "Remember to set the floppy size in the CMOS as well."
    
new_command("insert-floppy", insert_floppy_cmd,
            [arg(str_t, "drive-letter"),
             arg(filename_t(exist = 1, simpath = 1), "floppy-image"),
             arg(flag_t, "-rw"),
             arg(str_t, "size", "?", "1.44")],
            alias = "",
            type  = "i82077 commands",
            short = "insert floppy in drive",
	    namespace = "i82077",
            doc = """
Insert the file <arg>floppy-image</arg> as a floppy in the disk drive specified by
<arg>drive-letter</arg>. For floppies with a different size than 1.44 MB, the size
must be specified explicitly.

The <arg>-rw</arg> flag uses <arg>floppy-image</arg> in read-write mode, meaning
that no save or save-diff-file command to the associated image object need to be
used in order to save data written by the target software.
""", filename="/mp/simics-3.0/src/devices/82077/commands.py", linenumber="149")

def eject_floppy_cmd(obj, drive):
    drive = string.upper(drive)
    if not drive in ('A', 'B'):
        print "Incorrect drive-letter, use one of A and B"
        SIM_command_has_problem()
        return
    try:
        if drive == 'A' and len(obj.drives) < 1:
            raise Exception
        elif len(obj.drives) < 2:
            raise Exception
    except:
        print ("No drive '%s' connected to controller %s. "
               "Cannot insert floppy." % (drive, obj.name))
        SIM_command_has_problem()
        return
    if drive == 'A':
        fd = obj.drives[0]
    else:
        fd = obj.drives[1]
    if fd.image == None:
        print "No floppy in drive %s." % drive
        SIM_command_has_problem()
        return
    fd.disk_changed = 1
    fd.image = None
    print "Floppy ejected from drive '%s:'." % (drive)

new_command("eject-floppy", eject_floppy_cmd,
            [arg(str_t, "drive-letter")],
            type  = "i82077 commands",
            short = "eject floppy",
	    namespace = "i82077",
            doc = """
Eject the media from the disk drive specified by <i>drive-letter</i>.
""", filename="/mp/simics-3.0/src/devices/82077/commands.py", linenumber="196")
