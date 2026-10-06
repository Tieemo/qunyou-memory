// 本地持久化：图鉴解锁状态 + 历史最高分
const KEY_UNLOCK = 'qy_unlock_v1';
const KEY_BEST = 'qy_best_v1';

function getUnlocks() {
  try {
    const v = wx.getStorageSync(KEY_UNLOCK);
    if (v && typeof v === 'object' && !Array.isArray(v)) return v;
  } catch (e) {}
  return {};
}

function isUnlocked(id) {
  return !!getUnlocks()[id];
}

// 解锁一张卡；已解锁返回 false，新解锁返回 true
function unlockCard(id) {
  const u = getUnlocks();
  if (u[id]) return false;
  u[id] = Date.now();
  try {
    wx.setStorageSync(KEY_UNLOCK, u);
  } catch (e) {}
  return true;
}

function getBest() {
  try {
    const v = wx.getStorageSync(KEY_BEST);
    if (typeof v === 'number' && !isNaN(v)) return v;
  } catch (e) {}
  return null;
}

// 保存最高分；返回 { best, isNew }
function saveBest(score) {
  const prev = getBest();
  if (prev === null || score > prev) {
    try {
      wx.setStorageSync(KEY_BEST, score);
    } catch (e) {}
    return { best: score, isNew: true };
  }
  return { best: prev, isNew: false };
}

function ensureDefaults() {
  getUnlocks();
  getBest();
}

module.exports = {
  getUnlocks,
  isUnlocked,
  unlockCard,
  getBest,
  saveBest,
  ensureDefaults,
};
