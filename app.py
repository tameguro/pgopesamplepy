from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import calendar

YEAR_MONTH_FORMAT = "%Y%m"
DATE_FORMAT = "%Y%m%d"

app = Flask(__name__)

db_uri = "postgresql://maguro:password@localhost:5432/maguro_market"
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
    if max_id_num == None:
        max_id_num = 0

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

@app.route('/show_monthly_shift/')
@app.route('/show_monthly_shift/<string:year_month>')
def show_monthly_shift(year_month=None):
    if year_month == None:
        year_month = datetime.now().strftime(YEAR_MONTH_FORMAT)

    target_month = datetime.strptime(year_month, YEAR_MONTH_FORMAT)
    end_target = target_month + relativedelta(months=1, days=-1)

    pre_year_month = target_month + relativedelta(months=-1)

    next_year_month = target_month + relativedelta(months=1)

    monthly_shift = Shift.query.join(Employee, Shift.employee_id==Employee.employee_id) \
                    .add_columns(Shift.day, Employee.nickname, Shift.start_time, Shift.end_time) \
                    .filter(Shift.day.between(target_month, end_target)).order_by(Shift.start_time).all()

    monthly_calendar = calendar.Calendar(6).monthdatescalendar(target_month.year, target_month.month)

    return render_template('monthly_shift.html', title='月間シフト', target_month=target_month, \
                            pre_year_month=pre_year_month, next_year_month=next_year_month, \
                            monthly_cal=monthly_calendar, monthly_shift=monthly_shift)

@app.route('/show_daily_shift/')
@app.route('/show_daily_shift/<string:date>')
def show_daily_shift(date=None):
    if date == None:
        date = datetime.now().strftime(DATE_FORMAT)

    target_date = datetime.strptime(date, DATE_FORMAT)

    pre_date = target_date + timedelta(days=-1)

    next_date = target_date + timedelta(days=1)

    daily_shift = Shift.query.join(Employee, Shift.employee_id==Employee.employee_id) \
                .add_columns(Shift.day, Employee.employee_id, Employee.nickname, Shift.start_time, Shift.end_time) \
                .filter(Shift.day==target_date).order_by(Shift.start_time, Employee.employee_id).all()

    return render_template('daily_shift.html', title='当日のシフト', target_date=target_date, \
                            pre_date=pre_date, next_date=next_date, daily_shift=daily_shift)

@app.route('/add_daily_shift/')
@app.route('/add_daily_shift/<string:date>')
def add_daily_shift(date=None):
    if date == None:
        date = datetime.now().strftime(DATE_FORMAT)

    target_date = datetime.strptime(date, DATE_FORMAT)

    employees = Employee.query.order_by(Employee.employee_id).all()
    return render_template('add_daily_shift.html', title='シフト追加', target_date=target_date, employees=employees)

@app.route('/add_daily_shift_commit', methods=['POST'])
def add_daily_shift_commit():
    date = request.form['target_date']
    start_time_hour = request.form['start_time_hour']
    start_time_minute = request.form['start_time_minute']
    end_time_hour = request.form['end_time_hour']
    end_time_minute = request.form['end_time_minute']
    employee_id = request.form['employee']

    target_date = datetime.strptime(date, DATE_FORMAT)
    start_time = time(int(start_time_hour), int(start_time_minute), 0)
    end_time = time(int(end_time_hour), int(end_time_minute), 0)

    shift = Shift(day=target_date, employee_id=employee_id, start_time=start_time, end_time=end_time)
    db.session.add(shift)
    db.session.commit()

    redirect_uri = url_for('show_daily_shift', date=target_date.strftime('%Y%m%d'))
    return redirect(redirect_uri)

@app.route('/del_daily_shift', methods=['POST'])
def del_daily_shift():
    date = request.form['target_date']
    employee_id = request.form['del_id']

    target_date = datetime.strptime(date, DATE_FORMAT)

    db.session.query(Shift).filter(Shift.day==target_date, Shift.employee_id==employee_id).delete()
    db.session.commit()

    redirect_uri = url_for('show_daily_shift', date=date)
    return redirect(redirect_uri)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run()
