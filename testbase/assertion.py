# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
"""assert机制实现
"""

from __future__ import print_function, absolute_import

import ast
import copy
import inspect
import itertools
import pprint
import six
import sys
import threading
import traceback
import types

from testbase.util import Singleton, get_method_defined_class, smart_text

unary_map = {ast.Not: "not %s", ast.Invert: "~%s", ast.USub: "-%s", ast.UAdd: "+%s"}

binop_map = {
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.BitAnd: "&",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%%",  # escaped for string formatting
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Pow: "**",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in",
}

if sys.version_info >= (3, 5):
    ast_Call = ast.Call
else:

    def ast_Call(a, b, c):
        return ast.Call(a, b, c, None, None)

if hasattr(ast, "NameConstant"):
    _NameConstant = ast.NameConstant
else:

    def _NameConstant(c):
        return ast.Name(str(c), ast.Load())


def set_location(node, lineno, col_offset):
    """Set node location information recursively."""

    def _fix(node, lineno, col_offset):
        if "lineno" in node._attributes:
            node.lineno = lineno
        if "col_offset" in node._attributes:
            node.col_offset = col_offset
        for child in ast.iter_child_nodes(node):
            _fix(child, lineno, col_offset)

    _fix(node, lineno, col_offset)
    return node


def hook_function(func):
    code = func.__code__
    src_code = inspect.getsource(code)
    tree = ast.parse(src_code, "<string>", "exec")
    print_func = ast.Name(id="print", ctx=ast.Load())
    arg = ast.Str("hello world!")
    print_expr = ast.Expr(ast.Call(func=print_func, args=[arg], keywords=[]))
    test_func = tree.body[0]
    test_func.body.append(print_expr)
    ast.fix_missing_locations(tree)
    new_code = compile(tree, "<string>", "exec", dont_inherit=True)
    for item in new_code.co_consts:
        if isinstance(item, types.CodeType) and item.co_name == code.co_name:
            func.__code__ = copy.deepcopy(item)
            break
    else:
        raise RuntimeError("no match name function for %s" % code.co_name)


