from flask import Flask, send_from_directory
from flask import render_template, redirect, request, url_for, flash, abort, session
from werkzeug.utils import escape, secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from wtforms import ValidationError
from flask import jsonify
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from datetime import datetime
#import sqlite3



from myproject.models import User, db, login_manager, Product, ShoppingCart, ShoppingCartItem, Record, Farmer, Order, Activity
from myproject.forms import LoginForm, RegistrationForm, UploadForm
from flask_migrate import Migrate

import os
import traceback

#  取得目前文件資料夾路徑
base_dir = os.path.abspath(os.path.dirname(__file__))


#建立app實體
app = Flask(__name__)


app.config['SECRET_KEY']= 'asecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(base_dir, 'data.sqlite')

# 定义上传文件夹的路径
UPLOAD_FOLDER = os.path.join(base_dir, 'pictures')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)
#增加各頁面路由
#首頁
@app.route('/')
def home():
    user_id = session.get('user_id')
    print(user_id)
    
    if user_id:
        identity = session.get('identity')
        print(identity)
        if identity == 'user':
            latest_products = Product.query.filter(Product.quantity > 0).order_by(Product.id.desc()).limit(8).all()
            return render_template('Index.html', latest_products=latest_products)
        elif identity == 'farmer':
            return redirect(url_for('sellerHome'))
    else:
        # 查詢最後8個商品
        latest_products = Product.query.filter(Product.quantity > 0).order_by(Product.id.desc()).limit(8).all()
        return render_template('Index.html', latest_products=latest_products)

#農夫首頁(訂單管理)
@app.route('/SellerHome')
def sellerHome():
    return render_template('SellerHome.html')

#登入頁面
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    error_message = ''

    if form.validate_on_submit():
        if form.identity.data == 'user':
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                session['user_id'] = user.id
                session['identity'] = 'user'
                error_message = '您已經成功的登入系統'
                next = request.args.get('next', url_for('home'))
                return redirect(next)
            else:
                error_message = '(密碼錯誤)'
                if not user:
                    error_message = '(尚未註冊!請先註冊)'
        elif form.identity.data == 'farmer':
            farmer = Farmer.query.filter_by(email=form.email.data).first()
            if farmer and farmer.check_password(form.password.data):
                login_user(farmer)
                session['user_id'] = farmer.id
                session['identity'] = 'farmer'
                error_message = '您已經成功的登入系統'
                next = request.args.get('next', url_for('sellerHome'))
                return redirect(next)
            else:
                error_message = '(密碼錯誤)'
                if not farmer:
                    error_message = '(尚未註冊!請先註冊)'
        else:
            error_message = '(尚未註冊!請先註冊)'
    return render_template('Login.html',form=form,error_message=error_message)

# 登出(沒頁面，但仍需路由/logout提供給登出使用)
@app.route('/Logout', methods=['GET'])
@login_required  # 確認使用者狀態必須是在登入狀態
def logout():
    
    logout_user()
    session.clear()  # 確保清除所有 session 資料
    flash("您已經登出系統")
    return redirect(url_for('home'))

# 會員頁面
@app.route('/Member')
def showMember():
    user_id = current_user.get_id()
    member = User.query.get(user_id)  # 從資料庫中獲取該會員的資訊
    return render_template('Member.html', name=member.username, phone=member.phone, email=member.email)

#註冊
@app.route('/Signup',methods=['GET','POST']) #POST接收RegistrationForm表單的資料
def signup():
    form = RegistrationForm()
    error_message = ''

    if form.validate_on_submit():
        try:
            form.check_email()
            form.check_username()

            # 根据用户选择的身份存储用户信息到对应的表中
            if form.identity.data == 'user':
                user = User(email=form.email.data,
                            username=form.username.data,
                            password=form.password.data,
                            phone=form.phone.data)
                db.session.add(user)

            elif form.identity.data == 'farmer':
                farmer = Farmer(email=form.email.data,
                                username=form.username.data,
                                password=form.password.data,
                                phone=form.phone.data)
                db.session.add(farmer)
            # add to db table
            
            db.session.commit()
            flash('感謝註冊本系統成為會員，請重新登入~')
            next = request.args.get('next')
            if not next:
                next = url_for('login')
            return redirect(next)
        except ValidationError as e:
            error_message = str(e)
    return render_template('Signup.html',form=form, error_message=error_message)

