import numpy as np
from models.tables import Movie, Rating
from models import db


def _genre_vector(genres_str, all_genres):
    genres = set(genres_str.split('|')) if genres_str else set()
    return np.array([1 if g in genres else 0 for g in all_genres], dtype=float)


def content_based_recommend(user_id, top_n=10):
    """基于内容（类型）的过滤推荐"""
    all_movies = Movie.query.all()
    if not all_movies:
        return []

    # 收集所有类型
    all_genres = sorted(set(
        g for m in all_movies for g in (m.genres or '').split('|') if g
    ))

    # 用户已评分电影
    user_ratings = Rating.query.filter_by(user_id=user_id).all()
    if not user_ratings:
        # 冷启动：返回评分最高的电影
        return Movie.query.order_by(Movie.avg_rating.desc()).limit(top_n).all()

    rated_ids = {r.movie_id for r in user_ratings}

    # 构建用户偏好向量（加权平均）
    pref = np.zeros(len(all_genres))
    total_w = 0.0
    for r in user_ratings:
        m = Movie.query.get(r.movie_id)
        if m:
            vec = _genre_vector(m.genres, all_genres)
            pref += vec * r.rating
            total_w += r.rating
    if total_w > 0:
        pref /= total_w

    # 计算候选电影与用户偏好的余弦相似度
    scores = []
    for m in all_movies:
        if m.id in rated_ids:
            continue
        vec = _genre_vector(m.genres, all_genres)
        denom = np.linalg.norm(pref) * np.linalg.norm(vec)
        sim = float(np.dot(pref, vec) / denom) if denom > 0 else 0.0
        scores.append((m, sim))

    scores.sort(key=lambda x: -x[1])
    return [m for m, _ in scores[:top_n]]