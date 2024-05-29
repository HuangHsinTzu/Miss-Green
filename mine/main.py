from flask import Flask, render_template, redirect, request, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from wtforms import ValidationError
import os
import traceback
from myproject.models import User, db, login_manager, Product, Farmer, Activities_member
from myproject.forms import LoginForm, RegistrationForm, ActivitiesRegistrationForm
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError


# 取得目前文件資料夾路徑
base_dir = os.path.abspath(os.path.dirname(__file__))

# 建立app實體
app = Flask(__name__)

app.config['SECRET_KEY'] = 'asecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'data.sqlite')

db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

# 增加各頁面路由
# 首頁
@app.route('/')
def home():
    user_id = session.get('user_id')
    if user_id:
        identity = session.get('identity')
        if identity == 'user':
            return render_template('Index.html')
        elif identity == 'farmer':
            return redirect(url_for('sellerHome'))
    else:
        return render_template('Index.html')

# 農夫首頁(訂單管理)
@app.route('/sellerHome')
def sellerHome():
    return render_template('SellerHome.html')

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error_message = ''

    try:
        if form.validate_on_submit():
            if form.identity.data == 'user':
                user = User.query.filter_by(email=form.email.data).first()
                if user and user.check_password(form.password.data):
                    login_user(user)
                    session['user_id'] = user.id
                    session['identity'] = 'user'
                    flash('您已經成功的登入系統')
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
                    flash('您已經成功的登入系統')
                    next = request.args.get('next', url_for('sellerHome'))
                    return redirect(next)
                else:
                    error_message = '(密碼錯誤)'
                    if not farmer:
                        error_message = '(尚未註冊!請先註冊)'
            else:
                error_message = '(尚未註冊!請先註冊)'
    except Exception as e:
        error_message = f'發生錯誤: {str(e)}'
        return redirect(url_for('error', message=error_message))

    return render_template('Login.html', form=form, error_message=error_message)


# 登出(沒頁面，但仍需路由/logout提供給登出使用)
@app.route('/logout')
@login_required  # 確認使用者狀態必須是在登入狀態
def logout():
    logout_user()
    session.clear()  # 確保清除所有 session 資料
    flash("您已經登出系統")
    return redirect(url_for('home'))

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

# 會員頁面
@app.route('/member')
def showMember():
    user_id = current_user.get_id()
    member = User.query.get(user_id)  # 從資料庫中獲取該會員的資訊
    return render_template('Member.html', name=member.username, phone=member.phone, email=member.email)

# 商品
@app.route('/Items')
def showProducts():
    # 從資料庫中取得所有商品
    products = Product.query.all()
    return render_template('Items.html', products=products)

# 上架商品
@app.route('/upload', methods=['GET', 'POST'])
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
        image_url = request.form.get('image_url')

        # 检查数据是否有效
        if not all([productname, description, price, category, quantity]):
            return jsonify({'error': '所有字段都是必填项'}), 400

        try:
            # 添加商品到数据库
            new_product = farmer.add_product(productname, description, price, category, quantity, image_url)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': '数据库错误，无法添加商品'}), 500

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



#---updated start line-----------------------------------------------------------------------
# 1. 幫login()加try-except
# 2. 定義錯誤頁面的路由
# 3. home連接到的page
@app.route('/error')
def error():
    message = request.args.get('message', '未知錯誤')
    return render_template('error.html', message=message)
# 3. 活動報名

# 活動報名
@app.route('/ActivitiesRegistration', methods=['GET', 'POST'])
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
            User = User()
            new_Activity_mem = User.add_Activity_mem(name, phone, email)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': '資料庫錯誤，無法添加活動會員'}), 500
        
                # 将新商品信息返回给前端
        return jsonify({
            'id': new_Activity_mem.id,
            'name': new_Activity_mem.name,
            'phone': new_Activity_mem.phone,
            'email': new_Activity_mem.email
        }), 200
    
    else:        
    # 如果有錯誤，返回報名表單頁面並顯示錯誤信息
        return render_template("ActivitiesRegistration.html", form=form)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found: 404"), 404




'''
import os

print("Current working directory:", os.getcwd())
print("ActivitiesRegistration.html exists:", os.path.isfile('templates/ActivitiesRegistration.html'))

'''
# 啟動app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

