import pybsn
import argparse
import json
import textwrap
import re

parser = argparse.ArgumentParser(description='Display the schema in human readable form')

parser.add_argument('path', type=str, default='controller', nargs='?')
parser.add_argument('--host', '-H', type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument('--user', '-u', type=str, default="admin", help="Username")
parser.add_argument('--password', '-p', type=str, default="adminadmin", help="Password")

parser.add_argument("--max-depth", "-d", type=int, help="Maximum recursion depth")
parser.add_argument("--raw", action="store_true", help="Print raw JSON")
parser.add_argument("--verbose", "-v", action="store_true", help="Include descriptions in the output")

args = parser.parse_args()

bcf = pybsn.connect(args.host, args.user, args.password)

def pretty_type(node):
    if not 'typeSchemaNode' in node:
        return node.leafType.lower()

    t = node.typeSchemaNode

    if t.leafType == 'ENUMERATION':
        names = [x for x in t.typeValidator if x.type == 'ENUMERATION_VALIDATOR'][0].names
        return "enum { %s }" % ', '.join(names)
    elif t.leafType == 'UNION':
        names = [x.name for x in t.typeSchemaNodes]
        return "union { %s }" % ', '.join(names)
    else:
        return t.leafType.lower()

def traverse(node, depth=0, name="root"):
    def output(*s):
        print " " * (depth * 2) + ' '.join(s)

    if args.max_depth is not None and depth > args.max_depth:
        return

    if args.verbose and 'description' in node:
        description = re.sub(r"\s+", " ", node.description)
        indent = " "*(depth*2) + "  # "
        description = "\n" + textwrap.fill(
            description,
            initial_indent=indent,
            subsequent_indent=indent,
            width=70 - depth*2)
    else:
        description = ''

    if args.verbose:
        config = "config" in node.dataSources and "(config)" or ""
    else:
        config = ""

    if node.nodeType == 'CONTAINER' or node.nodeType == 'LIST_ELEMENT':
        if node.nodeType == 'CONTAINER':
            output(name, description)
        for child_name in node.childNodes:
            child = getattr(node.childNodes, child_name)
            traverse(child, depth+1, child_name)
    elif node.nodeType == 'LIST':
        output(name, "(list)", description)
        traverse(node.listElementSchemaNode, depth, name)
    elif node.nodeType == 'LEAF':
        output(name, ":", pretty_type(node), config, description)
    elif node.nodeType == 'LEAF_LIST':
        output(name, ":", "list of", pretty_type(node.leafSchemaNode), config, description)
    else:
        assert False, "unknown node type %s" % node.nodeType

path = args.path.replace('.', '/').replace('_', '-')

if args.raw:
    print json.dumps(bcf.schema(path), indent=4, cls=pybcf.BCFJSONEncoder)
else:
    traverse(bcf.schema(path), name=path)
