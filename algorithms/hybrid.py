from algorithms.collaborative import user_cf, item_cf
from algorithms.content_based  import content_based_recommend


def hybrid_recommend(user_id, top_n=10,
                     w_user_cf=0.4, w_item_cf=0.3, w_content=0.3):
    """混合推荐：User-CF + Item-CF + 内容过滤加权融合"""
    def movies_to_scored(movies, weight):
        return {m.id: (m, weight * (len(movies) - i))
                for i, m in enumerate(movies)}

    cf_u  = movies_to_scored(user_cf(user_id, top_n * 2), w_user_cf)
    cf_i  = movies_to_scored(item_cf(user_id, top_n * 2), w_item_cf)
    cb    = movies_to_scored(content_based_recommend(user_id, top_n * 2), w_content)

    # 合并得分
    all_ids = set(cf_u) | set(cf_i) | set(cb)
    merged = {}
    for mid in all_ids:
        score = 0.0
        movie  = None
        for d in [cf_u, cf_i, cb]:
            if mid in d:
                m, s = d[mid]
                score += s
                movie  = m
        merged[mid] = (movie, score)

    ranked = sorted(merged.values(), key=lambda x: -x[1])
    return [m for m, _ in ranked[:top_n]]