# B站数据问题技术方案和任务清单

## 📋 问题描述

两个页面的视频和播放量都是老数据：
- `https://essay.gradmotion.com/bilibili` - 前端展示页面
- `https://admin123.gradmotion.com/admin/bilibili` - 管理后台页面

## 🔍 数据流分析

### 1. 数据获取流程

```
Bilibili API
    ↓
BilibiliClient.get_all_data()
    ↓
fetch_bilibili_data.py
    ↓
数据库 (bilibili.db)
    ↓
API端点 (/api/bilibili/all, /api/admin/bilibili/videos)
    ↓
前端页面
```

### 2. 数据库配置

**配置位置：** `bilibili_models.py:202`
```python
BILIBILI_DATABASE_URL = os.getenv('BILIBILI_DATABASE_URL', 'sqlite:///./bilibili.db')
```

**潜在问题：**
- 默认使用相对路径 `./bilibili.db`
- 如果工作目录不同，会连接到不同的数据库文件
- 服务器上可能使用了不同的数据库文件

### 3. API端点分析

#### 3.1 `/api/bilibili/all` (前端展示页面)

**代码位置：** `app.py:1228-1400`

**数据来源：** 数据库
- 查询UP主：`session.query(BilibiliUp).filter_by(is_active=True).all()`
- 查询视频：`session.query(BilibiliVideo).filter_by(uid=up.uid, is_deleted=False).order_by(BilibiliVideo.pubdate_raw.desc()).limit(200)`

**字段映射：**
- `play`: `format_number(video.play)` - 实时格式化
- `play_raw`: `video.play or 0`
- `pubdate`: `format_timestamp(video.pubdate_raw)`

**缓存机制：** 5分钟缓存（`CACHE_DURATION = 300`）

#### 3.2 `/api/admin/bilibili/videos` (管理后台)

**代码位置：** `auth_routes.py:2015-2113`

**数据来源：** 数据库
- 查询：`session.query(BilibiliVideo, BilibiliUp).join(BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid)`
- 排序：`order_by(BilibiliVideo.pubdate_raw.desc().nullslast())`

**字段映射：**
- `video.to_dict()` - 使用模型方法
- `play`: `format_number(self.play)` - 实时格式化
- `play_raw`: `self.play`

### 4. 数据更新流程

**代码位置：** `fetch_bilibili_data.py:40-253`

**更新逻辑：**
1. 从API获取数据：`client.get_all_data(uid, video_count=video_count, fetch_all=fetch_all)`
2. 更新UP主信息：`up.name`, `up.fans`, `up.views_count` 等
3. 更新视频信息：
   - 查找或创建：`session.query(BilibiliVideo).filter_by(bvid=bvid).first()`
   - 更新播放量：`if play_raw > 0: video.play = play_raw`（只更新大于0的值）

**潜在问题：**
- 播放量更新条件：`if play_raw > 0` - 如果API返回0，不会更新
- 时间更新：`if pubdate_raw: video.pubdate_raw = pubdate_raw` - 只有非空才更新

## 🔎 排查重点

### 1. 数据库路径问题

**检查项：**
- [ ] 服务器上实际使用的数据库文件路径
- [ ] 环境变量 `BILIBILI_DATABASE_URL` 是否设置
- [ ] 工作目录是否一致
- [ ] 是否存在多个数据库文件

**检查命令：**
```bash
# 检查环境变量
echo $BILIBILI_DATABASE_URL

# 检查.env文件
grep BILIBILI_DATABASE_URL .env

# 检查实际数据库文件
find /srv/EmbodiedPulse2026 -name "bilibili.db" -type f

# 检查Python代码中使用的数据库URL
python3 -c "from bilibili_models import BILIBILI_DATABASE_URL; print(BILIBILI_DATABASE_URL)"
```

### 2. 数据库关联问题

**检查项：**
- [ ] UP主和视频的关联是否正确（`uid`字段）
- [ ] 外键关系是否正常
- [ ] 查询是否使用了正确的关联条件

