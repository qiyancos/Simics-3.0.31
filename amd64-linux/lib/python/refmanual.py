import sys
import string
import re
import os
import traceback
import random
import types
import posixpath

from sim_core import *
from cli import *
import conf
import sim
import __builtin__

#
# Some constants to play with
#

# minimum number of elements for a "long" table
min_long_table = 10

# core 'module' definitions
core_module = "Simics Core"
core_module_file = "libsimics-common.so"


#
# load all modules available (for internal reference manual)
#
def loadAllModules():
    
    def for_all_modules_cb(name, filename, version, info):
        try:
            print "Loading module", name, filename
            VT_load_module_file(filename)
        except:
            pass

    # add all other modules
    SIM_for_all_modules(for_all_modules_cb)



#
# Functions to handle labels and ids
#

# remove characters that are not allowed in ids
def labelEncode(str):
    res_str = ''
    for c in str:
        if c == '<':
            res_str = res_str + '_lt_'
        elif c == '>':
            res_str = res_str + '_gt_'
        elif c == '&':
            res_str = res_str + '_amp_'
        else:
            res_str = res_str + c
    return res_str

# return a base id for a class
def classId(c):
    return '__rm_class_' + labelEncode(c)

# return a base id for a module
def moduleId(m):
    return '__rm_module_' + labelEncode(m)

# return a base id for a command
def commandId(c):
    return '__rm_command_' + labelEncode(c)

# return a base id for an interface
def ifcId(c):
    return '__rm_interface_' + labelEncode(c)

# return a base id for an attribute
def attrId(c, a):
    return '__rm_attribute_' + labelEncode(c) + '_' + labelEncode(a)

# return a base id for a hap
def hapId(h):
    return '__rm_hap_' + labelEncode(h)


#
# Misc. helper functions
#

# return a string based on the attribute type
def typeEncode(t):
    if t == "i":
        return "Integer"
    elif t == "f":
        return "Float"
    elif t == "d":
        return "Data"
    elif t == "o":
        return "Object"
    elif (t == "o|n") or (t == "n|o"):
        return "Object or Nil"
    elif (t == "n"):
        return "Nil"
    elif (t == "s"):
        return "String"
    else:
        return t

# compare two commands by name
def cmp_cmd(a,b):
    return cmp(a["name"].lower(), b["name"].lower())

# compare two description items (module, class, attr, ..) by name
def cmp_item(a,b):
    return cmp(a.name.lower(), b.name.lower())

# Strip away the namespace from a command name
def stripCommandName(c):
    return c[c.rfind('.')+1:]



#
# Output handlers
# 
class GenericOutputHandler:
    def __init__(self, output_file):
        self.of = file(output_file, "w")

    # output functions
    def pr(self, s):
        self.of.write(s)
    def pn(self, s):
        self.of.write(s + "\n")

    #
    # output dependent functions
    #

    # encode special character for output
    # encode for XML output
    def encode(self, str):
        res_str = ''
        for c in str:
            if c == '<':
                res_str = res_str + '&lt;'
            elif c == '>':
                res_str = res_str + '&gt;'
            elif c == '&':
                res_str = res_str + '&amp;'
            else:
                res_str = res_str + c
        return res_str

    # return a link towards 'label' with text 'text'
    def makeLink(self, label, text):
        return text

    # return an index entry made from 'list'
    def makeIndex(self, list):
        return ""

    # equivalent to <add id="..." label="..."><name>...</name> ... </add>
    def beginAdd(self, id, label, type = ''):
        pass
    def endAdd(self):
        pass

    # equivalent to <section .../>
    def printSection(self, numbering, id):
        pass

    # equivalent to <doc> ... </doc>
    def beginDoc(self):
        pass
    def endDoc(self):
        pass

    # equivalent to <di type=""> + eventual <di-name>
    def beginDocItem(self, name):
        pass
    # equivalent to </di>
    def endDocItem(self):
        pass

    # tables
    def beginTable(self, length):
        pass
    def endTable(self):
        pass
    def beginRow(self):
        pass
    def endRow(self):
        pass
    def beginCell(self):
        pass
    def endCell(self):
        pass

    def makeTable(self, str):
        return str
    def makeRow(self, str):
        return str
    def makeCell(self, str):
        return str

    # description list
    def beginDList(self):
        pass
    def endDList(self):
        pass
    def beginDListTitle(self):
        pass
    def endDListTitle(self):
        pass
    def makeDListTitle(self, text):
        return text
    def beginDListItem(self):
        pass
    def endDListItem(self):
        pass
    
    # quote a string
    def q(self, text):
        return '"' + text + '"'
    
    #
    # list: list of strings to print
    # link_prefix: how to create the link name for nref
    # text_transform: change text before printing
    # pre: what to print before each element
    # post: what to print after each element
    # sep: what to print between each element
    #
    def printListWithSep(self, list, link_transform, text_transform,
                         pre, post, sep):
        l = len(list);
        for i in range(0, l):
            self.pr(pre)
            if link_transform:
                self.pr(self.makeLink(link_transform(list[i]),
                                      text_transform(list[i])))
            else:
                self.pr(text_transform(list[i]))
            self.pr(post)
            if i != (l-1):
                self.pr(sep)


#
# JDocu specialized output handler
#
class JdocuOutputHandler(GenericOutputHandler):

    def __init__(self, filename):
        GenericOutputHandler.__init__(self, filename)
        self.in_dlist_item = False

    # return a link towards 'label' with text 'text'
    def makeLink(self, label, text):
        return '<nref label="' + label + '">' + text + '</nref>'

    # return an index entry made from 'list'
    def makeIndex(self, list):
        return '<ndx>' + "!".join(list) + '</ndx>'

    # return a target link with 'label'
    def makeTarget(self, label):
        return '<ntarget label="' + label + '"/>'

    def beginAdd(self, id, label, name, type = ''):
        self.pr('<add id="' + id + '"')
        if label:
            self.pr(' label="' + label + '"')
        self.pn('>')
        self.pn('<name>' + name + '</name>')
    def endAdd(self):
        self.pn('</add>')

    def printSection(self, numbering, id):
        self.pn('<section numbering="' + numbering + '" id="' + id + '"/>')

    # equivalent to <doc>
    def beginDoc(self):
        self.pn('<doc>')
    # equivalent to </doc>
    def endDoc(self):
        self.pn('</doc>')

    # equivalent to <di type=""> + eventual <di-name>
    def beginDocItem(self, name):
        lname = name.lower()
        type = ""
        if (lname == "name" or
            lname == "short" or
            lname == "synopsis" or
            lname == "description" or
            lname == "parameters" or
            lname == "returnvalue" or
            lname == "exceptions"):
            type = lname
        if type:
            self.pn('<di type="' + type + '">')
        else:
            self.pn('<di>\n<di-name>' + name + '</di-name>')
            
    # equivalent to </di>
    def endDocItem(self):
        self.pn('</di>')

    # tables
    def beginTable(self, length):
        if length > min_long_table:
            self.pn('<table long="true">')
        else:
            self.pn('<table long="false">')
    def endTable(self):
        self.pn('</table>')
    def beginRow(self):
        self.pr('<tr>')
    def endRow(self):
        self.pn('</tr>')
    def beginCell(self):
        self.pr('<td>')
    def endCell(self):
        self.pr('</td>')

    def makeTable(self, str):
        return '<table>' + str + '</table>'
    def makeRow(self, str):
        return '<tr>' + str + '</tr>'
    def makeCell(self, str):
        return '<td>' + str + '</td>'

    # description list
    def beginDList(self):
        assert not self.in_dlist_item
        self.pn('<dl>')
    def endDList(self):
        if self.in_dlist_item:
            self.pr('</dd>')
            self.in_dlist_item = False
        self.pn('</dl>')
    def beginDListTitle(self):
        assert not self.in_dlist_item
        self.pr('<dt>')
    def endDListTitle(self):
        assert not self.in_dlist_item
        self.pn('</dt>')
    def makeDListTitle(self, text):
        return '<dt>' + text + '</dt>'
    def beginDListItem(self):
        if not self.in_dlist_item:
            self.pr('<dd>')
            self.in_dlist_item = True
        else:
            self.pr('\n\n')
    def endDListItem(self):
        assert self.in_dlist_item



