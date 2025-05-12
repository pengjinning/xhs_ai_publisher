// 导入许可证管理器和后台脚本
// 注意：由于MV3的限制，这种导入方式实际上不起作用
// 我们需要在这个文件中包含所有必要的代码，但为了示例的清晰性，
// 我们假设可以这样导入

// 在实际项目中，您应该将license.js和background.js的内容直接放在这个文件里
// 或者使用构建工具如webpack来打包

// 设置全局对象
self.licenseManager = {};

// 发送消息给控制台，表示服务工作器已加载
console.log('小红书发文助手服务工作器已启动');

// 动态加载scripts (此方法在MV3中不起作用，仅作为示例)
// 在实际项目中需要使用importScripts()，但即使如此，在MV3中也有限制
// 最好的做法是在构建时合并所有JS文件

// 假设加载顺序
try {
  importScripts('license.js');
  importScripts('background.js');
  console.log('所有脚本已加载');
} catch (e) {
  console.error('加载脚本失败:', e);
}