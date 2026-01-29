from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf.csrf import CSRFProtect
import secrets
import re


app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)


class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codename = db.Column(db.String(30), unique=True, nullable=False)
    contact_number = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    access_level_id = db.Column(db.Integer, db.ForeignKey('access_level.id'), nullable=False)


class AccessLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    agents = db.relationship('Agent', backref='access_info', lazy=True)


with app.app_context():
    db.create_all()

    if not AccessLevel.query.first():
        confidential = AccessLevel(name="Confidential")
        secret = AccessLevel(name="Secret")
        top_secret = AccessLevel(name="Top Secret")

        db.session.add_all([confidential, secret, top_secret])
        db.session.commit()


def validate_agent_data(data, current_id=None):
    errors = {}

    codename = data.get('codename', '').strip()
    if not codename:
        errors['codename'] = "Кодовое имя не может быть пустым!"
    elif len(codename) < 3:
        errors['codename'] = "Нужно минимум 3 символа!"
    else:
        existing_name = Agent.query.filter_by(codename=codename).first()
        if existing_name and (current_id is None or existing_name.id != current_id):
            errors['codename'] = "Это кодовое имя уже занято!"

    email = data.get('email', '').strip()
    if not email:
        errors['email'] = "Email не введен!"
    elif not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        errors['email'] = "Некорректный формат почты!"
    else:
        existing_email = Agent.query.filter_by(email=email).first()
        if existing_email and (current_id is None or existing_email.id != current_id):
            errors['email'] = "Этот Email уже используется!"

    contact_number = data.get('contact_number', '').strip()
    if contact_number:
        if not re.match(r'^\+7\d{10}$', contact_number):
            errors['contact_number'] = "Ошибка в номере!"
        else:
            existing_phone = Agent.query.filter_by(contact_number=contact_number).first()
            if existing_phone and (current_id is None or existing_phone.id != current_id):
                errors['contact_number'] = "Этот номер телефона уже используется!"

    access_level_id = data.get('access_level_id', '').strip()
    if not access_level_id:
        errors['access_level_id'] = "Уровень доступа не выбран!"
    else:
        try:
            level_id = int(access_level_id)
            level_exists = AccessLevel.query.get(level_id)
            if not level_exists:
                errors['access_level_id'] = "Указанный уровень доступа не существует!"
        except ValueError:
            errors['access_level_id'] = "Некорректный уровень доступа!"


    return errors


@app.route('/')
def agents_list():
    search = request.args.get('search', '').strip()
    level = request.args.get('level', '').strip()
    try:
        agents = Agent.query

        if search:
            agents = agents.filter(Agent.codename.contains(search))
        if level:
            try:
                level_id = int(level)
                if not AccessLevel.query.get(level_id):
                    flash("Указанный уровень доступа не существует", "warning")
                else:
                    agents = agents.filter_by(access_level_id=level_id)
            except ValueError:
                flash("Некорректный уровень доступа", "warning")

        return render_template('agents_list.html', agents=agents.all(), levels=AccessLevel.query.all())
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Ошибка базы данных: {e}")
        flash("Произошла ошибка при загрузке списка агентов", "danger")
        return render_template('agents_list.html', agents=[], levels=[])


@app.route('/add', methods=['GET', 'POST'])
def add_agent():
    form_data = {}
    errors = {}

    if request.method == 'POST':
        form_data = request.form.to_dict()
        errors = validate_agent_data(form_data)

        if not errors:
            try:
                new_agent = Agent(
                    codename=form_data['codename'].strip(),
                    contact_number=form_data.get('contact_number', '').strip() or None,
                    email=form_data['email'].strip(),
                    access_level_id=int(form_data['access_level_id'])
                )
                db.session.add(new_agent)
                db.session.commit()
                flash("Агент успешно добавлен в базу", "success")

                return redirect(url_for('agents_list'))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash("Ошибка при добавлении агента", "danger")

    return render_template('add_agent.html', levels=AccessLevel.query.all(),
                           errors=errors, form_data=form_data)


@app.route('/agent/<int:id>')
def view_agent(id):
    agent = Agent.query.get_or_404(id)
    return render_template('view_agent.html', agent=agent)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_agent(id):
    agent = Agent.query.get_or_404(id)
    errors = {}
    form_data = {
        'codename': agent.codename,
        'contact_number': agent.contact_number or '',
        'email': agent.email,
        'access_level_id': agent.access_level_id
    }

    if request.method == 'POST':
        form_data = request.form.to_dict()
        errors = validate_agent_data(form_data, id)

        if not errors:
            try:
                agent.codename = form_data['codename'].strip()
                agent.contact_number = form_data.get('contact_number', '').strip() or None
                agent.email = form_data['email'].strip()
                agent.access_level_id = int(form_data['access_level_id'])
                db.session.commit()
                flash("Досье агента успешно обновлено", "success")
                return redirect(url_for('agents_list'))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash("Ошибка при изменении досье", "danger")

    return render_template('edit_agent.html', agent=agent, levels=AccessLevel.query.all(),
                           errors=errors, form_data=form_data)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_agent(id):
    try:
        agent = Agent.query.get_or_404(id)
        db.session.delete(agent)
        db.session.commit()
        flash("Досье агента успешно удалено", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash("Ошибка при удалении агента", "danger")

    return redirect(url_for('agents_list'))


@app.route('/emergency-wipe', methods=['POST'])
def emergency_wipe():
    try:
        db.session.query(Agent).delete()
        db.session.commit()
        flash("!!!БАЗА ДАННЫХ УНИЧТОЖЕНА!!!", "danger")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Ошибка базы данных: {e}")
        flash("Произошла ошибка при очистке базы данных", "warning")

    return redirect(url_for('agents_list'))


if __name__ == '__main__':
    app.run(debug=True)
