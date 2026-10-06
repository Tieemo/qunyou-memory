// 游戏纯逻辑核心：不依赖 wx，可在 Node/QuickJS 中仿真测试。
// 规则（固定，禁止改动）：
//   相同好人 +1 留场 / 相同神人 0 留场 / 不同好人 0 盖回 / 好神混杂 -1 盖回 / 不同神人 -2 盖回
//   图鉴：翻到某卡第一张后 UNLOCK_WINDOW 个回合内配对成功 → 解锁
const { SCORE, UNLOCK_WINDOW, FACE_CARDS, TRAP_CARDS, getDifficulty } = require('../config/config');

function shuffle(arr, rng) {
  const r = rng || Math.random;
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    const t = arr[i];
    arr[i] = arr[j];
    arr[j] = t;
  }
  return arr;
}

// 两张牌结算（规则表）
function evaluatePair(a, b) {
  if (a.id === b.id) {
    return a.type === 'good'
      ? { match: true, delta: SCORE.GOOD_PAIR }
      : { match: true, delta: SCORE.TRAP_PAIR };
  }
  if (a.type !== b.type) return { match: false, delta: SCORE.MIXED_MISS };
  return a.type === 'good'
    ? { match: false, delta: SCORE.GOOD_MISS }
    : { match: false, delta: SCORE.TRAP_MISS };
}

// 按难度从卡池抽样出若干对（神人占比随难度提升）
function samplePairs(diffKey, rng) {
  const d = getDifficulty(diffKey);
  const r = rng || Math.random;
  const trapCount = Math.min(
    TRAP_CARDS.length,
    Math.max(1, Math.round(d.pairs * d.trapRatio))
  );
  const faces = shuffle(FACE_CARDS.slice(), r).slice(0, d.pairs - trapCount);
  const traps = shuffle(TRAP_CARDS.slice(), r).slice(0, trapCount);
  return traps.map(function (id) { return { id: id, type: 'trap' }; })
    .concat(faces.map(function (id) { return { id: id, type: 'good' }; }));
}

// 创建一局游戏。
// opts:
//   pairs: [{id, type}] 对子列表（与 deck 二选一）
//   deck : [{id, type}] 已展开的牌堆（每张出现两次，顺序即牌面顺序；测试用，不走洗牌）
//   rng  : 随机源
function createGame(opts) {
  opts = opts || {};
  const rng = opts.rng || Math.random;
  let deck;
  if (opts.deck) {
    deck = opts.deck.slice();
  } else {
    deck = [];
    (opts.pairs || []).forEach(function (p) {
      deck.push({ id: p.id, type: p.type });
      deck.push({ id: p.id, type: p.type });
    });
    shuffle(deck, rng);
  }

  const cards = deck.map(function (c, i) {
    return { key: i, id: c.id, type: c.type, state: 'down' };
  });

  const state = {
    cards: cards,
    turn: 0, // 已完成回合数（每回合翻 2 张）
    score: 0,
    matchedPairs: 0,
    totalPairs: cards.length / 2,
    firstRevealTurn: {}, // 卡 id -> 本局首次翻到它的回合
    unlockedThisGame: [], // 本局满足“3回合内”判定的新解锁卡 id
    flippedKeys: [], // 当前回合已翻开的 key
    over: false,
  };

  function currentTurn() {
    return state.turn + 1;
  }

  function canFlip(key) {
    const c = cards[key];
    return !!c && c.state === 'down' && state.flippedKeys.length < 2 && !state.over;
  }

  // 翻牌。返回值：
  //   { kind: 'flip', card }                       翻开第一张，回合未结束
  //   { kind: 'turn', turn, a, b, match, delta, score, unlockId, over, pairType }
  //                                                翻开第二张，本回合已结算
  //   null                                         该牌不可翻
  function flip(key) {
    if (!canFlip(key)) return null;
    const c = cards[key];
    c.state = 'up';
    if (state.firstRevealTurn[c.id] === undefined) {
      state.firstRevealTurn[c.id] = currentTurn();
    }
    state.flippedKeys.push(c.key);

    if (state.flippedKeys.length < 2) {
      return { kind: 'flip', card: c };
    }

    // 第二张落下：本回合结算
    state.turn = currentTurn();
    const a = cards[state.flippedKeys[0]];
    const b = c;
    const ev = evaluatePair(a, b);

    let unlockId = null;
    if (ev.match) {
      a.state = 'matched';
      b.state = 'matched';
      state.matchedPairs += 1;
      const t0 = state.firstRevealTurn[a.id];
      if (t0 !== undefined && state.turn - t0 <= UNLOCK_WINDOW) {
        unlockId = a.id;
        if (state.unlockedThisGame.indexOf(a.id) === -1) {
          state.unlockedThisGame.push(a.id);
        }
      }
      if (state.matchedPairs >= state.totalPairs) state.over = true;
    } else {
      a.state = 'down';
      b.state = 'down';
    }
    state.score += ev.delta;
    state.flippedKeys = [];

    return {
      kind: 'turn',
      turn: state.turn,
      a: a,
      b: b,
      match: ev.match,
      delta: ev.delta,
      score: state.score,
      unlockId: unlockId,
      over: state.over,
      pairType: a.id === b.id ? a.type : null,
    };
  }

  return {
    state: state,
    flip: flip,
    canFlip: canFlip,
    evaluatePair: evaluatePair,
  };
}

module.exports = {
  shuffle: shuffle,
  evaluatePair: evaluatePair,
  samplePairs: samplePairs,
  createGame: createGame,
  UNLOCK_WINDOW: UNLOCK_WINDOW,
};
