// 重置具身运势签状态
// 在浏览器控制台执行此代码

console.log('开始清除抽签记录...');

// 清除所有抽签相关的localStorage
localStorage.removeItem('fortuneDate');
localStorage.removeItem('fortuneMessage');
localStorage.removeItem('fortuneTimestamp');
localStorage.removeItem('fortuneCategory');

console.log('✅ 抽签记录已清除！');
console.log('刷新页面后即可重新抽签');

// 自动刷新页面
setTimeout(() => {
    location.reload();
}, 500);
