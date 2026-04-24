import sys, os, time, requests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.tables import Movie

# ← 把你的 TMDB API Key 填在这里
TMDB_API_KEY = '740bdd1e152e06edbeecf61831dcf198'
TMDB_SEARCH  = 'https://api.themoviedb.org/3/search/movie'
TMDB_IMG     = 'https://image.tmdb.org/t/p/w500'
PLACEHOLDER  = '/static/images/no_poster.jpg'


def fetch_poster(title, year=None):
    """根据片名+年份搜索 TMDB，返回封面 URL"""
    params = {
        'api_key':       TMDB_API_KEY,
        'query':         title,
        'language':      'en-US',
        'include_adult': False,
    }
    if year:
        params['year'] = year
    try:
        r = requests.get(TMDB_SEARCH, params=params, timeout=8)
        data = r.json()
        results = data.get('results', [])
        if results and results[0].get('poster_path'):
            return TMDB_IMG + results[0]['poster_path']
    except Exception as e:
        print(f'  请求失败: {e}')
    return None


def run():
    with app.app_context():
        # 只处理还没有封面的电影
        movies = Movie.query.filter(
            (Movie.poster_url == None) | (Movie.poster_url == '')
        ).all()
        total = len(movies)
        print(f'共需处理 {total} 部电影（已有封面的自动跳过）')

        success, fail = 0, 0
        for i, m in enumerate(movies, 1):
            url = fetch_poster(m.title, m.year)
            if url:
                m.poster_url = url
                success += 1
                print(f'[{i}/{total}] ✅ {m.title}')
            else:
                m.poster_url = PLACEHOLDER
                fail += 1
                print(f'[{i}/{total}] ⚠️  未找到: {m.title}')

            # 每50条提交一次，避免长事务
            if i % 50 == 0:
                db.session.commit()
                print(f'  已提交 {i} 条...')

            # TMDB 免费限速 40次/10秒，这里保守一点
            time.sleep(0.28)

        db.session.commit()
        print(f'\n🎉 完成！成功 {success} 部，未找到 {fail} 部')


if __name__ == '__main__':
    run()