#
# JDocu specialized output handler
#
class TerminalOutputHandler(GenericOutputHandler):
    def __init__(self):
        self.current_indent = 0
        self.buffer = ""

    # output functions
    def pr(self, s):
        while s:
            nextline = s.find('\n')
            if nextline == -1:
                self.buffer = self.buffer + s
                s = None
            else:
                if self.current_indent:
                    pr(" "*self.current_indent)
                format_print(self.buffer + s[0:nextline],
                             self.current_indent, 80)
                pr('\n')
                self.buffer = ''
                s = s[nextline+1:]
        
    def pn(self, s):
        self.pr(s + "\n")

    def incr_indent(self, n):
        self.current_indent = self.current_indent + n

    def decr_indent(self, n):
        self.current_indent = self.current_indent - n

    # return a link towards 'label' with text 'text'
    def makeLink(self, label, text):
        return text

    # return an index entry made from 'list'
    def makeIndex(self, list):
        return ''

    # return a target link with 'label'
    def makeTarget(self, label):
        return ''

    def beginAdd(self, id, label, name, type = ''):
        if type:
            self.pn('<i>' + type + ' <b>' + name + '</b></i>')
        else:
            self.pn('<b>' + name + '</b>')
        self.pn('')
        self.incr_indent(2)
    def endAdd(self):
        self.decr_indent(2)

    def printSection(self, numbering, id):
        pass

    # equivalent to <doc>
    def beginDoc(self):
        pass
    # equivalent to </doc>
    def endDoc(self):
        pass

    # equivalent to <di type=""> + eventual <di-name>
    def beginDocItem(self, name):
        lname = name.lower()
        type = ""
        if (lname == "name" or
            lname == "short" or
            lname == "synopsis" or
            lname == "description" or
            lname == "parameters" or
            lname == "returnvalue" or
            lname == "exceptions"):
            type = lname
        if type:
            self.pn('<b>' + name.capitalize() + '</b>')
        else:
            self.pn('<b>' + name + '</b>')
        self.incr_indent(2)
            
    # equivalent to </di>
    def endDocItem(self):
        self.pn('')
        self.pn('')
        self.decr_indent(2)

    # tables
    def beginTable(self, length):
        pass
    def endTable(self):
        pass        
    def beginRow(self):
        pass
    def endRow(self):
        self.pn('')
    def beginCell(self):
        pass
    def endCell(self):
        self.pr(' ')

    def makeTable(self, str):
        return str
    def makeRow(self, str):
        return str
    def makeCell(self, str, size = 20):
        return str + '&nbsp;'*(iff(len(str) > (size-1), 1, size-len(str)))

    # description list
    def beginDList(self):
        pass
    def endDList(self):
        pass
    def beginDListTitle(self):
        self.pr('<b>')
    def endDListTitle(self):
        self.pn('</b>')
    def makeDListTitle(self, text):
        return '<b>' + text + '</b>'
    def beginDListItem(self):
        pass
    def endDListItem(self):
        self.pn("\n")



#
# Generic Description Container
#
class GenericDesc:
    def __init__(self, verbose = 1):
        self.verbose = verbose
    def verbosePrint(self, str):
        if self.verbose:
            print str

#
# Command Description
#
class CmdDesc(GenericDesc):
    def __init__(self, verbose, name, cmd):
        self.name = name
        self.cmd = cmd
        self.module = None              # if this is a module command
        self.verbose = verbose
        self.doc_with_list = []

    def getSynopsis(self, command_list):
        if self.doc_with_list:
            syn_cmd_list = []
            for c in self.doc_with_list:
                if command_list.has_key(c):
                    syn_cmd_list.append(c)
            syn_cmd_list.sort()
        elif self.cmd["doc_with"] and command_list.has_key(self.cmd["doc_with"]):
            main_cmd = command_list[self.cmd["doc_with"]]
            syn_cmd_list = []
            for c in main_cmd.doc_with_list:
                if (c != self.name) and command_list.has_key(c):
                    syn_cmd_list.append(c)
            syn_cmd_list.append(main_cmd.name)
            syn_cmd_list.sort()
        else:
            syn_cmd_list = []

        syn_cmd_list = [self.name] + syn_cmd_list
        synopsis = ""
        for c in syn_cmd_list:
            synopsis = (synopsis
                        + get_synopsis(command_list[c].cmd, 0, 1, "jdocu")
                        + "<br/>")
        return synopsis[:-5]

    def getDoc(self, command_list, avoided_command_list):
        if self.cmd["doc_with"]:
            if command_list.has_key(self.cmd["doc_with"]):
                doc = command_list[self.cmd["doc_with"]].cmd["doc"]
            else:
                doc = avoided_command_list[self.cmd["doc_with"]].cmd["doc"]
        else:
            doc = self.cmd["doc"]
        return doc

    def getSeeAlso(self, command_list, avoided_command_list):
        if self.cmd["doc_with"]:
            if command_list.has_key(self.cmd["doc_with"]):
                s = command_list[self.cmd["doc_with"]].cmd["see_also"]
            else:
                s = avoided_command_list[self.cmd["doc_with"]].cmd["see_also"]
        else:
            s = self.cmd["see_also"]
        return s

    def printLong(self, o, doc, id = '', online = 0,
                  namespace = None, no_extern_link = 0):
        command_list = doc['command_list']
        avoided_command_list = doc['avoided_command_list']
        if online:
            cmd_name = o.encode(self.cmd["name"])
        else:
            cmd_name = o.encode(stripCommandName(self.cmd["name"]))
        o.beginAdd(id, "", cmd_name, 'Command')
        o.pr(o.makeTarget(commandId(self.cmd["name"])))

        if namespace:
            o.pr(o.makeIndex([o.encode(stripCommandName(self.name)),
                              "namespace command",
                              namespace]))
        else:
            o.pr(o.makeIndex([o.encode(self.name)]))

        o.beginDoc()

        # name
        if not online:
            o.beginDocItem('name')
            o.pr('<b>' + o.encode(self.cmd["name"]))
            if self.cmd["deprecated"]:
                o.pr(' &mdash; <i>deprecated</i>');
            o.pr('</b>')
            o.endDocItem()

        # aliases
        if (self.cmd["alias"]):
            o.beginDocItem('Alias')
            if self.cmd["namespace"]:
                aliases = []
                for a in self.cmd["alias"]:
                    aliases.append('<' + self.cmd["namespace"] + '>.' + a)
            else:
                aliases = self.cmd["alias"]
            for a in aliases:
                if namespace:
                    o.pr(o.makeIndex([o.encode(stripCommandName(a)),
                                      "namespace command",
                                      namespace]))
                else:
                    o.pr(o.makeIndex([o.encode(a)]))
                    
            o.printListWithSep(aliases, None, o.encode, "", "", ", ")
            o.endDocItem()

        # synopsis
        o.beginDocItem('synopsis')
        o.pr(self.getSynopsis(command_list))
        o.endDocItem()

        # description
        o.beginDocItem('description')
        if self.cmd["deprecated"]:
            o.pn('This command is deprecated, use '
                 + iff(no_extern_link,
                       o.encode(self.cmd["deprecated"]),
                       o.makeLink(commandId(self.cmd["deprecated"]),
                                  o.encode(self.cmd["deprecated"])))
                 + ' instead.')
            o.pn('')
        o.pr(self.getDoc(command_list, avoided_command_list).strip())
        o.endDocItem()

        # provided by
        if self.module:
            o.beginDocItem('Provided By')
            o.pr(iff(no_extern_link,
                     self.module,
                     o.makeLink(moduleId(self.module), self.module)))
            o.endDocItem()

        # doc items
        if self.cmd["doc_items"]:
            for di in self.cmd["doc_items"]:
                o.beginDocItem(di[0].capitalize())
                # hack around See Also
                if di[0].lower() == "see also":
                    o.pr(o.encode(di[1].strip()))
                else:
                    o.pr(di[1].strip())
                o.endDocItem()

        # see also
        see_also = self.getSeeAlso(command_list, avoided_command_list)
        if see_also:
            for c in see_also:
                if not command_list.has_key(c):
                    self.verbosePrint(
                        "CmdDesc::printLong(): " +
                        "*** unknown see also reference in command "
                        + self.cmd["name"] +": " + c)
            o.beginDocItem('See Also')
            o.printListWithSep(see_also,
                               iff(no_extern_link, None, commandId),
                               o.encode, "", "", ", ")
            o.endDocItem()

        o.endDoc()
        o.endAdd()

    def printComponentCommand(self, o, doc, id = '',
                              namespace = None, no_extern_link = 0):
        command_list = doc['command_list']
        avoided_command_list = doc['avoided_command_list']
        cmd_name = o.encode(stripCommandName(self.cmd["name"]))
        o.beginAdd(id, "", cmd_name, 'Command')
        o.pr(o.makeTarget(commandId(self.cmd["name"])))

        if namespace:
            o.pr(o.makeIndex([o.encode(stripCommandName(self.name)),
                              "namespace command",
                              namespace]))
        else:
            o.pr(o.makeIndex([o.encode(self.name)]))

        o.beginDoc()
        o.beginDocItem(get_synopsis(self.cmd, 0, 1, "jdocu"))
        o.pr(self.getDoc(command_list, avoided_command_list).strip())
        o.endDocItem()
        o.endDoc()
        o.endAdd()

