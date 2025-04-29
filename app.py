from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateTimeField, TextAreaField
from wtforms.validators import InputRequired, Length, Email
import os
import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///time_entries.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('time_entries', lazy=True))

# Forms
class TimeEntryForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description')
    start_time = DateTimeField('Start Time', validators=[InputRequired()], format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('End Time', validators=[InputRequired()], format='%Y-%m-%dT%H:%M')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=1, max=150)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    time_entries = TimeEntry.query.filter_by(user_id=current_user.id).all()
    current_time = datetime.datetime.now()
    return render_template('dashboard.html', time_entries=time_entries, current_time=current_time)

@app.route('/time_entry/new', methods=['GET', 'POST'])
@login_required
def new_time_entry():
    form = TimeEntryForm()
    if form.validate_on_submit():
        time_entry = TimeEntry(
            title=form.title.data,
            description=form.description.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            user_id=current_user.id
        )
        db.session.add(time_entry)
        db.session.commit()
        flash('Time entry created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_time_entry.html', form=form, edit=False)

@app.route('/time_entry/<int:time_entry_id>')
@login_required
def view_time_entry(time_entry_id):
    time_entry = TimeEntry.query.get_or_404(time_entry_id)
    if time_entry.user_id != current_user.id:
        flash("You are not authorized to view this entry.", "danger")
        return redirect(url_for('dashboard'))
    return render_template('view_time_entry.html', time_entry=time_entry)

@app.route('/time_entry/<int:time_entry_id>/delete')
@login_required
def delete_time_entry(time_entry_id):
    time_entry = TimeEntry.query.get_or_404(time_entry_id)
    if time_entry.user_id != current_user.id:
        flash("You can't delete someone else's entry!", "danger")
        return redirect(url_for('dashboard'))
    db.session.delete(time_entry)
    db.session.commit()
    flash('Time entry deleted.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/time_entry/<int:time_entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_time_entry(time_entry_id):
    time_entry = TimeEntry.query.get_or_404(time_entry_id)
    if time_entry.user_id != current_user.id:
        flash("Not authorized.", "danger")
        return redirect(url_for('dashboard'))
    form = TimeEntryForm(obj=time_entry)
    if form.validate_on_submit():
        time_entry.title = form.title.data
        time_entry.description = form.description.data
        time_entry.start_time = form.start_time.data
        time_entry.end_time = form.end_time.data
        db.session.commit()
        flash('Time entry updated successfully.', 'success')
        return redirect(url_for('view_time_entry', time_entry_id=time_entry.id))
    return render_template('add_time_entry.html', form=form, edit=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('register.html', form=form)

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# Make sure app runs when executed
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures the DB tables are created
    print("Flask app running...")
    app.run(debug=True)
