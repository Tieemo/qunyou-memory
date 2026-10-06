# -*- coding: utf-8 -*-
"""把小程序的逻辑模块（config/cards.js、config/config.js、utils/game.js）原样打包，
注入 web/template.html，生成仓库根目录的 index.html（Gitee Pages 入口）。
规则代码只有一份（utils/game.js），小程序与网页共用，改规则后重跑本脚本即可。"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "web", "template.html")
OUTPUT = os.path.join(ROOT, "index.html")
ENTRY = "utils/game.js"

sys.stdout.reconfigure(encoding="utf-8")


def find_requires(src):
    return re.findall(r"require\('([^']+)'\)", src)


def resolve_require(cur_rel, dep):
    base = os.path.dirname(cur_rel).split("/")
    for part in dep.split("/"):
        if part == ".":
            continue
        if part == "..":
            base.pop()
        else:
            base.append(part)
    return "/".join(base) + ".js"


def load(rel):
    path = os.path.join(ROOT, *rel.split("/"))
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def wrap_module(src, rel, registry):
    """生成浏览器 IIFE 模块，挂到 window.__web_modules[rel]。"""
    resolved = {d: resolve_require(rel, d) for d in find_requires(src)}
    for dep_rel in resolved.values():
        if dep_rel not in registry:
            wrap_module(load(dep_rel), dep_rel, registry)
    dep_map = json.dumps(resolved, ensure_ascii=False)
    body = (
        "window.__web_modules = window.__web_modules || {};\n"
        "window.__web_modules[%s] = (function () {\n"
        "  var module = { exports: {} };\n"
        "  var exports = module.exports;\n"
        "  var require = function (p) { return window.__web_modules[%s[p]]; };\n"
        % (json.dumps(rel), dep_map)
    )
    body += src
    body += "\n  return module.exports;\n})();"
    registry[rel] = body


def main():
    registry = {}
    wrap_module(load(ENTRY), ENTRY, registry)

    bundle = "\n".join(registry[rel] for rel in sorted(registry))
    bundle += (
        "\nwindow.Cards = window.__web_modules['config/cards.js'];"
        "\nwindow.Config = window.__web_modules['config/config.js'];"
        "\nwindow.GameCore = window.__web_modules['utils/game.js'];"
    )
    assert "</script" not in bundle, "源码中不允许出现 </script"

    with open(TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()
    assert "<!--__CORE_BUNDLE__-->" in html, "模板缺少占位符"
    html = html.replace("<!--__CORE_BUNDLE__-->", "<script>\n" + bundle + "\n</script>")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("已生成 %s（%.1f KB）" % (os.path.relpath(OUTPUT, ROOT), len(html.encode("utf-8")) / 1024))


if __name__ == "__main__":
    main()
