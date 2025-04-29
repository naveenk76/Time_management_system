from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateTimeField, TextAreaField
from wtforms.validators import InputRequired, Length, Email

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description')
    due_date = DateTimeField('Due Date', validators=[InputRequired()], format='%Y-%m-%dT%H:%M')  # updated format

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=1, max=150)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
