#!/usr/bin/env python

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


import lex, yacc
import os, subprocess, re, string, sys, shutil

#### LEX

tokens = ('COMMENT', 'COLON', 'COMMA', 'ID', 'LBRAC', 'LINECOMMENT', 'LPAR',
          'OBJECT', 'RAWEND', 'RAWSTART', 'RBRAC', 'RPAR', 'STRING', 'TYPE' )

t_LPAR     = r'\('
t_RPAR     = r'\)'
t_LBRAC    = r'{'
t_RBRAC    = r'}'
t_COLON    = r':'
t_COMMA    = r','
t_RAWEND   = r']'
t_RAWSTART = r'\[R'
# string ends with ", not \", except \\" that is ok.
# this does not work with \\\" within a string
t_STRING  = r'".*?(?<!(?<!\\)\\)"'

# use functions for most tokens to keep parse order

def t_COMMENT(t):
    r'/\*.*?\*/'
    pass

def t_LINECOMMENT(t):
    r'\#.*\n'
    pass

def t_ID(t):
    r'(\.|[A-Za-z0-9+/_-])+'
    if t.value in ['OBJECT', 'TYPE']:
        t.type = t.value
    return t

def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)

t_ignore  = ' \t'

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.skip(1)

#### YACC

def p_configuration(p):
    'configuration : objects'
    p[0] = p[1]

def p_objects(p):
    'objects : objects object'
    p[0] = p[1] + [p[2]]

def p_objects_empty(p):
    'objects : empty'
    p[0] = []

def p_object(p):
    'object : OBJECT ID TYPE ID LBRAC attributes RBRAC'
    p[0] = [p[2], p[4], p[6]]

def p_attributes(p):
    'attributes : attributes attribute'
    p[0] = p[1] + [p[2]]

def p_attributes_empty(p):
    'attributes : empty'
    p[0] = []

def p_attribute(p):
    'attribute : ID COLON value'
    p[0] = [p[1], p[3]]

def p_value_id(p):
    'value : ID'
    p[0] = p[1]

def p_value_string(p):
    'value : STRING'
    p[0] = p[1]

def p_value_raw(p):
    'value : RAWSTART ID STRING ID RAWEND'
    p[0] = (p[2], p[3], p[4])

def p_value_list(p):
    'value : LPAR valuelist RPAR'
    p[0] = p[2]

def p_valuelist(p):
    'valuelist : valuelist COMMA value'
    p[0] = p[1] + [p[3]]

def p_valuelist_value(p):
    'valuelist : value'
    p[0] = [p[1]]

def p_valuelist_empty(p):
    'valuelist : empty'
    p[0] = []

def p_value_dict(p):
    'value : LBRAC pairs RBRAC'
    p[0] = p[2]

def p_pairs(p):
    'pairs : pairs COMMA pair'
    p[0] = p[1].copy()
    p[0].update(p[3])

def p_pairs_pair(p):
    'pairs : pair'
    p[0] = p[1]

def p_pair(p):
    'pair : value COLON value'
    p[0] = {p[1] : p[3]}
    
def p_pair_empty(p):
    'pair : empty'
    p[0] = {}

def p_empty(p):
    'empty :'
    pass

# dummy rule to avoid unused warnings
def p_dummy(p):
    'configuration : COMMENT LINECOMMENT'
    pass

def p_error(p):
    print "Syntax error in input:", p

####

def init_parser():
    lex.lex(debug = 0, optimize = 1)
    yacc.yacc(debug = 0, optimize = 1)

def attr_string(a):
    if type(a) == type(()):
        return '[R %s "%s" %s ]' % (a[0], rawfile, a[2])
    elif type(a) == type([]):
        val = "("
        first = ""
        for aa in a:
            val += first + attr_string(aa)
            first = ", "
        return val + ")"
    elif type(a) == type({}):
        val = "{"
        first = ""
        for aa in a.items():
            val += first + attr_string(aa[0]) + " : " + attr_string(aa[1])
            first = ", "
        return val + "}"
    return a

def write_configuration(conf, filename):
    try:
        file = open(filename, "w")
    except Exception, msg:
        print "Failed opening output file '%s': %s" % (filename, msg)
        raise Exception
    for o in conf:
        file.write("OBJECT %s TYPE %s {\n" % (o[0], o[1]))
        for a in o[2]:
            file.write("\t%s: %s\n" % (a[0], attr_string(a[1])))
        file.write("}\n")
    file.close()

def read_configuration(filename):
    try:
        file = open(filename)
    except Exception, msg:
        print "Failed opening checkpoint file '%s'" % filename
        print "Error: %s" % msg
        sys.exit(1)
    try:
        return yacc.parse(string.join(file.readlines()))
    except Exception, msg:
        print "Failed parsing checkpoint file '%s'" % filename
        print "Error: %s" % msg
        sys.exit(1)

def get_attr(conf, o, a):
    try:
        [obj] = [x for x in conf if x[0] == o]
        [attr] = [x for x in obj[2] if x[0] == a]
        return attr[1]
    except:
        return None

