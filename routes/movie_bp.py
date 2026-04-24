from flask import Blueprint, request
from models.tables import Movie, Comment, Rating
from models import db
from utils import success, fail

movie_bp = Blueprint('movie', __name__, url_prefix='/api/movie')


# ───────────────────────────── 1. 电影列表（分页+搜索+类型筛选）──────
@movie_bp.route('/list', methods=['GET'])
def movie_list():
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    keyword  = request.args.get('keyword', '').strip()
    genre    = request.args.get('genre', '').strip()

    query = Movie.query
    if keyword:
        query = query.filter(Movie.title.ilike(f'%{keyword}%'))
    if genre:
        query = query.filter(Movie.genres.ilike(f'%{genre}%'))
    query = query.order_by(Movie.avg_rating.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    data = [{
        'movie_id':     m.id,
        'title':        m.title,
        'genres':       m.genres,
        'year':         m.year,
        'avg_rating':   m.avg_rating,
        'rating_count': m.rating_count,
        'poster_url':   m.poster_url or '', 
    } for m in pagination.items]
    return success({
        'total': pagination.total,
        'pages': pagination.pages,
        'page':  page,
        'list':  data,
    })


# ───────────────────────────── 2. 电影详情 ───────────────────────────
@movie_bp.route('/detail/<int:movie_id>', methods=['GET'])
def movie_detail(movie_id):
    m = Movie.query.get(movie_id)
    if not m:
        return fail('电影不存在', 404)
    comments = Comment.query.filter_by(
        movie_id=movie_id, is_visible=True)\
        .order_by(Comment.created_at.desc()).limit(20).all()
    comment_list = [{
        'comment_id': c.id,
        'user_id':    c.user_id,
        'content':    c.content,
        'time':       c.created_at.strftime('%Y-%m-%d %H:%M'),
    } for c in comments]
    return success({
        'movie_id':     m.id,
        'title':        m.title,
        'genres':       m.genres,
        'year':         m.year,
        'director':     m.director,
        'description':  m.description,
        'poster_url':   m.poster_url,
        'avg_rating':   m.avg_rating,
        'rating_count': m.rating_count,
        'comments':     comment_list,
    })


# ───────────────────────────── 3. 热门电影 ───────────────────────────
@movie_bp.route('/hot', methods=['GET'])
def hot_movies():
    top_n = int(request.args.get('top_n', 10))
    movies = Movie.query.filter(Movie.rating_count >= 20)\
                        .order_by(Movie.avg_rating.desc())\
                        .limit(top_n).all()
    data = [{
        'movie_id':     m.id,
        'title':        m.title,
        'genres':       m.genres,
        'avg_rating':   m.avg_rating,
        'rating_count': m.rating_count,
        'poster_url':   m.poster_url or '',
    } for m in movies]
    return success(data)


# ───────────────────────────── 4. 类型列表 ───────────────────────────
@movie_bp.route('/genres', methods=['GET'])
def genre_list():
    movies = Movie.query.with_entities(Movie.genres).all()
    genres = set()
    for (g,) in movies:
        if g:
            for item in g.split('|'):
                if item.strip():
                    genres.add(item.strip())
    return success(sorted(genres))


# ───────────────────────────── 5. 相似电影 ───────────────────────────
@movie_bp.route('/similar/<int:movie_id>', methods=['GET'])
def similar_movies(movie_id):
    top_n = int(request.args.get('top_n', 6))
    m = Movie.query.get(movie_id)
    if not m:
        return fail('电影不存在', 404)
    genres = set((m.genres or '').split('|'))
    candidates = Movie.query.filter(
        Movie.id != movie_id,
        Movie.genres.isnot(None)
    ).all()
    scored = []
    for c in candidates:
        c_genres = set((c.genres or '').split('|'))
        overlap = len(genres & c_genres)
        if overlap > 0:
            scored.append((c, overlap))
    scored.sort(key=lambda x: -x[1])
    data = [{
        'movie_id':   c.id,
        'title':      c.title,
        'genres':     c.genres,
        'avg_rating': c.avg_rating,
        'poster_url':   c.poster_url or '',
    } for c, _ in scored[:top_n]]
    return success(data)


# ───────────────────────────── 6. 电影评分分布（ECharts用）───────────
@movie_bp.route('/rating_dist/<int:movie_id>', methods=['GET'])
def rating_distribution(movie_id):
    if not Movie.query.get(movie_id):
        return fail('电影不存在', 404)
    ratings = Rating.query.filter_by(movie_id=movie_id).all()
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in ratings:
        key = int(round(r.rating))
        if key in dist:
            dist[key] += 1
    return success({'distribution': dist, 'total': len(ratings)})