class AssertionRewriter(ast.NodeVisitor):
    """assert rewriter
    """

    def rewrite(self, item):
        try:
            self.rewrite_(item)
        except:
            stack = traceback.format_exc()
            msg = "[WARN]rewrite item %s failed: %s" % (item, stack)
            print(msg, file=sys.stderr)

    def rewrite_(self, item):
        """Find all assert statements in *mod* and rewrite them."""
        func = item
        if func in _AssertHookedCache():
            return

        mod, func_node = get_func_mod_and_node(func)
        if mod is None and func_node is None:
            _AssertHookedCache().add(func)
            return

        # compatibility with py 2 and 3
        if sys.version_info[0] == 3:
            builtins_mod = "builtins"
        else:
            builtins_mod = "__builtin__"
        aliases = [
            ast.alias(builtins_mod, "_py_builtins_"),
            ast.alias("testbase.assertion", "_qtaf_assert_"),
        ]
        pos = 0
        lineno = func_node.lineno
        col_offset = func_node.col_offset

        imports = [
            ast.Import([alias], lineno=lineno, col_offset=col_offset) for alias in aliases
        ]
        imports.append(ast.ImportFrom(module="testbase.testresult", names=[ast.alias('EnumLogLevel', None)], level=0, lineno=lineno, col_offset=col_offset))
        func_node.body[pos:pos] = imports
        nodes = [func_node]
        self.rewrite_code = False
        while nodes:
            node = nodes.pop()
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    new_nodes = []
                    for child in value:
                        if isinstance(child, ast.Expr):
                            new_nodes.extend(self.visit(child))
                        else:
                            new_nodes.append(child)
                    setattr(node, field, new_nodes)
                if isinstance(value, ast.Expr):
                    self.visit(value)
        if self.rewrite_code:
            source_file = inspect.getsourcefile(func)
            new_code = compile(mod, source_file, "exec")
            set_func_code(func, new_code)
        _AssertHookedCache().add(func)

    def visit_Expr(self, expr):
        value = expr.value
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Attribute):
                if value.func.attr == "assert_":
                    return self.rewrite_assert_(expr)
            elif isinstance(value.func, ast.Name):
                if value.func.id == "assert_":
                    return self.rewrite_assert_(value)

        return [expr]

    def rewrite_assert_(self, elem):
        """rewrite the assert_ expression
        """
        self.rewrite_code = True
        self.statements = []
        self.variables = []
        self.variable_counter = itertools.count()
        self.stack = []
        self.on_failure = []
        self.push_format_context()

        # Rewrite assert into a bunch of statements.
        if isinstance(elem, ast.Expr):
            top_condition, explanation = self.visit(elem.value.args[1])
            msg_arg = elem.value.args[0]
            caller_id = "self"
        elif isinstance(elem, ast.Call):
            top_condition, explanation = self.visit(elem.args[1])
            msg_arg = elem.args[0]
            caller_id = "_qtaf_assert_"

        # Create failure message.
        body = self.on_failure
        negation = ast.UnaryOp(ast.Not(), top_condition)
        self.statements.append(ast.If(negation, body, []))
        assertmsg = self.helper("format_assertmsg", msg_arg)
        explanation = " " + explanation
        template = ast.BinOp(assertmsg, ast.Add(), ast.Str(explanation))
        msg = self.pop_format_context(template)
        fmt = self.helper("format_explanation", msg)
        log_record = ast.Attribute(
                                value=ast.Name(id=caller_id, ctx=ast.Load()),
                                attr='_log_assert_failed',
                                ctx=ast.Load())
        args = [fmt]
        exc = ast_Call(log_record, args, [])
        log_record_expr = ast.Expr(value=exc)
        body.append(log_record_expr)
        # Clear temporary variables by setting them to None.
        if self.variables:
            variables = [ast.Name(name, ast.Store()) for name in self.variables]
            clear = ast.Assign(variables, _NameConstant(None))
            self.statements.append(clear)
        # Fix line numbers.
        for stmt in self.statements:
            set_location(stmt, elem.lineno, elem.col_offset)
        return self.statements

    def variable(self):
        """Get a new variable."""
        # Use a character invalid in python identifiers to avoid clashing.
        name = "_py_assert" + str(next(self.variable_counter))
        self.variables.append(name)
        return name

    def assign(self, expr):
        """Give *expr* a name."""
        name = self.variable()
        self.statements.append(ast.Assign([ast.Name(name, ast.Store())], expr))
        return ast.Name(name, ast.Load())

    def display(self, expr):
        """Call py.io.saferepr on the expression."""
        return self.helper("saferepr", expr)

    def helper(self, name, *args):
        """Call a helper in this module."""
        py_name = ast.Name("_qtaf_assert_", ast.Load())
        attr = ast.Attribute(py_name, "_" + name, ast.Load())
        return ast_Call(attr, list(args), [])

    def builtin(self, name):
        """Return the builtin called *name*."""
        builtin_name = ast.Name("_py_builtins_", ast.Load())
        return ast.Attribute(builtin_name, name, ast.Load())

    def explanation_param(self, expr):
        """Return a new named %-formatting placeholder for expr.

        This creates a %-formatting placeholder for expr in the
        current formatting context, e.g. ``%(py0)s``.  The placeholder
        and expr are placed in the current format context so that it
        can be used on the next call to .pop_format_context().

        """
        specifier = "py" + str(next(self.variable_counter))
        self.explanation_specifiers[specifier] = expr
        return "%(" + specifier + ")s"

    def push_format_context(self):
        """Create a new formatting context.

        The format context is used for when an explanation wants to
        have a variable value formatted in the assertion message.  In
        this case the value required can be added using
        .explanation_param().  Finally .pop_format_context() is used
        to format a string of %-formatted values as added by
        .explanation_param().

        """
        self.explanation_specifiers = {}
        self.stack.append(self.explanation_specifiers)

    def pop_format_context(self, expl_expr):
        """Format the %-formatted string with current format context.

        The expl_expr should be an ast.Str instance constructed from
        the %-placeholders created by .explanation_param().  This will
        add the required code to format said string to .on_failure and
        return the ast.Name instance of the formatted string.

        """
        current = self.stack.pop()
        if self.stack:
            self.explanation_specifiers = self.stack[-1]
        keys = [ast.Str(key) for key in current.keys()]
        format_dict = ast.Dict(keys, list(current.values()))
        form = ast.BinOp(expl_expr, ast.Mod(), format_dict)
        name = "_py_format_" + str(next(self.variable_counter))
        self.on_failure.append(ast.Assign([ast.Name(name, ast.Store())], form))
        return ast.Name(name, ast.Load())

    def generic_visit(self, node):
        """Handle expressions we don't have custom code for."""
        assert isinstance(node, ast.expr)
        res = self.assign(node)
        return res, self.explanation_param(self.display(res))

    def visit_Name(self, name):
        # Display the repr of the name if it's a local variable or
        # _should_repr_global_name() thinks it's acceptable.
        locs = ast_Call(self.builtin("locals"), [], [])
        inlocs = ast.Compare(ast.Str(name.id), [ast.In()], [locs])
        dorepr = self.helper("should_repr_global_name", name)
        test = ast.BoolOp(ast.Or(), [inlocs, dorepr])
        expr = ast.IfExp(test, self.display(name), ast.Str(name.id))
        return name, self.explanation_param(expr)

    def visit_BoolOp(self, boolop):
        res_var = self.variable()
        expl_list = self.assign(ast.List([], ast.Load()))
        app = ast.Attribute(expl_list, "append", ast.Load())
        is_or = int(isinstance(boolop.op, ast.Or))
        body = save = self.statements
        fail_save = self.on_failure
        levels = len(boolop.values) - 1
        self.push_format_context()
        # Process each operand, short-circuting if needed.
        cond = None
        for i, v in enumerate(boolop.values):
            if i:
                fail_inner = []
                # cond is set in a prior loop iteration below
                self.on_failure.append(ast.If(cond, fail_inner, []))  # noqa
                self.on_failure = fail_inner
            self.push_format_context()
            res, expl = self.visit(v)
            body.append(ast.Assign([ast.Name(res_var, ast.Store())], res))
            expl_format = self.pop_format_context(ast.Str(expl))
            call = ast_Call(app, [expl_format], [])
            self.on_failure.append(ast.Expr(call))
            if i < levels:
                cond = res
                if is_or:
                    cond = ast.UnaryOp(ast.Not(), cond)
                inner = []
                self.statements.append(ast.If(cond, inner, []))
                self.statements = body = inner
        self.statements = save
        self.on_failure = fail_save
        expl_template = self.helper("format_boolop", expl_list, ast.Num(is_or))
        expl = self.pop_format_context(expl_template)
        return ast.Name(res_var, ast.Load()), self.explanation_param(expl)

    def visit_UnaryOp(self, unary):
        pattern = unary_map[unary.op.__class__]
        operand_res, operand_expl = self.visit(unary.operand)
        res = self.assign(ast.UnaryOp(unary.op, operand_res))
        return res, pattern % (operand_expl,)

    def visit_BinOp(self, binop):
        symbol = binop_map[binop.op.__class__]
        left_expr, left_expl = self.visit(binop.left)
        right_expr, right_expl = self.visit(binop.right)
        explanation = "(%s %s %s)" % (left_expl, symbol, right_expl)
        res = self.assign(ast.BinOp(left_expr, binop.op, right_expr))
        return res, explanation

    def visit_Call_35(self, call):
        """
        visit `ast.Call` nodes on Python3.5 and after
        """
        new_func, func_expl = self.visit(call.func)
        arg_expls = []
        new_args = []
        new_kwargs = []
        for arg in call.args:
            res, expl = self.visit(arg)
            arg_expls.append(expl)
            new_args.append(res)
        for keyword in call.keywords:
            res, expl = self.visit(keyword.value)
            new_kwargs.append(ast.keyword(keyword.arg, res))
            if keyword.arg:
                arg_expls.append(keyword.arg + "=" + expl)
            else:  # **args have `arg` keywords with an .arg of None
                arg_expls.append("**" + expl)

        expl = "%s(%s)" % (func_expl, ", ".join(arg_expls))
        new_call = ast.Call(new_func, new_args, new_kwargs)
        res = self.assign(new_call)
        res_expl = self.explanation_param(self.display(res))
        outer_expl = "%s\n{%s = %s\n}" % (res_expl, res_expl, expl)
        return res, outer_expl

    def visit_Starred(self, starred):
        # From Python 3.5, a Starred node can appear in a function call
        _, expl = self.visit(starred.value)
        return starred, "*" + expl

    def visit_Call_legacy(self, call):
        """
        visit `ast.Call nodes on 3.4 and below`
        """
        new_func, func_expl = self.visit(call.func)
        arg_expls = []
        new_args = []
        new_kwargs = []
        new_star = new_kwarg = None
        for arg in call.args:
            res, expl = self.visit(arg)
            new_args.append(res)
            arg_expls.append(expl)
        for keyword in call.keywords:
            res, expl = self.visit(keyword.value)
            new_kwargs.append(ast.keyword(keyword.arg, res))
            arg_expls.append(keyword.arg + "=" + expl)
        if call.starargs:
            new_star, expl = self.visit(call.starargs)
            arg_expls.append("*" + expl)
        if call.kwargs:
            new_kwarg, expl = self.visit(call.kwargs)
            arg_expls.append("**" + expl)
        expl = "%s(%s)" % (func_expl, ", ".join(arg_expls))
        new_call = ast.Call(new_func, new_args, new_kwargs, new_star, new_kwarg)
        res = self.assign(new_call)
        res_expl = self.explanation_param(self.display(res))
        outer_expl = "%s\n{%s = %s\n}" % (res_expl, res_expl, expl)
        return res, outer_expl

    # ast.Call signature changed on 3.5,
    # conditionally change  which methods is named
    # visit_Call depending on Python version
    if sys.version_info >= (3, 5):
        visit_Call = visit_Call_35
    else:
        visit_Call = visit_Call_legacy

    def visit_Attribute(self, attr):
        if not isinstance(attr.ctx, ast.Load):
            return self.generic_visit(attr)
        value, value_expl = self.visit(attr.value)
        res = self.assign(ast.Attribute(value, attr.attr, ast.Load()))
        res_expl = self.explanation_param(self.display(res))
        pat = "%s\n{%s = %s.%s\n}"
        expl = pat % (res_expl, res_expl, value_expl, attr.attr)
        return res, expl

    def visit_Compare(self, comp):
        self.push_format_context()
        left_res, left_expl = self.visit(comp.left)
        if isinstance(comp.left, (ast.Compare, ast.BoolOp)):
            left_expl = "({})".format(left_expl)
        res_variables = [self.variable() for i in range(len(comp.ops))]
        load_names = [ast.Name(v, ast.Load()) for v in res_variables]
        store_names = [ast.Name(v, ast.Store()) for v in res_variables]
        it = zip(range(len(comp.ops)), comp.ops, comp.comparators)
        expls = []
        syms = []
        results = [left_res]
        for i, op, next_operand in it:
            next_res, next_expl = self.visit(next_operand)
            if isinstance(next_operand, (ast.Compare, ast.BoolOp)):
                next_expl = "({})".format(next_expl)
            results.append(next_res)
            sym = binop_map[op.__class__]
            syms.append(ast.Str(sym))
            expl = "%s %s %s" % (left_expl, sym, next_expl)
            expls.append(ast.Str(expl))
            res_expr = ast.Compare(left_res, [op], [next_res])
            self.statements.append(ast.Assign([store_names[i]], res_expr))
            left_res, left_expl = next_res, next_expl
        # Use pytest.assertion.util._reprcompare if that's available.
        expl_call = self.helper(
            "call_reprcompare",
            ast.Tuple(syms, ast.Load()),
            ast.Tuple(load_names, ast.Load()),
            ast.Tuple(expls, ast.Load()),
            ast.Tuple(results, ast.Load()),
        )
        if len(comp.ops) > 1:
            res = ast.BoolOp(ast.And(), load_names)
        else:
            res = load_names[0]
        return res, self.explanation_param(self.pop_format_context(expl_call))


