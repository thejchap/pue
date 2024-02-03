const { h, resolveComponent, isVNode, withModifiers, resolveDirective } = Vue;
/**
 * pue entrypoint
 * fetch config from server, turn into vue-router routes
 */
export async function pue(
  opts = {
    basePath: "/_pue",
  }
) {
  const res = await fetch(`${opts.basePath}/routes`);
  const { routes } = await res.json();
  return routes.map((route) => config2Route(route, opts));
}
/**
 * builds a vue router route based on config from the server
 */
function config2Route(
  { path, name, children, componentEndpoint, redirect },
  opts
) {
  let component;
  if (componentEndpoint) {
    component = endpoint2LazyComponent(componentEndpoint, opts);
  }
  return {
    path,
    name,
    component,
    redirect,
    children: children.map((route) => config2Route(route, opts)),
  };
}
/**
 * builds a vue component based on config from the server
 * lazy-loaded by vue router when the route is visited
 * https://router.vuejs.org/guide/advanced/lazy-loading.html
 */
function endpoint2LazyComponent(endpoint, { basePath }) {
  return async () => {
    const path = `${basePath}/${endpoint}`;
    const res = await fetch(path);
    const {
      template,
      created,
      beforeMount,
      mounted,
      beforeUpdate,
      updated,
      beforeUnmount,
      unmounted,
      computed,
      watch,
      data,
    } = await res.json();
    return {
      mounted: script2Promise(mounted),
      created: script2Promise(created),
      beforeMount: script2Promise(beforeMount),
      beforeUpdate: script2Promise(beforeUpdate),
      updated: script2Promise(updated),
      beforeUnmount: script2Promise(beforeUnmount),
      unmounted: script2Promise(unmounted),
      computed: transformValues(computed, script2Func),
      watch: transformValues(watch, script2Func),
      data() {
        return data;
      },
      render() {
        return interpret(template, new Scope(this));
      },
    };
  };
}
/**
 * scripting
 */
// runtime state
class Scope {
  locals = new Map();
  currentVNode = null;
  constructor(component) {
    this.component = component;
  }
}
// helper - take a script config and turn it into an async function for the component
function script2Promise(script, ctx) {
  if (!script) {
    return;
  }
  return function () {
    ctx = ctx ?? new Scope(this);
    return interpretAsync(script, ctx);
  };
}
// helper - take a script config and turn it into a function for the component
function script2Func(script, ctx) {
  if (!script) {
    return;
  }
  return function () {
    ctx = ctx ?? new Scope(this);
    return interpret(script, ctx);
  };
}

/**
 * a little clunky - 2 separate interpreters
 * render functions are not async, so need to provide a path for sync scripts
 * but the rest of the component lifecycle hooks can be async and this makes
 * the scripting from the server a lot simpler (allows fetch, sleep, etc with simple client logic)
 */
