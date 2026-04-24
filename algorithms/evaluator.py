import numpy as np
from models.tables import Rating
from models import db
from algorithms.collaborative import user_cf, item_cf
from algorithms.svd_rec import svd_recommend


def compute_rmse(predictions, actuals):
    if not predictions:
        return None
    errors = [(p - a) ** 2 for p, a in zip(predictions, actuals)]
    return round(float(np.sqrt(np.mean(errors))), 4)


def evaluate_algorithms(sample_users=30):
    """对 User-CF / Item-CF / SVD 进行 RMSE + 精确率评估"""
    from models.tables import User
    users = User.query.limit(sample_users).all()
    results = {'user_cf': [], 'item_cf': [], 'svd': []}

    for u in users:
        ratings = Rating.query.filter_by(user_id=u.id).all()
        if len(ratings) < 5:
            continue
        # 留一法：最后一条作测试
        test   = ratings[-1]
        actual = test.rating

        for algo_name, algo_fn in [
            ('user_cf', user_cf),
            ('item_cf', item_cf),
            ('svd',     svd_recommend),
        ]:
            recs = algo_fn(u.id, top_n=20)
            rec_ids = [m.id for m in recs]
            # 若推荐列表包含测试电影则命中
            hit = 1 if test.movie_id in rec_ids else 0
            results[algo_name].append(hit)

    summary = {}
    for name, hits in results.items():
        if hits:
            summary[name] = {
                'precision': round(sum(hits) / len(hits), 4),
                'sample_count': len(hits)
            }
    return summary