const storage = require('./utils/storage');

App({
  onLaunch() {
    // 首次启动初始化存储，避免旧数据缺省值问题
    storage.ensureDefaults();
  },
  globalData: {}
});