// sync runtime
function interpret(ast, ctx) {
  switch (typeof ast) {
    case "string":
    case "boolean":
    case "number":
    case "bigint":
    case "undefined":
      return ast;
    case "object":
      if (ast === null) {
        return ast;
      }
      if (Array.isArray(ast)) {
        return ast.map((item) => interpret(item, ctx));
      }
      if (ast.isAsync) {
        throw new Error(`async not supported in render function (${ast.kind})`);
      }
      switch (ast.kind) {
        case "VNode":
          return interpretVNode(ast, ctx);
        case "Load":
          return interpretLoad(ast, ctx);
        case "Store":
          return interpretStore(ast, ctx);
        case "BinOp":
          return interpretBinOp(ast, ctx);
        case "If":
          return interpretIf(ast, ctx);
        case "Panic":
          return interpretPanic(ast, ctx);
        case "BoolOp":
          return interpretBoolOp(ast, ctx);
        case "UnaryOp":
          return interpretUnaryOp(ast, ctx);
        case "Log":
          return interpretLog(ast, ctx);
        case "Map":
          return interpretMap(ast, ctx);
        case "Filter":
          return interpretFilter(ast, ctx);
        case "Append":
          return interpretAppend(ast, ctx);
        case "Try":
          return interpretTry(ast, ctx);
        case "Compare":
          return interpretCompare(ast, ctx);
        case "Dictionary":
          return transformValues(ast.value, (val) => interpret(val, ctx));
        case "Breakpoint":
          debugger;
        case "Inspect":
          return ctx;
        default:
          throw new Error(`unexpected node kind: ${ast.kind}`);
      }
    default:
      throw new Error(`unexpected node type: ${typeof ast}`);
  }
}
// async runtime
async function interpretAsync(ast, ctx) {
  switch (typeof ast) {
    case "string":
    case "boolean":
    case "number":
    case "bigint":
    case "undefined":
      return ast;
    case "object":
      if (ast === null) {
        return ast;
      }
      if (Array.isArray(ast)) {
        const res = [];
        for (const item of ast) {
          res.push(await interpretAsync(item, ctx));
        }
        return res;
      }
      switch (ast.kind) {
        case "Load":
          return await interpretLoadAsync(ast, ctx);
        case "Store":
          return await interpretStoreAsync(ast, ctx);
        case "BinOp":
          return await interpretBinOpAsync(ast, ctx);
        case "If":
          return await interpretIfAsync(ast, ctx);
        case "Panic":
          return interpretPanic(ast);
        case "BoolOp":
          return await interpretBoolOpAsync(ast, ctx);
        case "UnaryOp":
          return await interpretUnaryOpAsync(ast, ctx);
        case "Log":
          return await interpretLogAsync(ast, ctx);
        case "Map":
          return await interpretMapAsync(ast, ctx);
        case "Filter":
          return await interpretFilterAsync(ast, ctx);
        case "Append":
          return await interpretAppendAsync(ast, ctx);
        case "Try":
          return await interpretTryAsync(ast, ctx);
        case "Compare":
          return await interpretCompareAsync(ast, ctx);
        case "Dictionary":
          return await transformValuesAsync(ast.value, (val) =>
            interpretAsync(val, ctx)
          );
        case "Sleep":
          return new Promise((resolve) => setTimeout(resolve, ast.ms));
        case "Inspect":
          return ctx;
        case "Breakpoint":
          debugger;
        case "Fetch":
          return await (
            await fetch(ast.url, {
              method: ast.method,
            })
          ).json();
      }
    default:
      throw new Error(`unexpected node: ${ast.kind}`);
  }
}
/**
 * visitors
 */
