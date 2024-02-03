from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Literal, Sequence, Tuple, Type, Union, cast
from fastapi import Request
from pydantic import BaseModel, Field, computed_field
from pydantic.alias_generators import to_camel
from abc import ABC, abstractmethod


# base
class PueModel(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True


# scripting

# runtime scope options for get/set
Scope = Literal["local", "component"]


class AST(PueModel):
    is_async: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def kind(self) -> str:
        return self.__class__.__name__


class If(AST):
    condition: Expr
    then_clause: Block
    else_clause: Block | None = None


class For(AST):
    value: str
    iterable: Expr
    body: Block


class Map(AST):
    value: str
    iterable: Expr
    body: Block


class Filter(AST):
    value: str
    iterable: Expr
    body: Block


class Append(AST):
    iterable: Expr
    value: Expr


class Try(AST):
    try_clause: Block
    catch_clause: Block | None
    finally_clause: Block | None


class Store(AST):
    name: str
    scope: Scope
    value: Expr


class Load(AST):
    name: str
    scope: Scope


class Inspect(AST):
    pass


class Breakpoint(AST):
    pass


class BoolOp(AST):
    op: Literal["and", "or"]
    left: Expr
    right: Expr


LogLevel = Literal["log", "info", "warn", "debug", "error"]


class Log(AST):
    value: Expr
    level: LogLevel = "log"


class Panic(AST):
    msg: str


HTTPMethod = Literal["get", "post", "put", "delete"]


class Fetch(AST):
    is_async: bool = True
    url: str
    method: HTTPMethod
    headers: Dict[str, str] | None = None


class Sleep(AST):
    is_async: bool = True
    ms: int


CompareType = Literal[
    "eq",
    "neq",
    "lt",
    "lte",
    "gt",
    "gte",
    "in",
    "nin",
]


class Compare(AST):
    op: CompareType
    left: Expr
    right: Expr


BinOpType = Literal[
    "add",
    "sub",
    "mul",
    "div",
    "mod",
    "pow",
    "floordiv",
    "lshift",
    "rshift",
    "bitand",
    "bitor",
    "bitxor",
]


class BinOp(AST):
    left: Expr
    op: BinOpType
    right: Expr


UnaryOpType = Literal["invert", "not", "uadd", "usub"]


class UnaryOp(AST):
    op: UnaryOpType
    expr: Expr


class Dictionary(AST):
    value: Dict[str, Expr]


PropKey = Tuple[str, ...] | str


class VNode(AST):
    # in a vue vnode, the first param is the "type", which can either be a string or a component
    # for pue, this will always be a string, and the frontend will fork based on if the type type is "string" or "component"
    v_node_type_type: Literal["string", "component"]
    v_node_type_val: str
    props: Dict[PropKey, Script] = {}
    children: List[Union[VNode, Expr]] = []


Constant = str | int | float | bool | None
Expr = (
    BoolOp
    | BinOp
    | UnaryOp
    | If
    | Map
    | Compare
    | Load
    | Dictionary
    | Constant
    | Fetch
    | VNode
    | Filter
    | Inspect
)
Statement = Expr | Log | Panic | Try | Sleep | For | Store | Append | Breakpoint
Block = Tuple[Statement] | Sequence[Statement] | Statement
Script = Block
Template = VNode | Expr

# config


class Route(PueModel):
    path: str
    name: str | None = None
    redirect: str | None = None
    component: Type[Component] | None = Field(exclude=True, default=None)
    children: List[Route] = []

    # https://docs.pydantic.dev/2.0/usage/computed_fields/
    @computed_field  # type: ignore[misc]
    @property
    def component_endpoint(self) -> str | None:
        if not self.component:
            return None
        return self.component.endpoint_path()


class RouteConfigResponse(PueModel):
    routes: List[Route]


class ComponentEndpointResponse(PueModel):
    template: Template
    created: Script | None = None
    before_mount: Script | None = None
    mounted: Script | None = None
    before_update: Script | None = None
    updated: Script | None = None
    before_unmount: Script | None = None
    unmounted: Script | None = None
    computed: Dict[str, Script] | None = None
    watch: Dict[str, Script] | None = None
    data: Dict[str, Any] = {}


class Component(ABC):
    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def endpoint_path(cls) -> str:
        return f"components/{cls.name()}"

    @abstractmethod
    async def async_template(self, req: Request) -> Template: ...
    async def async_mounted(self) -> Script | None: ...
    async def async_created(self) -> Script | None: ...
    async def async_before_mount(self) -> Script | None: ...
    async def async_before_update(self) -> Script | None: ...
    async def async_updated(self) -> Script | None: ...
    async def async_before_unmount(self) -> Script | None: ...
    async def async_unmounted(self) -> Script | None: ...
    async def async_computed(self) -> Dict[str, Script] | None: ...
    async def async_watch(self) -> Dict[str, Script] | None: ...
    async def async_data(self) -> Dict[str, Any]:
        return {}

    @classmethod
    async def async_endpoint(cls, req: Request) -> ComponentEndpointResponse:
        instance = cls()
        (
            template,
            mounted,
            created,
            before_mount,
            before_update,
            updated,
            before_unmount,
            unmounted,
            data,
            computed,
            watch,
        ) = await asyncio.gather(
            instance.async_template(req=req),
            instance.async_mounted(),
            instance.async_created(),
            instance.async_before_mount(),
            instance.async_before_update(),
            instance.async_updated(),
            instance.async_before_unmount(),
            instance.async_unmounted(),
            instance.async_data(),
            instance.async_computed(),
            instance.async_watch(),
        )
        return ComponentEndpointResponse(
            template=cast(Template, template),
            mounted=cast(Script, mounted),
            created=cast(Script, created),
            before_mount=cast(Script, before_mount),
            before_update=cast(Script, before_update),
            updated=cast(Script, updated),
            before_unmount=cast(Script, before_unmount),
            unmounted=cast(Script, unmounted),
            data=cast(Dict[str, Any], data),
            computed=cast(Union[Dict[str, Script], None], computed),
            watch=cast(Union[Dict[str, Script], None], watch),
        )
