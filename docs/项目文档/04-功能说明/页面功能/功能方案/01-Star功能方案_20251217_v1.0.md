# Star功能方案设计

## 📋 功能概述

实现类似GitHub的Star功能，允许用户收藏/取消收藏论文，方便后续查看和管理。

## 🎯 核心需求

1. **用户Star论文**：点击Star按钮收藏论文
2. **查看Star列表**：查看所有已收藏的论文
3. **取消Star**：取消收藏
4. **Star统计**：显示每篇论文的Star数量
5. **个人Star管理**：查看和管理自己的收藏

## 🏗️ 技术方案

### 1. 数据库设计

#### 方案A：基于Cookie的轻量级方案（推荐用于MVP）

**优点**：
- 无需用户注册登录
- 实现简单快速
- 适合初期版本

**缺点**：
- 数据存储在浏览器，换设备会丢失
- 无法跨设备同步

**表结构**：
```sql
-- 论文Star统计表
CREATE TABLE paper_stars (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(50) NOT NULL,
    star_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(paper_id)
);

-- 用户Star记录表（基于Cookie ID）
CREATE TABLE user_stars (
    id SERIAL PRIMARY KEY,
    cookie_id VARCHAR(64) NOT NULL,  -- 浏览器Cookie ID
    paper_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cookie_id, paper_id)
);
```

#### 方案B：基于用户系统的完整方案（长期方案）

**优点**：
- 数据持久化，跨设备同步
- 支持用户管理
- 可扩展性强

**缺点**：
- 需要用户注册登录系统
- 实现复杂度较高

**表结构**：
```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 论文Star统计表
CREATE TABLE paper_stars (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(50) NOT NULL,
    star_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(paper_id)
);

-- 用户Star记录表
CREATE TABLE user_stars (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    paper_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, paper_id)
);
```

### 2. 推荐方案：混合方案（渐进式实现）

**阶段1：MVP版本（基于Cookie）**
- 快速实现，无需登录
- 使用Cookie存储用户标识
- 支持基本的Star功能

**阶段2：增强版本（可选登录）**
- 保留Cookie方式
- 增加可选登录功能
- 登录后数据迁移到用户账户

**阶段3：完整版本（用户系统）**
- 完整的用户注册登录
- 数据持久化
- 跨设备同步

## 💻 实现方案

### 阶段1：MVP版本实现

#### 后端API设计

```python
# models.py
class PaperStar(Base):
    __tablename__ = 'paper_stars'
    id = Column(Integer, primary_key=True)
    paper_id = Column(String(50), unique=True, nullable=False)
    star_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class UserStar(Base):
    __tablename__ = 'user_stars'
    id = Column(Integer, primary_key=True)
    cookie_id = Column(String(64), nullable=False)
    paper_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint('cookie_id', 'paper_id'),)

# app.py
import uuid
from flask import request, jsonify

def get_or_create_cookie_id():
    """获取或创建Cookie ID"""
    cookie_id = request.cookies.get('user_id')
    if not cookie_id:
        cookie_id = str(uuid.uuid4())
    return cookie_id

@app.route('/api/star', methods=['POST'])
def toggle_star():
    """Star/取消Star论文"""
    data = request.json
    paper_id = data.get('paper_id')
    cookie_id = get_or_create_cookie_id()
    
    session = get_session()
    try:
        # 检查是否已Star
        user_star = session.query(UserStar).filter_by(
            cookie_id=cookie_id,
            paper_id=paper_id
        ).first()
        
        paper_star = session.query(PaperStar).filter_by(
            paper_id=paper_id
        ).first()
        
        if user_star:
            # 取消Star
            session.delete(user_star)
            if paper_star:
                paper_star.star_count = max(0, paper_star.star_count - 1)
            result = {'starred': False}
        else:
            # 添加Star
            new_star = UserStar(
                cookie_id=cookie_id,
                paper_id=paper_id
            )
            session.add(new_star)
            if paper_star:
                paper_star.star_count += 1
            else:
                paper_star = PaperStar(paper_id=paper_id, star_count=1)
                session.add(paper_star)
            result = {'starred': True}
        
        session.commit()
        
        # 返回更新后的Star数量
        result['star_count'] = paper_star.star_count if paper_star else 0
        return jsonify(result)
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/star/status', methods=['GET'])
def get_star_status():
    """获取论文Star状态"""
    paper_id = request.args.get('paper_id')
    cookie_id = get_or_create_cookie_id()
    
    session = get_session()
    try:
        user_star = session.query(UserStar).filter_by(
            cookie_id=cookie_id,
            paper_id=paper_id
        ).first()
        
        paper_star = session.query(PaperStar).filter_by(
            paper_id=paper_id
        ).first()
        
        return jsonify({
            'starred': user_star is not None,
            'star_count': paper_star.star_count if paper_star else 0
        })
    finally:
        session.close()

@app.route('/api/star/list', methods=['GET'])
def get_starred_papers():
    """获取用户Star的论文列表"""
    cookie_id = get_or_create_cookie_id()
    
    session = get_session()
    try:
        user_stars = session.query(UserStar).filter_by(
            cookie_id=cookie_id
        ).order_by(UserStar.created_at.desc()).all()
        
        paper_ids = [star.paper_id for star in user_stars]
        
        # 获取论文详情
        papers = session.query(Paper).filter(
            Paper.arxiv_id.in_(paper_ids)
        ).all()
        
        result = []
        for paper in papers:
            result.append({
                'arxiv_id': paper.arxiv_id,
                'title': paper.title,
                'authors': paper.authors,
                'published_date': paper.published_date.isoformat() if paper.published_date else None,
                'categories': paper.categories,
                'pdf_url': paper.pdf_url
            })
        
        return jsonify({'papers': result})
    finally:
        session.close()
```