#
# Module Description
#
class ModuleDesc(GenericDesc):
    def __init__(self, verbose, name, filename, unload):
        self.verbose = verbose
        self.name = name
        self.filename = filename
        if (unload == "UNLOAD"):
            self.unload = 1
        else:
            self.unload = 0
        self.classes = []
        self.commands = {}
        self.haps = VT_get_implemented_haps(name)

    def print_name(self, o):
        o.pr(self.name)

    def print_short(self, o):
        o.pr(self.name)

    def printLong(self, o, doc, online = 0, no_extern_link = 0):
        class_list = doc['class_list']
        id = moduleId(self.name)
        o.beginDoc()

        # name
        if not online:
            o.beginDocItem('name')
            o.pr(o.encode(self.name))
            o.endDocItem()
            o.pr(o.makeTarget(id))
        else:
            o.beginAdd('', '', self.name, 'Module')
            
        o.pr(o.makeIndex([self.name]))

        # filename
        o.beginDocItem('Filename')
        o.pr('    <file>' + os.path.basename(self.filename) + '</file>')
        o.endDocItem()

        # classes
        if self.classes:
            o.beginDocItem('Classes')
            o.beginTable(len(self.classes))
            self.classes.sort()
            for c in self.classes:
                cl = class_list[c]
                o.pr(o.makeRow(o.makeCell(
                    iff(no_extern_link,
                        cl.name,
                        o.makeLink(classId(cl.name), cl.name)))))
            o.endTable()
            o.endDocItem()
        if self.haps:
            o.beginDocItem('Haps')
            o.beginTable(len(self.haps))
            self.haps.sort()
            for h in self.haps:
                o.pr(o.makeRow(o.makeCell(
                    iff(no_extern_link,
                        h,
                        o.makeLink(hapId(h), h)))))
            o.endTable()
            o.endDocItem()
        if self.commands:
            o.beginDocItem('Global Commands')
            o.beginTable(len(self.commands))
            cmds = self.commands.values()
            cmds.sort(cmp_item)
            for c in cmds:
                o.beginRow()
                o.pr(o.makeCell(
                    iff(no_extern_link,
                        o.encode(c.cmd["name"]),
                        o.makeLink(commandId(c.cmd["name"]),
                                   o.encode(c.cmd["name"])))))
                o.beginCell()
                if c.cmd["deprecated"]:
                    o.pr("<i>deprecated</i> &mdash; ")
                o.pr(c.cmd["short"])
                o.endCell()
                o.endRow()
            o.endTable()
            o.endDocItem()
        o.endDoc()

#
# group connectors with same base-name together
#
def group_connector_info(connectors):
    def add_cnt_info():
        if last - 1 > start:
            new_cnts['%s[%d-%d]' % (cnt, start, last - 1)] = info
        else:
            new_cnts['%s%d' % (cnt, start)] = info

    new_cnts = {}
    cnt_info = {}
    for cnt in connectors:
        m = re.match('(.*?)([0-9]*)$', cnt)
        if not m.group(2):
            new_cnts[m.group(1)] = connectors[cnt]
        elif not m.group(1) in cnt_info:
            cnt_info[m.group(1)] = [int(m.group(2))]
        else:
            cnt_info[m.group(1)] += [int(m.group(2))]
    for cnt in cnt_info:
        cnt_info[cnt].sort()
        start = cnt_info[cnt][0]
        last = start
        for i in cnt_info[cnt]:
            info = connectors[cnt + `start`]
            if (i != last
                or info != connectors[cnt + `i`]):
                add_cnt_info()
                start = last = i
            last += 1
        if i == last - 1:
            add_cnt_info()
    return new_cnts

