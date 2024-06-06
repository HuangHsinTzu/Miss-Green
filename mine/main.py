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



from myproject.models import User, db, login_manager, Product, ShoppingCart, ShoppingCartItem, Record, Farmer, Order, Activity, Activities_reg_rec
from myproject.forms import LoginForm, RegistrationForm, UploadForm, ActivitiesRegistrationForm
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
    if user_id:
        is_logged_in = 'user_id' in session
        print(is_logged_in)
        identity = session.get('identity')
        if identity == 'user':
            latest_products = Product.query.filter(Product.quantity > 0).order_by(Product.id.desc()).limit(8).all()
            return render_template('Index.html', latest_products=latest_products, is_logged_in=is_logged_in)
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
    user_id = session.get('user_id')
    is_logged_in = 'user_id' in session
    form = LoginForm()
    print(is_logged_in)
    try:
        if form.validate_on_submit():
            if form.identity.data == 'user':
                user = User.query.filter_by(email=form.email.data).first()
                if user and user.check_password(form.password.data):
                    login_user(user)
                    session['user_id'] = user.id
                    session['identity'] = 'user'
                    flash('您已經成功的登入系統')
                    is_logged_in = 'user_id' in session
                    print(is_logged_in)
                    next = request.args.get('next', url_for('home'))
                    return redirect(next)
                else:                    
                    if not user:
                        flash('尚未註冊!請先註冊')
                    else:
                        flash('密碼錯誤')
            elif form.identity.data == 'farmer':
                farmer = Farmer.query.filter_by(email=form.email.data).first()
                if farmer and farmer.check_password(form.password.data):
                    login_user(farmer)
                    session['user_id'] = farmer.id
                    session['identity'] = 'farmer'
                    flash('您已經成功的登入系統')
                    next = request.args.get('next', url_for('sellerHome'))
                    return redirect(next)
                else:
                    flash('密碼錯誤')
                    if not farmer:
                        flash('尚未註冊!請先註冊')
            else:
                flash('尚未註冊!請先註冊')
    except Exception as e:
        flash(f'發生錯誤: {str(e)}')
        return redirect(url_for('error', message=f'發生錯誤: {str(e)}'))

    return render_template('Login.html', form=form, is_logged_in=is_logged_in)


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
    is_logged_in = 'user_id' in session
    user_id = current_user.get_id()
    member = User.query.get(user_id)  # 從資料庫中獲取該會員的資訊
    return render_template('Member.html', name=member.username, phone=member.phone, email=member.email, is_logged_in=is_logged_in)

#註冊
@app.route('/Signup',methods=['GET','POST']) #POST接收RegistrationForm表單的資料
def signup():
    is_logged_in = 'user_id' in session
    form = RegistrationForm()

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
            flash(str(e))
    return render_template('Signup.html',form=form, is_logged_in=is_logged_in)

# 商品
@app.route('/Items')
def showProducts():
    is_logged_in = 'user_id' in session
    # 從資料庫中取得所有商品
    products = Product.query.filter(Product.quantity > 0).all()
    #將products轉為字典
    products_dict = [product_to_dict(product) for product in products]
    return render_template('Items.html', products=products_dict, is_logged_in=is_logged_in)

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
    is_logged_in = 'user_id' in session
    print(is_logged_in)
    product_id = request.args.get('product_id')
    if product_id:
        product = Product.query.filter_by(id =product_id).first()
        if product:
            return render_template('ProductDetail.html', product=product, is_logged_in=is_logged_in)
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
        status = 1
        
        # 检查数据是否有效
        if not all([activityname, date, location, fee, description]) or not image_file:
            return jsonify({'error': '所有字段都是必填项'}), 400

        # 將字符串日期轉換為 datetime 對象
        event_date = datetime.strptime(date, '%Y-%m-%d')

        if image_file and allowed_file(image_file.filename):
            filename = image_file.filename
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('uploaded_file', filename=filename, _external=True)
        
            try:
            # 添加商品到数据库
                new_activity = farmer.add_activity(image_url, activityname, event_date, location, fee, description)
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
            'event_date': new_activity.event_date.strftime('%Y/%m/%d'),
            'image_url': new_activity.image_url,
        }), 200

    else:    
        # 獲取該農夫上架的所有商品
        farmer_activities = farmer.activities.all()
        return render_template('AddActivities.html', farmer_activities=farmer_activities)

