// 全局配置：卡池(cards.js 自动生成) + 计分规则常量 + 难度
// 注意：计分规则与图鉴判定窗口为固定规则，禁止改动。
const cards = require('./cards');

// ---------- 计分规则（规则表，禁止改动） ----------
const SCORE = {
  GOOD_PAIR: 1, // 相同好人卡 → 留在场上明牌，+1分
  TRAP_PAIR: 0, // 相同神人卡 → 留在场上明牌，0分
  GOOD_MISS: 0, // 不同好人卡 → 盖回，0分
  MIXED_MISS: -1, // 好人+神人 → 盖回，-1分
  TRAP_MISS: -2, // 不同神人卡 → 盖回，-2分
};

// ---------- 图鉴判定（禁止改动） ----------
// 翻到某卡第一张后，自己 UNLOCK_WINDOW 个回合内翻到第二张配对成功 → 解锁
const UNLOCK_WINDOW = 3;

// ---------- 难度（卡池大小） ----------
const DIFFICULTY = {
  easy: {
    key: 'easy',
    name: '简单',
    pairs: 8, // 4×4
    trapRatio: 0.25,
    desc: '4×4 牌阵 · 8 对',
  },
  normal: {
    key: 'normal',
    name: '标准',
    pairs: 10, // 4×5
    trapRatio: 0.35,
    desc: '4×5 牌阵 · 10 对',
  },
  hard: {
    key: 'hard',
    name: '困难',
    pairs: 12, // 4×6
    trapRatio: 0.45,
    desc: '4×6 牌阵 · 12 对',
  },
};
const DEFAULT_DIFFICULTY = 'normal';

function getDifficulty(key) {
  return DIFFICULTY[key] || DIFFICULTY[DEFAULT_DIFFICULTY];
}

// ---------- 图片路径（包内相对路径，禁止写死绝对路径） ----------
function faceImg(id) {
  return '/assets/face/' + id + '.jpg';
}
function trapImg(id) {
  return '/assets/trap/' + id + '.jpg';
}
function cardImg(id, type) {
  return type === 'trap' ? trapImg(id) : faceImg(id);
}

module.exports = {
  // 卡池
  BACK_IMG: cards.BACK_IMG,
  FACE_CARDS: cards.FACE_CARDS,
  TRAP_CARDS: cards.TRAP_CARDS,
  // 规则
  SCORE,
  UNLOCK_WINDOW,
  // 难度
  DIFFICULTY,
  DEFAULT_DIFFICULTY,
  getDifficulty,
  // 路径
  faceImg,
  trapImg,
  cardImg,
};
