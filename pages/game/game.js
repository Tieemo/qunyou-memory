const config = require('../../config/config');
const gameCore = require('../../utils/game');
const storage = require('../../utils/storage');

const COLS = 4;

// 回合反馈文案与样式
function feedbackOf(res, combo) {
  if (res.match) {
    if (res.pairType === 'good') {
      return {
        text: combo >= 2 ? '好人配对 连击×' + combo + '  +1' : '好人配对  +1',
        cls: 'fb-good',
      };
    }
    return { text: '神人现身  0（留场）', cls: 'fb-trap' };
  }
  if (res.pairType === null) return { text: '好神混杂  -1', cls: 'fb-bad' };
  return res.pairType === 'good'
    ? { text: '好人错过  0', cls: 'fb-zero' }
    : { text: '神人相冲  -2', cls: 'fb-bad' };
}

Page({
  data: {
    backImg: config.BACK_IMG,
    diffName: '',
    rows: [],
    upMap: {},
    matchedMap: {},
    shakeMap: {},
    score: 0,
    turn: 0,
    matchedPairs: 0,
    totalPairs: 0,
    combo: 0,
    feedback: '翻开两张牌，开始游戏',
    feedbackCls: '',
    floats: [],
    locked: false,
    best: null,
    showEnd: false,
    endScore: 0,
    endTurns: 0,
    endUnlocks: [],
    endUnlockTotal: 0,
    endTotalCards: 0,
    endIsNew: false,
  },

  onLoad(options) {
    this.diffKey = (options && options.diff) || config.DEFAULT_DIFFICULTY;
    this.floatSeq = 0;
    this.timers = [];
    this.newUnlocks = [];
    const d = config.getDifficulty(this.diffKey);
    this.setData({ diffName: d.name });
    this.startRound();
  },

  onUnload() {
    this.clearTimers();
  },

  later(fn, ms) {
    const id = setTimeout(fn, ms);
    this.timers.push(id);
    return id;
  },

  clearTimers() {
    (this.timers || []).forEach(clearTimeout);
    this.timers = [];
  },

  startRound() {
    this.clearTimers();
    const pairs = gameCore.samplePairs(this.diffKey);
    this.core = gameCore.createGame({ pairs: pairs });
    this.newUnlocks = [];
    this.setData({
      rows: this.buildRows(this.core.state.cards),
      upMap: {},
      matchedMap: {},
      shakeMap: {},
      score: 0,
      turn: 0,
      matchedPairs: 0,
      totalPairs: this.core.state.totalPairs,
      combo: 0,
      feedback: '翻开两张牌，开始游戏',
      feedbackCls: '',
      floats: [],
      locked: false,
      showEnd: false,
      best: storage.getBest(),
    });
  },

  buildRows(cards) {
    const rows = [];
    for (let i = 0; i < cards.length; i += COLS) {
      rows.push(
        cards.slice(i, i + COLS).map(function (c) {
          return {
            key: c.key,
            id: c.id,
            type: c.type,
            img: config.cardImg(c.id, c.type),
          };
        })
      );
    }
    return rows;
  },

  onCardTap(e) {
    if (this.data.locked || !this.core) return;
    const key = Number(e.currentTarget.dataset.key);
    const res = this.core.flip(key);
    if (!res) return;

    const upMap = Object.assign({}, this.data.upMap);
    upMap[key] = true;

    if (res.kind === 'flip') {
      this.setData({ upMap: upMap });
      return;
    }

    // 本回合结算
    const combo = res.match && res.pairType === 'good' ? this.data.combo + 1 : 0;
    const fb = feedbackOf(res, combo);
    this.pushFloat(res.delta);
    if (res.delta < 0) this.vibrate();
    this.setData({
      upMap: upMap,
      locked: true,
      turn: res.turn,
      score: res.score,
      matchedPairs: this.core.state.matchedPairs,
      combo: combo,
      feedback: fb.text,
      feedbackCls: fb.cls,
    });

    const k1 = res.a.key;
    const k2 = res.b.key;

    if (res.match) {
      this.later(() => {
        const matchedMap = Object.assign({}, this.data.matchedMap);
        matchedMap[k1] = true;
        matchedMap[k2] = true;
        this.setData({ matchedMap: matchedMap });
        if (res.unlockId && storage.unlockCard(res.unlockId)) {
          this.newUnlocks.push({
            id: res.unlockId,
            type: res.pairType,
            img: config.cardImg(res.unlockId, res.pairType),
          });
        }
        if (res.over) {
          this.later(() => this.showEnd(), 750);
        } else {
          this.setData({ locked: false });
        }
      }, 480);
    } else {
      const shakeMap = Object.assign({}, this.data.shakeMap);
      shakeMap[k1] = true;
      shakeMap[k2] = true;
      this.setData({ shakeMap: shakeMap });
      this.later(() => {
        const up = Object.assign({}, this.data.upMap);
        const sh = Object.assign({}, this.data.shakeMap);
        delete up[k1];
        delete up[k2];
        delete sh[k1];
        delete sh[k2];
        this.setData({ upMap: up, shakeMap: sh, locked: false });
      }, 720);
    }
  },

  pushFloat(delta) {
    const seq = ++this.floatSeq;
    const item = {
      key: seq,
      text: delta > 0 ? '+' + delta : String(delta),
      cls: delta > 0 ? 'plus' : delta < 0 ? 'minus' : 'zero',
    };
    const floats = this.data.floats.concat(item);
    this.setData({ floats: floats });
    this.later(() => {
      this.setData({ floats: this.data.floats.filter(f => f.key !== seq) });
    }, 900);
  },

  vibrate() {
    try {
      if (wx.vibrateShort) wx.vibrateShort({ type: 'light' });
    } catch (e) {}
  },

  showEnd() {
    const score = this.core.state.score;
    const bestRes = storage.saveBest(score);
    const unlocks = storage.getUnlocks();
    this.setData({
      showEnd: true,
      locked: true,
      endScore: score,
      endTurns: this.core.state.turn,
      endUnlocks: this.newUnlocks,
      endUnlockTotal: Object.keys(unlocks).length,
      endTotalCards: config.FACE_CARDS.length + config.TRAP_CARDS.length,
      endIsNew: bestRes.isNew,
      best: bestRes.best,
    });
  },

  onRestart() {
    this.startRound();
  },

  onBackHome() {
    wx.navigateBack({
      fail() {
        wx.reLaunch({ url: '/pages/index/index' });
      },
    });
  },

  onOpenCollection() {
    wx.navigateTo({ url: '/pages/collection/collection' });
  },
});
