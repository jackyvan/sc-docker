#!/usr/bin/env python3.6
import ast
import io
import sys
import astunparse
from astunparse import unparser
from yapf.yapflib.yapf_api import FormatCode


def traverse_children_first(f):
    def _f(self, node):
        Python36to34.generic_visit(self, node)
        return f(self, node)

    return _f


class Python36to34(ast.NodeTransformer):
    """ All of the following method operate on nodes which are either 3.6 specific 
    or have some 3.6 specific field which needed to be fixed."""
    found_name_tuple = False
    py36modules = {'typing'}

    def visit_Import(self, node):
        node.names = [n for n in node.names if (n.name != 'typing')]
        if (not node.names):
            return None
        return node

    def visit_ImportFrom(self, node):
        if (node.module in self.py36modules):
            return None
        return node

    @traverse_children_first
    def visit_Module(self, node):
        if self.found_name_tuple:
            node.body.insert(
                0,
                ast.ImportFrom(
                    module='collections',
                    names=[ast.alias(name='namedtuple', asname=None)],
                    level=0))
        return node

    @traverse_children_first
    def visit_AnnAssign(self, node):
        if node.value:
            updated = ast.Assign(targets=[node.target], value=node.value)
        else:
            updated = ast.Assign(
                targets=[node.target], value=ast.NameConstant(value=None))
        return ast.copy_location(updated, node)

    @traverse_children_first
    def visit_arg(self, node):
        node.annotation = None
        return node

    def visit_ClassDef(self, node):
        if ((len(node.bases) == 1) and isinstance(node.bases[0], ast.Name) and
            ('NamedTuple' in node.bases[0].id)):
            self.found_name_tuple = True
            params = [
                ast.Str(s=x.target.id) for x in node.body
                if isinstance(x, ast.AnnAssign)
            ]
            remaining_body = [
                x for x in node.body if (not isinstance(x, ast.AnnAssign))
            ]
            if (not any([isinstance(x, ast.Pass) for x in remaining_body])):
                remaining_body.append(ast.Pass())
            node.bases = [
                ast.Call(
                    func=ast.Name(id='namedtuple', ctx=ast.Load()),
                    args=[
                        ast.Str(s=node.name), ast.Tuple(
                            elts=params, ctx=ast.Load())
                    ],
                    keywords=[])
            ]
            node.body = remaining_body
        Python36to34.generic_visit(self, node)
        return self._parse_doc(node)

    @traverse_children_first
    def visit_FunctionDef(self, node):
        node.returns = None
        node = self._parse_doc(node)
        return node

    @traverse_children_first
    def _parse_doc(self, node):
        first_in_body = node.body[0]
        if (isinstance(first_in_body, ast.Expr) and
                isinstance(first_in_body.value, ast.Str)):
            first_in_body.value = Doc(first_in_body.value.s)
        return node

    def visit_AsyncFor(self, node):
        raise NotImplementedError('AsyncFor is python3.6 specific')

    def visit_AsyncFunctionDef(self, node):
        raise NotImplementedError('AsyncFunctionDef is python3.6 specific')

    def visit_AsyncWith(self, node):
        raise NotImplementedError('AsyncWith is python3.6 specific')

    def visit_Await(self, node):
        raise NotImplementedError('Await is python3.6 specific')

    def visit_Constant(self, node):
        raise NotImplementedError('Constant is python3.6 specific')

    @traverse_children_first
    def visit_FormattedValue(self, node):
        return node

    @traverse_children_first
    def visit_JoinedStr(self, node):
        formatted_str = ''.join([(n.s if isinstance(n, ast.Str) else '%s')
                                 for n in node.values])
        values = ast.Tuple(
            elts=[
                n.value for n in node.values
                if isinstance(n, ast.FormattedValue)
            ],
            ctx=ast.Load())
        return ast.BinOp(
            left=ast.Str(s=formatted_str), op=ast.Mod(), right=values)

    def visit_MatMult(self, node):
        raise NotImplementedError('MatMult is python3.6 specific')


class DocUnparser(astunparse.Unparser):
    def __init__(self, tree, file=sys.stdout):
        astunparse.Unparser.__init__(self, tree, file)

    def _Doc(self, tree):
        self.__multi_line_Str(tree)

    def _Str(self, tree):
        if ("""
""" in tree.s):
            self.__multi_line_Str(tree)
        else:
            astunparse.Unparser._Str(self, tree)

    def __multi_line_Str(self, tree):
        self.write('"""')
        self.write(tree.s)
        self.write('"""')

    def write_pair(self, pair):
        (k, v) = pair
        if k:
            self.dispatch(k)
            self.write(': ')
            self.dispatch(v)
        else:
            self.write('**')
            self.dispatch(v)

    def _Dict(self, t):
        self.write('{')
        unparser.interleave((lambda: self.write(', ')), self.write_pair,
                            zip(t.keys, t.values))
        self.write('}')


class Doc(ast.Str):
    def __init__(self, s):
        ast.Str.__init__(self, s=s)


def main():
    if (len(sys.argv) >= 2):
        file_in = sys.argv[1]
    else:
        file_in = './scripts/inject_syslog_parsers.py'
    if (len(sys.argv) == 3):
        file_out = sys.argv[2]
    else:
        file_out = None
    with open(file_in) as f:
        source_code = f.read()
    st = ast.parse(source_code, file_in)
    st = Python36to34().visit(st)
    sio = io.StringIO()
    if source_code.startswith('#!'):
        sio.writelines([source_code[:source_code.find("""
""")]])
    DocUnparser(st, sio)
    shaved_code = sio.getvalue()
    (formatted_code, _) = FormatCode(shaved_code, print_diff=False)
    if file_out:
        with open(file_out, 'w') as f:
            f.write(formatted_code)
    else:
        print(formatted_code)


if (__name__ == '__main__'):
    try:
        main()
    except Exception as e:
        sys.stderr.write(('conversion failed on file %s with exception: %s' %
                          (sys.argv[1:], e)))
