const config = require('../../config/config');
const storage = require('../../utils/storage');

Page({
  data: {
    backImg: config.BACK_IMG,
    heroFace: '',
    heroTrap: '',
    best: null,
    diffList: [],
  },

  onLoad() {
    const diffs = Object.keys(config.DIFFICULTY).map(function (key) {
      const d = config.DIFFICULTY[key];
      return {
        key: d.key,
        name: d.name,
        desc: d.desc,
        trapPercent: Math.round(d.trapRatio * 100),
      };
    });
    this.setData({
      diffList: diffs,
      heroFace: config.faceImg(config.FACE_CARDS[0]),
      heroTrap: config.trapImg(config.TRAP_CARDS[0]),
    });
  },

  onShow() {
    this.setData({ best: storage.getBest() });
  },

  onStart(e) {
    const key = e.currentTarget.dataset.key;
    wx.navigateTo({ url: '/pages/game/game?diff=' + key });
  },

  onOpenCollection() {
    wx.navigateTo({ url: '/pages/collection/collection' });
  },
});