#商品
@app.route('/Items')
def showProducts():
    # 從資料庫中取得所有商品
    products = Product.query.filter(Product.quantity > 0).all()
    #將products轉為字典
    products_dict = [product_to_dict(product) for product in products]
    return render_template('Items.html', products=products_dict)

#將products轉為字典
def product_to_dict(product):
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'category': product.category,
        'quantity': product.quantity,
        'image_url': product.image_url,
    }

#呈現商品詳細資料
@app.route('/ProductDetail', methods=['GET'])
def ProductDetail():
    product_id = request.args.get('product_id')
    if product_id:
        product = Product.query.filter_by(id =product_id).first()
        if product:
            return render_template('ProductDetail.html', product=product)
    return "Product not found", 404



#上架商品
@app.route('/Upload', methods=['GET', 'POST'])
def upload():
    
    # 獲取當前登錄的農夫用户
    farmer = Farmer.query.get(current_user.id)
    
    if request.method == 'POST':
       
        # 获取表单数据
        productname = request.form.get('productname')
        description = request.form.get('description')
        price = request.form.get('price')
        category = request.form.get('category')
        quantity = request.form.get('quantity')
        image_file = request.files.get('image_file')
        
        # 打印调试信息
        print(f"Received data: {productname}, {description}, {price}, {category}, {quantity}")
        
        # 检查数据是否有效
        if not all([productname, description, price, category, quantity]) or not image_file:
            return jsonify({'error': '所有字段都是必填项'}), 400

        if image_file and allowed_file(image_file.filename):
            filename = image_file.filename
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('uploaded_file', filename=filename, _external=True)
            
            try:
            # 添加商品到数据库
                new_product = farmer.add_product(productname, description, price, category, quantity, image_url)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                print(f"Database error: {str(e)}")
                return jsonify({'error': '數據庫錯誤，無法添加商品'}), 500
        # 将新商品信息返回给前端
        return jsonify({
            'id': new_product.id,
            'name': new_product.name,
            'description': new_product.description,
            'price': new_product.price,
            'category': new_product.category,
            'quantity': new_product.quantity,
            'image_url': new_product.image_url
        }), 200

    else:        
        # 獲取該農夫上架的所有商品
        farmer_products = farmer.products.all()
        return render_template('Upload.html', farmer_products=farmer_products)

#上傳圖片
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

#更新上架商品
@app.route('/Upload/reload', methods=['POST'])
def reload():
    # 获取表单数据
    productname = request.form.get('productname')
    description = request.form.get('description')
    price = request.form.get('price')
    category = request.form.get('category')
    quantity = request.form.get('quantity')
    image_file = request.files.get('image_file')

    original_name = request.form.get('original_name')
    original_price = request.form.get('original_price')
    original_description = request.form.get('original_description')

    # 打印调试信息
    print(f"Received data: {productname}, {description}, {price}, {category}, {quantity}")
    # 将价格字符串转换为浮点数，去掉货币符号
    original_price = float(original_price.replace('$', ''))
    price = float(price.replace('$', ''))
    
    # 获取当前用户的ID
    farmer_id = current_user.id

    # 根据当前用户的ID和其他信息来确定要更新的商品
    product = Product.query.filter_by(farmer_id=farmer_id, name=original_name, price=original_price, description=original_description).first()

    if product:
        # 更新商品信息
        product.name = productname
        product.description = description
        product.price = price
        product.category = category
        product.quantity = quantity

        # 如果上传了新的图片文件，保存图片并更新商品的图片URL
        if image_file:
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(file_path)
            product.image_url = url_for('uploaded_file', filename=filename, _external=True)

        # 提交到数据库
        db.session.commit()

        # 返回更新后的商品信息
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': product.category,
            'quantity': product.quantity,
            'image_url': product.image_url
        }), 200
    else:
        return jsonify({'error': '未找到要更新的商品'}), 404