def _call_reprcompare(ops, results, expls, each_obj):
    for _, res, expl in zip(range(len(ops)), results, expls):
        try:
            done = not res
        except Exception:
            done = True
        if done:
            break
    return expl


def _saferepr(obj):
    """Get a safe repr of an object for assertion error messages.

    The assertion formatting (util.format_explanation()) requires
    newlines to be escaped since they are a special character for it.
    Normally assertion.util.format_explanation() does this but for a
    custom repr it is possible to contain one of the special escape
    sequences, especially '\n{' and '\n}' are likely to be present in
    JSON reprs.

    """
    if isinstance(obj, types.MethodType):
        if obj.__self__:
            obj_repr = "self.%s" % obj.__func__.__name__
    elif isinstance(obj, type):
        obj_repr = obj.__name__
    elif isinstance(obj, six.string_types):
        obj_repr = '"%s"' % smart_text(obj)
    else:
        obj_repr = pprint.saferepr(obj)
    return obj_repr


def _should_repr_global_name(obj):
    return not hasattr(obj, "__name__") and not callable(obj)


def _format_assertmsg(obj):
    """Format the custom assertion message given.

    For strings this simply replaces newlines with '\n~' so that
    util.format_explanation() will preserve them instead of escaping
    newlines.  For other objects py.io.saferepr() is used first.

    """
    # reprlib appears to have a bug which means that if a string
    # contains a newline it gets escaped, however if an object has a
    # .__repr__() which contains newlines it does not get escaped.
    # However in either case we want to preserve the newline.
