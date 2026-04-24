# 工具函数模块
from functools import wraps
from flask import jsonify, session
from flask_login import current_user


def success(data=None, msg='ok'):
    return jsonify({'code': 200, 'msg': msg, 'data': data})

def fail(msg='error', code=400):
    return jsonify({'code': code, 'msg': msg, 'data': None}), code

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_id'):
            return fail('请先登录管理员账号', 401)
        return f(*args, **kwargs)
    return decorated

def log_action(user_id, action, target_id=None, target_type=None):
    from models.tables import Log
    from models import db
    from flask import request
    entry = Log(
        user_id     = user_id,
        action      = action,
        target_id   = target_id,
        target_type = target_type,
        ip_address  = request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()