**检查命令：**
```sql
-- 检查UP主和视频的关联
SELECT u.uid, u.name, COUNT(v.bvid) as video_count
FROM bilibili_ups u
LEFT JOIN bilibili_videos v ON u.uid = v.uid
WHERE u.is_active = true
GROUP BY u.uid, u.name;

-- 检查视频的UP主是否存在
SELECT v.bvid, v.uid, v.title, u.name as up_name
FROM bilibili_videos v
LEFT JOIN bilibili_ups u ON v.uid = u.uid
WHERE v.is_deleted = false
LIMIT 10;
```

### 3. 数据更新问题

**检查项：**
- [ ] 数据抓取脚本是否正常运行
- [ ] 定时任务是否配置正确
- [ ] 播放量是否真的更新了
- [ ] 更新时间戳是否最新

**检查命令：**
```bash
# 检查最近更新的视频
python3 -c "
from bilibili_models import get_bilibili_session, BilibiliVideo
from datetime import datetime, timedelta
session = get_bilibili_session()
recent = session.query(BilibiliVideo).order_by(BilibiliVideo.updated_at.desc()).limit(10).all()
for v in recent:
    print(f'{v.bvid}: {v.title[:30]} - 播放量: {v.play:,} - 更新时间: {v.updated_at}')
session.close()
"

# 检查特定视频的播放量
python3 -c "
from bilibili_models import get_bilibili_session, BilibiliVideo
session = get_bilibili_session()
video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()
if video:
    print(f'BV号: {video.bvid}')
    print(f'标题: {video.title}')
    print(f'播放量: {video.play:,}')
    print(f'更新时间: {video.updated_at}')
else:
    print('视频不存在')
session.close()
"
```

### 4. API查询问题

**检查项：**
- [ ] API查询是否正确使用了数据库
- [ ] 查询条件是否正确
- [ ] 排序是否正确
- [ ] 字段映射是否正确

**检查命令：**
```bash
# 测试API端点
curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 -m json.tool | head -50

# 测试管理后台API
curl -s -H "Authorization: Bearer YOUR_TOKEN" "http://localhost:5001/api/admin/bilibili/videos?page=1&per_page=10" | python3 -m json.tool | head -50
```

## 📝 任务清单

### 阶段1：数据库配置检查

- [ ] **任务1.1：检查服务器数据库路径**
  - 检查环境变量 `BILIBILI_DATABASE_URL`
  - 检查 `.env` 文件配置
  - 检查实际数据库文件位置
  - 检查工作目录

- [ ] **任务1.2：验证数据库连接**
  - 测试数据库连接是否正常
  - 检查数据库文件权限
  - 检查数据库文件大小和修改时间

- [ ] **任务1.3：检查数据库一致性**
  - 检查是否存在多个数据库文件
  - 检查数据抓取脚本使用的数据库
  - 检查API使用的数据库
  - 确保使用同一个数据库文件

### 阶段2：数据完整性检查

- [ ] **任务2.1：检查UP主数据**
  - 检查UP主数量
  - 检查UP主基本信息（名称、粉丝数等）
  - 检查UP主统计数据（视频数、播放量等）
  - 检查最后更新时间

- [ ] **任务2.2：检查视频数据**
  - 检查视频数量
  - 检查视频基本信息（标题、BV号等）
  - 检查视频统计数据（播放量、评论数、收藏数等）
  - 检查发布时间和更新时间

- [ ] **任务2.3：检查数据关联**
  - 检查UP主和视频的关联（`uid`字段）
  - 检查是否有孤立视频（没有对应UP主）
  - 检查是否有UP主没有视频

### 阶段3：数据更新检查

- [ ] **任务3.1：检查数据抓取脚本**
  - 检查脚本是否正常运行
  - 检查脚本使用的数据库路径
  - 检查脚本的更新逻辑
  - 检查脚本的错误处理