#     if isinstance(obj, six.text_type) or isinstance(obj, six.binary_type):
    if isinstance(obj, six.string_types):
        s = smart_text(obj)
        is_repr = False
    else:
        s = pprint.saferepr(obj)
        is_repr = True
    t = str
    s = s.replace(t("\n"), t("\n~")).replace(t("%"), t("%%"))
    if is_repr:
        s = s.replace(t("\\n"), t("\n~"))
    return s + "\n"


def _format_explanation(explanation):
    """This formats an explanation

    Normally all embedded newlines are escaped, however there are
    three exceptions: \n{, \n} and \n~.  The first two are intended
    cover nested explanations, see function and attribute explanations
    for examples (.visit_Call(), visit_Attribute()).  The last one is
    for when one explanation needs to span multiple lines, e.g. when
    displaying diffs.
    """
    raw_lines = (explanation or '').split('\n')
    # escape newlines not followed by {, } and ~
    msg = raw_lines[0]
    raw_lines = raw_lines[1:]
    lines = raw_lines[:1]
    for l in raw_lines[1:]:
        if l.startswith('{') or l.startswith('}') or l.startswith('~'):
            lines.append(l)
        else:
            lines[-1] += '\\n' + l

    result = lines[:1]
    stack = [0]
    stackcnt = [0]
    for line in lines[1:]:
        if line.startswith('{'):
            if stackcnt[-1]:
                s = 'and   '
            else:
                s = 'where '
            stack.append(len(result))
            stackcnt[-1] += 1
            stackcnt.append(0)
            result.append(' +' + '  ' * (len(stack) - 1) + s + line[1:])
        elif line.startswith('}'):
            stack.pop()
            stackcnt.pop()
            result[stack[-1]] += line[1:]
        else:
            assert line.startswith('~')
            result.append('  ' * len(stack) + line[1:])
    assert len(stack) == 1
    result[0] = " [%s] assert " % msg + result[0]
    return '\n'.join(result)


