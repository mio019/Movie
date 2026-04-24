"""
init_db.py
运行此脚本初始化数据库，创建全部7张表
使用方式：python init_db.py
"""

import sqlite3
import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'movie_recommend.db')

# 建表 SQL
SCHEMA = """
-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,           -- 存储哈希值
    email       TEXT    UNIQUE,
    avatar      TEXT    DEFAULT 'default.png',
    gender      TEXT    DEFAULT '未知',     -- 男/女/未知
    age         INTEGER DEFAULT 0,
    occupation  TEXT    DEFAULT '',
    created_at  TEXT    DEFAULT (datetime('now','localtime')),
    is_active   INTEGER DEFAULT 1          -- 1正常 0禁用
);

-- 2. 管理员表
CREATE TABLE IF NOT EXISTS admins (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now','localtime'))
);

-- 3. 电影表
CREATE TABLE IF NOT EXISTS movies (
    id          INTEGER PRIMARY KEY,       -- 直接使用 MovieLens movie_id
    title       TEXT    NOT NULL,
    release_year INTEGER DEFAULT 0,
    genres      TEXT    DEFAULT '',        -- 用 | 分隔，如 "Action|Comedy"
    imdb_url    TEXT    DEFAULT '',
    poster_url  TEXT    DEFAULT '',
    overview    TEXT    DEFAULT '',
    avg_rating  REAL    DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0
);

-- 4. 评分表
CREATE TABLE IF NOT EXISTS ratings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    movie_id    INTEGER NOT NULL,
    rating      REAL    NOT NULL CHECK(rating >= 1 AND rating <= 5),
    rated_at    TEXT    DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id)  REFERENCES users(id),
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    UNIQUE(user_id, movie_id)              -- 每用户每电影只能评一次
);

-- 5. 评论表
CREATE TABLE IF NOT EXISTS comments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    movie_id    INTEGER NOT NULL,
    content     TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now','localtime')),
    is_visible  INTEGER DEFAULT 1,         -- 1显示 0管理员隐藏
    FOREIGN KEY (user_id)  REFERENCES users(id),
    FOREIGN KEY (movie_id) REFERENCES movies(id)
);

-- 6. 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    movie_id    INTEGER NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id)  REFERENCES users(id),
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    UNIQUE(user_id, movie_id)
);

-- 7. 日志表
CREATE TABLE IF NOT EXISTS logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,                   -- NULL 表示管理员操作
    action      TEXT    NOT NULL,          -- 如 login / rate / favorite / recommend
    detail      TEXT    DEFAULT '',        -- 操作详情，JSON字符串
    ip          TEXT    DEFAULT '',
    created_at  TEXT    DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 常用索引
CREATE INDEX IF NOT EXISTS idx_ratings_user    ON ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_ratings_movie   ON ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_comments_movie  ON comments(movie_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user  ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_user       ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_action     ON logs(action);
"""

def init_db():
    # 确保 database 目录存在
    os.makedirs(DB_DIR, exist_ok=True)

    if os.path.exists(DB_PATH):
        print(f"[警告] 数据库已存在：{DB_PATH}")
        confirm = input("是否重新初始化？这将清空所有数据！(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消，退出。")
            sys.exit(0)
        os.remove(DB_PATH)
        print("[信息] 已删除旧数据库。")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.executescript(SCHEMA)
        conn.commit()
        print("=" * 50)
        print("[成功] 数据库初始化完成！")
        print(f"[路径] {DB_PATH}")
        print("[建表] users / admins / movies / ratings / comments / favorites / logs")
        print("=" * 50)
    except Exception as e:
        print(f"[错误] 建表失败：{e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    # 插入默认管理员账户
    insert_default_admin()

def insert_default_admin():
    """插入默认管理员账户 admin / admin123"""
    from werkzeug.security import generate_password_hash
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        hashed_pw = generate_password_hash('admin123')
        cursor.execute(
            "INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
            ('admin', hashed_pw)
        )
        conn.commit()
        print("[成功] 默认管理员账户已创建：用户名 admin  密码 admin123")
    except Exception as e:
        print(f"[错误] 创建管理员失败：{e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()