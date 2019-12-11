
##  Copyright 2003-2007 Virtutech AB

# handle the code from the 'extra_simics_path' in the .config files

if 'extra_simics_path' in dir():
    if sys.platform == "win32":
        path_sep = ";"
    else:
        path_sep = ":"
        
    for p in extra_simics_path.split(path_sep):
        print "Added to search path: %s" % p
        SIM_add_directory(p, 1)
