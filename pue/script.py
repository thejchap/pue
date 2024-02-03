from __future__ import annotations
from typing import Dict
from . import models as m


def sleep(ms: int):
    return m.Sleep(ms=ms)


def inspect():
    return m.Inspect()


def breakpoint():
    return m.Breakpoint()


def log_level(level: m.LogLevel):
    def inner(value: m.Expr):
        return m.Log(value=value, level=level)

    return inner


log = log_level("log")
info = log_level("info")
warn = log_level("warn")
debug = log_level("debug")
error = log_level("error")


def append(iterable: m.Expr, value: m.Expr):
    return m.Append(iterable=iterable, value=value)


def scope_proxy(scope: m.Scope):
    class Proxy:
        def get(self, name: str):
            return m.Load(name=name, scope=scope)

        def set_(self, name: str, value: m.Expr):
            return m.Store(name=name, scope=scope, value=value)

    return Proxy()


this = scope_proxy("component")
local = scope_proxy("local")


def obj(value: Dict[str, m.Expr] = {}):
    return m.Dictionary(value=value)


def filter(iterable: m.Expr, value: str, body: m.Expr):
    return m.Filter(value=value, iterable=iterable, body=body)


def map(iterable: m.Expr, value: str, body: m.Expr):
    return m.Map(value=value, iterable=iterable, body=body)


def try_(
    try_clause: m.Block, catch: m.Block | None = None, finally_: m.Block | None = None
):
    return m.Try(try_clause=try_clause, catch_clause=catch, finally_clause=finally_)


def panic(msg: str):
    return m.Panic(msg=msg)


def fetch(
    url: str, method: m.HTTPMethod = "get", headers: Dict[str, str] | None = None
):
    return m.Fetch(url=url, method=method, headers=headers)


def if_(
    condition: m.Expr,
    then: m.Block | None = None,
    else_: m.Block | None = None,
):
    return m.If(condition=condition, then_clause=then, else_clause=else_)


def binop(op: m.BinOpType):
    def inner(left: m.Expr, right: m.Expr):
        return m.BinOp(op=op, left=left, right=right)

    return inner


def unaryop(op: m.UnaryOpType):
    def inner(expr: m.Expr):
        return m.UnaryOp(op=op, expr=expr)

    return inner


def comparison(op: m.CompareType):
    def inner(left: m.Expr, right: m.Expr):
        return m.Compare(op=op, left=left, right=right)

    return inner


add = binop("add")
sub = binop("sub")
mul = binop("mul")
div = binop("div")
mod = binop("mod")
pow_ = binop("pow")
floordiv = binop("floordiv")
lshift = binop("lshift")
rshift = binop("rshift")
bitand = binop("bitand")
bitor = binop("bitor")
bitxor = binop("bitxor")
not_ = unaryop("not")
invert = unaryop("invert")
uadd = unaryop("uadd")
usub = unaryop("usub")
gt = comparison("gt")
gte = comparison("gte")
lt = comparison("lt")
lte = comparison("lte")
eq = comparison("eq")
neq = comparison("neq")
in_ = comparison("in")
nin = comparison("nin")