def set_attr(conf, o, a, v):
    try:
        [obj] = [x for x in conf if x[0] == o]
        [attr] = [x for x in obj[2] if x[0] == a]
        attr[1] = v
    except:
        pass

def get_simics_path(conf):
    paths = get_attr(conf, "sim", "simics_path")
    if not paths:
        # persistent state files do not have any simics_path for example
        return None
    return [p for p in paths if not "%simics%" in p]

def get_mergelist_and_patch(conf, skip):
    merge_list = []
    images = [o[0] for o in conf if o[1] == "image"]
    for i in images:
        files = get_attr(conf, i, "files")
        last = len(files) - 1
        if last < 0:
            continue
        id = first = skip
        new_files = files[:skip]
        while first <= last:
            next = min(first + 1, last)
            # merge all files, keep matching ones together
            while (files[first][2] == files[next][2]
                   and files[first][3] == files[next][3]
                   and files[first][4] == files[next][4]):
                next += 1
                if next > last:
                    break
            new_files += [['"%s-%s-%d.craff"' % (dstfile, i, id)] + files[first][1:]]
            merge_list += [["%s-%s-%d.craff" % (dst, i, id)] +
                           [[string.strip(f[0], '"') for f in files[first:next]]]]
            id += 1
            first = next
        set_attr(conf, i, "files", new_files)
    return merge_list

def expand_checkpoint_path(f, path):
    match = re.match("%([0-9]*)%/(.*)", f)
    if match:
        path_with_sep = "%s%s" % (path[int(match.group(1))], os.sep)
        return os.path.join(path_with_sep, match.group(2))
    else:
        raise Exception


def file_exists(filename):
    try:
        os.stat(filename)
        return filename
    except:
        return None

def find_image_files(merge_list, path, checkpoint_path):
    for m in range(0, len(merge_list)):
        for i in range(0, len(merge_list[m][1])):
            f = merge_list[m][1][i]
            file = None
            try:
                file = file_exists(expand_checkpoint_path(f, checkpoint_path))
            except:
                for p in path:
                    file = os.path.join(p, f)
                    if file_exists(file):
                        break
                    file = None
            if not file:
                print "File %s not found. Add a path to this file." % f
                raise Exception
            merge_list[m][1][i] = file
    return merge_list

def run_command(cmd):
    res = subprocess.call(cmd)
    if res != 0:
        print
        print "Command returned an error, checkpoint not merged!"
        print "Command string: %s" % cmd
        print
        sys.exit(1)

####

if len(sys.argv) < 3:
    print "Usage:"
    print
    print "checkpoint-merge <src checkpoint> <dst checkpoint> [<image path>]*"
    print
    print "<src checkpoint>: the checkpoint file to merge files from."
    print "<dst checkpoint>: the new checkpoint file."
    print "<image path>    : paths to checkpoint files."
    print
    sys.exit(1)

craff_ok = False
if sys.platform == "win32" or sys.platform == "cygwin":
    craff_ok = subprocess.call("craff -h", stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT) == 0
else:
    craff_ok = os.system("craff -h 2>&1 > /dev/null") == 0

if not craff_ok:
    print "\nCan't find craff utility in path.\n"
    sys.exit(1)

src = sys.argv[1]
dst = sys.argv[2]
path = sys.argv[3:]
dstfile = os.path.basename(dst)
chkptdir = os.path.dirname(src)
if chkptdir == '':
    chkptdir = '.'
path = [chkptdir] + path
rawfile = "%s.raw" % dstfile

# Supporting 'skip' requires path handling of files that are
# skipped, not simple in the general case.
skip = 0

init_parser()

conf = read_configuration(src)

sp = get_simics_path(conf)
if sp:
    path += sp
checkpoint_path = [string.strip(p, '"') for p in
                   get_attr(conf, "sim", "checkpoint_path")]
if skip == 0:
    # only remove if no references may be left
    set_attr(conf, "sim", "checkpoint_path", [])

merge_list = get_mergelist_and_patch(conf, skip)
if len(merge_list):
    try:
        merge_list = find_image_files(merge_list, path, checkpoint_path)
    except:
        sys.exit(1)

    print
    print "Running craff to merge checkpoint image files."
    i = 1
    for m in merge_list:
        print "Creating %s (%d of %d)" % (m[0], i, len(merge_list))
        cmd = ["craff", "-o", m[0]]
        for f in m[1]:
            cmd.append(f)
        run_command(cmd)
        i += 1

try:
    if os.path.exists("%s.raw" % src):
        shutil.copy("%s.raw" % src, "%s.raw" % dst)
except Exception, msg:
    print
    print "Copying of .raw file failed, checkpoint not merged!"
    print "Error message: %s" % msg
    print
    sys.exit(1)

write_configuration(conf, dst)

print
print "Finished writing merged checkpoint: %s" % dst
print "Try the new checkpoint before removing old ones."
print
