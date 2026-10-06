# -*- coding: utf-8 -*-
"""用 QuickJS 加载 utils/game.js（连同 config），仿真验证：
1. 计分规则表（5 种两牌组合）
2. 图鉴“3 回合内”判定（边界 3 解锁 / 4 不解锁 / 当回合解锁 / 神人卡解锁）
3. 随机完整对局 200 局：每回合与 Python 独立复算比对
"""
import json
import os
import random
import re
import sys

import quickjs

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAILS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("[%s] %s %s" % (status, name, detail))
    if not cond:
        FAILS.append(name)


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


def load_module(ctx, registry, rel):
    """把项目内 CommonJS 模块加载进 JS 上下文，挂在 __registry[rel]。"""
    if rel in registry:
        return
    path = os.path.join(ROOT, *rel.split("/"))
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    resolved = {d: resolve_require(rel, d) for d in find_requires(src)}
    for dep_rel in resolved.values():
        load_module(ctx, registry, dep_rel)
    wrapper = (
        "var __registry = __registry || {};"
        "__registry[%s] = (function(){"
        " var __m = {exports:{}};"
        " var module = __m, exports = __m.exports;"
        " var require = function(p){ return __registry[%s[p]]; };"
        "\n%s\n return __m.exports; })();"
        % (json.dumps(rel), json.dumps(resolved), src)
    )
    ctx.eval(wrapper)
    registry[rel] = True


HELPERS = """
var __g = null;
function __newGame(deck){ __g = __createGame({deck: deck}); }
function __flip(k){ var r = __g.flip(k); return r ? JSON.stringify(r) : 'null'; }
function __canFlip(k){ return __g.canFlip(k); }
function __state(){
  var s = __g.state;
  return JSON.stringify({
    turn: s.turn, score: s.score,
    matchedPairs: s.matchedPairs, totalPairs: s.totalPairs,
    unlockedThisGame: s.unlockedThisGame, over: s.over,
    cards: s.cards.map(function(c){ return {key:c.key,id:c.id,type:c.type,state:c.state}; })
  });
}
function __samplePairs(diff, seed){
  var r = (function(seed){ var x = seed; return function(){ x = (x*1103515245+12345)%2147483648; return x/2147483648; }; })(seed);
  return JSON.stringify(__sample(diff, r));
}
function __evalPair(a, b){ return JSON.stringify(__evaluatePair(a, b)); }
"""


def build_context():
    ctx = quickjs.Context()
    registry = {}
    load_module(ctx, registry, "utils/game.js")
    ctx.eval(
        "var __createGame = __registry['utils/game.js'].createGame;"
        "var __sample = __registry['utils/game.js'].samplePairs;"
        "var __evaluatePair = __registry['utils/game.js'].evaluatePair;"
    )
    ctx.eval(HELPERS)
    return ctx


def js(ctx, code):
    v = ctx.eval(code)
    if isinstance(v, str):
        return json.loads(v)
    return v


def expected_delta(a, b):
    """Python 独立复算规则表"""
    if a["id"] == b["id"]:
        return (True, 1 if a["type"] == "good" else 0)
    if a["type"] != b["type"]:
        return (False, -1)
    return (False, 0 if a["type"] == "good" else -2)


def deck_of(pairs):
    """pairs: [(id, type)]；展开成每张两次"""
    d = []
    for cid, t in pairs:
        d.append({"id": cid, "type": t})
        d.append({"id": cid, "type": t})
    return d


def key_of(state, cid, exclude=()):
    for c in state["cards"]:
        if c["id"] == cid and c["key"] not in exclude and c["state"] == "down":
            return c["key"]
    raise RuntimeError("card not found: %s" % cid)


def play_turn(ctx, state, cid1, cid2):
    """连续翻两张牌（第二卷与第一卷不是同一张物理牌），返回第二张的结算结果"""
    r1 = js(ctx, "__flip(%d)" % key_of(state, cid1))
    assert r1 and r1["kind"] == "flip", r1
    state2 = refresh(ctx)
    r2 = js(ctx, "__flip(%d)" % key_of(state2, cid2, exclude=(r1["card"]["key"],)))
    return r2


def refresh(ctx):
    return js(ctx, "__state()")


