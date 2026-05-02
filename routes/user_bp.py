from flask import Blueprint, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
from models.tables import User, Movie, Rating, Comment, Favorite
from utils import success, fail, log_action

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


# ───────────────────────────── 1. 注册 ─────────────────────────────
@user_bp.route('/register', methods=['POST'])
def register():
    d = request.get_json()
    if not d:
        return fail('参数错误')
    username = d.get('username', '').strip()
    email    = d.get('email', '').strip()
    password = d.get('password', '').strip()
    if not all([username, email, password]):
        return fail('用户名、邮箱、密码不能为空')
    if User.query.filter_by(username=username).first():
        return fail('用户名已存在')
    if User.query.filter_by(email=email).first():
        return fail('邮箱已被注册')
    u = User(
        username = username,
        email    = email,
        password = generate_password_hash(password),
        age      = d.get('age'),
        gender   = d.get('gender'),
        occupation = d.get('occupation'),
    )
    db.session.add(u)
    db.session.commit()
    log_action(u.id, 'register')
    return success({'user_id': u.id, 'username': u.username}, '注册成功')


# ───────────────────────────── 2. 登录 ─────────────────────────────
@user_bp.route('/login', methods=['POST'])
def login():
    d = request.get_json()
    username = d.get('username', '').strip()
    password = d.get('password', '').strip()
    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password, password):
        return fail('用户名或密码错误')
    if not u.is_active:
        return fail('账号已被禁用')
    login_user(u)
    log_action(u.id, 'login')
    return success({
        'user_id':  u.id,
        'username': u.username,
        'email':    u.email,
        'avatar':   u.avatar,
    }, '登录成功')


# ───────────────────────────── 3. 登出 ─────────────────────────────
@user_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    log_action(current_user.id, 'logout')
    logout_user()
    return success(msg='已退出登录')


# ───────────────────────────── 4. 获取个人信息 ─────────────────────
@user_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    u = current_user
    return success({
        'user_id':    u.id,
        'username':   u.username,
        'email':      u.email,
        'avatar':     u.avatar,
        'age':        u.age,
        'gender':     u.gender,
        'occupation': u.occupation,
        'created_at': u.created_at.strftime('%Y-%m-%d'),
    })


# ───────────────────────────── 5. 修改个人信息 ─────────────────────
@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    d = request.get_json()
    u = current_user
    for field in ['age', 'gender', 'occupation', 'avatar']:
        if field in d:
            setattr(u, field, d[field])
    if 'email' in d:
        if User.query.filter(User.email == d['email'], User.id != u.id).first():
            return fail('邮箱已被使用')
        u.email = d['email']
    db.session.commit()
    return success(msg='信息已更新')


# ───────────────────────────── 6. 修改密码 ─────────────────────────
@user_bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    d = request.get_json()
    old_pwd = d.get('old_password', '')
    new_pwd = d.get('new_password', '')
    if not check_password_hash(current_user.password, old_pwd):
        return fail('原密码错误')
    if len(new_pwd) < 6:
        return fail('新密码不能少于6位')
    current_user.password = generate_password_hash(new_pwd)
    db.session.commit()
    return success(msg='密码修改成功')