- [ ] **任务3.2：检查定时任务**
  - 检查定时任务配置
  - 检查定时任务是否运行
  - 检查定时任务的日志
  - 检查定时任务的执行时间

- [ ] **任务3.3：手动触发数据更新**
  - 手动运行数据抓取脚本
  - 检查更新后的数据
  - 验证播放量是否更新
  - 验证视频列表是否更新

### 阶段4：API检查

- [ ] **任务4.1：检查API查询逻辑**
  - 检查查询条件是否正确
  - 检查排序是否正确
  - 检查字段映射是否正确
  - 检查缓存机制

- [ ] **任务4.2：检查API返回数据**
  - 检查返回的数据格式
  - 检查返回的数据内容
  - 检查播放量字段
  - 检查视频列表

- [ ] **任务4.3：检查前端数据展示**
  - 检查前端API调用
  - 检查前端数据渲染
  - 检查前端缓存机制
  - 检查前端错误处理

### 阶段5：问题修复

- [ ] **任务5.1：修复数据库路径问题**
  - 统一数据库路径配置
  - 使用绝对路径或环境变量
  - 确保所有组件使用同一个数据库

- [ ] **任务5.2：修复数据更新问题**
  - 修复播放量更新逻辑
  - 修复时间更新逻辑
  - 修复数据抓取脚本
  - 修复定时任务配置

- [ ] **任务5.3：修复API查询问题**
  - 修复查询条件
  - 修复排序逻辑
  - 修复字段映射
  - 修复缓存机制

## 🛠️ 诊断脚本

### 脚本1：数据库配置检查

```bash
#!/bin/bash
# scripts/check_bilibili_database_config.sh

echo "=== B站数据库配置检查 ==="
echo ""

# 1. 检查环境变量
echo "1. 环境变量检查"
echo "   BILIBILI_DATABASE_URL: $BILIBILI_DATABASE_URL"
echo ""

# 2. 检查.env文件
echo "2. .env文件检查"
if [ -f .env ]; then
    grep BILIBILI_DATABASE_URL .env || echo "   ⚠️  .env文件中未找到BILIBILI_DATABASE_URL"
else
    echo "   ⚠️  .env文件不存在"
fi
echo ""

# 3. 检查Python代码中的配置
echo "3. Python代码中的配置"
python3 << EOF
import os
from dotenv import load_dotenv
load_dotenv()

from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine
print(f"   数据库URL: {BILIBILI_DATABASE_URL}")

if BILIBILI_DATABASE_URL.startswith('sqlite'):
    db_file = BILIBILI_DATABASE_URL.replace('sqlite:///', '').replace('sqlite:///', '')
    import os
    if os.path.isabs(db_file):
        print(f"   ✅ 使用绝对路径: {db_file}")
    else:
        cwd = os.getcwd()
        abs_path = os.path.join(cwd, db_file)
        print(f"   ⚠️  使用相对路径: {db_file}")
        print(f"   实际路径: {abs_path}")
        if os.path.exists(abs_path):
            size = os.path.getsize(abs_path) / (1024 * 1024)
            mtime = os.path.getmtime(abs_path)
            from datetime import datetime
            print(f"   文件大小: {size:.2f} MB")
            print(f"   修改时间: {datetime.fromtimestamp(mtime)}")
        else:
            print(f"   ❌ 数据库文件不存在")
EOF
```

### 脚本2：数据完整性检查