#農夫編輯活動取得原始資料
@app.route('/GetActivityDetail', methods=['GET'])
def get_activity_detail():
    activity_id = request.args.get('id')
    if not activity_id:
        return jsonify({'error': '活動ID缺失'}), 400

    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify({'error': '活動未找到'}), 404

    activity_data = {
        'id': activity.id,
        'name': activity.name,
        'event_date': activity.event_date.strftime('%Y/%m/%d'),
        'location': activity.location,
        'fee': activity.fee,
        'description': activity.description,
        'image_url': activity.image_url
    }
    return jsonify(activity_data)

#農夫編輯活動後更新
@app.route('/UpdateActivity', methods=['POST'])
def update_activity():
    activity_id = request.form.get('id')
    if not activity_id:
        return jsonify({'error': '活動ID缺失'}), 400

    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify({'error': '活動未找到'}), 404

    print("Received name:", request.form.get('activityname'),request.form.get('location'))
    activity.name = request.form.get('activityname', activity.name)
    # 將字符串日期轉換為 datetime 對象
    date_str = request.form.get('event_date', None)
    if date_str:
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%d')
            activity.event_date = event_date
        except ValueError:
            return jsonify({'error': '無效的日期格式，應為YYYY-MM-DD'}), 400
    else:
        activity.event_date = activity.event_date
    activity.location = request.form.get('location', activity.location)
    activity.fee = request.form.get('fee', activity.fee)
    activity.description = request.form.get('description', activity.description)
    image_file = request.form.get('image_file')

    if image_file:
        filename = secure_filename(image_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(file_path)
        activity.image_url = url_for('uploaded_file', filename=filename, _external=True)

    db.session.commit()
    return jsonify({'success': True})

#農夫刪除活動
@app.route('/DeleteActivity', methods=['POST'])
def delete_activity():
    activity_id = request.form.get('id')
    if not activity_id:
        return jsonify({'error': '活動ID缺失'}), 400

    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify({'error': '活動未找到'}), 404

    # 将状态更新为 "0"
    activity.status = "已取消"
    db.session.commit()
    return jsonify({'success': True})

#呈現活動報名狀況詳細資料
@app.route('/ActivityDetail', methods=['GET'])
def activityDetail():
    activity_id = request.args.get('activity_id')
    if activity_id:
        activity = Activity.query.filter_by(id =activity_id).first()
        if activity:
            # 从 activities_reg_rec 表中检索具有特定 activity_id 的数据
            try:
                activity_reg_data = Activities_reg_rec.query.filter_by(activity_id=activity_id).all()
                print(activity_reg_data)
                return render_template('ActivityDetail.html', activity=activity, activity_reg_data=activity_reg_data)
            except IntegrityError as e:
                db.session.rollback()
                print(f"Database error: {str(e)}")
                return "An error occurred while querying the database", 500
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
        activity_id = request.form.get('activity_id') # 獲取 activity_id

        print(f"Received data: {name}, {phone}, {email}, {activity_id}")

        if not all([name, phone, email, activity_id]):
            return jsonify({'error': '所有欄位都是必填項'}), 400
        try:
            user_id = current_user.id
            # 使用当前登录用户的 ID 创建 User 的实例
            user = db.session.get(User, current_user.id)
            if not user:
                return jsonify({'error': '用戶不存在'}), 404
            # 确保 activity_id 对应的活动存在
            activity = db.session.get(Activity, activity_id)
            if not activity:
                return jsonify({'error': '活动不存在'}), 404
            new_Activity_mem = user.add_Activity_mem(name, phone, email, user_id, activity_id)
            db.session.commit()

            # 獲取使用者成功報名的活動
            activities_reg = Activities_reg_rec.query.filter_by(activities_member_email=user.email).all()

        except IntegrityError as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': '資料庫錯誤，無法添加活動會員'}), 500
        
                # 将新商品信息返回给前端
        return jsonify({
            'name': new_Activity_mem.activities_member_name,
            'phone': new_Activity_mem.activities_member_phone,
            'email': new_Activity_mem.activities_member_email,
            'activity_id': new_Activity_mem.activity_id,
            'activities': [{'name': activity.activities_member_name, 'phone': activity.activities_member_phone, 'email': activity.activities_member_email} for activity in activities_reg]
        }), 200
    
    elif request.method == 'GET':
        # 取得當前日期和時間
        current_time = datetime.now()

        # 获取当前用户的已报名活动记录，并过滤未过期的活动
        user = db.session.get(User, current_user.id)
        if not user:
            return jsonify({'error': '用戶不存在'}), 404
        
        activities_regs = Activities_reg_rec.query.join(Activity, Activities_reg_rec.activity_id == Activity.id)\
            .filter(Activities_reg_rec.activities_member_email == user.email, Activity.event_date > current_time).all() # 獲取會員的報名紀錄
        activities_regs_dict = [activities_reg_to_dict(activities_reg) for activities_reg in activities_regs]
        activities = Activity.query.filter(Activity.event_date > current_time).all()
        activities_dict = [activity_to_dict(activity) for activity in activities]
        print(activities_regs_dict)
        form = ActivitiesRegistrationForm()
        # 如果有錯誤，返回報名表單頁面並顯示錯誤信息
        return render_template("ActivitiesRegistration.html", form=form, activities=activities_dict, user_activities=activities_regs_dict)

#將activities轉為字典
def activity_to_dict(activity):
    return {
        'id': activity.id,
        'name': activity.name,
        'event_date':activity.event_date.strftime('%Y/%m/%d'),
        'description': activity.description,
        'fee': activity.fee,
        'image_url': activity.image_url,
        'location': activity.location,
        'status': activity.status
    }

def activities_reg_to_dict(activities_reg):
    return {
        'id': activities_reg.activity.id,
        'name': activities_reg.activity.name,
        'event_date': activities_reg.activity.event_date,
        'location': activities_reg.activity.location,
        'status': activities_reg.activity.status
    }

# 取消報名
@app.route('/CancelRegistration', methods=['POST'])
def cancel_registration():
    try:
        data = request.get_json()
        activity_id = data.get('activity_id')
        user_id = current_user.id
        # Find the registration entry
        registration = Activities_reg_rec.query.filter_by(user_id=user_id, activity_id=activity_id).first()

        if registration:
            db.session.delete(registration)
            db.session.commit()
            return jsonify({"message": "Registration cancelled successfully."}), 200
        else:
            return jsonify({"message": "Registration not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found: 404"), 404

#添加商品到購物車
@app.route('/SaveCart', methods=['POST'])
def save_cart():
    data = request.get_json()
    product_ids = data.get('product_ids')
    buyer_id = current_user.get_id()  # 假设有一个函数可以获取当前用户的 ID

    if not product_ids:
        return jsonify({'success': False, 'message': 'No products in cart'})

    # 查找或创建购物车
    cart = ShoppingCart.query.filter_by(buyer_id=buyer_id).first()
    if not cart:
        cart = ShoppingCart(buyer_id=buyer_id)
        db.session.add(cart)

    # 清除当前购物车的所有商品
    cart.clear_cart()

    # 添加所有商品到购物车
    for product_id in product_ids:
        cart.add_item(product_id)

    return jsonify({'success': True, 'message': 'Cart saved successfully'})

#移除購物車商品
@app.route('/RemoveFromCart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required'})

    buyer_id = current_user.get_id()
    cart = ShoppingCart.query.filter_by(buyer_id=buyer_id).first()

    if cart and cart.remove_item(product_id):
        return jsonify({'success': True, 'message': 'Product removed from cart'})
    else:
        return jsonify({'success': False, 'message': 'Product not found in cart'})


#呈現使用者購物車內容
@app.route('/Checkout', methods=['GET', 'POST'])
def checkout():
    user_id = current_user.get_id()
    shopping_cart = ShoppingCart.query.filter_by(buyer_id=user_id).first()
    if shopping_cart:
        # 获取购物车中的所有商品
        cart_items = shopping_cart.items
        cart_items_dict = [item_to_dict(item) for item in cart_items ]
    else:
        cart_items_dict = []

    return render_template('CheckOut.html', items=cart_items_dict)

def item_to_dict(item):
    return{
        'id':item.id,
        'name':item.name,
        'price':item.price,
        'quantity':item.quantity,
    }

# 啟動app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=6001)
