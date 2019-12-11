#!/usr/bin/python
# This script really wants Python 2.4

##  Copyright 2005-2007 Virtutech AB
##  
##  The contents herein are Source Code which are a subset of Licensed
##  Software pursuant to the terms of the Virtutech Simics Software
##  License Agreement (the "Agreement"), and are being distributed under
##  the Agreement.  You should have received a copy of the Agreement with
##  this Licensed Software; if not, please contact Virtutech for a copy
##  of the Agreement prior to using this Licensed Software.
##  
##  By using this Source Code, you agree to be bound by all of the terms
##  of the Agreement, and use of this Source Code is subject to the terms
##  the Agreement.
##  
##  This Source Code and any derivatives thereof are provided on an "as
##  is" basis.  Virtutech makes no warranties with respect to the Source
##  Code or any derivatives thereof and disclaims all implied warranties,
##  including, without limitation, warranties of merchantability and
##  fitness for a particular purpose and non-infringement.


import sys
import re
import os.path
from optparse import OptionParser

latestvers = "1.0"

keyword_translations = {
    ('0.9','1.0') : { 'verbatim'  : 'extern',
                      'log-group' : 'loggroup',
                      'except'    : 'catch',
                      'fail'      : 'throw',
                      'exit'      : 'return'}
    }

def convert(filename):
    tofilename = os.path.basename(filename) + '-' + options.tovers + '.dml'
    infile = file(filename, 'r')
    outfile = file(tofilename, 'w')

    # Initial comment
    ln = infile.readline()
    while ln and re.match(r'^\s*(//.*|)$', ln):
        outfile.write(ln)
        ln = infile.readline()

    # Is it a dml version marker?
    m = re.match(r'^\s*dml\s+([0-9.]+)\s*;.*$', ln)
    if m:
        print 'VERS %r' % m.group(1)
        vers = m.group(1)
        if options.tovers == vers:
            fromvers = vers
            sys.stderr.write("*** nop: %r is already DML %s\n" %
                             (filename, vers))
            outfile.write("dml %s;\n" % options.tovers)
            for ln in infile:
                outfile.write(ln)
            return
        elif options.fromvers in ('any', vers):
            fromvers = vers
        else:
            sys.stderr.write("*** version mismatch: %r is DML %s\n" %
                             (filename, vers))
            fromvers = vers

        ln = infile.readline()
    else:
        if options.verbose:
            print "... source has no version tag, assuming DML 0.9"
        fromvers = "0.9"

    if options.verbose:
        print "... converting from DML %s to DML %s" % (fromvers, options.tovers)
    outfile.write("dml %s;\n" % options.tovers)

    while ln:
        # import foo -> import "foo.dml"
        m = re.match(r'(\s*import\s+)([a-zA-Z][-_a-zA-Z0-9]*)', ln)
        if m:
            mod = m.group(2)
            if fromvers == '0.9':
                if mod == 'builtin':
                    mod = 'utility'
                elif mod == 'io-mapped':
                    mod = 'io-memory'
            ln = m.group(1) + '"%s.dml"' % mod + ln[m.end():]

        # identifier transformations
        instring = False
        i = 0
        while i < len(ln):
            if ln[i:i+2] == '//':
                break
            elif ln[i] == '"':
                i += 1
                while ln[i] != '"':
                    if ln[i] == '\\':
                        i += 1
                    i += 1
                    if i >= len(ln):
                        sys.stderr.write('*** multi-line string? %d %r\n' % (i, ln))
                i += 1
            else:
                m = re.match(r'[a-zA-Z_]([a-zA-Z0-9_-]*[a-zA-Z0-9_]|)', ln[i:])
                if m:
                    ident = m.group()
                    replacement = keyword_translations[(fromvers,options.tovers)].get(ident)
                    if not replacement:
                        replacement = ident.replace('-', '_')
                    if options.verbose and replacement != ident:
                        print "... changing %s -> %s" % (ident, replacement)
                    ln = ln[:i] + replacement + ln[i + len(ident):]
                    i += len(ident)
                else:
                    i += 1

        # Log statements
        m = re.match(r'''(\s*)
            log \s+
            (info|undefined|spec_violation|target_error|unimplemented) \s+
            (\d+) \s+
            \(([^)]*)\)''', ln, re.X)
        if m:
            pfx = m.group(1)
            cls = m.group(2)
            lvl = m.group(3)
            grp = m.group(4)
            rest = ln[m.end():]
            ln = pfx + 'log "%s"' % cls
            if 1 or lvl != '1' or grp != '0':
                ln += ', %s' % lvl
            if grp != '0':
                ln += ', %s' % grp
            ln += ':' + rest

        m = re.match(r'''(\s*) log \s+ error \s+ \(([^)]*)\)''', ln, re.X)
        if m:
            pfx = m.group(1)
            grp = m.group(2)
            rest = ln[m.end():]
            ln = pfx + 'log "error"'
            if 1 or grp != '0':
                ln += ', 1, %s' % grp
            ln += ':' + rest

        # for (a <= i < b) -> for (i = 0; i++; i < b)
        m = re.match(r'''(\s*) for \s*
                     \( (.*\S) \s*<=\s* ([a-zA-Z][a-zA-Z0-9_]*)
                     \s*<\s* (.*\S) \)''', ln, re.X)
        if m:
            ident = m.group(3)
            ln = '%sfor (%s = %s; %s < %s; %s++)' % \
                 (m.group(1), ident, m.group(2), ident, m.group(4), ident)

        # field FFF a:b  ->  field FFF [a:b]
        m = re.match(r'''(\s* field \s*
                          [a-zA-Z0-9_]+ \s*)
                         (\d+ \s* : \s* (?:\d+|\$[a-zA-Z0-9_]+))''', ln, re.X)
        if m:
            ln = "%s[%s]%s" % (m.group(1), m.group(2), ln[m.end():])


        # finalize -> post_init
        #m = re.match(r'''finalize''', ln, re.X)
        #if m:
        #    ln = "%s%s%s" % (m.group(1), "post_init", ln[m.end():])

        # Done with conversions

        outfile.write(ln)
        ln = infile.readline()


optp = OptionParser(usage = "%prog [options] filename ...")
optp.add_option("-v", "--verbose",
                action = "store_true",
                default = False,
                help = "verbose output")
optp.add_option("-f", "--from",
                dest = "fromvers",
                default = "any",
                help = "convert from version VERS [default %default]",
                metavar = "VERS")
optp.add_option("-t", "--to",
                dest = "tovers",
                default = latestvers,
                help = "convert to version VERS [default %default]",
                metavar = "VERS")

options, args = optp.parse_args()

if options.tovers != '1.0':
    sys.stderr.write('*** can only convert to DML 1.0')
    sys.exit(1)

for f in args:
    print "Converting %r from %s to %s" % (f, options.fromvers, options.tovers)
    convert(f)