#刪除商品
@app.route('/Delete_product', methods=['POST'])
def delete_product():
    # 获取表单数据
    productname = request.json.get('productname')
    description = request.json.get('description')
    # 获取当前用户的ID
    farmer_id = current_user.id

    # 查询要删除的商品
    product = Product.query.filter_by(farmer_id=farmer_id, name=productname, description=description).first()

    if product:
        # 删除商品
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': '商品删除成功'}), 200
    else:
        return jsonify({'error': '未找到要删除的商品'}), 404

#上架活動
@app.route('/Add_activities', methods = ['GET', 'POST'])
def add_activities():
    # 獲取當前登錄的農夫用户
    farmer = Farmer.query.get(current_user.id)

    if request.method == 'POST':
        # 获取表单数据
        activityname = request.form['activitiyname']
        date = request.form['date']
        location = request.form['location']
        fee = request.form['fee']
        description = request.form['description']
        image_file = request.files['image']
        capacity = request.form['capacity']

        # 检查数据是否有效
        if not all([activityname, date, location, fee, description, capacity]) or not image_file:
            return jsonify({'error': '所有字段都是必填项'}), 400

        # 將字符串日期轉換為 datetime 對象
        event_date = datetime.strptime(date, '%Y-%m-%d')

        if image_file and allowed_file(image_file.filename):
            filename = image_file.filename
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('uploaded_file', filename=filename, _external=True)
        
            try:
            # 添加商品到数据库
                new_activity = farmer.add_activity(image_url, activityname, event_date, location, fee, description, capacity)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                print(f"Database error: {str(e)}")
                return jsonify({'error': '數據庫錯誤，無法添加活動'}), 500
        return jsonify({
            'id': new_activity.id,
            'name': new_activity.name,
            'description': new_activity.description,
            'fee': new_activity.fee,
            'location': new_activity.location,
            'date': new_activity.event_date.strftime('%Y/%m/%d'),
            'image_url': new_activity.image_url,
            'capacity':new_activity.capacity
        }), 200

    else:    
        # 獲取該農夫上架的所有商品
        farmer_activities = farmer.activities.all()
        return render_template('AddActivities.html', farmer_activities=farmer_activities)

#呈現活動報名狀況詳細資料
@app.route('/ActivityDetail', methods=['GET'])
def activityDetail():
    activity_id = request.args.get('activity_id')
    if activity_id:
        activity = Activity.query.filter_by(id =activity_id).first()
        if activity:
            return render_template('ActivityDetail.html', activity=activity)
    return "Activity not found", 404

#活動報名
@app.route('/ActivitiesRegistration', methods=['GET', 'POST'])
@login_required
def activitiesRegistration():
    form = ActivitiesRegistrationForm()
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')

        print(f"Received data: {name}, {phone}, {email}")

        if not all([name, phone, email]):
            return jsonify({'error': '所有欄位都是必填項'}), 400
        try: 
            # 使用当前登录用户的 ID 创建 User 的实例
            user = db.session.get(User, current_user.id)
            if not user:
                return jsonify({'error': '用戶不存在'}), 404
            new_Activity_mem = user.add_Activity_mem(name, phone, email)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': '資料庫錯誤，無法添加活動會員'}), 500
        
                # 将新商品信息返回给前端
        return jsonify({
            'id': new_Activity_mem.activities_member_id,
            'name': new_Activity_mem.activities_member_name,
            'phone': new_Activity_mem.activities_member_phone,
            'email': new_Activity_mem.activities_member_email
        }), 200
    
    else:        
    # 如果有錯誤，返回報名表單頁面並顯示錯誤信息
        return render_template("ActivitiesRegistration.html", form=form)


#啟動app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)