def main():
    ctx = build_context()

    # ---------- 1. 规则表 ----------
    print("== 计分规则表 ==")
    cases = [
        ({"id": "A", "type": "good"}, {"id": "A", "type": "good"}, True, 1, "相同好人 +1"),
        ({"id": "T", "type": "trap"}, {"id": "T", "type": "trap"}, True, 0, "相同神人 0"),
        ({"id": "A", "type": "good"}, {"id": "B", "type": "good"}, False, 0, "不同好人 0"),
        ({"id": "A", "type": "good"}, {"id": "T", "type": "trap"}, False, -1, "好神混杂 -1"),
        ({"id": "T", "type": "trap"}, {"id": "S", "type": "trap"}, False, -2, "不同神人 -2"),
    ]
    for a, b, m, d, name in cases:
        r = js(ctx, "__evalPair(%s, %s)" % (json.dumps(a), json.dumps(b)))
        check(name, r["match"] == m and r["delta"] == d, str(r))

    # ---------- 2. 图鉴 3 回合判定 ----------
    print("== 图鉴解锁判定 ==")

    # 2a. 同回合翻到第一张并配对 → 解锁
    js(ctx, "__newGame(%s)" % json.dumps(deck_of([("A", "good"), ("B", "good"), ("C", "good")])))
    out = play_turn(ctx, refresh(ctx), "A", "A")
    check("同回合首翻即配对 → 解锁", out["unlockId"] == "A", str(out))

    # 2b. 第1回合翻到A（未配），第4回合配对 → 间隔3 → 解锁
    js(ctx, "__newGame(%s)" % json.dumps(deck_of([("A", "good"), ("B", "good"), ("C", "good"), ("D", "good")])))
    play_turn(ctx, refresh(ctx), "A", "B")    # t1: 首次见 A
    play_turn(ctx, refresh(ctx), "C", "D")    # t2
    play_turn(ctx, refresh(ctx), "B", "C")    # t3
    out = play_turn(ctx, refresh(ctx), "A", "A")  # t4: 间隔 = 3
    check("首翻后第3个回合配对（间隔=3）→ 解锁", out["unlockId"] == "A", str(out))

    # 2c. 第1回合翻到A，第5回合配对 → 间隔4 → 不解锁
    js(ctx, "__newGame(%s)" % json.dumps(deck_of([("A", "good"), ("B", "good"), ("C", "good"), ("D", "good")])))
    play_turn(ctx, refresh(ctx), "A", "B")    # t1
    play_turn(ctx, refresh(ctx), "C", "D")    # t2
    play_turn(ctx, refresh(ctx), "B", "C")    # t3
    play_turn(ctx, refresh(ctx), "B", "D")    # t4
    out = play_turn(ctx, refresh(ctx), "A", "A")  # t5: 间隔 = 4
    check("首翻后第4个回合配对（间隔=4）→ 不解锁", out["unlockId"] is None, str(out))

    # 2d. 神人卡同样可解锁（间隔 2）
    js(ctx, "__newGame(%s)" % json.dumps(deck_of([("T", "trap"), ("S", "trap"), ("B", "good")])))
    play_turn(ctx, refresh(ctx), "T", "S")   # t1 首次见 T（不同神人 → -2 盖回）
    play_turn(ctx, refresh(ctx), "S", "B")   # t2
    out = play_turn(ctx, refresh(ctx), "T", "T")  # t3 间隔 = 2 → 解锁
    check("神人卡 3 回合内配对 → 解锁", out["unlockId"] == "T", str(out))

    # 2e. 翻牌保护：已翻开的牌不能再翻；miss 盖回后可再翻
    js(ctx, "__newGame(%s)" % json.dumps(deck_of([("A", "good"), ("B", "good")])))
    ka = key_of(refresh(ctx), "A")
    r1 = js(ctx, "__flip(%d)" % ka)
    check("第一张翻开", r1 and r1["kind"] == "flip")
    again = js(ctx, "__flip(%d)" % ka)
    check("已翻开的牌不能再翻", again is None)
    st = refresh(ctx)
    r = js(ctx, "__flip(%d)" % key_of(st, "B"))
    check("第二张落下即结算", r and r["kind"] == "turn")
    can_again = js(ctx, "__canFlip(%d)" % key_of(refresh(ctx), "A"))
    check("盖回后可再次翻开的牌", can_again is True)

    # ---------- 3. 随机完整对局 ----------
    print("== 随机对局仿真（200 局） ==")
    rng = random.Random(20261005)
    bad_turns = 0
    for g in range(200):
        diff = rng.choice(["easy", "normal", "hard"])
        pairs = js(ctx, "__samplePairs('%s', %d)" % (diff, rng.randint(1, 2 ** 31 - 1)))
        ids = [p["id"] for p in pairs]
        assert len(ids) == len(set(ids)), "对子 id 重复: %s" % ids
        js(ctx, "__newGame(%s)" % json.dumps(deck_of([(p["id"], p["type"]) for p in pairs])))

        first_reveal = {}
        turn = 0
        score = 0
        matched = 0
        unlocked = []
        guard = 0
        over = False
        while not over:
            guard += 1
            if guard > 2000:
                raise RuntimeError("对局未正常结束")
            st = refresh(ctx)
            downs = [c for c in st["cards"] if c["state"] == "down"]
            assert len(downs) % 2 == 0
            a, b = rng.sample(downs, 2)
            turn += 1
            for c in (a, b):
                if c["id"] not in first_reveal:
                    first_reveal[c["id"]] = turn
            r1 = js(ctx, "__flip(%d)" % a["key"])
            r2 = js(ctx, "__flip(%d)" % b["key"])
            exp_match, exp_delta = expected_delta(a, b)
            if r2["match"] != exp_match or r2["delta"] != exp_delta:
                bad_turns += 1
                print("  计分不一致:", a, b, r2)
                continue
            score += exp_delta
            if exp_match:
                matched += 1
                gap = turn - first_reveal[a["id"]]
                exp_unlock = a["id"] if gap <= 3 else None
                if r2["unlockId"] != exp_unlock:
                    bad_turns += 1
                    print("  解锁不一致:", a["id"], "gap", gap, r2["unlockId"])
                if exp_unlock and exp_unlock not in unlocked:
                    unlocked.append(exp_unlock)
            over = r2["over"]

        fin = refresh(ctx)
        ok = (
            fin["over"] is True
            and fin["turn"] == turn
            and fin["score"] == score
            and fin["matchedPairs"] == fin["totalPairs"] == matched
            and sorted(fin["unlockedThisGame"]) == sorted(unlocked)
        )
        if not ok:
            bad_turns += 1
            print("  终局不一致:", fin, "python:", turn, score, matched, unlocked)

    check("200 局随机对局全部一致（计分/回合/解锁/终局）", bad_turns == 0, "不一致次数=%d" % bad_turns)

    print()
    if FAILS:
        print("FAILED: %d 项" % len(FAILS))
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