#
# Class Description
#
class ClassDesc(GenericDesc):
    def __init__(self, verbose, side_effect, internal, c):
        self.verbose = verbose
        self.side_effect = side_effect
        self.internal = internal
        info = VT_get_class_info(c, verbose, side_effect)

        self.name = c
        self.description = info[0]
        if not self.description:
            self.verbosePrint("ClassDesc() *** no description for class " + c)
            self.description = "<todo>No description</todo>"
        self.parent = info[1]
        self.kind = info[2]
        self.ifc_list = info[3]
        self.attr_list = info[4]
        self.module = info[5]
        self.named_ifc_list = info[6]

        self.attr_info = {}
        self.commands = {}
        self.class_hierarchy = []

        # gather attribute information
        ati = VT_get_all_attributes(self.name, verbose, side_effect)
        for a in ati:
            attr_i = AttrDesc()
            attr_i.name = a[0]
            attr_i.rw = a[1]
            attr_i.attributes = a[2]
            attr_i.description = a[3]
            if not attr_i.description:
                self.verbosePrint("ClassDesc() *** no description for attribute " + self.name + "." + attr_i.name)
                attr_i.description = "<todo>No description</todo>"
            attr_i.type = a[4]
            attr_i.indexed_type = a[5]
            if not attr_i.type and not attr_i.indexed_type:
                self.verbosePrint("ClassDesc() *** no type for attribute " + self.name + "." + attr_i.name)
            self.attr_info[attr_i.name] = attr_i
            self.verbosePrint("ClassDesc():     attribute " + attr_i.name)

    def updateModules(self, module_list):
        # update modules
        tmp_cd_module = []
        if self.module:
            for m in self.module:
                # a class may be also declared by a non-loaded module
                try:
                    md = module_list[m]
                    md.classes = md.classes + [self.name]
                    tmp_cd_module = tmp_cd_module + [m]
                    self.verbosePrint("ClassDesc::updateModules():     updating module " + m)
                except:
                    pass
        else:
            md = module_list[core_module]
            md.classes = md.classes + [self.name]
            tmp_cd_module = [core_module]
            self.verbosePrint("ClassDesc::updateModules():     updating module " + md.name)
            
        # update the module list so that it contains only documented modules
        self.module = tmp_cd_module

    def updateInterfaces(self, ifc_list, online = 0):
        # update interface list
        if self.ifc_list:
            new_ifc_list = []
            named_ifcs = set([x[0] for x in self.named_ifc_list])
            for ifc in self.ifc_list + list(named_ifcs):
                # avoid interfaces starting with _ or without documentation
                try:
                    desc = VT_get_interface_info(ifc, self.verbose, self.side_effect)
                except:
                    self.verbosePrint("ClassDesc::updateInterfaces() *** no description for interface" + ifc)
                    # set a todo if internal manual
                    if self.internal:
                        desc = "<todo>No description found</todo>"
                    else:
                        desc = ""

                # ignore internal or not documented interfaces, except when
                # internal or online
                if (not self.internal
                    and ((ifc[0] == '_')
                         or (not online and desc == ""))):
                    self.verbosePrint("ClassDesc::updatesInterfaces(): " +
                                      "ignoring internal interface " + ifc)
                else:
                    if ifc in self.ifc_list:
                        new_ifc_list.append(ifc)

                    try:
                        ifcd = ifc_list[ifc]
                    except:
                        ifcd = IfcDesc(self.verbose)
                        ifcd.name = ifc
                        ifcd.description = desc
                        ifc_list[ifc] = ifcd
                        self.verbosePrint("ClassDesc::updateInterfaces():     interface" + ifc)
                    ifcd.classes.append(self.name)
            # update the interface list to hide the internal ones
            self.ifc_list = new_ifc_list

    def updateClassHierarchy(self, class_list):
        # build class hierarchy for each class and sort out attributes
        try:
            current_class = class_list[self.parent]
        except:
            current_class = None
            
        while current_class and current_class != "":
            self.class_hierarchy = [current_class] + self.class_hierarchy
            self.verbosePrint("ClassDesc::updateClassHierarchy(): parent = "
                              + current_class.parent)
            try:
                current_class = class_list[current_class.parent]
            except:
                current_class = None

        real_attr_list = []
        for a in self.attr_list:
            inherited = 0
            for cl in self.class_hierarchy:
                if a in cl.attr_list:
                    inherited = 1
                # nothing found before? then we keep this attribute
            if not inherited:
                real_attr_list.append(a)
        real_attr_list.sort()
        self.attr_list = real_attr_list

    def printLong(self, o, doc, no_extern_link = 0):
        ifc_list = doc['ifc_list']
        id = classId(self.name)

        o.beginAdd(id, id, o.encode(self.name), 'Class')
        o.pr(o.makeIndex([self.name]))
        o.beginDoc()

        # Modules
        o.beginDocItem('Provided by')
        o.printListWithSep(self.module, iff(no_extern_link, None, moduleId),
                           o.encode, "", "", ", ")
        o.endDocItem()

        # Class hierarchy
        o.beginDocItem('Class Hierarchy')
        class_hier = []
        for c in self.class_hierarchy:
            class_hier.append(c.name)
        if class_hier:
            o.printListWithSep(class_hier, iff(no_extern_link, None, classId),
                               o.encode, "", "", " &rarr; ")
            o.pr(" &rarr; ")
            
        o.pr('<class>' + o.encode(self.name) + '</class>')
        o.endDocItem()

        # Interfaces
        o.beginDocItem('Interfaces Implemented')
        if self.ifc_list:
            o.printListWithSep(self.ifc_list, iff(no_extern_link, None, ifcId),
                               o.encode, "", "", ", ")
        else:
            o.pr('None')
        o.endDocItem()

        if self.named_ifc_list:
            o.beginDocItem('Ports')

            def text_transform(ni):
                if no_extern_link:
                    ifc_text = o.encode(ni[0])
                else:
                    ifc_text = o.makeLink(ifcId(ni[0]), o.encode(ni[0]))

                return "%s (%s)"%(o.encode(ni[1]), ifc_text)

            o.printListWithSep(self.named_ifc_list, None, text_transform,
                               "", "", ", ")
            o.endDocItem()

        # Description
        o.beginDocItem('description')
        o.pn('<insert id=' + o.q(id + "_desc") + '/>')
        o.endDocItem()
        o.endDoc()
        
        # compute how many attributes there are
        attr_nb = 0
        for c in self.class_hierarchy:
            attr_nb = attr_nb + len(c.attr_list)
        attr_nb = attr_nb + len(self.attr_list)

        if attr_nb:
            o.printSection("false", id + "_attributes")
            
        # compute how many commands there are
        cmd_nb = 0
        for i in self.ifc_list:
            cmd_nb = cmd_nb + len(ifc_list[i].commands)
        cmd_nb = cmd_nb + len(self.commands)

        if cmd_nb:
            o.printSection("false", id + "_commands")
            
        if self.commands:
             o.printSection("false", id + "_commands_full")
            
        o.endAdd()
        o.beginAdd(id + "_desc", "", "")
        o.pr(self.description)
        o.pn('')
        o.endAdd()

    def printSingleAttribute(self, o, doc, a, online = 0, no_extern_link = 0):
        attr = self.attr_info[a]
        o.beginDList()
        if online:
            o.pn('<i>Attribute &lt;' + self.name
                 + '&gt;.<b><attr>' + attr.name + '</attr></b></i>')
            o.incr_indent(2)
            o.pn('')
        else:
            o.pr(o.makeDListTitle('<attr>' + attr.name + '</attr>'))
            o.pn(o.makeTarget(attrId(self.name, a)))

        o.beginDListItem()

        chkp_type       = attr.attributes & Sim_Attr_Flag_Mask
        class_attr      = attr.attributes & Sim_Attr_Class
        internal_attr   = attr.attributes & Sim_Attr_Internal

        integer_indexed = attr.attributes & Sim_Attr_Integer_Indexed
        string_indexed  = attr.attributes & Sim_Attr_String_Indexed
        list_indexed    = attr.attributes & Sim_Attr_List_Indexed
        persistent      = attr.attributes & Sim_Attr_Persistent

        type_words = []
        
        if chkp_type == 0:
            o.pr('<b>Required</b> ')
        elif chkp_type == 1:
            o.pr('<b>Optional</b> ')
        elif chkp_type == 3:
            o.pr('<b>Session</b> ')
        elif chkp_type == 4:
            o.pr('<b>Pseudo</b> ')
        else:
            o.pr('<todo>No checkpoint type</todo>')

        if class_attr:
            o.pr('<b>class</b> ')

        o.pr('attribute; ')
        if attr.rw == 3:
            o.pr('<b>read/write</b> ')
        elif attr.rw & 1:
            o.pr('<b>read-only</b> ')
        else:
            o.pr('<b>write-only</b> ')
        o.pr('access; ')
        if not attr.type and not attr.indexed_type:
            o.pr('type: <b>unknown type</b>')
        elif attr.type:
            o.pr('type: <b>' + typeEncode(attr.type) + '</b>')

        if integer_indexed or string_indexed or list_indexed:
            o.pr('; ')
            index_list = []
            if integer_indexed:
                index_list.append("integer")
            if string_indexed:
                index_list.append("string")
            if list_indexed:
                index_list.append("list")
            index_list[0].capitalize()
            o.printListWithSep(index_list, None, lambda x: x,
                               "<b>", "</b>", " or ")
            o.pr(' indexed; ')
            if attr.indexed_type:
                o.pr(' indexed type: <b>' + typeEncode(attr.indexed_type)
                     + '</b>')
            else:
                o.pr(' indexed type: <b>unknown type</b>')

        if persistent:
            o.pr('; <b>persistent</b> attribute');

        o.pr('.')
        o.endDListItem()

        o.beginDListItem()
        if attr.description:
            o.pr(attr.description)
        else:
            o.pr("<todo>This attribute has no description.</todo>")
        o.endDListItem()
        o.endDList()

    def printAttributes(self, o, doc, extended = 1, no_extern_link = 0):
        #
        # Attributes
        #
        id = classId(self.name)
        o.beginAdd(id + '_attributes', '', 'Attributes')
        o.beginDoc()

        # Attributes inherited from parent class
        for c in self.class_hierarchy:
            o.beginDocItem('Attributes inherited from class '
                           + iff(no_extern_link,
                                 c.name,
                                 o.makeLink(classId(c.name), c.name)))
            if c.attr_list:
                # define a function for attribute links
                def attrClassId(a):
                    return attrId(c.name, a)
                o.printListWithSep(c.attr_list,
                                   iff(no_extern_link, None, attrClassId),
                                   o.encode, "<attr>", "</attr>", ", ")
            o.endDocItem()

        # just a summary of attributes?
        if not extended:
            o.beginDocItem('Attributes declared in '
                           + iff(no_extern_link,
                                 self.name,
                                 o.makeLink(classId(self.name),
                                            self.name)))
            if self.attr_list:
                # define a function for attribute links
                def attrClassId(a):
                    return attrId(self.name, a)
                o.printListWithSep(self.attr_list,
                                   iff(no_extern_link, None, attrClassId),
                                   o.encode, "<attr>", "</attr>", ", ")
            o.endDocItem()
            return
        elif self.attr_list:
            # Attributes description
            o.beginDocItem('Attribute List')
            for a in self.attr_list:
                self.printSingleAttribute(o, doc, a,
                                          no_extern_link = no_extern_link)
            o.endDocItem()
            
        o.endDoc()
        o.endAdd()

    def printCommands(self, o, doc, no_extern_link = 0):
        #
        # Command list
        #
        ifc_list = doc['ifc_list']

        # compute how many commands there are
        id = classId(self.name)
        
        cmd_nb = 0
        for i in self.ifc_list:
            cmd_nb = cmd_nb + len(ifc_list[i].commands)
        cmd_nb = cmd_nb + len(self.commands)

        if cmd_nb:
            o.beginAdd(id + "_commands", "", 'Command List')
            o.beginDoc()
            
            # Commands inherited from interfaces
            for i in self.ifc_list:
                ifc = ifc_list[i]
                ifc_c = ifc.commands.keys()
                ifc_c.sort()

                def stripAndEncodeCmd(c):
                    return o.encode(stripCommandName(c))
            
                if ifc_c:
                    o.beginDocItem('Commands defined by interface '
                                   + iff(no_extern_link,
                                         i,
                                         o.makeLink(ifcId(i), i)))
                    o.printListWithSep(ifc_c,
                                       iff(no_extern_link, None, commandId),
                                       stripAndEncodeCmd,
                                       "", "", ", ")
                    o.endDocItem()

            # Short command description
            cmd_list = self.commands.keys()
            cmd_list.sort()
            if cmd_list:
                o.beginDocItem('Commands')
                o.beginTable(len(cmd_list))
                for c in cmd_list:
                    o.beginRow()
                    o.pr(o.makeCell('<cmd>'
                                    + o.makeLink(commandId(c),
                                                 o.encode(stripCommandName(c)))
                                    + '</cmd>'))
                    o.beginCell()
                    if self.commands[c].cmd["deprecated"]:
                        o.pr('<i>deprecated</i> &mdash; ')
                    o.pr(self.commands[c].cmd["short"])
                    o.endCell()
                    o.endRow()
                o.endTable()
                o.endDocItem()

            o.endDoc()
            o.endAdd()

    def printAllCommands(self, o, doc, no_extern_link = 0):
        #
        # Command Description
        #
        # Short command description
        id = classId(self.name)
        
        cmd_list = self.commands.keys()
        cmd_list.sort()
        if cmd_list:
            o.beginAdd(id + "_commands_full", "", 'Command Descriptions')
            for c in cmd_list:
                o.pn('<insert id=' + o.q("__rm_cmd_" + labelEncode(c)) + '/>')
            o.endAdd()
            o.pn('')
        
            for c in cmd_list:
                cmd = self.commands[c]
                cmd.printLong(o, doc, "__rm_cmd_" + labelEncode(c),
                              namespace = self.name,
                              no_extern_link = no_extern_link)

    def printComponent(self, o, doc, no_extern_link = 0):
        #
        # Formatted output for component info in target guide
        #
        ifc_list = doc['ifc_list']
        id = classId(self.name)

        o.beginAdd(id, id, o.encode(self.name), 'Class')
        o.pr(o.makeIndex([self.name]))
        o.beginDoc()

        # Description
        o.beginDocItem('description')
        o.pr(self.description)
        o.endDocItem()

        if self.attr_list:
            # Attributes description
            o.beginDocItem('Attributes')
            for a in self.attr_list:
                self.printSingleAttribute(o, doc, a,
                                          no_extern_link = no_extern_link)
            o.endDocItem()

        cmd_list = sorted(self.commands.keys())
        if cmd_list and self.name not in ('component', 'top-component'):
            o.beginDocItem('Commands')
            o.pn('<insert id=' + o.q("__rm_gcmd_create-"
                                     + labelEncode(self.name)) + '/>')
            o.pn('<insert nowarning="true" id='
                 + o.q("__rm_gcmd_new-" + labelEncode(self.name)) + '/>')
            for c in cmd_list:
                o.pn('<insert id=' + o.q("__rm_cmd_" + labelEncode(c)) + '/>')
            o.pn('')
            o.endDocItem()

        connectors = sim.classes[self.name].classattrs.connectors
        connectors = group_connector_info(connectors)
        if len(connectors.keys()):
            o.beginDocItem('Connectors')
            o.pn('<br/>')
            o.beginTable(len(connectors.keys()))
            o.pr(o.makeRow(o.makeCell('<b>Name</b>')
                           + o.makeCell('<b>Type</b>')
                           + o.makeCell('<b>Direction</b>')))
            cnt = [None] * 3
            cnt[0] = [x for x in connectors.keys() if
                      connectors[x]['direction'] == 'up']
            cnt[1] = [x for x in connectors.keys() if
                      connectors[x]['direction'] == 'down']
            cnt[2] = [x for x in connectors.keys() if
                      connectors[x]['direction'] == 'any']
            for c in cnt:
                for a in sorted(c):
                    o.pr(o.makeRow(o.makeCell(a)
                                   + o.makeCell(connectors[a]['type'])
                                   + o.makeCell(connectors[a]['direction'])))
            o.endTable()
            o.endDocItem()
        o.endDoc()
        o.endAdd()

        # namespace commands
        for c in cmd_list:
            cmd = self.commands[c]
            cmd.printComponentCommand(o, doc, "__rm_cmd_" + labelEncode(c),
                                      namespace = self.name,
                                      no_extern_link = no_extern_link)


