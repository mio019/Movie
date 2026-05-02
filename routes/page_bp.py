from flask import Blueprint, render_template
from flask_login import login_required

page_bp = Blueprint('page', __name__)

@page_bp.route('/')
def index():
    return render_template('user/index.html')

@page_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    return render_template('user/login.html')

@page_bp.route('/register')
def register_page():
    return render_template('user/register.html')

@page_bp.route('/movies')
def movies_page():
    return render_template('user/movies.html')

@page_bp.route('/movie/<int:movie_id>')
def movie_detail_page(movie_id):
    return render_template('user/movie_detail.html', movie_id=movie_id)

@page_bp.route('/profile')
def profile_page():
    return render_template('user/profile.html')

@page_bp.route('/recommend')
def recommend_page():
    return render_template('user/recommend.html')

@page_bp.route('/favorites')
def favorites_page():
    return render_template('user/favorites.html')

@page_bp.route('/admin')
def admin_index():
    return render_template('admin/dashboard.html')

@page_bp.route('/admin/users')
def admin_users():
    return render_template('admin/users.html')

@page_bp.route('/admin/movies')
def admin_movies():
    return render_template('admin/movies.html')

@page_bp.route('/admin/comments')
def admin_comments():
    return render_template('admin/comments.html')