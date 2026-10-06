const config = require('../../config/config');
const storage = require('../../utils/storage');

Page({
  data: {
    backImg: config.BACK_IMG,
    list: [],
    unlockedCount: 0,
    total: 0,
  },

  onShow() {
    this.refresh();
  },

  refresh() {
    const unlocks = storage.getUnlocks();
    const list = [];
    config.FACE_CARDS.forEach(function (id) {
      list.push(buildItem(id, 'good', unlocks));
    });
    config.TRAP_CARDS.forEach(function (id) {
      list.push(buildItem(id, 'trap', unlocks));
    });
    let count = 0;
    list.forEach(function (i) {
      if (i.unlocked) count++;
    });
    this.setData({
      list: list,
      unlockedCount: count,
      total: list.length,
    });
  },
});

function buildItem(id, type, unlocks) {
  const unlocked = !!unlocks[id];
  return {
    id: id,
    type: type,
    name: unlocked ? id : '???',
    img: config.cardImg(id, type),
    unlocked: unlocked,
    typeName: type === 'good' ? '好人' : '神人',
  };
}
