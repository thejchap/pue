from fastapi import FastAPI, Request
import pue
from pue import dom as h, script as s
from pue.script import this, local


class App(pue.Component):
    NAV = [
        {"name": "Todos", "to": "/todos"},
        {"name": "Fetch", "to": "/fetch"},
    ]

    async def async_template(self, req: Request):
        return h.div(
            h.nav(
                *[
                    h.RouterLink(
                        nav["name"],
                        as_="a",
                        to=nav["to"],
                        exact_active_class="bg-indigo-100 text-indigo-700",
                        class_="text-gray-500 hover:text-gray-700 rounded-md px-3 py-2 text-sm font-medium",
                    )
                    for nav in self.NAV
                ],
                class_="flex space-x-4",
            ),
            h.main(h.RouterView(), class_="pt-10"),
            h.footer(
                h.p(
                    "Made by ",
                    h.a(
                        "thejchap",
                        href="https://github.com/thejchap",
                        target="_blank",
                        class_="font-semibold text-indigo-600 hover:text-indigo-500",
                    ),
                    class_="text-xs leading-5 text-gray-500",
                ),
                class_="mt-6",
            ),
            class_="p-6",
        )


class Todos(pue.Component):
    async def async_data(self):
        return {
            "todos": [],
            "new_todo": "",
        }

    async def async_computed(self):
        return {
            "completed": s.filter(
                this.get("todos"),
                "todo",
                local.get("todo.completed"),
            ),
            "incomplete": s.filter(
                this.get("todos"),
                "todo",
                s.not_(
                    local.get("todo.completed"),
                ),
            ),
        }

    async def async_template(self, req: Request):
        return h.div(
            *_header(
                "Pue - Todos Example",
                "https://github.com/thejchap/pue/blob/main/example.py",
            ),
            h.form(
                h.input_(
                    type_="text",
                    placeholder="What needs to be done?",
                    autofocus=True,
                    class_="mr-2 flex-1 rounded-md border-0 py-2.5 text-sm text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                    value=this.get("new_todo"),
                    on_input=this.set_("new_todo", local.get("$event.target.value")),
                ),
                h.button(
                    "Add",
                    disabled=s.not_(this.get("new_todo.length")),
                    type_="submit",
                    class_="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed",
                ),
                props={
                    ("onSubmit", "prevent"): (
                        s.append(
                            this.get("todos"),
                            s.obj(
                                {
                                    "id": this.get("todos.length"),
                                    "title": this.get("new_todo"),
                                    "completed": False,
                                }
                            ),
                        ),
                        this.set_("new_todo", ""),
                    )
                },
                class_="mb-6 flex",
            ),
            s.if_(
                s.gt(this.get("incomplete.length"), 0),
                then=_todo_list(todos=this.get("incomplete"), title="Incomplete"),
            ),
            s.if_(
                s.gt(this.get("completed.length"), 0),
                then=_todo_list(todos=this.get("completed"), title="Completed"),
            ),
            class_="block",
        )


def _todo_list(todos: s.m.Expr, title: str):
    return h.section(
        h.legend(
            title,
            class_="text-base font-semibold leading-6 text-gray-900",
        ),
        h.div(
            s.map(
                todos,
                "todo",
                h.div(
                    h.div(
                        h.input_(
                            type_="checkbox",
                            class_="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",
                            checked=local.get("todo.completed"),
                            on_change=(
                                local.set_(
                                    "todo.completed",
                                    local.get("$event.target.checked"),
                                ),
                            ),
                        ),
                        class_="flex h-6 items-center",
                    ),
                    h.div(
                        h.label(
                            local.get("todo.title"),
                            class_=[
                                "font-medium text-gray-900",
                                s.if_(local.get("todo.completed"), then="line-through"),
                            ],
                        ),
                        class_="ml-3 text-sm leading-6",
                    ),
                    class_="relative flex items-start py-4",
                    key=local.get("todo.id"),
                ),
            ),
            class_="my-4 divide-y divide-gray-200 border-b border-t border-gray-200",
        ),
    )


class FetchExample(pue.Component):
    async def async_data(self):
        return {
            "photos": [],
            "is_loading": True,
            "error": None,
        }

    async def async_mounted(self):
        return s.try_(
            this.set_(
                "photos",
                s.fetch("https://picsum.photos/v2/list?limit=16"),
            ),
            catch=this.set_("error", local.get("error.message")),
            finally_=this.set_("is_loading", False),
        )

    async def async_template(self, req: Request):
        return h.div(
            *_header(
                "Pue - Fetch Example",
                "https://github.com/thejchap/pue/blob/main/example.py",
            ),
            s.if_(
                this.get("error"),
                then=h.div(
                    h.div(
                        h.div(
                            h.p(
                                this.get("error"),
                                class_="text-sm font-medium text-red-800",
                            ),
                            class_="flex-shrink-0",
                        ),
                        class_="flex",
                    ),
                    class_="rounded-md bg-red-50 p-4",
                ),
            ),
            s.if_(
                this.get("is_loading"),
                then=h.div(
                    class_="animate-spin inline-block w-12 h-12 border-[3px] border-current border-t-transparent text-indigo-600 rounded-full dark:text-indigo-500"
                ),
                else_=h.div(
                    s.map(
                        this.get("photos"),
                        "photo",
                        h.div(
                            h.div(
                                h.img(
                                    src=local.get("photo.download_url"),
                                    class_="h-full w-full object-cover object-center lg:h-full lg:w-full",
                                ),
                                class_="aspect-h-1 aspect-w-1 w-full overflow-hidden rounded-md bg-gray-200 lg:aspect-none group-hover:opacity-75 lg:h-80",
                            ),
                            h.div(
                                h.h3(
                                    local.get("photo.author"),
                                    class_="text-sm text-gray-700",
                                ),
                                class_="mt-4 flex justify-between",
                            ),
                            class_="group relative",
                        ),
                    ),
                    class_="mt-6 grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4 xl:gap-x-8",
                ),
            ),
        )


def _header(title: str, code_ptr: str):
    return (
        h.h1(
            title,
            class_="text-3xl font-bold tracking-tight text-gray-90",
        ),
        h.p(
            h.a(
                "Click here",
                href=code_ptr,
                target="_blank",
                class_="font-semibold text-indigo-600 hover:text-indigo-500",
            ),
            " to view source code",
            class_="mt-4 mb-6 text-lg leading-8 text-gray-600",
        ),
    )


PUE = pue.Pue(
    routes=[
        pue.Route(
            path="/",
            component=App,
            children=[
                pue.Route(
                    name="Index",
                    path="",
                    redirect="todos",
                ),
                pue.Route(
                    name="Todos",
                    path="todos",
                    component=Todos,
                ),
                pue.Route(
                    name="Fetch",
                    path="fetch",
                    component=FetchExample,
                ),
            ],
        )
    ]
)
APP = FastAPI()
APP.mount(PUE.config_path, PUE.config_api)
APP.mount(PUE.index_path, PUE.index_api)
