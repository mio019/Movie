import numpy as np
from models.tables import Rating, Movie
from models import db


def svd_recommend(user_id, top_n=10, n_factors=50):
    """基于 SVD 矩阵分解的推荐"""
    rows = Rating.query.all()
    if not rows:
        return []

    # 构建用户-电影评分矩阵
    user_ids  = sorted(set(r.user_id  for r in rows))
    movie_ids = sorted(set(r.movie_id for r in rows))
    u_idx = {u: i for i, u in enumerate(user_ids)}
    m_idx = {m: i for i, m in enumerate(movie_ids)}

    R = np.zeros((len(user_ids), len(movie_ids)))
    for r in rows:
        R[u_idx[r.user_id]][m_idx[r.movie_id]] = r.rating

    # 均值中心化
    user_mean = np.true_divide(R.sum(1), (R != 0).sum(1) + 1e-9)
    R_centered = R.copy()
    for i in range(R.shape[0]):
        R_centered[i][R[i] != 0] -= user_mean[i]

    # SVD 分解（截断）
    k = min(n_factors, min(R.shape) - 1)
    U, sigma, Vt = np.linalg.svd(R_centered, full_matrices=False)
    U  = U[:, :k]
    S  = np.diag(sigma[:k])
    Vt = Vt[:k, :]

    R_pred = U @ S @ Vt

    if user_id not in u_idx:
        return []

    ui = u_idx[user_id]
    rated_indices = set(np.where(R[ui] != 0)[0])
    preds = [(movie_ids[j], R_pred[ui][j] + user_mean[ui])
             for j in range(len(movie_ids)) if j not in rated_indices]
    preds.sort(key=lambda x: -x[1])
    top_ids = [mid for mid, _ in preds[:top_n]]
    movies = Movie.query.filter(Movie.id.in_(top_ids)).all()
    id_map = {m.id: m for m in movies}
    return [id_map[mid] for mid in top_ids if mid in id_map]