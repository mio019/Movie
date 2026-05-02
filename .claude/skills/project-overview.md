---
name: project-overview
description: 电影推荐系统项目全貌 —— 结构、数据库、API、算法、当前数据状态。适合在开始任何修改前调用，快速理解项目。
---

# 电影推荐系统 (CineRec) 项目全貌

## 一、项目概要

基于 Flask + SQLite 的电影推荐 Web 应用，使用 MovieLens 100K 数据集，实现了多种推荐算法。

**技术栈：** Flask + SQLAlchemy + Flask-Login + SQLite + 原生 JS (无框架)

---

## 二、目录结构

```
movie_recommendation/
├── app.py                    # Flask 主入口，注册蓝图
├── config.py                 # 配置 (DB路径、SECRET_KEY)
├── requirements.txt          # 依赖
├── import_data.py            # [旧] 直接SQL建表脚本 (已不用)
│
├── database/
│   ├── movie_rec.db          # SQLite 数据库 (已导入数据)
│   ├── init_db.py            # [旧] 建表脚本 (已不用)
│   ├── import_data.py        # ★ 数据导入脚本：从data/ml-100k导入 → 运行此脚本填充DB
│   └── fetch_posters.py      # 海报抓取脚本
│
├── data/ml-100k/             # MovieLens 100K 原始数据集
│   ├── u.data                # 10万条评分 (user_id, movie_id, rating, timestamp)
│   ├── u.item                # 1682部电影 (id, title, release_date, genres, ...)
│   ├── u.user                # 943个用户 (id, age, gender, occupation, zip)
│   ├── u.genre               # 19种电影类型
│   ├── ua.base / ua.test     # 训练/测试集分割
│   └── u1~u5.base/test       # 5折交叉验证集
│
├── models/
│   ├── __init__.py           # SQLAlchemy db 实例
│   └── tables.py             # ★ 数据模型: User, Admin, Movie, Rating, Comment, Favorite, Log
│
├── routes/
│   ├── __init__.py           # 空
│   ├── user_bp.py            # ★ 用户API: 注册/登录/评分/评论/收藏/推荐
│   ├── movie_bp.py           # ★ 电影API: 列表/详情/热门/类型/相似电影/评分分布
│   ├── admin_bp.py           # 管理员API
│   └── page_bp.py            # ★ 页面路由: 渲染HTML模板
│
├── algorithms/
│   ├── __init__.py           # 导出各算法函数
│   ├── collaborative.py      # User-CF + Item-CF 协同过滤
│   ├── svd_rec.py            # SVD 矩阵分解
│   ├── content_based.py      # 基于电影类型的内容推荐
│   ├── hybrid.py             # 混合推荐 (融合多算法)
│   └── evaluator.py          # 算法评估 (RMSE/Precision/Recall)
│
├── templates/
│   ├── user/                 # 用户端页面
│   │   ├── index.html        # 首页
│   │   ├── login.html / register.html
│   │   ├── movies.html       # 电影列表 (搜索+类型筛选)
│   │   ├── movie_detail.html # ★ 电影详情 (评分+评论+收藏)
│   │   ├── recommend.html    # 推荐页 (可选算法)
│   │   └── profile.html      # 个人中心
│   └── admin/                # 管理端 (dashboard/users/movies/comments)
│
├── static/
│   ├── css/main.css
│   └── js/main.js            # 前端API封装 + 工具函数
│
└── utils/
    └── __init__.py           # success/fail JSON响应, log_action, admin_required
```

---

## 三、数据库详解 (SQLite: database/movie_rec.db)

### 3.1 表结构 (7张表)

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| **users** | 用户 | id, username, email, password(hash), age, gender, occupation |
| **admins** | 管理员 | id, username, password(hash) |
| **movies** | 电影 | id, title, genres(\|分隔), year, avg_rating, rating_count, poster_url, description |
| **ratings** | 评分 | id, user_id→users, movie_id→movies, rating(1-5), timestamp, UNIQUE(user_id,movie_id) |
| **comments** | 文字评论 | id, user_id→users, movie_id→movies, content, is_visible(1/0) |
| **favorites** | 收藏 | id, user_id→users, movie_id→movies, UNIQUE(user_id,movie_id) |
| **logs** | 操作日志 | id, user_id, action, target_id, target_type, ip_address |

### 3.2 当前数据量

