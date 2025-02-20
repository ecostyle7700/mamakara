from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mamakara.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # セキュリティのため変更推奨
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ユーザーモデル
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 投稿モデル
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())

# ログイン管理
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ホーム（投稿一覧）
@app.route('/')
def index():
    posts = db.session.query(Post, User.username).join(User, Post.user_id == User.id).order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)


# ユーザー登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('このユーザー名は既に使われています。', 'danger')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('登録成功！ログインしてください。', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('ログインしました！', 'success')
            return redirect(url_for('index'))
        flash('ログイン失敗。ユーザー名またはパスワードが違います。', 'danger')
    return render_template('login.html')

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('login'))

# 投稿作成
@app.route('/post', methods=['POST'])
@login_required
def post():
    content = request.form['content']
    new_post = Post(user_id=current_user.id, content=content)
    db.session.add(new_post)
    db.session.commit()
    flash('投稿しました！', 'success')
    return redirect(url_for('index'))

# データベース初期化用（初回実行時のみ）
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("データベースを作成しました。")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render の環境変数 PORT を取得、なければ 5000 を使用
    app.run(host="0.0.0.0", port=port)