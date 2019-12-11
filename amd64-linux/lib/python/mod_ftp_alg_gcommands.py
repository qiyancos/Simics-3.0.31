from cli import *

def enable_ftp_alg_cmd(sn, check_enabled = True):
    try:
        in_obj = SIM_get_object("%s_port_forward_in" % sn.name)
    except:
        print ("The service node %s does not have incoming port forwarding "
               "enabled." % sn.name)
        SIM_command_has_problem()
        return
    try:
        out_obj = SIM_get_object("%s_port_forward_out" % sn.name)
    except:
        print ("The service node %s does not have outgoing port forwarding "
               "enabled." % sn.name)
        SIM_command_has_problem()
        return

    if len([x for x in in_obj.algs if x.classname == 'ftp-alg']):
        if check_enabled:
            print "FTP ALG already enabled for service-node %s." % sn.name
        return

    alg_name = get_available_object_name(sn.name + "_ftp_alg")
    alg_obj = SIM_create_object("ftp-alg", alg_name,
                                [["forward_handler", out_obj],
                                 ["incoming_handler", in_obj]])
    in_obj.algs = in_obj.algs + [alg_obj]
    out_obj.algs = out_obj.algs + [alg_obj]

# Add enable-ftp-alg command to service node namespace

new_command("enable-ftp-alg", enable_ftp_alg_cmd,
            [],
            type = "service-node commands",
            short = "enable FTP ALG",
            namespace = "service-node",
            doc = """
Enable the FTP ALG. FTP ALG processing is needed to support port forwarded
FTP from the outside network to simulated machines.
""", filename="/mp/simics-3.0/src/extensions/ftp_alg/gcommands.py", linenumber="33")
