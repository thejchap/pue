from __future__ import annotations
import os
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from . import models as m

_DIR = os.path.dirname(os.path.realpath(__file__))


class Pue:
    config_path = "/_pue"
    # catch all route for / so we can use vue-router WebHistory
    index_path = "/"

    def __init__(self, routes: List[m.Route]):
        self._routes = routes
        self.config_api = self._build_config_api()
        self.index_api = self._build_index_api()

    def _build_config_api(self):
        app = FastAPI()
        app.get(
            "/client.js",
            response_class=FileResponse,
        )(self.async_js_endpoint)
        app.get(
            "/routes",
            response_model=m.RouteConfigResponse,
        )(self.async_routes_endpoint)

        def add_component_route(route: m.Route):
            if route.component:
                app.get(
                    "/" + route.component.endpoint_path(),
                    response_model=m.ComponentEndpointResponse,
                )(route.component.async_endpoint)
            for child in route.children:
                add_component_route(child)

        for route in self._routes:
            add_component_route(route)
        return app

    async def async_js_endpoint(self, req: Request) -> FileResponse:
        return FileResponse(
            f"{_DIR}/client.js",
            headers={
                "Content-Type": "application/javascript",
                "Cache-Control": "no-cache",
            },
        )

    async def async_routes_endpoint(self, req: Request):
        return m.RouteConfigResponse(routes=self._routes)

    def _build_index_api(self):
        app = FastAPI()
        app.get("{full_path:path}", response_class=HTMLResponse)(
            self.async_default_index
        )
        return app

    async def async_default_index(self):
        return """\
<!DOCTYPE html>
<html class="h-full bg-gray-50">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>pue example app</title>
        <link rel="icon" href="https://zany.sh/favicon.svg" />
        <script type="importmap">
            {
                "imports": {
                    "pue": "/_pue/client.js"
                }
            }
        </script>

        <!-- load things from cdn because easy -->
        <script src="https://cdn.tailwindcss.com?plugins=forms"></script>
        <script src="https://unpkg.com/vue@3"></script>
        <script src="https://unpkg.com/vue-router@4"></script>

        <script type="module">
            // minimal js required to bootstrap the app
            import { pue } from "pue";

            // normal vue/vue router stuff
            const app = Vue.createApp();
            const history = VueRouter.createWebHistory();

            // load pue config from server
            const routes = await pue()

            // pue routes are the only routes in this app
            // could be nested/only used for a part of the app
            const router = VueRouter.createRouter({
                history,
                routes,
            });

            // normal vue stuff
            app.use(router)
            app.mount("#app");
        </script>
    </head>

    <body class="h-full">
        <div id="app"><router-view></router-view></div>
    </body>

</html>
        """.strip()