#### 前端实现

```javascript
// static/js/star.js
class StarManager {
    constructor() {
        this.cookieId = this.getOrCreateCookieId();
        this.init();
    }
    
    getOrCreateCookieId() {
        let cookieId = this.getCookie('user_id');
        if (!cookieId) {
            cookieId = this.generateUUID();
            this.setCookie('user_id', cookieId, 365);
        }
        return cookieId;
    }
    
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    
    setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${date.toUTCString()};path=/`;
    }
    
    async init() {
        // 为所有论文添加Star按钮
        this.addStarButtons();
        // 加载Star状态
        await this.loadStarStatuses();
    }
    
    addStarButtons() {
        document.querySelectorAll('.paper-item').forEach(paperItem => {
            const paperId = paperItem.dataset.paperId;
            if (!paperId) return;
            
            const starBtn = document.createElement('button');
            starBtn.className = 'star-btn';
            starBtn.dataset.paperId = paperId;
            starBtn.innerHTML = '<i class="far fa-star"></i> <span class="star-count">0</span>';
            starBtn.addEventListener('click', (e) => this.toggleStar(e));
            
            // 插入到论文标题旁边
            const titleEl = paperItem.querySelector('.paper-title');
            if (titleEl) {
                titleEl.parentNode.insertBefore(starBtn, titleEl.nextSibling);
            }
        });
    }
    
    async loadStarStatuses() {
        const paperItems = document.querySelectorAll('.paper-item');
        for (const item of paperItems) {
            const paperId = item.dataset.paperId;
            if (!paperId) continue;
            
            try {
                const response = await fetch(`/api/star/status?paper_id=${paperId}`);
                const data = await response.json();
                
                const starBtn = item.querySelector(`.star-btn[data-paper-id="${paperId}"]`);
                if (starBtn) {
                    starBtn.classList.toggle('starred', data.starred);
                    starBtn.querySelector('.star-count').textContent = data.star_count;
                    starBtn.querySelector('i').className = data.starred ? 'fas fa-star' : 'far fa-star';
                }
            } catch (error) {
                console.error('加载Star状态失败:', error);
            }
        }
    }
    
    async toggleStar(event) {
        const btn = event.currentTarget;
        const paperId = btn.dataset.paperId;
        
        try {
            const response = await fetch('/api/star', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ paper_id: paperId })
            });
            
            const data = await response.json();
            
            // 更新UI
            btn.classList.toggle('starred', data.starred);
            btn.querySelector('.star-count').textContent = data.star_count;
            btn.querySelector('i').className = data.starred ? 'fas fa-star' : 'far fa-star';
            
            // 显示提示
            this.showNotification(data.starred ? '已收藏' : '已取消收藏');
        } catch (error) {
            console.error('Star操作失败:', error);
            this.showNotification('操作失败，请重试', 'error');
        }
    }
    
    showNotification(message, type = 'success') {
        // 实现通知提示
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 2000);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    new StarManager();
});
```

#### CSS样式

```css
/* static/css/star.css */
.star-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;
}

.star-btn:hover {
    border-color: #ffa500;
    background: #fff8e1;
}

.star-btn.starred {
    color: #ffa500;
    border-color: #ffa500;
    background: #fff8e1;
}

.star-btn i {
    font-size: 16px;
}

.star-count {
    font-size: 12px;
    color: #666;
}
```

## 📊 功能扩展

### 1. Star排行榜
- 显示最受欢迎的论文（Star数最多）
- 按时间维度统计（今日/本周/本月最热）

### 2. Star分类
- 支持为Star的论文添加标签
- 按标签分类查看

### 3. Star导出
- 导出Star列表为CSV/Markdown
- 生成个人阅读清单

### 4. Star分享
- 分享Star列表
- 生成Star论文合集链接

## 🚀 实施计划

### 阶段1：MVP（1-2周）
- [ ] 数据库表设计
- [ ] 后端API实现
- [ ] 前端Star按钮和交互
- [ ] 基本测试

### 阶段2：增强（2-3周）
- [ ] Star列表页面
- [ ] Star统计展示
- [ ] 性能优化

### 阶段3：扩展（3-4周）
- [ ] 用户系统（可选）
- [ ] Star分类和标签
- [ ] 导出功能

## 💡 技术要点

1. **Cookie管理**：使用HttpOnly Cookie存储用户ID
2. **并发控制**：使用数据库事务确保Star计数准确
3. **性能优化**：批量加载Star状态，减少API调用
4. **用户体验**：即时反馈，无需刷新页面

