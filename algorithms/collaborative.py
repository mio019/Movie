import numpy as np
from models import db
from models.tables import Rating, Movie
from sqlalchemy import func


def _get_rating_matrix():
    """返回 {user_id: {movie_id: rating}} 字典"""
    rows = Rating.query.all()
    matrix = {}
    for r in rows:
        matrix.setdefault(r.user_id, {})[r.movie_id] = r.rating
    return matrix


def _cosine_similarity(vec_a, vec_b):
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    a = np.array([vec_a[k] for k in common])
    b = np.array([vec_b[k] for k in common])
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def user_cf(user_id, top_n=10, sim_k=20):
    """User-based Collaborative Filtering"""
    matrix = _get_rating_matrix()
    if user_id not in matrix:
        return []
    target = matrix[user_id]
    # 计算与其他用户的相似度
    sims = []
    for uid, ratings in matrix.items():
        if uid == user_id:
            continue
        s = _cosine_similarity(target, ratings)
        if s > 0:
            sims.append((uid, s))
    sims.sort(key=lambda x: -x[1])
    neighbors = sims[:sim_k]

    # 聚合邻居评分
    rated = set(target.keys())
    scores = {}
    sim_sum = {}
    for uid, sim in neighbors:
        for mid, r in matrix[uid].items():
            if mid in rated:
                continue
            scores.setdefault(mid, 0)
            sim_sum.setdefault(mid, 0)
            scores[mid]   += sim * r
            sim_sum[mid]  += abs(sim)

    pred = {mid: scores[mid] / sim_sum[mid]
            for mid in scores if sim_sum[mid] > 0}
    top = sorted(pred, key=lambda x: -pred[x])[:top_n]
    return _fetch_movies(top)


def item_cf(user_id, top_n=10, sim_k=20):
    """Item-based Collaborative Filtering"""
    matrix = _get_rating_matrix()
    if user_id not in matrix:
        return []
    rated = matrix[user_id]

    # 构建物品向量 {movie_id: {user_id: rating}}
    item_matrix = {}
    for uid, ratings in matrix.items():
        for mid, r in ratings.items():
            item_matrix.setdefault(mid, {})[uid] = r

    # 计算候选电影得分
    candidate_scores = {}
    for mid_rated, r_rated in rated.items():
        if mid_rated not in item_matrix:
            continue
        sims = []
        for mid_cand, vec in item_matrix.items():
            if mid_cand in rated:
                continue
            s = _cosine_similarity(item_matrix[mid_rated], vec)
            if s > 0:
                sims.append((mid_cand, s))
        sims.sort(key=lambda x: -x[1])
        for mid_cand, s in sims[:sim_k]:
            candidate_scores.setdefault(mid_cand, 0)
            candidate_scores[mid_cand] += s * r_rated

    top = sorted(candidate_scores, key=lambda x: -candidate_scores[x])[:top_n]
    return _fetch_movies(top)


def _fetch_movies(movie_ids):
    if not movie_ids:
        return []
    movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()
    id_map = {m.id: m for m in movies}
    return [id_map[mid] for mid in movie_ids if mid in id_map]