from flask import Flask, render_template, g, request, redirect, url_for
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import calendar

app = Flask(__name__)

db_uri = os.environ.get('DATABASE_URL') or "postgresql://maguro:password@localhost:5432/maguro_market"
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Employee(db.Model):
    __tablename__ = "employees"
    employee_id = db.Column(db.String(), primary_key=True)
    nickname = db.Column(db.String(), nullable=False)

class Shift(db.Model):
    __tablename__ = "shifts"
    day = db.Column(db.Date(), primary_key=True)
    employee_id = db.Column(db.String(), primary_key=True)
    start_time = db.Column(db.Time(), nullable=False)
    end_time= db.Column(db.Time(), nullable=False)

@app.route('/')
def top():
    return render_template('index.html', title='従業員シフト入力システム')

@app.route('/employee')
def employee_list():
    employees = Employee.query.order_by(Employee.employee_id).all()
    return render_template('employee.html', title='従業員一覧', employees=employees)

@app.route('/add_employee')
def add_employee():
    return render_template('add_employee.html', title='従業員追加')

@app.route('/add_employee_commit', methods=['POST'])
def add_employee_commit():
    nickname = request.form['nickname']
    max_id_num = db.session.query(db.func.max(Employee.employee_id)).scalar()
    employee_id = str(int(max_id_num) + 1).zfill(6)
    employee = Employee(employee_id=employee_id, nickname=nickname)
    db.session.add(employee)
    db.session.commit()

    return redirect("/employee")

@app.route('/edit_employee', methods=['POST'])
def edit_employee():
    employee_id = request.form['employee_id']
    employee = Employee.query.filter(Employee.employee_id==employee_id).one()

    return render_template("edit_employee.html", title="従業員ニックネーム編集", employee=employee)

@app.route('/edit_employee_commit', methods=['POST'])
def edit_employee_commit():
    employee_id = request.form['employee_id']
    nickname = request.form['nickname']

    employee = db.session.query(Employee).filter(Employee.employee_id==employee_id).one()
    employee.nickname = nickname
    db.session.commit()

    return redirect("/employee")

@app.route('/del_employee', methods=['POST'])
def del_employee():
    employee_id = request.form['employee_id']
    employee = Employee.query.filter(Employee.employee_id==employee_id).one()

    return render_template("del_employee.html", title="従業員削除確認", employee=employee)

@app.route('/del_employee_commit', methods=['POST'])
def del_employee_commit():
    employee_id = request.form['employee_id']

    db.session.query(Shift).filter(Shift.employee_id==employee_id).delete()
    db.session.query(Employee).filter(Employee.employee_id==employee_id).delete()
    db.session.commit()

    return redirect("/employee")

@app.route('/show_monthly_shift', methods=['GET', 'POST'])
def show_monthly_shift():
    year = request.args.get('year')
    month = request.args.get('month')

    if is_year(year) == False or is_month(month) == False:
        year = datetime.now().strftime('%Y')
        month = datetime.now().strftime('%m')

    year = int(year)
    month = int(month)

    target_month = datetime(year, month, 1)
    end_target = target_month + relativedelta(months=1, days=-1)
    monthly_shift = Shift.query.join(Employee, Shift.employee_id==Employee.employee_id).add_columns(Shift.day, Employee.nickname, Shift.start_time, Shift.end_time).filter(Shift.day.between(target_month, end_target)).order_by(Shift.start_time).all()

    pre = target_month + relativedelta(months=-1)
    pre_year = pre.year
    pre_month = pre.month

    next = target_month + relativedelta(months=1)
    next_year = next.year
    next_month = next.month

    monthly_calendar = calendar.Calendar(6).monthdatescalendar(year, month)

    return render_template('monthly_shift.html', title='月間シフト', year=year, month=month, pre_year=pre_year, pre_month=pre_month, next_year=next_year, next_month=next_month, monthly_cal=monthly_calendar, monthly_shift=monthly_shift)