def get_func_name(func):
    if isinstance(func, types.MethodType):
        if sys.version_info[0] == 3:
            return func.__func__.__name__
        else:
            return func.__name__
    else:
        return func.__name__


def get_func_source_code(func):
    if isinstance(func, types.MethodType):
        if sys.version_info[0] == 3:
            src_code = inspect.getsource(func.__self__.__class__)
        else:
            im_class = get_method_defined_class(func)
            src_code = inspect.getsource(im_class)
    else:
        src_code = inspect.getsource(func)

    indent = inspect.indentsize(src_code)
    if indent > 0:
        lines = src_code.split("\n")
        src_code = ""
        for line in lines:
            src_code += line[indent:] + "\n"
    src_code = "# -*- coding: utf-8 -*-\n\n" + src_code  # coding specification
    return src_code


def get_func_mod_and_node(func):
    func_name = get_func_name(func)
    src_code = get_func_source_code(func)
    if isinstance(func, types.MethodType):
        mod = ast.parse(src_code)
        ast_cls = mod.body[0]
        for item in ast_cls.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == func_name:
                    func_node = item
                    break
        else:
            return None, None
    else:
        mod = ast.parse(src_code)
        func_node = mod.body[0]
    ast.increment_lineno(func_node, func.__code__.co_firstlineno - func_node.lineno)
    return mod, func_node


def get_func_compiled_code(func, new_code):
    func_name = get_func_name(func)
    if isinstance(func, types.MethodType):
        for item in new_code.co_consts:
            if isinstance(item, types.CodeType):
                for sub_item in item.co_consts:
                    if isinstance(sub_item, types.CodeType) and sub_item.co_name == func_name:
                        return sub_item
    elif isinstance(func, types.FunctionType):
        for item in new_code.co_consts:
            if isinstance(item, types.CodeType) and item.co_name == func_name:
                return item
    else:
        raise RuntimeError("%s not supported yet" % repr(func))


def set_func_code(func, new_code):
    new_func_code = get_func_compiled_code(func, new_code)
    if isinstance(func, types.MethodType):
        if sys.version_info[0] == 3:
            func.__code__ = new_func_code
        else:
            func.__func__.__code__ = new_func_code
    else:
        func.__code__ = new_func_code


class _AssertHookedCache(six.with_metaclass(Singleton, object)):

    def __init__(self):
        self._lock = threading.Lock()
        self.__cache = set()

    def add(self, func):
        with self._lock:
            self.__cache.add(self._hash_func(func))

    def __contains__(self, func):
        item = self._hash_func(func)
        return item in self.__cache

    def __iter__(self):
        return self.__cache.__iter__()

    def _hash_func(self, func):
        if isinstance(func, (types.FunctionType, types.MethodType)):
            return func
        else:
            raise ValueError("func must be a callable type or object")


if __name__ == "__main__":
    pass
