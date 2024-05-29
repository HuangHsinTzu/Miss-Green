#from myproject import db, login_manager
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from datetime import datetime


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

#繼承資料庫db.Model與UserMixin建立買家資料表User Class
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    # columns
    id       = db.Column('id',db.Integer, primary_key = True)
    email    = db.Column(db.String(64),unique=True, index=True)
    username = db.Column(db.String(64),unique=True, index=True)
    password = db.Column(db.String(128))
    phone = db.Column(db.String(32))

    # 定義與購物車的關聯
    cart = db.relationship('ShoppingCart', backref='user', uselist=False)
    
    def __init__(self, email, username, password, phone):
        """初始化"""
        self.email = email
        self.username = username
        self.password = password
        self.phone = phone
    
    def check_password(self, password):
        """檢查使用者密碼"""
        return self.password == password 

    def add_Activity_mem(self, activities_member_name, activities_member_phone, activities_member_email):
        new_ACtivity_mem = Activities_member(activities_member_id=self.id, activities_member_name=activities_member_name, activities_member_phone=activities_member_phone, activities_member_email=activities_member_email)
        db.session.add(new_ACtivity_mem)

        return new_ACtivity_mem
#賣家
class Farmer(UserMixin, db.Model):
    __tablename__ = 'farmers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    username = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(32))

    products = db.relationship('Product', backref='farmer', lazy='dynamic')

    def __init__(self, email, username, password, phone):
        self.username = username
        self.email = email
        self.password = password
        self.phone = phone

    def check_password(self, password):
        """檢查使用者密碼"""
        return self.password == password

    def add_product(self, name, description, price, category, quantity, image_url):
        new_product = Product(name=name, description=description, price=price, category=category, quantity=quantity, image_url=image_url, farmer_id=self.id)
        db.session.add(new_product)
        

        return new_product

    def remove_product(self, product_id):
        product = Product.query.get(product_id)
        if product and product.farmer_id == self.id:
            db.session.delete(product)
            db.session.commit()

    def get_orders(self):
        return Order.query.join(Product).filter(Product.farmer_id == self.id).all()

#對應出資料庫中實際的User
#載入已登入的用戶
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    if user:
        return user
    else:
        return Farmer.query.get(user_id)


#商品
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(256), nullable=False)

    # 外鍵關係
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)

    def __init__(self, name, description, price, category, quantity, image_url, farmer_id):
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.quantity = quantity
        self.image_url = image_url
        self.farmer_id = farmer_id

#購物車
class ShoppingCart(db.Model):
    __tablename__ = 'shoppingcart'

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    items = db.relationship('Product', secondary='shopping_cart_products')

    def __init__(self, buyer_id):
        self.buyer_id = buyer_id

    def add_item(self, product_id):
        product = Product.query.get(product_id)
        if product:
            self.items.append(product)
            db.session.commit()
            return True
        return False

    def remove_item(self, product_id):
        product = Product.query.get(product_id)
        if product in self.items:
            self.items.remove(product)
            db.session.commit()
            return True
        return False

    def clear_cart(self):
        self.items = []
        db.session.commit()

#Product和ShoppingCart間的多對多關聯表
class ShoppingCartItem(db.Model):
    __tablename__ = 'shopping_cart_products'
    cart_id = db.Column(db.Integer, db.ForeignKey('shoppingcart.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)

    def __init__(self, cart_id, product_id):
        self.cart_id = cart_id
        self.product_id = product_id

#購買紀錄
class Record(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, user_id, product_id, quantity):
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity

#訂單
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity

#活動報名
class Activities_member(UserMixin, db.Model):
    __tablename__ = 'activities_members'
    activities_member_id = db.Column(db.Integer, primary_key = True)
    activities_member_name = db.Column(db.String(32), nullable = False)
    activities_member_phone = db.Column(db.String(32), nullable = False)
    activities_member_email = db.Column(db.String(32), nullable = False)

