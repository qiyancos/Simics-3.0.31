try:
    import sys,dml.dmlc

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    exitstatus = dml.dmlc.compile(sys.argv)
except KeyboardInterrupt:
    exitstatus = 1

sys.exit(exitstatus)