function interpretVNode(ast, ctx) {
  const {
    vNodeTypeType: typeType,
    vNodeTypeVal: type,
    children,
    props: rawProps,
  } = ast;
  ctx.currentVNode = ast;
  const props = interpretProps(rawProps, ctx);
  ctx.currentVNode = null;
  if (typeType === "component") {
    const component = resolveComponent(type);
    if (children.length === 0) {
      //  if no children, prevent from children being interpreted as a slot https://vuejs.org/api/render-function#h
      return h(component, props);
    }
    return h(component, props, () =>
      children.map((c) => {
        const child = interpret(c, ctx);
        if (isVNode(child)) {
          return child;
        }
        if (typeof child === "string") {
          return child;
        }
        return child;
      })
    );
  } else if (typeType === "string") {
    return h(
      type,
      props,
      children.map((c) => {
        const child = interpret(c, ctx);
        if (isVNode(child)) {
          return child;
        }
        if (typeof child === "string") {
          return child;
        }
        return child;
      })
    );
  }
  throw new Error(`unexpected v node type: ${typeType}`);
}
async function interpretLoadAsync(ast, ctx) {
  return interpretLoad(ast, ctx);
}
function interpretLoad({ scope, name }, ctx) {
  if (scope === "local") {
    const [key, ...rest] = name.split(".");
    const obj = ctx.locals.get(key);
    if (rest.length === 0) {
      return obj;
    }
    return queryObject(obj, rest.join("."));
  } else if (scope === "component") {
    return queryObject(ctx.component, name);
  }
  throw new Error(`unexpected scope for get: ${scope}`);
}
async function interpretStoreAsync({ scope, name, value }, ctx) {
  const val = await interpretAsync(value, ctx);
  return doStore(scope, name, val, ctx);
}
function interpretStore({ scope, name, value }, ctx) {
  const val = interpret(value, ctx);
  return doStore(scope, name, val, ctx);
}
function doStore(scope, name, value, ctx) {
  if (scope === "local") {
    let obj = ctx.locals;
    const parts = name.split(".");
    const key = parts.pop();
    for (const part of parts) {
      if (!obj.has(part)) {
        // TODO
        throw new Error(`invalid key path: ${name}`);
      }
      obj = obj.get(part);
    }
    if (obj instanceof Map) {
      obj.set(key, value);
    } else {
      obj[key] = value;
    }
  } else if (scope === "component") {
    ctx.component[name] = value;
  }
}
async function interpretBinOpAsync({ left, right, op }, ctx) {
  const l = await interpretAsync(left, ctx);
  const r = await interpretAsync(right, ctx);
  return doBinOp(l, r, op);
}
function interpretBinOp({ left, right, op }, ctx) {
  const l = interpret(left, ctx);
  const r = interpret(right, ctx);
  return doBinOp(l, r, op);
}
function doBinOp(l, r, op) {
  switch (op) {
    case "add":
      return l + r;
    case "sub":
      return l - r;
    case "mul":
      return l * r;
    case "div":
      return l / r;
    case "mod":
      return l % r;
    case "pow":
      return l ** r;
    case "floordiv":
      return Math.floor(l / r);
    case "lshift":
      return l << r;
    case "rshift":
      return l >> r;
    case "bitand":
      return l & r;
    case "bitor":
      return l | r;
    case "bitxor":
      return l ^ r;
    default:
      throw new Error(`unexpected bin op: ${op}`);
  }
}
function interpretIf({ condition, thenClause, elseClause }, ctx) {
  if (interpret(condition, ctx, interpret)) {
    return interpret(thenClause, ctx, interpret);
  }
  return interpret(elseClause, ctx, interpret);
}
async function interpretIfAsync({ condition, thenClause, elseClause }, ctx) {
  if (await interpretAsync(condition, ctx)) {
    return await interpretAsync(thenClause, ctx);
  }
  return await interpretAsync(elseClause, ctx);
}
function interpretPanic({ msg }) {
  throw new Error(msg);
}
async function interpretBoolOpAsync({ left, right, op }, ctx) {
  const l = await interpretAsync(left, ctx);
  const r = await interpretAsync(right, ctx);
  return doBoolOp(l, r, op);
}
function interpretBoolOp({ left, right, op }, ctx) {
  const l = interpret(left, ctx);
  const r = interpret(right, ctx);
  return doBoolOp(l, r, op);
}
function doBoolOp(l, r, op) {
  switch (op) {
    case "and":
      return l && r;
    case "or":
      return l || r;
    default:
      throw new Error(`unexpected bool op: ${op}`);
  }
}
async function interpretLogAsync({ value }, ctx) {
  console.log(await interpretAsync(value, ctx));
}
function interpretLog({ value }, ctx) {
  console.log(interpret(value, ctx));
}
function interpretFilter({ value, iterable, body }, ctx) {
  const items = interpret(iterable, ctx);
  return items.filter((item) => {
    const newCtx = new Scope(ctx.component);
    newCtx.locals = new Map(ctx.locals);
    newCtx.locals.set(value, item);
    return interpret(body, newCtx);
  });
}
function interpretFilterAsync({ value, iterable, body }, ctx) {
  const items = interpret(iterable, ctx);
  return items.filter(async (item) => {
    const newCtx = new Scope(ctx.component);
    newCtx.locals = new Map(ctx.locals);
    newCtx.locals.set(value, item);
    return await interpretAsync(body, newCtx);
  });
}
function interpretMap({ value, iterable, body }, ctx) {
  const items = interpret(iterable, ctx);
  return items.map((item) => {
    const newCtx = new Scope(ctx.component);
    newCtx.locals = new Map(ctx.locals);
    newCtx.locals.set(value, item);
    return interpret(body, newCtx);
  });
}
async function interpretMapAsync({ value, iterable, body }, ctx) {
  const items = await interpretAsync(iterable, ctx);
  return items.map(async (item) => {
    const newCtx = new Scope(ctx.component);
    newCtx.locals = new Map(ctx.locals);
    newCtx.locals.set(value, item);
    return await interpretAsync(body, newCtx);
  });
}
function interpretAppend({ value, iterable }, ctx) {
  const items = interpret(iterable, ctx);
  const val = interpret(value, ctx);
  items.push(val);
}
async function interpretAppendAsync({ value, iterable }, ctx) {
  const items = await interpretAsync(iterable, ctx);
  const val = await interpretAsync(value, ctx);
  items.push(val);
}
function interpretTry({ tryClause, catchClause, finallyClause }, ctx) {
  try {
    return interpret(tryClause, ctx);
  } catch (e) {
    ctx.locals.set("error", e);
    return interpret(catchClause, ctx);
  } finally {
    return interpret(finallyClause, ctx);
  }
}
async function interpretTryAsync(
  { tryClause, catchClause, finallyClause },
  ctx
) {
  try {
    return await interpretAsync(tryClause, ctx);
  } catch (e) {
    ctx.locals.set("error", e);
    return await interpretAsync(catchClause, ctx);
  } finally {
    return await interpretAsync(finallyClause, ctx);
  }
}
function interpretUnaryOp({ expr, op }, ctx) {
  const v = interpret(expr, ctx);
  return doUnaryOp(v, op);
}
async function interpretUnaryOpAsync({ expr, op }, ctx) {
  const v = await interpretAsync(expr, ctx);
  return doUnaryOp(v, op);
}
function doUnaryOp(v, op) {
  switch (op) {
    case "invert":
      return -v;
    case "not":
      return !v;
    case "uadd":
      return +v;
    case "usub":
      return -v;
    default:
      throw new Error(`unexpected unary op: ${op}`);
  }
}
function interpretCompare({ left, right, op }, ctx) {
  const l = interpret(left, ctx);
  const r = interpret(right, ctx);
  return doCompare(l, r, op);
}
async function interpretCompareAsync({ left, right, op }, ctx) {
  const l = await interpretAsync(left, ctx);
  const r = await interpretAsync(right, ctx);
  return doCompare(l, r, op);
}
function doCompare(l, r, op) {
  switch (op) {
    case "eq":
      return l === r;
    case "neq":
      return l !== r;
    case "lte":
      return l < r;
    case "le":
      return l <= r;
    case "gt":
      return l > r;
    case "gte":
      return l >= r;
    case "in":
      return r.includes(l);
    case "nin":
      return !r.includes(l);
    default:
      throw new Error(`unexpected compare op: ${op}`);
  }
}
/**
 * https://vuejs.org/api/render-function.html#h
 * https://vuejs.org/api/render-function.html#withmodifiers
 */
