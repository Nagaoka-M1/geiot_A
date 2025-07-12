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
# 生産者モデル（消費者用）
class Producer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(1000), nullable=False)
    profile_image = db.Column(db.String(200), nullable=True)
    youtube_video = db.Column(db.String(200), nullable=True)

# アプリケーションコンテキストを手動で開始（データベース作成）
with app.app_context():
    db.create_all()

# 初期データを追加（もしデータが空の場合）
with app.app_context():
    if not Producer.query.first():
        producer = Producer(account_name='立花考志', bio='日本のトランプです。', profile_image='https://pbs.twimg.com/profile_images/1930450937124139008/3akLDAFa_400x400.jpg', youtube_video='https://www.youtube.com/embed/nf12HjJd4g0?si=RinXHtxi7Ogq5yuH')
        db.session.add(producer)
        db.session.commit()

# 生産者用プロフィール表示ページ
@app.route('/producer/profile')
def producer_profile():
    # サンプルで消費者1のデータを仮に表示
    producer = Producer.query.first()  # 最初のプロデューサーを取得
    return render_template('preview_profile.html', producer=producer)

# 生産者用プロフィール編集ページ
@app.route('/producer/edit-profile', methods=['GET', 'POST'])
def producer_edit_profile():
    producer = Producer.query.first()  # 最初のプロデューサーを取得

    if request.method == 'POST':
        producer.account_name = request.form['account_name']
        producer.bio = request.form['bio']
        producer.profile_image = request.form['profile_image']
        producer.youtube_video = request.form['youtube_video']
        
        # 変更をデータベースに保存
        db.session.commit()
        
        flash('プロフィールが更新されました。', 'success')
        return redirect(url_for('producer_profile'))  # 編集後にプロフィールページへリダイレクト

    return render_template('edit_profile.html', producer=producer)


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


