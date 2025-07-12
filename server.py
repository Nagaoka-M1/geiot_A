from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)

# セキュリティのためのセッションキー設定
app.secret_key = 'your_secret_key_very_secret_and_random' # より複雑なキーに変更推奨

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 消費者モデル
class Consumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # Consumer は複数の CartItem を持つ (1対多のリレーション)
    cart_items = db.relationship('CartItem', backref='consumer', lazy=True, cascade="all, delete-orphan")

# 生産者モデル（消費者用）
class Producer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(1000), nullable=False)
    profile_image = db.Column(db.String(200), nullable=True)
    youtube_video = db.Column(db.String(200), nullable=True)

# 商品モデルを追加
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False) # 価格は整数で保存
    description = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    # Product は複数の CartItem に含まれうる (1対多のリレーション)
    cart_items = db.relationship('CartItem', backref='product', lazy=True, cascade="all, delete-orphan")

# カートアイテムモデルを追加
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # 同じ消費者と商品の組み合わせでユニークであることを保証 (オプション)
    # __table_args__ = (db.UniqueConstraint('consumer_id', 'product_id', name='_consumer_product_uc'),)


# アプリケーションコンテキストを手動で開始（データベース作成）
with app.app_context():
    db.create_all()

# 初期データを追加（もしデータが空の場合）
with app.app_context():
    # 生産者データの追加
    if not Producer.query.first():
        producer = Producer(account_name='立花考志', bio='日本のトランプです。', profile_image='https://pbs.twimg.com/profile_images/1930450937124139008/3akLDAFa_400x400.jpg', youtube_video='https://www.youtube.com/embed/nf12HjJd4g0?si=RinXHtxi7Ogq5yuH')
        db.session.add(producer)
        db.session.commit()

    # 商品データの追加
    if not Product.query.first():
        products_data = [
            {'name': '新鮮トマト', 'price': 300, 'description': '甘くてみずみずしい採れたてトマト。', 'image_url': 'https://via.placeholder.com/150/FF6347/FFFFFF?text=Tomato'},
            {'name': 'ほうれん草', 'price': 200, 'description': '栄養満点、シャキシャキのほうれん草。', 'image_url': 'https://via.placeholder.com/150/228B22/FFFFFF?text=Spinach'},
            {'name': '大根', 'price': 250, 'description': '煮物にもサラダにも万能な大根。', 'image_url': 'https://via.placeholder.com/150/ADD8E6/000000?text=Radish'},
            {'name': 'キャベツ', 'price': 180, 'description': '炒め物や生で食べても美味しいキャベツ。', 'image_url': 'https://via.placeholder.com/150/3CB371/FFFFFF?text=Cabbage'},
            {'name': 'キュウリ', 'price': 150, 'description': '新鮮で歯ごたえの良いキュウリ。', 'image_url': 'https://via.placeholder.com/150/6B8E23/FFFFFF?text=Cucumber'},
            {'name': 'なす', 'price': 220, 'description': '煮ても焼いても美味しいとろけるナス。', 'image_url': 'https://via.placeholder.com/150/8B008B/FFFFFF?text=Eggplant'},
            {'name': 'ピーマン', 'price': 160, 'description': '彩り豊かで苦味の少ないピーマン。', 'image_url': 'https://via.placeholder.com/150/008000/FFFFFF?text=Pepper'},
            {'name': 'じゃがいも', 'price': 280, 'description': 'ホクホクとした食感のじゃがいも。', 'image_url': 'https://via.placeholder.com/150/DAA520/FFFFFF?text=Potato'},
        ]
        for data in products_data:
            product = Product(**data)
            db.session.add(product)
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
            session['consumer_id'] = consumer.id # ログイン成功時にセッションにIDを保存
            flash('ログインしました！', 'success')
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

# 消費者ログアウト
@app.route('/consumer/logout')
def consumer_logout():
    session.pop('consumer_id', None) # セッションからユーザーIDを削除
    flash('ログアウトしました。', 'info')
    return redirect(url_for('index'))

# カートに商品を追加するAPIエンドポイント
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'consumer_id' not in session:
        return {'status': 'error', 'message': 'ログインが必要です。'}, 401 # ログインしていない場合はエラー

    consumer_id = session['consumer_id']
    data = request.get_json() # JSON形式でデータを受け取る
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1) # 数量が指定されなければデフォルト1

    if not product_id:
        return {'status': 'error', 'message': '商品IDが必要です。'}, 400

    product = Product.query.get(product_id)
    if not product:
        return {'status': 'error', 'message': '商品が見つかりません。'}, 404

    # 既存のカートアイテムを検索
    cart_item = CartItem.query.filter_by(consumer_id=consumer_id, product_id=product_id).first()

    if cart_item:
        # 既存のアイテムがある場合は数量を更新
        cart_item.quantity += quantity
    else:
        # 新しいアイテムとして追加
        cart_item = CartItem(consumer_id=consumer_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return {'status': 'success', 'message': 'カートに商品を追加しました！'}

# カートから商品を削除するAPIエンドポイント
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'consumer_id' not in session:
        return {'status': 'error', 'message': 'ログインが必要です。'}, 401

    consumer_id = session['consumer_id']
    data = request.get_json()
    cart_item_id = data.get('cart_item_id')

    if not cart_item_id:
        return {'status': 'error', 'message': 'カートアイテムIDが必要です。'}, 400

    cart_item = CartItem.query.filter_by(id=cart_item_id, consumer_id=consumer_id).first()

    if not cart_item:
        return {'status': 'error', 'message': 'カートアイテムが見つからないか、あなたのカートにはありません。'}, 404

    db.session.delete(cart_item)
    db.session.commit()
    return {'status': 'success', 'message': 'カートから商品を削除しました。'}

# メインページ
@app.route('/')
def index():
    products = Product.query.all() # 全ての商品を取得
    return render_template('index.html', products=products) # 商品データをテンプレートに渡す

# カート表示ページ
@app.route('/cart')
def view_cart():
    if 'consumer_id' not in session:
        flash('カートを見るにはログインが必要です。', 'warning')
        return redirect(url_for('consumer_login'))

    consumer_id = session['consumer_id']
    # ログインしているユーザーのカートアイテムと、それに関連する商品情報を取得
    cart_items = CartItem.query.filter_by(consumer_id=consumer_id).all()
    
    # 合計金額を計算
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


# 生産者ダッシュボード
@app.route('/producer')
def producer():
    return render_template('producer_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)