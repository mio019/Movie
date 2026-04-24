from flask import Flask, jsonify
from config import Config
from models import db, login_manager

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'user.login'

from models.tables import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注册 API 蓝图
from routes.user_bp  import user_bp
from routes.admin_bp import admin_bp
from routes.movie_bp import movie_bp
from routes.page_bp  import page_bp

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(movie_bp)
app.register_blueprint(page_bp)

@app.route('/api/status')
def status():
    return jsonify({'project': '电影推荐系统', 'status': 'running', 'version': '1.0.0'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)