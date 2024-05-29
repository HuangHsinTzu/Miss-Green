from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Regexp
from wtforms import ValidationError

from myproject.models import User, Farmer

#登入表單
class LoginForm(FlaskForm):
    email = StringField('', validators=[DataRequired(), Email()]) #email格式的檢查Email()
    password = PasswordField('',validators=[DataRequired()]) #必填的欄位檢查validators=[DataRequired()]
    identity = StringField('',validators=[DataRequired()])
    submit = SubmitField('')

#註冊表單
class RegistrationForm(FlaskForm):
    email = StringField('', validators=[DataRequired(), Email()])
    username = StringField('', validators=[DataRequired(), Regexp('^[a-zA-Z]+$', message='只能使用英文字母')])
    password = PasswordField('', validators=[DataRequired(), Length(min=8, message='密碼至少需要8個字元'), EqualTo('pass_confirm', message='密碼需要吻合')])
    pass_confirm = PasswordField('', validators=[DataRequired()])
    phone = StringField('', validators=[DataRequired()])
    identity = StringField('',validators=[DataRequired()])
    submit = SubmitField('')

    def check_email(self):
        """檢查Email"""
        if self.identity.data == "user":
            if User.query.filter_by(email=self.email.data).first():
                raise ValidationError('(電子郵件已經被註冊過了!)')
        elif self.identity.data == "farmer":
            if Farmer.query.filter_by(email=self.email.data).first():
                raise ValidationError('(電子郵件已經被註冊過了!)')

    def check_username(self):
        """檢查username"""
        if self.identity.data == "user":
            if User.query.filter_by(username=self.username.data).first():
                raise ValidationError('(使用者名稱已經存在!)')
        elif self.identity.data == "farmer":
            if Farmer.query.filter_by(username=self.username.data).first():
                raise ValidationError('(使用者名稱已經存在!)')

    def __repr__(self):
        return 'username:%s, email:%s' % (self.username, self.email)

#上架商品表單
class UploadForm(FlaskForm):
    productname = StringField('', validators=[DataRequired()])
    price = StringField('', validators=[DataRequired()])
    category = StringField('', validators=[DataRequired()])
    image_url = StringField('', validators=[DataRequired()])
    description = StringField('', validators=[DataRequired()])
    quantity = StringField('', validators=[DataRequired()])
    submit = SubmitField('')

# 活動報名表單
class ActivitiesRegistrationForm(FlaskForm):
    name = StringField('', validators=[DataRequired()])
    phone = StringField('', validators=[DataRequired()])
    email = StringField('', validators=[DataRequired()])
    submit = SubmitField('')
