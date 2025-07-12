from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# セキュリティのためのセッションキー設定
app.secret_key = 'your_secret_key'

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 消費者モデル
class Consumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# アプリケーションコンテキストを手動で開始（データベース作成）
with app.app_context():
    db.create_all()

# 消費者用ログインページ
@app.route('/consumer/login', methods=['GET', 'POST'])
def consumer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 消費者をデータベースから検索
        consumer = Consumer.query.filter_by(username=username).first()
        
        if consumer and check_password_hash(consumer.password, password):
            return redirect(url_for('index'))  # ログイン成功後、メインページにリダイレクト
        else:
            flash('ログイン失敗: ユーザー名またはパスワードが間違っています', 'danger')
    
    return render_template('consumer_login.html')

# 消費者登録ページ
@app.route('/consumer/register', methods=['GET', 'POST'])
def consumer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        # パスワードの確認
        if password != password_confirm:
            flash('パスワードが一致しません', 'danger')
            return redirect(url_for('consumer_register'))
        
        # 既存のユーザー名チェック
        if Consumer.query.filter_by(username=username).first():
            flash('このユーザー名はすでに存在します', 'danger')
            return redirect(url_for('consumer_register'))
        
        # 新しい消費者を作成してデータベースに追加
        hashed_password = generate_password_hash(password)
        new_consumer = Consumer(username=username, password=hashed_password)
        db.session.add(new_consumer)
        db.session.commit()

        flash('アカウントが作成されました。ログインしてください。', 'success')
        return redirect(url_for('consumer_login'))  # 登録後にログインページにリダイレクト

    return render_template('consumer_register.html')

# メインページ（仮）
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