class AttrDesc(GenericDesc):
    def __init__(self):
        self.name = ""
        self.rw = 0
        self.attributes = 0
        self.description = ""
        self.type = ""
        self.indexed_type = ""

class IfcDesc(GenericDesc):
    def __init__(self, verbose):
        self.verbose = verbose
        self.name = ""
        self.description = ""
        self.commands = {}
        self.classes = []

    def printLong(self, o, doc, online = 0, no_extern_link = 0):
        id = ifcId(self.name)
        o.beginAdd(id, id, o.encode(self.name), 'Interface')         

        o.pr(o.makeIndex([self.name]))

        o.beginDoc()

        # there should be some classes implementing it, otherwise it wouldn't
        # be in the list
        self.classes.sort()
        o.beginDocItem('Implemented By')
        o.printListWithSep(self.classes,
                           iff(no_extern_link, None, classId),
                           o.encode, "", "", ", ")
        o.endDocItem()

        if not online:
            o.beginDocItem('description')
            o.pn(self.description)
            o.endDocItem()

        if self.commands:
            o.beginDocItem('Command List')
            o.beginTable(len(self.commands.values()))
            cmds = self.commands.values()
            cmds.sort(cmp_item)
            for c in cmds:
                o.beginRow()
                cmd_n = o.encode(stripCommandName(c.cmd["name"]))
                o.pr(o.makeCell(iff(no_extern_link,
                                    cmd_n,
                                    o.makeLink(commandId(c.cmd["name"]),
                                               cmd_n))))
                o.beginCell()
                if c.cmd["deprecated"]:
                    o.pr('<i>deprecated</i> &mdash; ')
                o.pr(c.cmd["short"])
                o.endCell()
                o.endRow()
            o.endTable()
            o.endDocItem()
        o.endDoc()
        if self.commands:
            o.printSection('', id + "_commands_full")
        o.endAdd()

    def printAllCommands(self, o, doc, no_extern_link = 0):
        #
        # Command Description
        #
        id = ifcId(self.name)
        cmd_list = self.commands.keys()
        cmd_list.sort()
        if cmd_list:
            o.beginAdd(id + "_commands_full", '', 'Command Descriptions')
            for c in cmd_list:
                o.pn('<insert id=' + o.q("__rm_cmd_" + labelEncode(c)) + '/>')
            o.endAdd()

            for c in cmd_list:
                cmd = self.commands[c]
                cmd.printLong(o, doc, "__rm_cmd_" + labelEncode(c),
                              namespace = self.name,
                              no_extern_link = no_extern_link)

class HapDesc(GenericDesc):
    def __init__(self, verbose):
        self.verbose = verbose
        self.name = ""
        self.param_types = ""
        self.param_names = []
        self.index = ""
        self.help = ""
        self.modules = []

    def printLong(self, o, doc, no_extern_link = 0):
        o.beginAdd(hapId(self.name), hapId(self.name), o.encode(self.name),
                   'Hap')
        o.pr(o.makeIndex([self.name]))
        o.beginDoc()

        # Module
        o.beginDocItem('Provided By')
        o.printListWithSep(self.modules, iff(no_extern_link, None, moduleId),
                           o.encode, "", "", ", ")
        o.endDocItem()

        o.beginDocItem('Callback Type')
        pnames = ["callback_data", "trigger_obj"]
        if self.param_names:
            pnames = pnames + self.param_names
        o.pr('    <tt>' + hap_c_arguments("noc" + self.param_types, pnames,
                                          breakline = "<br/>")
           + '</tt>')
        o.endDocItem()

        if self.index:
            o.beginDocItem('Index')
            o.pr(self.index)
            o.endDocItem()

        o.beginDocItem('description')
        o.pr('  ' + self.help.strip())
        o.endDocItem()
        o.endDoc()
        o.endAdd()


#
# Gathering documentation
#

# Build a complete list of modules and return it
def build_module_list(verbose, side_effect, internal):
    module_list = {}
    
    def for_all_modules_cb(name, filename, version, info):
        (loaded, unload) = info.split(" ")
        if (loaded == "LOADED"):
            module = ModuleDesc(verbose, name, filename, unload);
            module_list[name] = module
            if verbose:
                print "build_module_list(): adding module", module.name, "(", module.filename, module.unload, ")"

    # add Simics Core as a dummy module
    module = ModuleDesc(verbose, core_module, core_module_file, "")
    module_list[module.name] = module

    # add all other modules
    SIM_for_all_modules(for_all_modules_cb)
    return module_list


# Build a complete class list and return it
# Needs a ready module list to update, build an interface list at the same time
def build_class_and_ifc_list(verbose, side_effect, internal, online,
                             module_list):
    class_list = {}
    ifc_list = {}

    cll = SIM_get_all_classes()
    for c in cll:
        try:
            cd = class_list[c]
            continue
        except:
            pass
        
        cd = ClassDesc(verbose, side_effect, internal, c)
        if verbose:
            print "build_class_list(): adding class", cd.name
        class_list[cd.name] = cd

        cd.updateModules(module_list)
        cd.updateInterfaces(ifc_list, online)

    for c in cll:
        cd = class_list[c]
        cd.updateClassHierarchy(class_list)
        
    return (class_list, ifc_list)

# Build a command list and update class/ifc/module
def build_command_list(verbose, side_effect, internal, online,
                       module_list, class_list, ifc_list):
    command_list = {}
    alias_list = {}
    groups = {}
    avoided_command_list = {}
    doc_with_list = {}

    cmd_list = simics_commands(internal = iff(internal, 1, None))
    for cmd in cmd_list:
        command_desc = CmdDesc(verbose, cmd["name"], cmd)
        cmd_ns = cmd["namespace"]

        # doc_with - update the list of commands documented together
        if cmd["doc_with"]:
            main_command = cmd["doc_with"]
            if doc_with_list.has_key(main_command):
                doc_with_list[main_command].append(cmd["name"])
            else:
                doc_with_list[main_command] = [cmd["name"]]

        # check what kind of command it is
        add_to_list = 1
        if cmd_ns:
            if class_list.has_key(cmd_ns):
                # class command
                c = class_list[cmd_ns]
                if verbose:
                    print "build_command_list(): adding command", cmd["name"], "to class", cmd_ns
            elif ifc_list.has_key(cmd_ns):
                # interface command
                c = ifc_list[cmd_ns]
                if verbose:
                    print "build_command_list(): adding command", cmd["name"], "to interface", cmd_ns
            else:
                # nothing found
                if verbose:
                    print "build_command_list(): *** unknown namespace", cmd_ns, "for command", cmd["name"]
                c = None
                add_to_list = 0
        else:
            if module_list.has_key(cmd["module"]):
                # module command
                c = module_list[cmd["module"]]
                command_desc.module = c.name
                if verbose:
                    print "build_command_list(): adding command", cmd["name"], "to module", cmd["module"]
            elif cmd["module"]:
                # global module commands, but module is not loaded
                if online:
                    # document it with a non-loaded module
                    c = None
                    command_desc.module = cmd["module"]  + " (not loaded)"
                else:
                    # skip the command alltogether, otherwise we may document
                    # commands that are not supposed to be documented because
                    # the module is not part of the package
                    c = None
                    add_to_list = 0
            else:
                # core command
                c = module_list[core_module]
                command_desc.module = c.name
                if verbose:
                    print "build_command_list(): adding command", cmd["name"], "to module", core_module

        # complete info and add command to list
        if add_to_list:
            if cmd['type'] and type([]) == type(cmd['type']):
                for t in cmd['type']:
                    if groups.has_key(t):
                        groups[t].append(cmd)
                    else:
                        groups[t] = [cmd]

            for alias in cmd['alias']:
                if cmd["namespace"]:
                    alias_list['<' + cmd["namespace"] + '>.' + alias] = command_desc
                else:
                    alias_list[alias] = command_desc

            command_list[cmd["name"]] = command_desc
        else:
            avoided_command_list[cmd["name"]] = command_desc

        if c:
            c.commands[cmd["name"]] = command_desc

    for c in doc_with_list.keys():
        if command_list.has_key(c):
            command_list[c].doc_with_list = doc_with_list[c]
        elif avoided_command_list.has_key(c):
            avoided_command_list[c].doc_with_list = doc_with_list[c]

    return (command_list, avoided_command_list, alias_list, groups)

# build a hap list and update the core module on the hap it defined
def build_hap_list(verbose, side_effect, internal, module_list):

    hap_list = {}
    haps = conf.sim.hap_list

    for h in haps:
        hd = HapDesc(verbose)
        hd.name = h[0]
        hd.param_types = h[1]
        hd.param_names = h[2]
        hd.index = h[3]
        hd.help = h[4]
        hd.modules = []
        hap_list[hd.name] = hd

    for m in module_list.values():
        for h in m.haps:
            hap_list[h].modules.append(m.name)

    for h in hap_list.values():
        if not h.modules:
            h.modules = [core_module]
            module_list[core_module].haps.append(h.name)

    return hap_list

