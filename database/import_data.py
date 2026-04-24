import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import app
from models import db
from models.tables import User, Movie, Rating, Admin

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml-100k')

def import_movies():
    print("导入电影数据...")
    genres_list = [
        'unknown','Action','Adventure','Animation',"Children's",'Comedy',
        'Crime','Documentary','Drama','Fantasy','Film-Noir','Horror',
        'Musical','Mystery','Romance','Sci-Fi','Thriller','War','Western'
    ]
    path = os.path.join(DATA_DIR, 'u.item')
    rows = open(path, encoding='latin-1').readlines()
    count = 0
    for line in rows:
        parts = line.strip().split('|')
        if len(parts) < 24:
            continue
        movie_id = int(parts[0])
        title_raw = parts[1]
        # 从标题提取年份，如 "Toy Story (1995)"
        year = None
        if '(' in title_raw and ')' in title_raw:
            try:
                year = int(title_raw[title_raw.rfind('(')+1:title_raw.rfind(')')])
            except:
                pass
        title = title_raw[:title_raw.rfind('(')].strip() if '(' in title_raw else title_raw

        genre_flags = parts[5:24]
        genres = '|'.join([genres_list[i] for i, f in enumerate(genre_flags) if f == '1'])

        if not Movie.query.get(movie_id):
            m = Movie(id=movie_id, title=title, year=year, genres=genres)
            db.session.add(m)
            count += 1
    db.session.commit()
    print(f"  ✅ 导入电影 {count} 部")


def import_users():
    print("导入用户数据...")
    path = os.path.join(DATA_DIR, 'u.user')
    rows = open(path, encoding='latin-1').readlines()
    count = 0
    for line in rows:
        parts = line.strip().split('|')
        if len(parts) < 4:
            continue
        user_id    = int(parts[0])
        age        = int(parts[1])
        gender     = parts[2]
        occupation = parts[3]
        if not User.query.get(user_id):
            u = User(
                id         = user_id,
                username   = f'user_{user_id}',
                email      = f'user_{user_id}@movielens.com',
                password   = generate_password_hash('123456'),
                age        = age,
                gender     = gender,
                occupation = occupation,
            )
            db.session.add(u)
            count += 1
    db.session.commit()
    print(f"  ✅ 导入用户 {count} 人")


def import_ratings():
    print("导入评分数据（10万条，稍等）...")
    path = os.path.join(DATA_DIR, 'u.data')
    df = pd.read_csv(path, sep='\t', header=None,
                     names=['user_id','movie_id','rating','timestamp'])
    count = 0
    batch = []
    for _, row in df.iterrows():
        batch.append(Rating(
            user_id  = int(row['user_id']),
            movie_id = int(row['movie_id']),
            rating   = float(row['rating']),
            timestamp= datetime.fromtimestamp(int(row['timestamp']))
        ))
        if len(batch) >= 2000:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            count += len(batch)
            batch = []
            print(f"  已导入 {count} 条...", end='\r')
    if batch:
        db.session.bulk_save_objects(batch)
        db.session.commit()
        count += len(batch)

    # 更新每部电影的平均分和评分数
    print("\n  更新电影平均评分...")
    from sqlalchemy import func
    results = db.session.query(
        Rating.movie_id,
        func.avg(Rating.rating).label('avg'),
        func.count(Rating.rating).label('cnt')
    ).group_by(Rating.movie_id).all()
    for r in results:
        m = Movie.query.get(r.movie_id)
        if m:
            m.avg_rating    = round(float(r.avg), 2)
            m.rating_count  = r.cnt
    db.session.commit()
    print(f"  ✅ 导入评分 {count} 条")


def create_admin():
    print("创建默认管理员...")
    if not Admin.query.filter_by(username='admin').first():
        a = Admin(
            username = 'admin',
            password = generate_password_hash('admin123')
        )
        db.session.add(a)
        db.session.commit()
        print("  ✅ 管理员账号：admin / admin123")
    else:
        print("  管理员已存在，跳过")


if __name__ == '__main__':
    with app.app_context():
        import_movies()
        import_users()
        import_ratings()
        create_admin()
        print("\n🎉 全部数据导入完成！")