| 表 | 行数 | 来源 |
|----|------|------|
| users | 944 | 943 来自 MovieLens (user_1~user_943) + 1 新注册 |
| admins | 1 | admin / admin123 |
| movies | 1,682 | MovieLens u.item |
| ratings | ~100,000 | MovieLens u.data (943用户 × ~106部/人) |
| comments | ~3 | **空数据集**——MovieLens 无文字评论，只有新用户发表的几条 |
| favorites | ~3 | 新用户操作产生 |
| logs | ~97 | 用户操作日志 |

### 3.3 关键事实

- **MovieLens 用户可登录**：用户名 `user_1` ~ `user_943`，密码统一为 `123456`
- **MovieLens 只含评分，不含评论**：comments 表几乎没有数据
- **10万条评分存在但"不可见"**：前端只展示聚合后的 avg_rating / rating_count，个体评分没有展示
- **评分已关联用户**：每一条 rating 都有 user_id，技术上可以追溯"谁评了什么"
- **电影封面为空**：poster_url 大多为空, fetch_posters.py 可能未执行或失败

---

## 四、API 接口

### 4.1 用户相关 `/api/user/`

| 方法 | 路径 | 说明 | 需登录 |
|------|------|------|--------|
| POST | /register | 注册 | ❌ |
| POST | /login | 登录 | ❌ |
| POST | /logout | 登出 | ✅ |
| GET | /profile | 获取个人信息 | ✅ |
| PUT | /profile | 修改个人信息 | ✅ |
| PUT | /password | 修改密码 | ✅ |
| POST | /rate | 提交评分 {movie_id, rating} | ✅ |
| POST | /comment | 提交评论 {movie_id, content} | ✅ |
| POST | /favorite | 添加收藏 {movie_id} | ✅ |
| DELETE | /favorite/<id> | 取消收藏 | ✅ |
| GET | /favorites | 收藏列表 | ✅ |
| GET | /my_ratings | 我的评分记录 | ✅ |
| GET | /recommend | 获取推荐 (?algo=hybrid&top_n=10) | ✅ |
| GET | /evaluate | 算法评估结果 | ❌ |

### 4.2 电影相关 `/api/movie/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /list | 电影列表 (?page=&keyword=&genre=) |
| GET | /detail/<id> | ★ 电影详情 (含最近20条评论) |
| GET | /hot | 热门电影 |
| GET | /genres | 所有电影类型列表 |
| GET | /similar/<id> | 相似电影 (基于类型重叠) |
| GET | /rating_dist/<id> | 评分分布 (1-5星各有多少人) |

---

## 五、推荐算法 (5种)

| 算法 | 函数 | 原理 |
|------|------|------|
| User-CF | `user_cf(uid, top_n)` | 找相似用户 → 聚合他们喜欢的电影 |
| Item-CF | `item_cf(uid, top_n)` | 基于用户已评分的电影 → 找相似电影 |
| SVD | `svd_recommend(uid, top_n)` | 矩阵分解预测评分 → 推荐高预测分电影 |
| Content-Based | `content_based_recommend(uid, top_n)` | 基于用户偏好类型 → 匹配同类型电影 |
| Hybrid | `hybrid_recommend(uid, top_n)` | 融合 User-CF + Item-CF + SVD |

算法评估 (`evaluator.py`) 支持 RMSE、Precision@K、Recall@K 三个指标。

---

## 六、当前已知问题

1. **评论表几乎为空** — MovieLens 数据集不含文字评论，详情页评论区形同虚设
2. **10万条评分不可见** — 虽有评分数据但前端只展示聚合值，没有"谁评了多少分"的展示
3. **评分分布接口未被使用** — `/api/movie/rating_dist/<id>` 已实现但前端未接入
4. **相似电影算法简陋** — 仅基于类型重叠，未用协同过滤或 embedding
5. **电影封面缺失** — 海报未抓取，大量电影无图
6. **import_data.py 有两份** — 根目录和 database/ 下都有，功能不同；init_db.py 也是两份逻辑
7. **用户端页面强制登录** — 未登录看不到任何内容 (如 movie_detail.html)

---

## 七、启动方式

```bash
cd movie_recommendation
python app.py          # 启动 Flask (port 5000, debug mode)
```

默认管理员：admin / admin123
MovieLens 用户：user_1 ~ user_943 / 密码均为 123456
