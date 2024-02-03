from typing import Dict, Literal
from . import models as m
from pydantic.alias_generators import to_camel


def node(type_val: str, type_type: Literal["string", "component"]):
    def builder(
        *children: m.Template, props: Dict[m.PropKey, m.Script] = {}, **kwargs: m.Script
    ):
        return m.VNode(
            v_node_type_type=type_type,
            v_node_type_val=type_val,
            children=list(children),
            props={
                **props,
                **{
                    # remove trailing underscores from keys
                    # assuming these are to handle python reserved words aka "class_"
                    to_camel(k.removesuffix("_")): v
                    for k, v in kwargs.items()
                },
            },
        )

    return builder


def component(type_val: str):
    return node(type_val, "component")


def tag(type_val: str):
    return node(type_val, "string")


# html elements
a = tag("a")
div = tag("div")
span = tag("span")
nav = tag("nav")
h1 = tag("h1")
h2 = tag("h2")
h3 = tag("h3")
h4 = tag("h4")
h5 = tag("h5")
h6 = tag("h6")
p = tag("p")
input_ = tag("input")
label = tag("label")
legend = tag("legend")
img = tag("img")
header = tag("header")
footer = tag("footer")
form = tag("form")
button = tag("button")
section = tag("section")
article = tag("article")
main = tag("main")
ul = tag("ul")
li = tag("li")

# components
RouterView = component("RouterView")
RouterLink = component("RouterLink")
