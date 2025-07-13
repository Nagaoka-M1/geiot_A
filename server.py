from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import uuid

app = Flask(__name__)

# セキュリティのためのセッションキー設定
app.secret_key = 'your_secret_key_very_secret_and_random' # より複雑なキーに変更推奨

# ファイルアップロード設定
UPLOAD_FOLDER = 'static/uploads' # 画像を保存するフォルダ
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # 許可するファイル拡張子
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# UPLOAD_FOLDERが存在しない場合は作成
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Consumer, Producer, Product, CartItem モデルの定義
class Consumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    cart_items = db.relationship('CartItem', backref='consumer', lazy=True, cascade="all, delete-orphan")

class Producer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(1000), nullable=False)
    profile_image = db.Column(db.String(200), nullable=True) # 画像URLを保存
    youtube_video = db.Column(db.String(200), nullable=True)
    products = db.relationship('Product', backref='producer', lazy=True, cascade="all, delete-orphan")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    producer_id = db.Column(db.Integer, db.ForeignKey('producer.id'), nullable=False)
    cart_items = db.relationship('CartItem', backref='product', lazy=True, cascade="all, delete-orphan")

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

with app.app_context():
    db.create_all()

# 初期データを追加（もしデータが空の場合）
with app.app_context():
    producer1 = Producer.query.filter_by(username='tachi_farm').first()
    if not producer1:
        # 新しい初期プロフィール画像を static/uploads に保存する例
        default_profile_image_filename = 'default_producer_profile.jpg'
        default_profile_image_path = os.path.join(app.config['UPLOAD_FOLDER'], default_profile_image_filename)
        # ダミー画像ファイルを生成 (もし存在しなければ)
        if not os.path.exists(default_profile_image_path):
            from PIL import Image, ImageDraw, ImageFont # Pillow ライブラリが必要
            try:
                img = Image.new('RGB', (400, 400), color = (76, 175, 80)) # Green-500
                d = ImageDraw.Draw(img)
                # フォントのパスは環境によって異なる可能性があります
                try:
                    font = ImageFont.truetype("arial.ttf", 80) # Windows
                except IOError:
                    try:
                        font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 80) # macOS
                    except IOError:
                        font = ImageFont.load_default() # Fallback
                
                text = "P" # ProducerのP
                text_bbox = d.textbbox((0,0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = (400 - text_width) / 2
                y = (400 - text_height) / 2
                d.text((x, y), text, fill=(255, 255, 255), font=font)
                img.save(default_profile_image_path)
            except ImportError:
                print("Pillow library not found. Please install it with 'pip install Pillow' to generate default image.")
                # Pillowがない場合は、手動で画像を配置するか、他のデフォルトURLを設定
                # 仮のURLを設定し、ユーザーに手動で画像をアップロードしてもらう
                pass 
        
        profile_image_url = url_for('static', filename=f'uploads/{default_profile_image_filename}') if os.path.exists(default_profile_image_path) else 'https://via.placeholder.com/120/CCCCCC/FFFFFF?text=No+Image'


        producer1 = Producer(
            username='tachi_farm',
            password=generate_password_hash('password123'),
            account_name='立花考志',
            bio='日本のトランプです。',
            profile_image=profile_image_url, # 生成したURLを使用
            youtube_video='https://www.youtube.com/embed/M0000000000' # サンプル動画URLを埋め込み形式に
        )
        db.session.add(producer1)
        db.session.commit()
    else:
        # 既存のプロデューサーに username と password がなければ追加（または更新）
        if not producer1.username or not producer1.password:
            producer1.username = 'tachi_farm'
            producer1.password = generate_password_hash('password123')
            db.session.commit()
        # YouTube動画URLがまだ更新されていなければ、埋め込み形式に更新
        if not producer1.youtube_video or not producer1.youtube_video.startswith('https://www.youtube.com/embed/'):
             producer1.youtube_video = 'https://www.youtube.com/embed/M0000000000'
             db.session.commit()
        # プロフィール画像が設定されていなければ、デフォルトを設定 (必要であれば)
        if not producer1.profile_image:
            # ここでデフォルト画像を再設定するかは要検討。通常は登録時に設定される。
            pass


    if not Product.query.first():
        products_data = [
            {'name': '新鮮トマト', 'price': 300, 'description': '甘くてみずみずしい採れたてトマト。', 'image_url': 'https://via.placeholder.com/150/FF6347/FFFFFF?text=Tomato', 'producer_id': producer1.id},
            {'name': 'ほうれん草', 'price': 200, 'description': '栄養満点、シャキシャキのほうれん草。', 'image_url': 'https://via.placeholder.com/150/228B22/FFFFFF?text=Spinach', 'producer_id': producer1.id},
            {'name': '大根', 'price': 250, 'description': '煮物にもサラダにも万能な大根。', 'image_url': 'https://via.placeholder.com/150/ADD8E6/000000?text=Radish', 'producer_id': producer1.id},
            {'name': 'キャベツ', 'price': 180, 'description': '炒め物や生で食べても美味しいキャベツ。', 'image_url': 'https://via.placeholder.com/150/3CB371/FFFFFF?text=Cabbage', 'producer_id': producer1.id},
        ]
        for data in products_data:
            product = Product(**data)
            db.session.add(product)
        db.session.commit()

# 生産者用プロフィール表示ページ (既存の/producer/profileを動的に変更)
@app.route('/producer/profile')
def producer_profile():
    if 'producer_id' not in session:
        flash('生産者としてログインしてください。', 'warning')
        return redirect(url_for('producer_login'))
    
    producer = Producer.query.get(session['producer_id'])
    if not producer:
        flash('生産者アカウントが見つかりません。', 'danger')
        session.pop('producer_id', None)
        return redirect(url_for('producer_login'))
        
    return render_template('preview_profile.html', producer=producer)

# 個別の生産者の公開プロフィールページ (新しいルート)
@app.route('/producer/<int:producer_id>')
def view_producer_profile(producer_id):
    producer = Producer.query.get(producer_id)
    if not producer:
        flash('指定された生産者が見つかりません。', 'danger')
        return redirect(url_for('index'))
    return render_template('public_producer_profile.html', producer=producer)


# 生産者用プロフィール編集ページ
@app.route('/producer/edit-profile', methods=['GET', 'POST'])
def producer_edit_profile():
    if 'producer_id' not in session:
        flash('生産者としてログインしてください。', 'warning')
        return redirect(url_for('producer_login'))
    
    producer = Producer.query.get(session['producer_id'])
    if not producer:
        flash('生産者アカウントが見つかりません。', 'danger')
        session.pop('producer_id', None)
        return redirect(url_for('producer_login'))

    if request.method == 'POST':
        producer.account_name = request.form['account_name']
        producer.bio = request.form['bio']
        producer.youtube_video = request.form['youtube_video']
        
        profile_image_file = request.files.get('profile_image_file') # ファイルを受け取るための新しい名前

        # プロフィール画像のファイルがアップロードされた場合
        if profile_image_file and allowed_file(profile_image_file.filename):
            filename = str(uuid.uuid4()) + os.path.splitext(profile_image_file.filename)[1]
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image_file.save(filepath)
            producer.profile_image = url_for('static', filename=f'uploads/{filename}')
        # ファイルがアップロードされず、かつ既存の画像URLもクリアしたい場合 (オプション)
        # elif not profile_image_file and 'profile_image_file' in request.files and not request.form.get('current_profile_image_url'):
        #     producer.profile_image = None # 画像を削除するロジック

        db.session.commit()
        
        flash('プロフィールが更新されました。', 'success')
        return redirect(url_for('producer_profile'))

    return render_template('edit_profile.html', producer=producer)

# 生産者ログインページ
@app.route('/producer/login', methods=['GET', 'POST'])
def producer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        producer = Producer.query.filter_by(username=username).first()

        if producer and check_password_hash(producer.password, password):
            session['producer_id'] = producer.id
            flash('生産者としてログインしました！', 'success')
            return redirect(url_for('producer_dashboard'))
        else:
            flash('ログイン失敗: ユーザー名またはパスワードが間違っています', 'danger')
    return render_template('producer_login.html')

# 生産者登録ページ
@app.route('/producer/register', methods=['GET', 'POST'])
def producer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        account_name = request.form['account_name']
        bio = request.form.get('bio', '')
        # 登録時にはプロフィール画像のファイルアップロードは受け付けない（URLは可能）
        # もし登録時にファイルアップロードもさせたい場合は、`request.files.get('profile_image_file')`を処理
        profile_image_url_input = request.form.get('profile_image', '')
        youtube_video = request.form.get('youtube_video', '')

        if password != password_confirm:
            flash('パスワードが一致しません', 'danger')
            return redirect(url_for('producer_register'))
        
        if Producer.query.filter_by(username=username).first():
            flash('このユーザー名はすでに存在します', 'danger')
            return redirect(url_for('producer_register'))
        
        hashed_password = generate_password_hash(password)
        new_producer = Producer(
            username=username,
            password=hashed_password,
            account_name=account_name,
            bio=bio,
            profile_image=profile_image_url_input, # ここはURLを受け取るか、上記でファイル処理
            youtube_video=youtube_video
        )
        db.session.add(new_producer)
        db.session.commit()

        flash('生産者アカウントが作成されました。ログインしてください。', 'success')
        return redirect(url_for('producer_login'))

    return render_template('producer_register.html')


@app.route('/producer/logout')
def producer_logout():
    session.pop('producer_id', None)
    flash('生産者アカウントからログアウトしました。', 'info')
    return redirect(url_for('index'))


# 商品出品APIエンドポイント
@app.route('/api/products', methods=['POST'])
def add_product():
    if 'producer_id' not in session:
        return jsonify({'status': 'error', 'message': '生産者としてログインが必要です。'}), 401

    producer_id = session['producer_id']
    producer = Producer.query.get(producer_id)
    if not producer:
        return jsonify({'status': 'error', 'message': '生産者アカウントが見つかりません。'}), 404

    name = request.form.get('productName')
    price_str = request.form.get('productPrice')
    description = request.form.get('productDescription')
    product_image = request.files.get('productImage')

    if not all([name, price_str, description, product_image]):
        return jsonify({'status': 'error', 'message': 'すべてのフィールドを入力してください。'}), 400

    try:
        price = int(price_str)
        if price < 0:
            return jsonify({'status': 'error', 'message': '価格は0以上である必要があります。'}), 400
    except ValueError:
        return jsonify({'status': 'error', 'message': '価格は有効な数値である必要があります。'}), 400

    image_url = None
    if product_image and allowed_file(product_image.filename):
        filename = str(uuid.uuid4()) + os.path.splitext(product_image.filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        product_image.save(filepath)
        image_url = url_for('static', filename=f'uploads/{filename}')
    else:
        return jsonify({'status': 'error', 'message': '無効なファイル形式です。許可されるのはpng, jpg, jpeg, gifです。'}), 400

    new_product = Product(
        name=name,
        price=price,
        description=description,
        image_url=image_url,
        producer_id=producer.id
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({'status': 'success', 'message': '商品が正常に出品されました！', 'product_id': new_product.id}), 201


# 消費者用ログインページ
@app.route('/consumer/login', methods=['GET', 'POST'])
def consumer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        consumer = Consumer.query.filter_by(username=username).first()
        
        if consumer and check_password_hash(consumer.password, password):
            session['consumer_id'] = consumer.id
            flash('ログインしました！', 'success')
            return redirect(url_for('index'))
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
        
        if password != password_confirm:
            flash('パスワードが一致しません', 'danger')
            return redirect(url_for('consumer_register'))
        
        if Consumer.query.filter_by(username=username).first():
            flash('このユーザー名はすでに存在します', 'danger')
            return redirect(url_for('consumer_register'))
        
        hashed_password = generate_password_hash(password)
        new_consumer = Consumer(username=username, password=hashed_password)
        db.session.add(new_consumer)
        db.session.commit()

        flash('アカウントが作成されました。ログインしてください。', 'success')
        return redirect(url_for('consumer_login'))

    return render_template('consumer_register.html')

# 消費者ログアウト
@app.route('/consumer/logout')
def consumer_logout():
    session.pop('consumer_id', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('index'))

# カートに商品を追加するAPIエンドポイント
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'consumer_id' not in session:
        return jsonify({'status': 'error', 'message': 'ログインが必要です。'}), 401

    consumer_id = session['consumer_id']
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'status': 'error', 'message': '商品IDが必要です。'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'status': 'error', 'message': '商品が見つかりません。'}), 404

    cart_item = CartItem.query.filter_by(consumer_id=consumer_id, product_id=product_id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(consumer_id=consumer_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'カートに商品を追加しました！'})

# カートから商品を削除するAPIエンドポイント
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'consumer_id' not in session:
        return jsonify({'status': 'error', 'message': 'ログインが必要です。'}), 401

    consumer_id = session['consumer_id']
    data = request.get_json()
    cart_item_id = data.get('cart_item_id')

    if not cart_item_id:
        return jsonify({'status': 'error', 'message': 'カートアイテムIDが必要です。'}), 400

    cart_item = CartItem.query.filter_by(id=cart_item_id, consumer_id=consumer_id).first()

    if not cart_item:
        return jsonify({'status': 'error', 'message': 'カートアイテムが見つからないか、あなたのカートにはありません。'}), 404

    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'カートから商品を削除しました。'})