# ───────────────────────────── 7. 提交评分 ─────────────────────────
@user_bp.route('/rate', methods=['POST'])
@login_required
def rate_movie():
    d = request.get_json()
    movie_id = d.get('movie_id')
    rating   = float(d.get('rating', 0))
    if not movie_id or not (1 <= rating <= 5):
        return fail('参数错误，评分范围 1-5')
    if not Movie.query.get(movie_id):
        return fail('电影不存在')
    existing = Rating.query.filter_by(
        user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        existing.rating = rating
    else:
        db.session.add(Rating(
            user_id=current_user.id, movie_id=movie_id, rating=rating))
    # 更新电影平均分
    db.session.commit()
    _update_movie_avg(movie_id)
    log_action(current_user.id, 'rate', movie_id, 'movie')
    return success(msg='评分成功')


# ───────────────────────────── 8. 提交评论 ─────────────────────────
@user_bp.route('/comment', methods=['POST'])
@login_required
def add_comment():
    d = request.get_json()
    movie_id = d.get('movie_id')
    content  = d.get('content', '').strip()
    if not movie_id or not content:
        return fail('参数错误')
    if not Movie.query.get(movie_id):
        return fail('电影不存在')
    c = Comment(user_id=current_user.id, movie_id=movie_id, content=content)
    db.session.add(c)
    db.session.commit()
    log_action(current_user.id, 'comment', movie_id, 'movie')
    return success({'comment_id': c.id}, '评论成功')


# ───────────────────────────── 9. 收藏 ──────────────────────────────
@user_bp.route('/favorite', methods=['POST'])
@login_required
def add_favorite():
    d = request.get_json()
    movie_id = d.get('movie_id')
    if not movie_id or not Movie.query.get(movie_id):
        return fail('电影不存在')
    if Favorite.query.filter_by(
            user_id=current_user.id, movie_id=movie_id).first():
        return fail('已在收藏夹中')
    db.session.add(Favorite(user_id=current_user.id, movie_id=movie_id))
    db.session.commit()
    return success(msg='收藏成功')


# ───────────────────────────── 10. 取消收藏 ─────────────────────────
@user_bp.route('/favorite/<int:movie_id>', methods=['DELETE'])
@login_required
def remove_favorite(movie_id):
    fav = Favorite.query.filter_by(
        user_id=current_user.id, movie_id=movie_id).first()
    if not fav:
        return fail('收藏记录不存在')
    db.session.delete(fav)
    db.session.commit()
    return success(msg='已取消收藏')


# ───────────────────────────── 11. 收藏列表 ─────────────────────────
@user_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    data = []
    for f in favs:
        m = Movie.query.get(f.movie_id)
        if m:
            data.append({
                'movie_id':    m.id,
                'title':       m.title,
                'genres':      m.genres,
                'avg_rating':  m.avg_rating,
                'year':        m.year,
                'poster_url':  m.poster_url or '',
            })
    return success(data)


# ───────────────────────────── 12. 我的评分记录 ──────────────────────
@user_bp.route('/my_ratings', methods=['GET'])
@login_required
def my_ratings():
    ratings = Rating.query.filter_by(user_id=current_user.id)\
                          .order_by(Rating.timestamp.desc()).all()
    data = []
    for r in ratings:
        m = Movie.query.get(r.movie_id)
        if m:
            data.append({
                'movie_id': m.id,
                'title':    m.title,
                'rating':   r.rating,
                'time':     r.timestamp.strftime('%Y-%m-%d'),
            })
    return success(data)


# ───────────────────────────── 13. 获取推荐列表 ──────────────────────
@user_bp.route('/recommend', methods=['GET'])
@login_required
def recommend():
    algo = request.args.get('algo', 'hybrid')
    top_n = int(request.args.get('top_n', 10))
    uid = current_user.id

    from algorithms import (user_cf, item_cf, svd_recommend,
                            content_based_recommend, hybrid_recommend)
    fn_map = {
        'user_cf': user_cf,
        'item_cf': item_cf,
        'svd':     svd_recommend,
        'content': content_based_recommend,
        'hybrid':  hybrid_recommend,
    }
    fn = fn_map.get(algo, hybrid_recommend)
    movies = fn(uid, top_n=top_n)
    log_action(uid, f'recommend_{algo}')
    data = [{
        'movie_id':    m.id,
        'title':       m.title,
        'genres':      m.genres,
        'avg_rating':  m.avg_rating,
        'rating_count':m.rating_count,
        'year':        m.year,
        'poster_url':   m.poster_url or '',
    } for m in movies]
    return success(data)


# ───────────────────────────── 14. 算法评估结果 ──────────────────────
@user_bp.route('/evaluate', methods=['GET'])
def evaluate():
    from algorithms import evaluate_algorithms
    result = evaluate_algorithms(sample_users=30)
    return success(result)


# ─────────────────────── 内部：更新电影均分 ──────────────────────────
def _update_movie_avg(movie_id):
    from sqlalchemy import func
    row = db.session.query(
        func.avg(Rating.rating).label('avg'),
        func.count(Rating.rating).label('cnt')
    ).filter(Rating.movie_id == movie_id).first()
    m = Movie.query.get(movie_id)
    if m and row:
        m.avg_rating   = round(float(row.avg), 2)
        m.rating_count = row.cnt
        db.session.commit()