def gather_documentation(internal, verbose, side_effect, online):
    # if internal, load all available modules before gathering doc.
    if internal:
        loadAllModules()
    doc = {}
    doc["module_list"] = build_module_list(verbose, side_effect, internal)
    (c,i) = build_class_and_ifc_list(verbose, side_effect, internal,
                                         online, doc["module_list"])
                                         
    doc["class_list"] = c
    doc["ifc_list"] = i
    (cl,acl,al,gl) = build_command_list(verbose,
                                        side_effect,
                                        internal,
                                        online,
                                        doc["module_list"],
                                        doc["class_list"],
                                        doc["ifc_list"])
    doc["command_list"] = cl
    doc["avoided_command_list"] = acl
    doc["alias_list"] = al
    doc["category_list"] = gl
    
    doc["hap_list"] = build_hap_list(verbose, side_effect, internal,
                                     doc["module_list"])
    return doc

def DOC_gather_documentation(internal = 0, verbose = 0, side_effect = 0,
                             online = 0):
    try:
        return gather_documentation(internal, verbose, side_effect, online)
    except:
        traceback.print_exc()
        return {}



#
# Reference manual
# 


# print the command chapter in reference manual
def print_command_chapter(o, doc, no_extern_link = 0):

    module_list = doc['module_list']
    class_list = doc['class_list']
    ifc_list = doc['ifc_list']
    command_list = doc['command_list']
    
    gcmd = []
    for m in module_list:
        gcmd = gcmd + module_list[m].commands.values()

    gcmd.sort(key = lambda x: x.name)
    
    for g in gcmd:
        g.printLong(o, doc, '__rm_gcmd_' + labelEncode(g.name),
                    no_extern_link = no_extern_link)

    o.pn('<add id="__rm_command_description">')
    o.pn('<name>Global Command Descriptions</name>')
    for g in gcmd:
        o.pn('<insert id=' + o.q('__rm_gcmd_' + labelEncode(g.name)) + '/>')
    o.pn('</add>')
    o.pn('')

    # now add the command type documentation
    for c in class_list:
        gcmd = gcmd + class_list[c].commands.values()

    for i in ifc_list:
        gcmd = gcmd + ifc_list[i].commands.values()

    groups = doc['category_list']
    group_list = groups.keys()
    group_list.sort()
    for g in groups.keys():
        o.pn('<add id=' + o.q('__rm_command_group_' + g) + '>')
        o.pn('<name>' + g + '</name>')
        o.pn('<table>')
        groups[g].sort(cmp_cmd)
        for c in groups[g]:
            o.pn('<tr><td>')
            o.pn('  <nref label=' + o.q(commandId(c["name"])) + '>'
               + o.encode(c["name"]) + '</nref>')
            o.pr('</td><td>')
            if c["deprecated"]:
                o.pr('<i>deprecated</i> &mdash; ')
            o.pn(c["short"] + '</td></tr>')
        o.pn('</table>')
        o.pn('</add>')

    # section for categories
    o.pn('<add id="__rm_command_categories">')
    o.pn('<name>By Categories</name>')
    o.pn('')
    for g in group_list:
        o.pn('<section numbering="false" id='
           + o.q('__rm_command_group_' + g) + '/>')
    o.pn('</add>')

    # complete command list
    o.pn('<add id="__rm_command_complete_list">')
    o.pn('<name>Complete List</name>')
    o.pn('')
    o.pn('<table>')

    # add all aliases to the list
    ccmd = []
    for c in gcmd:
        ccmd.append(c.cmd)
        for a in c.cmd["alias"]:
            if c.cmd["namespace"]:
                cname = '<' + c.cmd["namespace"] + '>.' + a
            else:
                cname = a
            ccmd.append({ "name" : cname,
                          "short" : 'alias for <nref label="'
                          + commandId(c.cmd["name"]) + '">'
                          + o.encode(c.cmd["name"]) + '</nref>',
                          "is_alias_for" : c.cmd["name"],
                          "deprecated" : c.cmd["deprecated"]})
    
    ccmd.sort(cmp_cmd)
    for c in ccmd:
        o.pr('<tr><td>')
        if c.has_key("is_alias_for"):
            link = c["is_alias_for"]
        else:
            link = c["name"]
        o.pr('<nref label=' + o.q(commandId(link)) + '>'
           + o.encode(c["name"]) + '</nref>')
        o.pr('</td><td>')
        if c["deprecated"]:
            o.pr('<i>deprecated</i> &mdash; ')  
        o.pn(c["short"] + '</td></tr>')
            
    o.pn('</table>')
    o.pn('</add>')
    o.pn('')
    
    o.pn('<add id="__rm_command_list">')
    o.pn('<name>Commands</name>')
    o.pn('')
    o.pn('<section id="__rm_command_complete_list"/>')
    o.pn('<section id="__rm_command_categories"/>')
    o.pn('<section id="__rm_command_description"/>')
    o.pn('')
    o.pn('</add>')
    
def print_reference_manual(filename, doc, no_extern_link = 0):
    o = JdocuOutputHandler(filename)

    module_list = doc['module_list']
    class_list = doc['class_list']
    ifc_list = doc['ifc_list']
    hap_list = doc['hap_list']
    command_list = doc['command_list']

    o.pn('/*')
    o.pn('')

    # global commands
    print_command_chapter(o, doc,
                          no_extern_link = no_extern_link)

    # modules
    modules = module_list.values()
    modules.sort(cmp_item)

    o.pn('<add id="__rm_module_list">')
    o.pn('<name>Modules</name>')
    o.pn('')
    for m in modules:
        m.printLong(o, doc, no_extern_link = no_extern_link)
    o.pn('')
    o.pn('</add>')

    # classes
    classes = class_list.values()
    classes.sort(cmp_item)
    for c in classes:
        c.printLong(o, doc, no_extern_link = no_extern_link)
        c.printAttributes(o, doc, no_extern_link = no_extern_link)
        c.printCommands(o, doc, no_extern_link = no_extern_link)
        c.printAllCommands(o, doc, no_extern_link = no_extern_link)

    o.pn('<add id="__rm_class_list">')
    o.pn('<name>Classes</name>')
    o.pn('')
    for c in classes:
        o.pn('   <section pagebreak="true" numbering="false" id='
           + o.q(classId(c.name)) + '/>')
    o.pn('')
    o.pn('</add>')

    # interfaces
    ifcs = ifc_list.values()
    ifcs.sort(cmp_item)
    for i in ifcs:
        i.printLong(o, doc, no_extern_link = no_extern_link)
        i.printAllCommands(o, doc, no_extern_link = no_extern_link)

    o.pn('<add id="__rm_interface_list">')
    o.pn('<name>Interfaces</name>')
    o.pn('')
    for i in ifcs:
        o.pn('   <section pagebreak="true" numbering="false" id='
           + o.q(ifcId(i.name)) + '/>')
    o.pn('')
    o.pn('</add>')

    # haps
    haps = hap_list.values()
    haps.sort(cmp_item)
    for h in haps:
        h.printLong(o, doc, no_extern_link = no_extern_link)

    o.pn('<add id="__rm_hap_list" label="haps-chapter">')
    o.pn('<name>Haps</name>')
    o.pn('')
    for h in haps:
        o.pn('   <section numbering="false" id=' + o.q(hapId(h.name)) + '/>')
    o.pn('')
    o.pn('</add>')

    o.pn('')
    o.pn('*/')
    o.of.close()
    
def DOC_print_reference_manual(filename, doc, no_extern_link = 0):
    try:
        print_reference_manual(filename, doc,
                               no_extern_link = no_extern_link)
        return 1
    except:
        traceback.print_exc()
        try:
            os.remove(filename)
            return 1
        except:
            print "Failed to remove", filename
            return 0

def print_component_info(filename, doc, no_extern_link = 0):
    o = JdocuOutputHandler(filename)

    class_list = doc['class_list']

    o.pn('/*')
    o.pn('')

    # classes
    classes = class_list.values()
    classes.sort(cmp_item)
    for c in classes:
        if not 'component' in c.ifc_list:
            continue
        c.printComponent(o, doc, no_extern_link = no_extern_link)

    # global commands
    module_list = doc['module_list']
    gcmd = []
    for m in module_list:
        gcmd = gcmd + module_list[m].commands.values()

    gcmd.sort(key = lambda x: x.name)
    
    for g in gcmd:
        g.printComponentCommand(o, doc, '__rm_gcmd_' + labelEncode(g.name),
                                no_extern_link = no_extern_link)

    o.pn('')
    o.pn('*/')
    o.of.close()

def DOC_print_component_info(filename, doc, no_extern_link = 0):
    try:
        print_component_info(filename, doc,
                             no_extern_link = no_extern_link)
        return 1
    except:
        traceback.print_exc()
        try:
            os.remove(filename)
            return 1
        except:
            print "Failed to remove", filename
            return 0


def get_all_command_categories(cmds):
    # gather a list of categories
    category_set = {}
    for c in cmds:
        if c.has_key("type") and type(c["type"]) == type([]):
            for t in c["type"]:
                category_set[t] = 1
    return category_set.keys()

#
# List of what the help command allows:
# * commands:
#    cmd
#    object.cmd
#    class.cmd
#    interface.cmd
#    <class>.cmd
#    <interface>.cmd
# * class:
#    class
#    <class>
# * interface
#    interface
#    <interface>
# * attribute:
#    class.attribute
#    <class>.attribute
#    object.attribute
# * module
# * hap
# * api (functions and types)
#