@app.route('/show_daily_shift', methods=['GET', 'POST'])
def show_daily_shift():
    year = request.args.get('year')
    month = request.args.get('month')
    date = request.args.get('date')

    if is_year(year) == False or is_month(month) == False or is_date(date) == False:
        year = datetime.now().strftime('%Y')
        month = datetime.now().strftime('%m')
        date = datetime.now().strftime('%d')

    year = int(year)
    month = int(month)
    date = int(date)

    target_date = datetime(year, month, date)
    daily_shift = Shift.query.join(Employee, Shift.employee_id==Employee.employee_id).add_columns(Shift.day, Employee.employee_id, Employee.nickname, Shift.start_time, Shift.end_time).filter(Shift.day==target_date).order_by(Shift.start_time, Employee.employee_id).all()

    pre = target_date + timedelta(days=-1)
    pre_year = pre.year
    pre_month = pre.month
    pre_date = pre.day

    next = target_date + timedelta(days=1)
    next_year = next.year
    next_month = next.month
    next_date = next.day

    return render_template('daily_shift.html', title='当日のシフト', year=year, month=month, date=date, pre_year=pre_year, pre_month=pre_month, pre_date=pre_date, next_year=next_year, next_month=next_month, next_date=next_date, daily_shift=daily_shift)

@app.route('/add_daily_shift')
def add_daily_shift():
    year = request.args.get('year')
    month = request.args.get('month')
    date = request.args.get('date')

    if is_year(year) == False or is_month(month) == False or is_date(date) == False:
        year = datetime.now().strftime('%Y')
        month = datetime.now().strftime('%m')
        date = datetime.now().strftime('%d')

    year = int(year)
    month = int(month)
    date = int(date)

    employees = Employee.query.order_by(Employee.employee_id).all()
    return render_template('add_daily_shift.html', title='シフト追加', year=year, month=month, date=date, employees=employees)

@app.route('/add_daily_shift_commit', methods=['POST'])
def add_daily_shift_commit():
    year = request.form['year']
    month = request.form['month']
    date = request.form['date']
    start_time_hour = request.form['start_time_hour']
    start_time_minute = request.form['start_time_minute']
    end_time_hour = request.form['end_time_hour']
    end_time_minute = request.form['end_time_minute']
    employee_id = request.form['employee']

    year = int(year)
    month = int(month)
    date = int(date)
    start_time_hour = int(start_time_hour)
    start_time_minute = int(start_time_minute)
    end_time_hour = int(end_time_hour)
    end_time_minute = int(end_time_minute)

    target_date = datetime(year, month, date)
    start_time = time(start_time_hour, start_time_minute, 0)
    end_time = time(end_time_hour, end_time_minute, 0)

    shift = Shift(day=target_date, employee_id=employee_id, start_time=start_time, end_time=end_time)
    db.session.add(shift)
    db.session.commit()

    redirect_uri = url_for('show_daily_shift', year=year, month=month, date=date)
    return redirect(redirect_uri)

@app.route('/del_daily_shift', methods=['POST'])
def del_daily_shift():
    year = request.form['year']
    month = request.form['month']
    date = request.form['date']
    employee_id = request.form['del_id']

    year = int(year)
    month = int(month)
    date = int(date)

    target_date = datetime(year, month, date)

    db.session.query(Shift).filter(Shift.day==target_date, Shift.employee_id==employee_id).delete()
    db.session.commit()

    redirect_uri = url_for('show_daily_shift', year=year, month=month, date=date)
    return redirect(redirect_uri)

def is_year(year):

    if year is None:
        return False

    if year.isdecimal() == False:
        return False

    return True

def is_month(month):

    if month is None:
        return False

    try:
        int(month)
    except Exception as e:
        return False

    if int(month) < 1 or int(month) > 12:
        return False

    return True

def is_date(date):

    if date is None:
        return False

    try:
        int(date)
    except Exception as e:
        return False

    if int(date) < 1 or int(date) > 31:
        return False

    return True

if __name__ == '__main__':
    app.run()
