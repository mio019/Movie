from flask import Blueprint, request, session
from werkzeug.security import check_password_hash
from models import db
from models.tables import Admin, User, Movie, Rating, Comment, Log
from utils import success, fail, admin_required
from sqlalchemy import func
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ───────────────────────────── 1. 管理员登录 ─────────────────────────
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    d = request.get_json()
    username = d.get('username', '').strip()
    password = d.get('password', '').strip()
    a = Admin.query.filter_by(username=username).first()
    if not a or not check_password_hash(a.password, password):
        return fail('账号或密码错误')
    session['admin_id']   = a.id
    session['admin_name'] = a.username
    return success({'admin_id': a.id, 'username': a.username}, '登录成功')


# ───────────────────────────── 2. 管理员登出 ─────────────────────────
@admin_bp.route('/logout', methods=['POST'])
@admin_required
def admin_logout():
    session.pop('admin_id',   None)
    session.pop('admin_name', None)
    return success(msg='已退出')


# ───────────────────────────── 3. 数据大屏统计 ───────────────────────
@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    user_count   = User.query.count()
    movie_count  = Movie.query.count()
    rating_count = Rating.query.count()
    comment_count= Comment.query.count()

    # 近7天每日新增评分
    today = datetime.utcnow().date()
    daily_ratings = []
    for i in range(6, -1, -1):
        day   = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end   = datetime.combine(day, datetime.max.time())
        cnt = Rating.query.filter(
            Rating.timestamp >= day_start,
            Rating.timestamp <= day_end
        ).count()
        daily_ratings.append({'date': str(day), 'count': cnt})

    # 类型分布
    movies = Movie.query.with_entities(Movie.genres).all()
    genre_count = {}
    for (g,) in movies:
        for genre in (g or '').split('|'):
            if genre:
                genre_count[genre] = genre_count.get(genre, 0) + 1
    genre_dist = sorted(genre_count.items(), key=lambda x: -x[1])[:10]

    # 评分分布
    rating_dist = {}
    for score in [1, 2, 3, 4, 5]:
        cnt = Rating.query.filter(
            Rating.rating >= score - 0.5,
            Rating.rating <  score + 0.5
        ).count()
        rating_dist[score] = cnt

    # Top10 热门电影
    top_movies = Movie.query.filter(Movie.rating_count > 0)\
                            .order_by(Movie.avg_rating.desc())\
                            .limit(10).all()

    return success({
        'summary': {
            'users':    user_count,
            'movies':   movie_count,
            'ratings':  rating_count,
            'comments': comment_count,
        },
        'daily_ratings': daily_ratings,
        'genre_dist':    [{'name': k, 'value': v} for k, v in genre_dist],
        'rating_dist':   rating_dist,
        'top_movies': [{
            'id':           m.id,
            'title':        m.title,
            'avg_rating':   m.avg_rating,
            'rating_count': m.rating_count,
        } for m in top_movies],
    })


# ───────────────────────────── 4. 用户管理（列表+搜索+禁用）──────────
@admin_bp.route('/users', methods=['GET'])
@admin_required
def user_list():
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    keyword  = request.args.get('keyword', '').strip()
    query = User.query
    if keyword:
        query = query.filter(
            (User.username.ilike(f'%{keyword}%')) |
            (User.email.ilike(f'%{keyword}%'))
        )
    pg = query.paginate(page=page, per_page=per_page, error_out=False)
    data = [{
        'user_id':    u.id,
        'username':   u.username,
        'email':      u.email,
        'gender':     u.gender,
        'occupation': u.occupation,
        'is_active':  u.is_active,
        'created_at': u.created_at.strftime('%Y-%m-%d'),
    } for u in pg.items]
    return success({'total': pg.total, 'pages': pg.pages, 'list': data})


@admin_bp.route('/users/<int:user_id>/toggle', methods=['PUT'])
@admin_required
def toggle_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return fail('用户不存在', 404)
    u.is_active = not u.is_active
    db.session.commit()
    status = '启用' if u.is_active else '禁用'
    return success(msg=f'用户已{status}')


# ───────────────────────────── 5. 电影管理（增删改）─────────────────
@admin_bp.route('/movies', methods=['GET'])
@admin_required
def movie_list():
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    keyword  = request.args.get('keyword', '').strip()
    query = Movie.query
    if keyword:
        query = query.filter(Movie.title.ilike(f'%{keyword}%'))
    pg = query.order_by(Movie.id).paginate(
        page=page, per_page=per_page, error_out=False)
    data = [{
        'movie_id':     m.id,
        'title':        m.title,
        'genres':       m.genres,
        'year':         m.year,
        'avg_rating':   m.avg_rating,
        'rating_count': m.rating_count,
    } for m in pg.items]
    return success({'total': pg.total, 'pages': pg.pages, 'list': data})


@admin_bp.route('/movies/<int:movie_id>', methods=['PUT'])
@admin_required
def update_movie(movie_id):
    m = Movie.query.get(movie_id)
    if not m:
        return fail('电影不存在', 404)
    d = request.get_json()
    for field in ['title', 'genres', 'year', 'director', 'description', 'poster_url']:
        if field in d:
            setattr(m, field, d[field])
    db.session.commit()
    return success(msg='电影信息已更新')


@admin_bp.route('/movies/<int:movie_id>', methods=['DELETE'])
@admin_required
def delete_movie(movie_id):
    m = Movie.query.get(movie_id)
    if not m:
        return fail('电影不存在', 404)
    db.session.delete(m)
    db.session.commit()
    return success(msg='电影已删除')


# ───────────────────────────── 6. 评论管理（列表+删除）──────────────
@admin_bp.route('/comments', methods=['GET'])
@admin_required
def comment_list():
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    pg = Comment.query.order_by(Comment.created_at.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
    data = [{
        'comment_id': c.id,
        'user_id':    c.user_id,
        'movie_id':   c.movie_id,
        'content':    c.content,
        'is_visible': c.is_visible,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
    } for c in pg.items]
    return success({'total': pg.total, 'pages': pg.pages, 'list': data})


@admin_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@admin_required
def delete_comment(comment_id):
    c = Comment.query.get(comment_id)
    if not c:
        return fail('评论不存在', 404)
    c.is_visible = False
    db.session.commit()
    return success(msg='评论已隐藏')