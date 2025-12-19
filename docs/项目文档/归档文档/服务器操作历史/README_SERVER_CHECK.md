# 检查服务器视频数据指南

## 问题说明

您说得对！我一直在操作**本地数据库**，但实际需要检查**服务器上的数据库**。

## 快速检查方法

### 方法1：直接在服务器上运行（推荐）

SSH连接到服务器后，运行：

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate
python3 << 'EOF'
from bilibili_models import get_bilibili_session, BilibiliVideo

session = get_bilibili_session()
video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()

if video:
    print(f"✅ 找到视频:")
    print(f"BV号: {video.bvid}")
    print(f"标题: {video.title}")
    print(f"播放量: {video.play:,}")
    print(f"播放量(格式化): {video.play_formatted}")
    print(f"更新时间: {video.updated_at}")
    
    if video.play == 5530:
        print(f"\n⚠️  播放量是5530，需要更新！")
    elif video.play == 162712:
        print(f"\n✅ 播放量已更新为162,712")
else:
    print("❌ 未找到视频")

session.close()
EOF
```

### 方法2：使用远程检查脚本

在本地运行：

```bash
# 设置服务器信息
export SERVER_HOST="essay.gradmotion.com"  # 或您的服务器IP
export SERVER_USER="root"  # 或您的SSH用户名

# 检查服务器数据
./scripts/check_server_video_simple.sh $SERVER_HOST $SERVER_USER
```

### 方法3：在服务器上更新播放量

SSH连接到服务器后：

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate

# 更新逐际动力的所有视频播放量
python3 scripts/update_video_play_counts.py --uids 1172054289 --force

# 或者只更新单个视频
python3 scripts/fetch_single_video.py BV1L8qEBKEFW --uid 1172054289
```

## 服务器信息

根据部署脚本，服务器配置应该是：
- **服务器地址**: `essay.gradmotion.com` 或您的服务器IP
- **应用目录**: `/srv/EmbodiedPulse2026`
- **SSH用户**: 通常是 `root` 或您配置的用户

## 重要提示

⚠️ **本地数据库 vs 服务器数据库**

- **本地数据库**: `/Users/dong/Documents/Cursor/Embodied Pulse/bilibili.db`
- **服务器数据库**: `/srv/EmbodiedPulse2026/bilibili.db` 或 PostgreSQL

所有更新操作都应该在**服务器上**执行，而不是本地！

## 下一步

请提供：
1. 服务器SSH连接信息（如果需要我帮您创建连接脚本）
2. 或者直接在服务器上运行上述检查命令，告诉我结果

