from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    attendances = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)

with app.app_context():
    db.create_all()
    # add main user for login
    check_user = User.query.filter_by(username='CSE').first()
    if check_user == None:
        pwd = generate_password_hash('7150', method='pbkdf2:sha256')
        u = User(username='CSE', password=pwd)
        db.session.add(u)
        db.session.commit()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form.get('username')
        pwd = request.form.get('password')
        
        user = User.query.filter_by(username=uname).first()
        if user != None:
            if check_password_hash(user.password, pwd):
                session['user_id'] = user.id
                return redirect('/dashboard')
            else:
                flash('Wrong password', 'error')
        else:
            flash('User not found', 'error')
            
    return render_template('cse.html', page='login')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id')
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
        
    all_students = Student.query.all()
    total = len(all_students)
    
    dt = datetime.now().date()
    
    records = Attendance.query.filter_by(date=dt).all()
    
    p_count = 0
    a_count = 0
    for r in records:
        if r.status == 'Present':
            p_count = p_count + 1
        elif r.status == 'Absent':
            a_count = a_count + 1
            
    return render_template('cse.html', page='dashboard', total_students=total, present_count=p_count, absent_count=a_count, today=dt)

@app.route('/students', methods=['GET', 'POST'])
def students():
    if 'user_id' not in session:
        return redirect('/login')
        
    if request.method == 'POST':
        r_num = request.form.get('roll_number')
        s_name = request.form.get('name')
        sem = request.form.get('semester')
        
        check = Student.query.filter_by(roll_number=r_num).first()
        if check != None:
            flash('Roll number already exists', 'error')
        else:
            s = Student(roll_number=r_num, name=s_name, semester=sem)
            db.session.add(s)
            db.session.commit()
            
    st_list = Student.query.all()
    return render_template('cse.html', page='students', students=st_list)

@app.route('/delete_student/<int:id>')
def delete_student(id):
    if 'user_id' not in session:
        return redirect('/login')
        
    s = Student.query.get(id)
    if s != None:
        # delete attendance
        Attendance.query.filter_by(student_id=id).delete()
        db.session.delete(s)
        db.session.commit()
        
    return redirect('/students')

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user_id' not in session:
        return redirect('/login')
        
    if request.method == 'POST':
        d = request.form.get('date')
        if d == None or d == '':
            dt_obj = datetime.now().date()
        else:
            dt_obj = datetime.strptime(d, '%Y-%m-%d').date()
            
        all_s = Student.query.all()
        for s in all_s:
            val = request.form.get('status_' + str(s.id))
            if val != None:
                record = Attendance.query.filter_by(student_id=s.id, date=dt_obj).first()
                if record != None:
                    record.status = val
                else:
                    new_a = Attendance(student_id=s.id, date=dt_obj, status=val)
                    db.session.add(new_a)
        
        db.session.commit()
        return redirect('/attendance?date=' + dt_obj.strftime('%Y-%m-%d'))
        
    else:
        d = request.args.get('date')
        if d == None or d == '':
            dt_obj = datetime.now().date()
        else:
            dt_obj = datetime.strptime(d, '%Y-%m-%d').date()
            
        all_s = Student.query.all()
        records = Attendance.query.filter_by(date=dt_obj).all()
        
        a_dict = {}
        for r in records:
            a_dict[r.student_id] = r.status
            
        return render_template('cse.html', page='attendance', students=all_s, selected_date=dt_obj, attendance_dict=a_dict)

import webbrowser
import os
from threading import Timer

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Timer(1, open_browser).start()
    app.run(debug=True, port=5000)