help_parser_filter = ['object', 'class', 'command', 'attribute',
                      'interface', 'module', 'api', 'hap', 'category']
complete_parser_filter = ['object', 'class', 'command',
                          'attribute', 'interface', 'hap', 'category']

def help_parser(str, complete = 0):

    #print
    #print "calling help_parser(str =", str, " complete =", complete

    orig_filter = ""                    # filter in query
    orig_namespace = ""                 # namespace in query
    orig_item = ""                      # item in query

    namespace = ""
    filter = []

    item_is_partial_namespace = 0       # 1 if item is '<...'
    item_is_complete_namespace = 0      # 1 if item i '<...>'
    namespace_has_brackets = 0          # 1 if namespace is '<..>'

    # does the list of completion contains a potential namespace?
    completion_contains_namespace = 0
    completion_contains_filter = 0
        
    # start by parsing out a potential filter
    colon = str.find(':')
    if colon != -1:
        orig_filter = str[0:colon]
        str = str[colon+1:]
        if not (orig_filter in help_parser_filter):
            if not complete:
                print ("Wrong specifier, use one of the following: "
                       + "object, class, command, attribute, interface, "
                       + "api, module")
            filter = []
        else:
            filter = [orig_filter]
    else:
        if complete:
            filter = complete_parser_filter
        else:
            filter = help_parser_filter

    # find out if we have a 'namespace'
    dot = str.find('.')
    arrow = str.find('->')
    if arrow != -1:
        if dot != -1:
            # this is a badly-constructed name
            filter = []
        else:
            # only attributes can be documented this way
            if orig_filter and orig_filter != 'attribute':
                filter = []
            else:
                filter = ['attribute']

    # default namespace marker that works for every case
    namespace_marker = "."
    if dot != -1 and dot != 0:
        orig_namespace = str[0:dot]
        orig_item = str[dot+1:]
        item = orig_item
        # parse away '<' and '>'
        if orig_namespace[0] == '<' and orig_namespace[-1] == '>':
            namespace = orig_namespace[1:-1]
            namespace_has_brackets = 1
        else:
            namespace = orig_namespace

    elif arrow != -1:
        orig_namespace = str[0:arrow]
        orig_item = str[arrow+2:]
        item = orig_item
        # parse away '<' and '>'
        if orig_namespace[0] == '<' and orig_namespace[-1] == '>':
            namespace = orig_namespace[1:-1]
            namespace_has_brackets = 1
        else:
            namespace = orig_namespace
        namespace_marker = '->' # replace the namespace marker
    
    else:
        orig_item = str
        # strip away potential '>'
        if orig_item:
            if orig_item[0] == '<':
                item = orig_item[1:]
                item_is_partial_namespace = 1
                if item and item[-1] == '>':
                    item = item[:-1]
                    item_is_complete_namespace = 1
            else:
                item = orig_item
        else:
            item = ""
            orig_item = ""

    #print "orig_filter", orig_filter                                
    #print "orig_namespace", orig_namespace                          
    #print "orig_item", orig_item                                    
    #print "filter", filter                                          
    #print "namespace", namespace                                    
    #print "item", item                                              
    #print "item_is_partial_namespace", item_is_partial_namespace    
    #print "item_is_complete_namespace", item_is_complete_namespace  
    #print "namespace_has_brackets", namespace_has_brackets          

    # look at the potential namespaces we will be looking at
    potential_namespaces = {}
    if namespace:
        for o in SIM_all_objects():
            ifcs = SIM_get_attribute(o, "iface")
            if not namespace_has_brackets and namespace == o.name:
                potential_namespaces[(o.classname, "class")] = 1
                if ifcs:
                    for i in ifcs:
                        potential_namespaces[(i, "ifc")] = 1
            elif ifcs:
                if namespace in ifcs:
                    potential_namespaces[(namespace, "ifc")] = 1
        for c in SIM_all_classes():
            if c == namespace:
                potential_namespaces[(c, "class")] = 1

    #print "potential_namespaces", potential_namespaces

    # results
    results = []                        # exact results (for parsing)
    tab_results = []                    # tab-completion results

    # look for matching filters
    if complete and len(filter) > 1 and not namespace:
        for f in help_parser_filter:
            if f.startswith(item):
                tab_results.append(f + ":")
                completion_contains_filter = 1

    # look for matching commands
    cmds = simics_commands()
    potential_cmds = []
    if potential_namespaces:
        for (n,t) in potential_namespaces.keys():
            potential_cmds.append('<' + n + '>.' + item)
    else:
        potential_cmds.append(item)

    category_list = get_all_command_categories(cmds)

    # tab-complete on categories
    if ('category' in filter) and not namespace:
        cat_results = []
        for c in category_list:
            if c == item:
                results.append(("category", item))
            if complete and c.startswith(item):
                cat_results.append(c)
        tab_results = tab_results + cat_results
                    
    # look in command only if we are not tab-completing a namespace
    if ('command' in filter) and (not item_is_partial_namespace):
        for c in cmds:
            # avoid completing on namespace commands without namespace
            if c['namespace'] and not namespace:
                continue
            # gather command name + aliases
            cnames = [c['name']]
            for a in c['alias']:
                if c['namespace']:
                    cnames.append('<' + c['namespace'] + ">." + a)
                else:
                    cnames.append(a)
            for cname in cnames:
                for pc in potential_cmds:
                    if cname == pc:
                        results.append(('command', pc))
                    if complete and cname.startswith(pc):
                        if orig_namespace:
                            tab_results.append(orig_namespace + namespace_marker
                                               + stripCommandName(cname))
                        else:
                            tab_results.append(cname)

    #print "tab_results after commands", tab_results

    # look for matching object, only if not tab-completing a namespace
    if (not potential_namespaces
        and not item_is_partial_namespace
        and ('object' in filter
             or (not namespace and complete and ('attribute' in filter
                                                 or 'command' in filter)))):
        for o in SIM_all_objects():
            if item == o.name:
                results.append(('class', o.classname))
            if complete and o.name.startswith(item):
                tab_results.append(o.name)
                completion_contains_namespace = 1
                
    #print "tab_results after objects", tab_results
                
    # look for matching class
    if (not potential_namespaces
        and ('class' in filter
             or (not namespace and complete and ('attribute' in filter
                                                 or 'command' in filter)))):
        for c in SIM_all_classes():
            if c == item:
                if not ("class", item) in results:
                    results.append(('class', item))
            # don't count a match if item is complete namespace
            if (complete
                and c.startswith(item)
                and not item_is_complete_namespace):
                completion_contains_namespace = 1
                tab_results.append(iff(item_is_partial_namespace,
                                       '<' + c + '>', c))

    #print "tab_results after classes", tab_results

    # look for matching interface
    if (not potential_namespaces
        and ('interface' in filter
             or (not namespace and complete and ('command' in filter)))):
        iface_list = {}
        for o in SIM_all_objects():
            ifcs = SIM_get_attribute(o, "iface")
            if ifcs:
                for i in ifcs:
                    iface_list[i] = 1

        for i in iface_list.keys():
            if item == i:
                results.append(("interface", item))
            if (complete
                and i.startswith(item)
                and not item_is_complete_namespace):
                completion_contains_namespace = 1
                tab_results.append(iff(item_is_partial_namespace,
                                       '<' + i + '>', i))

    #print "tab_results after interfaces", tab_results
                
    # look for matching attributes
    if potential_namespaces and ('attribute' in filter):
        potential_classes = []
        for (n,t) in potential_namespaces.keys():
            if t == "class":
                potential_classes.append(n)
        for c in potential_classes:
            info = VT_get_class_info(c, 0, 0)
            for i in info[4]:
                if item == i:
                    results.append(('attribute', (c, item)))
                if complete and i.startswith(item):
                    tab_results.append(orig_namespace + namespace_marker + i)

    #print "tab_results after attributes", tab_results

    # look for matching module
    if (not potential_namespaces
        and not item_is_partial_namespace
        and ('module' in filter)):
        class ModuleList:
            def __init__(self):
                self.list = []
            def add(self, str):
                self.list.append(str)
            
        module_list = ModuleList()
        def mod_list_callback(name, file, usr_ver, attrs):
            (loaded, unload) = attrs.split(" ")
            if (loaded == "LOADED"):
                module_list.add(name)

        SIM_for_all_modules(mod_list_callback)
        for i in module_list.list:
            if item == i:
                results.append(('module', item))
            if complete and i.startswith(item):
                tab_results.append(i)

    #print "tab_results after modules", tab_results

    # look for matching hap
    if (not potential_namespaces
        and not item_is_partial_namespace
        and ('hap' in filter)):
        haps = conf.sim.hap_list
        for h in haps:
            if h[0] == item:
                results.append(('hap', item))
            if complete and h[0].startswith(item):
                tab_results.append(h[0])

    #print "tab_results after haps", tab_results

    # look for matching api information
    if (not potential_namespaces
        and not item_is_partial_namespace
        and ('api' in filter)):        
        if api_help.has_key(item):                            
            results.append(('api', item))                     
        if complete:                                     
            for k in api_help.keys():                         
                if k.startswith(item):                        
                    tab_results.append(k)                     

    #print "tab_results after api", tab_results

    if complete:
        # work-around so that we don't have only one completion if we are
        # still completing on a namespace or a filter
        if len(tab_results) == 1:
            # namespace
            if (completion_contains_namespace and
                ('command' in filter or 'attribute' in filter)):
                if orig_filter:
                    new_completions = help_parser(orig_filter + ":"
                                                  + tab_results[0]
                                                  + '.', 1)
                else:
                    new_completions = help_parser(tab_results[0]
                                                  + '.', 1)
                if new_completions:
                    if len(filter) == 1:
                        # no need to complete with the filter, it's already
                        # done by the recursive call to the parser
                        return new_completions
                    else:
                        tab_results = [tab_results[0],
                                       tab_results[0] + '.']
            elif (completion_contains_filter):
                new_completions = help_parser(tab_results[0], 1)
                return new_completions
            
        # print "tab_results after adding '.' or '->'", tab_results
        if len(filter) == 1 and orig_filter:
            tresults = []
            for t in tab_results:
                # check if the result is quoted first
                if t and len(t) > 1 and t[0] == '"' and t[-1] == '"':
                    tresults.append('"' + filter[0] + ":" + t[1:])
                else:
                    tresults.append(filter[0] + ":" + t)
        else:
            tresults = tab_results
        # print "final tresults", tresults
        return tresults
    else:
        return results

