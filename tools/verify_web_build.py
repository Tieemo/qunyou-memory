# -*- coding: utf-8 -*-
"""验证 web/index.html 构建产物：抽出内联的 core bundle，
在 QuickJS 里跑一遍规则表与图鉴判定，确认打包过程没有破坏逻辑。"""
import json
import os
import re
import sys

import quickjs

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")

fails = []


def check(name, cond, detail=""):
    print("[%s] %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        fails.append(name)


def main():
    with open(HTML, "r", encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"<script>\n(window\.__web_modules.*?)</script>", html, re.S)
    assert m, "未找到 core bundle"
    bundle = m.group(1)

    ctx = quickjs.Context()
    ctx.eval("var window = globalThis;")
    ctx.eval(bundle)
    ctx.eval(
        """
        function __deck(pairs){
          var d = [];
          pairs.forEach(function(p){ d.push({id:p[0],type:p[1]}); d.push({id:p[0],type:p[1]}); });
          return d;
        }
        function __play(g, ids){
          // 依次翻出 ids（按 id 找未翻开的物理牌），返回最后一次结算
          var out = null;
          ids.forEach(function(cid){
            for (var i = 0; i < g.state.cards.length; i++){
              var c = g.state.cards[i];
              if (c.id === cid && c.state === 'down'){
                var r = g.flip(c.key);
                if (r && r.kind === 'turn') out = r;
                break;
              }
            }
          });
          return out;
        }
        """
    )

    # 规则表
    cases = [
        ('A', 'good', 'A', 'good', True, 1),
        ('T', 'trap', 'T', 'trap', True, 0),
        ('A', 'good', 'B', 'good', False, 0),
        ('A', 'good', 'T', 'trap', False, -1),
        ('T', 'trap', 'S', 'trap', False, -2),
    ]
    for a_id, a_t, b_id, b_t, mch, delta in cases:
        r = json.loads(
            ctx.eval(
                "JSON.stringify(window.GameCore.evaluatePair({id:'%s',type:'%s'},{id:'%s',type:'%s'}))"
                % (a_id, a_t, b_id, b_t)
            )
        )
        check("规则 %s+%s" % (a_t, b_t), r["match"] == mch and r["delta"] == delta, str(r))

    # 图鉴判定：间隔 3 解锁 / 间隔 4 不解锁
    ctx.eval("var g1 = window.GameCore.createGame({deck: __deck([['A','good'],['B','good'],['C','good'],['D','good']])});")
    ctx.eval("__play(g1, ['A','B','C','D','B','C'])")
    r = json.loads(ctx.eval("JSON.stringify(__play(g1, ['A','A']))"))
    check("网页包 间隔=3 解锁", r["unlockId"] == "A", str(r))

    ctx.eval("var g2 = window.GameCore.createGame({deck: __deck([['A','good'],['B','good'],['C','good'],['D','good']])});")
    ctx.eval("__play(g2, ['A','B','C','D','B','C','B','D'])")
    r = json.loads(ctx.eval("JSON.stringify(__play(g2, ['A','A']))"))
    check("网页包 间隔=4 不解锁", r["unlockId"] is None, str(r))

    print()
    if fails:
        print("FAILED: %d 项" % len(fails))
        sys.exit(1)
    print("WEB BUILD VERIFIED")


if __name__ == "__main__":
    main()
