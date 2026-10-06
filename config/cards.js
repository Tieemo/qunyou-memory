// 卡池配置：文件名（不含扩展名）即卡牌 ID，新增卡只需把图片放进对应目录并在下列数组加名字。
// 原始大图在 好人群友卡牌卡面/ 神人群友卡牌卡面/ 卡背/，由 tools/compress_assets.py 压缩生成 assets/ 下的 jpg。
const BACK_IMG = '/assets/back.jpg';

const FACE_CARDS = [
  'Franny',
  'wada大王',
  '一只鱼傻了吧唧',
  '中药',
  '冰糖',
  '土豆',
  '在羽',
  '墨海波澜一笔生',
  '好吉咪',
  '妖妖',
  '小楼一夜恨春雨',
  '年',
  '张螂',
  '悦瑛',
  '橙子',
  '白写',
  '耶耶',
  '谢清玄',
  '超级无敌大S派',
  '雲',
  '鸩',
  '鹅',
  '🍐',
];

const TRAP_CARDS = [
  'Freeze',
  'Q群管理',
  'duoduo&史迪奇',
  'wxl',
  '判刑管子',
  '悦',
  '熊哥',
  '猫哥',
  '玩动',
];

module.exports = {
  BACK_IMG,
  FACE_CARDS,
  TRAP_CARDS,
};