topic_priority = ['category', 'command', 'class', 'interface', 'hap',
                  'module', 'attribute', 'api']

def help_select_topic(match):
    # select the most appropriate in order of priority
    real_match = []
    other_match = []
    for cat in topic_priority:
        for (t,n) in match:
            if t == cat:
                real_match = [(t,n)]
            else:
                other_match.append((t,n))
        if real_match:
            return (real_match, other_match)
        else:
            other_match = []
    # should never come here, there wouldn't be any real_match?
    raise "Error: Several topics were found but none of them can be selected"

def help_cmd(str):

    # help without argument?
    if not str:
        format_print("The 'help' command prints out information on any topic, like a command, a class, an object, an interface, a hap, a module, an attribute or a function or type from the Simics API.\n\n", 0, terminal_width() - 1)
        format_print("To get more information about the help command, type 'help help'\n\n", 0, terminal_width() - 1)
        print
        format_print("To get you started, here is a list of command categories:\n\n", 0, terminal_width() - 1)
        cat_list = get_all_command_categories(simics_commands())
        cat_list.sort()
        for c in cat_list:
            print "  " + c
        format_print("Type 'help <arg>category</arg>' to list the commands for a specific category.\n\n", 0, terminal_width() - 1)
        doc_path = os.path.join(conf.sim.simics_base, 'doc')
        print
        format_print("The complete Simics documentation is available as PDF files in the %s directory.\n\n" % doc_path, 0, terminal_width() - 1)
        print
        return
    
    doc = DOC_gather_documentation(online = 1)
    match = help_parser(str)
    if not match:
        print "No help topic matching '" + str + "'"
        return

    other_match = []
    real_match = match

    # if several matches, select the one with highest priority
    if len(match) > 1:
        (real_match, other_match) = help_select_topic(match)

    o = TerminalOutputHandler()
    (t,n) = real_match[0]
    if   t == "class":
        cl = doc['class_list'][n]
        cl.printLong(o, doc)
        cl.printCommands(o, doc)
        cl.printAttributes(o, doc, extended = 0)
    elif t == "command":
        try:
            cmd = doc['command_list'][n]
        except:
            cmd = doc['alias_list'][n]
        cmd.printLong(o, doc, online = 1)
    elif t == "interface":
        ifc = doc['ifc_list'][n]
        ifc.printLong(o, doc, online = 1)
    elif t == "attribute":
        cl = doc['class_list'][n[0]]
        cl.printSingleAttribute(o, doc, n[1], online = 1)
    elif t == "module":
        md = doc['module_list'][n]
        md.printLong(o, doc, online = 1)
    elif t == "hap":
        hp = doc['hap_list'][n]
        hp.printLong(o, doc)
    elif t == "api":
        d = api_help[n]
        format_print('<b>' + str + '</b>', 0, terminal_width() - 1)
        pr('\n\n')
        print_wrap_code(d, terminal_width() - 1)
    elif t == "category":
        cmds = simics_commands()
        gcmds = doc['category_list'][n]
        gcmds.sort()
        max_len = 0
        for gc in gcmds:
            max_len = iff(len(gc['name'])>max_len, len(gc['name']), max_len)

        o.pn("<b>Commands available in category " + n + "</b>")
        o.incr_indent(2)
        for gc in gcmds:
            o.pr(o.encode(gc['name']) + '&nbsp;'*(max_len - len(gc['name']) + 3))
            o.pn(gc['short'])

    if other_match:
        format_print("<b>Note</b> that your request also matched " +
                     "other topics:\n\n",
                     0, terminal_width() -1)
        for (t,n) in other_match:
            if t == 'attribute':
                print "  " + t + ':' + n[0] + '.' + n[1]
            else:
                print "  " + t + ':' + n

def help_exp(comp):
    try:
        c = help_parser(comp, complete = 1)
    except:
        traceback.print_exc()
        return []
    return c

new_command("help", help_cmd, [arg(str_t, "topic", "?", expander = help_exp)],
            short = "help command",
            alias=["h", "man"],
            pri=1000,
            type = ["Help"],
            see_also = ["apropos", "api-help", "api-apropos"],
            doc = """
Prints help information on <arg>topic</arg>. <arg>topic</arg> can be a command, a class, an object, an interface, a module, a hap, an attribute or a function or type from the Simics API.

To refine your search, you may use filters in the topic as shown below:
   <cmd>help</cmd> topic = command:break
The recognized filters are command:, class:, object:, interface:, module:, hap:, attribute: and api:.

By default, the help command does not provided tab-completion on <arg>topic</arg> for modules and api symbols unless the specific filter is provided.
""", filename="/mp/simics-3.0/src/core/common/refmanual.py", linenumber="2412")

_tagfilter = re.compile("</?(tt|i|b|em|br/?)>")

def _regexp_find(text, pattern):
    return pattern.search(_tagfilter.sub("", text))

def _substring_find(text, pattern):
    return string.find(_tagfilter.sub("", string.lower(text)), pattern) >= 0

def apropos_cmd(text, regexp = 0):
    doc = DOC_gather_documentation(online = 1)

    if regexp:
        finder = _regexp_find
        try:
            pattern = re.compile(text, re.IGNORECASE)
        except Exception, msg:
            print "Invalid regular expression '%s': %s" % (text, msg)
            return
        desc = "Text matching the regular expression"
    else:
        finder = _substring_find
	pattern = string.lower(text)
        desc = "The text"

    # look in commands
    def search_cmd_see_also(sc, pattern):
        if sc["see_also"]:
            for s in sc["see_also"]:
                if finder(s, pattern):
                    return 1
        return 0
    
    cmd_found = []
    cmds = doc['command_list'].values()
    for c in cmds:
        sc = c.cmd
        if (finder(sc["doc"], pattern)
            or finder(sc["name"], pattern)
            or finder(sc["short"], pattern)
            or finder(sc["group_short"], pattern)
            or search_cmd_see_also(sc, pattern)):
            cmd_found.append(('command', c.name))
        elif type("") == type(sc["alias"]):
            if finder(sc["alias"], pattern):
                cmd_found.append(('command', c.name))
        else:
            for a in sc["alias"]:
                if finder(a, pattern):
                    cmd_found.append(('command', c.name))
                    break
    cmd_found.sort()

    # look in class documentation
    class_found = []
    attr_found = []
    classes = doc['class_list'].values()
    for c in classes:
        if (finder(c.name, pattern)
            or finder(c.description, pattern)
            or finder(c.description, pattern)):
            class_found.append(('class', c.name))
        for a in c.attr_info.values():
            if (finder(a.name, pattern)
                or finder(a.description, pattern)):
                attr_found.append(('attribute', '<' + c.name + '>.' + a.name))
    class_found.sort()
    attr_found.sort()

    # look in interface list
    ifc_found = []
    interfaces = doc['ifc_list'].values()
    for i in interfaces:
        if (finder(i.name, pattern)):
            ifc_found.append(('interface', i.name))
    ifc_found.sort()

    # look in hap_list
    hap_found = []
    haps = doc['hap_list'].values()
    for h in haps:
        if (finder(h.name, pattern)
            or finder(h.help, pattern)):
            hap_found.append(('hap', h.name))
    hap_found.sort()

    found = cmd_found + class_found + attr_found + ifc_found + hap_found
    if found:
        print "%s '%s' appears in the documentation" % (desc, text)
        print "for the following items:\n"
        for t,n in found:
            print '%-10s     %s'%(t.capitalize(), n)
        print
    else:
        print "%s '%s' cannot be found in any documentation." % (desc, text)
        
new_command("apropos", lambda re, str: apropos_cmd(str, re),
            [arg(flag_t, "-r"), arg(str_t, "string") ],
            short = "search for text in documentation",
            alias = "a", pri = 1000,
            type = "help commands",
            see_also = ["api-apropos", "help"],
            doc = """
Use <b>apropos</b> <i>string</i> to list all commands for which the
documentation contains the text <i>string</i>. If the <tt>-r</tt> flag
is used, interpret <i>string</i> as a regular expression.
""", filename="/mp/simics-3.0/src/core/common/refmanual.py", linenumber="2523")