```bash
#!/bin/bash
# scripts/check_bilibili_data_integrity.sh

echo "=== B站数据完整性检查 ==="
echo ""

python3 << EOF
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from datetime import datetime, timedelta
from sqlalchemy import func

session = get_bilibili_session()

try:
    # 1. 检查UP主数据
    print("1. UP主数据检查")
    ups = session.query(BilibiliUp).filter_by(is_active=True).all()
    print(f"   活跃UP主数量: {len(ups)}")
    
    for up in ups[:5]:  # 只显示前5个
        video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
            uid=up.uid, is_deleted=False
        ).scalar()
        total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
            uid=up.uid, is_deleted=False
        ).scalar() or 0
        
        print(f"   - {up.name} (UID: {up.uid})")
        print(f"     视频数: {video_count} (数据库: {up.videos_count})")
        print(f"     总播放量: {total_views:,} (数据库: {up.views_count:,})")
        print(f"     最后更新: {up.last_fetch_at}")
    
    # 2. 检查视频数据
    print("\n2. 视频数据检查")
    total_videos = session.query(func.count(BilibiliVideo.bvid)).filter_by(
        is_deleted=False
    ).scalar()
    print(f"   总视频数: {total_videos}")
    
    # 检查最近更新的视频
    recent_videos = session.query(BilibiliVideo).filter_by(
        is_deleted=False
    ).order_by(BilibiliVideo.updated_at.desc()).limit(5).all()
    
    print("\n   最近更新的5个视频:")
    for video in recent_videos:
        print(f"   - {video.bvid}: {video.title[:40]}")
        print(f"     播放量: {video.play:,} | 更新时间: {video.updated_at}")
    
    # 3. 检查数据关联
    print("\n3. 数据关联检查")
    orphan_videos = session.query(BilibiliVideo).filter_by(
        is_deleted=False
    ).outerjoin(BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid).filter(
        BilibiliUp.uid == None
    ).count()
    
    print(f"   孤立视频数（没有对应UP主）: {orphan_videos}")
    
    # 4. 检查数据新鲜度
    print("\n4. 数据新鲜度检查")
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)
    
    recent_updates = session.query(func.count(BilibiliVideo.bvid)).filter(
        BilibiliVideo.updated_at >= one_day_ago,
        BilibiliVideo.is_deleted == False
    ).scalar()
    
    print(f"   24小时内更新的视频数: {recent_updates}")
    
finally:
    session.close()
EOF
```

### 脚本3：API测试

```bash
#!/bin/bash
# scripts/test_bilibili_apis.sh

echo "=== B站API测试 ==="
echo ""

# 1. 测试前端API
echo "1. 测试 /api/bilibili/all"
curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print(f\"   成功: 返回 {len(data.get('data', []))} 个UP主\")
    if data.get('data'):
        first = data['data'][0]
        print(f\"   第一个UP主: {first.get('user_info', {}).get('name')}\")
        videos = first.get('videos', [])
        if videos:
            print(f\"   视频数: {len(videos)}\")
            print(f\"   第一个视频播放量: {videos[0].get('play')}\")
else:
    print(f\"   失败: {data.get('message')}\")
"

echo ""
echo "2. 测试管理后台API（需要token）"
echo "   请手动测试: curl -H 'Authorization: Bearer TOKEN' http://localhost:5001/api/admin/bilibili/videos?page=1&per_page=10"
```

## 🎯 预期结果

### 正常情况

1. **数据库配置：**
   - 使用绝对路径或环境变量
   - 所有组件使用同一个数据库文件
   - 数据库文件存在且可访问

2. **数据完整性：**
   - UP主数据完整
   - 视频数据完整
   - 数据关联正确
   - 数据新鲜（24小时内更新）

3. **API功能：**
   - API查询正确
   - 返回数据格式正确
   - 播放量数据最新
   - 视频列表最新

### 问题情况

1. **数据库路径问题：**
   - 使用相对路径导致不同组件使用不同数据库
   - 环境变量未设置
   - 数据库文件不存在或不可访问

2. **数据更新问题：**
   - 数据抓取脚本未运行
   - 定时任务未配置
   - 播放量未更新
   - 更新时间戳过旧

3. **API查询问题：**
   - 查询条件错误
   - 排序错误
   - 字段映射错误
   - 缓存机制问题

## 📌 下一步行动

1. **立即执行诊断脚本**，检查数据库配置和数据完整性
2. **根据诊断结果**，确定问题根源
3. **修复问题**，统一数据库路径，确保数据更新
4. **验证修复**，测试API和前端页面