function interpretProps(props, ctx) {
  if (!props) {
    return props;
  }
  return Object.entries(props).reduce((acc, [rawKey, rawVal]) => {
    const keyParts = rawKey.split(",");
    if (!keyParts.length) {
      throw new Error(`invalid key: ${rawKey}`);
    }
    let [key, ...modifiers] = keyParts;
    let val = rawVal;
    // if key starts with on, it's an event listener
    if (key.match(/^on[A-Z]/)) {
      let handler = async (evt) => {
        const newCtx = new Scope(ctx.component);
        newCtx.locals = new Map(ctx.locals);
        newCtx.locals.set("$event", evt);
        return await interpretAsync(rawVal, newCtx);
      };
      // if multiple parts, it was a tuple. use first part as key, rest as modifiers
      if (modifiers.length) {
        handler = withModifiers(handler, modifiers);
      }
      acc[key] = handler;
    } else {
      // otherwise just use raw value for key
      // and evaluate the val expression
      acc[key] = interpret(val, ctx);
    }
    return acc;
  }, {});
}
/**
 * utils
 */
function queryObject(obj, query) {
  return query.split(".").reduce((a, b) => a[b], obj);
}
function transformValues(obj, transform) {
  if (!obj) {
    return obj;
  }
  return Object.entries(obj).reduce(
    (acc, [key, val]) => ({
      ...acc,
      [key]: transform(val),
    }),
    {}
  );
}
async function transformValuesAsync(obj, transform) {
  if (!obj) {
    return obj;
  }
  return Object.entries(obj).reduce(
    async (acc, [key, val]) => ({
      ...(await acc),
      [key]: await transform(val),
    }),
    Promise.resolve({})
  );
}