# メインページ
@app.route('/')
def index():
    products = Product.query.options(db.joinedload(Product.producer)).all()
    return render_template('index.html', products=products)

# カート表示ページ
@app.route('/cart')
def view_cart():
    if 'consumer_id' not in session:
        flash('カートを見るにはログインが必要です。', 'warning')
        return redirect(url_for('consumer_login'))

    consumer_id = session['consumer_id']
    cart_items = CartItem.query.filter_by(consumer_id=consumer_id).options(db.joinedload(CartItem.product)).all()
    
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


# 生産者ダッシュボード
@app.route('/producer')
def producer_dashboard():
    if 'producer_id' not in session:
        flash('生産者としてログインしてください。', 'warning')
        return redirect(url_for('producer_login'))
    
    producer = Producer.query.get(session['producer_id'])
    if not producer:
        flash('生産者アカウントが見つかりません。', 'danger')
        session.pop('producer_id', None)
        return redirect(url_for('producer_login'))
        
    return render_template('producer_dashboard.html', producer=producer)

if __name__ == '__main__':
    # Pillow がインストールされていない場合は警告を表示
    try:
        import PIL
    except ImportError:
        print("\nWARNING: Pillow library is not installed. Default profile image generation may fail.")
        print("Please install it with 'pip install Pillow' for full functionality.\n")
    app.run(debug=True)