from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Замените на свой секретный ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///salon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Модель записи
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(255), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    appointment_date = db.Column(db.String(10), nullable=False)
    appointment_time = db.Column(db.String(5), nullable=False)

# Создание базы данных
with app.app_context():
    db.create_all()
    # Добавьте администратора (один раз)
    if not User.query.first():
        admin = User(username='admin', password='password')  # В реальности используйте хеширование пароля
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Форма для входа
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = StringField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

# Форма для записи
class AppointmentForm(FlaskForm):
    client_name = StringField('Имя клиента', validators=[DataRequired()])
    service = SelectField('Услуга', choices=[('Маникюр', 'Маникюр'), ('Педикюр', 'Педикюр'), ('Наращивание ногтей', 'Наращивание ногтей')], validators=[DataRequired()])
    appointment_date = DateField('Дата', validators=[DataRequired()])
    appointment_time = TimeField('Время', validators=[DataRequired()])
    submit = SubmitField('Записаться')

    def validate_appointment_date(self, field):
        if field.data < datetime.now().date():
            raise ValidationError('Дата записи не может быть в прошлом.')

    def validate_appointment_time(self, field):
        if self.appointment_date.data == datetime.now().date() and field.data < datetime.now().time():
            raise ValidationError('Время записи не может быть в прошлом.')

# Маршрут для входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:  # В реальности используйте хеширование
            login_user(user)
            return redirect(url_for('appointments'))
        flash('Неверный логин или пароль', 'danger')
    return render_template('login.html', form=form)

# Маршрут для выхода
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Добавление записи
@app.route('/add_appointment', methods=['GET', 'POST'])
def add_appointment():
    form = AppointmentForm()
    if form.validate_on_submit():
        new_appointment = Appointment(
            client_name=form.client_name.data,
            service=form.service.data,
            appointment_date=form.appointment_date.data.strftime('%Y-%m-%d'),
            appointment_time=form.appointment_time.data.strftime('%H:%M')
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash('Запись успешно добавлена!', 'success')
        return redirect(url_for('index'))
    return render_template('add_appointment.html', form=form)

# Список записей (только для администратора)
@app.route('/appointments')
@login_required
def appointments():
    all_appointments = Appointment.query.all()
    return render_template('appointments.html', appointments=all_appointments)

if __name__ == '__main__':
    app.run(debug=True)
