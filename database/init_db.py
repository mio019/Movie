import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.tables import User, Admin, Movie, Rating, Comment, Favorite, Log

with app.app_context():
    db.create_all()
    print("✅ 数据库初始化完成，7张表已创建")
    print("   - users       用户表")
    print("   - admins      管理员表")
    print("   - movies      电影表")
    print("   - ratings     评分表")
    print("   - comments    评论表")
    print("   - favorites   收藏夹表")
    print("   - logs        日志表")