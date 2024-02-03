# pue
server-driven [vue.js](https://vuejs.org/) ui

## example
see the [example app](https://github.com/thejchap/pue/blob/main/example.py) running <a href="https://pue-example.fly.dev" target="_blank">here</a>.

## overview
proof-of-concept i hacked together last weekend. omits all frontend build shenanigans and uses cdn vue/vue-router just to illustrate an e2e working example. vue components are written in python and served to the frontend via an api endpoint. there is a dsl to allow you to script some client side logic also in python, but the idea is more to just have python do stuff (data fetching/whatever) and render a layout that it returns to the frontend, maybe as a sub-application inside a larger vue app.

inspired by:
- [dash](https://github.com/plotly/dash?tab=readme-ov-file)
- bloks (ig internal library for server-driven mobile uis)

## getting started
```bash
python --version # 3.12
git clone https://github.com/thejchap/pue.git
cd pue && make
```