from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
import yaml
import datetime

app = Flask(__name__)
app.secret_key = 'hello'
# Configure db
db = yaml.load(open('config.ymal'), Loader=yaml.FullLoader)

app.config['MYSQL_HOST'] = db['host']
app.config['MYSQL_USER'] = db['user']
app.config['MYSQL_PASSWORD'] = db['password']
app.config['MYSQL_DB'] = db['dbname']
app.config['MYSQL_PORT'] = db['port']

mysql = MySQL(app)


@app.route('/index', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        session.pop('student_name', None)
        session.pop('student_id', None)
        loginDetails = request.form
        account_type = loginDetails['account']
        if account_type == 'Professor':

            professor_name = loginDetails['name']
            professor_password = loginDetails['password']

            cur = mysql.connection.cursor()
            cur.execute('SELECT id_teacher, name, password FROM teacher WHERE name = "' +
                        professor_name+'"AND password = "'+professor_password+'"')
            result = cur.fetchall()

            if result:
                session['professor_name'] = professor_name
                session['professor_id'] = result[0][0]
                print(session['professor_id'])
                print(session['professor_name'])
                flash("You're Logged in", category='success')
                return redirect(url_for('admin_homepage'))
            else:
                flash("Enter correct details", category='warning')
                return render_template('index.html')
        elif account_type == 'Student':
            student_name = loginDetails['name']
            student_password = loginDetails['password']

            cur = mysql.connection.cursor()
            cur.execute('SELECT id_student, name, password FROM student WHERE name = "' +
                        student_name+'"AND password = "'+student_password+'"')
            result = cur.fetchall()

            if result:
                session['student_name'] = student_name
                session['student_id'] = result[0][0]
                flash("You're Logged in", category='success')
                return redirect(url_for('student_homepage'))
            else:
                flash("Enter correct details", category='warning')
                return render_template('index.html')
    return render_template('index.html')


@app.route('/admin_homepage', methods=['POST', 'GET'])
def admin_homepage():
    if 'professor_name' in session:
        professor_name = session['professor_name']
        professor_id = session['professor_id']
        cur = mysql.connection.cursor()
        cur.execute('SELECT course FROM att_tracker WHERE id_teacher = "' +
                    str(professor_id)+'"AND teacher_name = "'+professor_name+'"AND status = "open"')
        results = cur.fetchall()
        print(results)
        return render_template('admin_homepage.html', professor_name=professor_name.upper(), results=results)
    else:
        flash("Please login to continue", category='info')
        return render_template('index.html')


@app.route('/student_homepage')
def student_homepage():
    if 'student_name' in session:
        student_name = session['student_name']
        student_id = session['student_id']
        course_list = ['cloud_computing_lab', 'human_machine_interaction',
                       'project_management', 'distributed_computing']
        attended_list = []
        total_lectures = []
        cur = mysql.connection.cursor()
        cur.execute('SELECT COUNT(*) FROM att_tracker')
        result = cur.fetchall()
        total_lectures.append(result[0][0])
        for course in course_list:
            cur = mysql.connection.cursor()
            cur.execute('SELECT COUNT(*) FROM '+course +
                        ' WHERE student_id = "'+str(student_id)+'"')
            result = cur.fetchall()
            attended_list.append(result[0][0])
            print(attended_list)
        try:
            attendance_data = [total_lectures[0], sum(attended_list), total_lectures[0] - sum(attended_list),
                               round(sum(attended_list)/total_lectures[0]*100)]
        except ZeroDivisionError:
            attendance_data = [total_lectures[0], sum(attended_list), total_lectures[0] - sum(attended_list),
                               0]
        print(attendance_data)
        return render_template('student_homepage.html', student_name=student_name.upper(),
                               total=attendance_data[0], attended=attendance_data[1], missed=attendance_data[2], percentage=attendance_data[3])
    else:
        flash("Please login to continue")
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    if 'professor_name' in session:
        session.pop('professor_name', None)
        session.pop('professor_id', None)
        flash("You're logged out", category='primary')
        return redirect(url_for('index'))
    if 'student_name' in session:
        session.pop('student_name', None)
        session.pop('student_id', None)
        flash("You're logged out", category='primary')
        return redirect(url_for('index'))


@app.route('/mark_attendance', methods=['POST', 'GET'])
def mark_attendance():
    if request.method == 'POST':
        subject = request.form.get('select_widget')
        print(subject)
        cur = mysql.connection.cursor()
        status = 'open'
        cur.execute('SELECT * FROM att_tracker WHERE status = "' +
                    status+'"AND course = "'+subject+'"')
        results = cur.fetchall()
        print(len(results))
        print(results)
        if len(results) > 0:
            name = session['student_name']
            student_id = session['student_id']
            subject_name_underscored = subject.replace(' ', '_')
            print(subject_name_underscored)
            print(student_id)
            q1 = 'INSERT INTO '+subject_name_underscored + \
                '(student_id, student_name, marking_time, marking_date)'
            q2 = 'VALUES("'+str(student_id)+'","'+name+'", now(), CURDATE())'
            cur.execute(q1+q2)
            mysql.connection.commit()
            cur.close()
            flash("Attendance marked for {} successfully".format(
                subject.replace('_', ' ').upper()), category='success')
            return redirect(url_for('student_homepage'))
        else:
            flash("Attendance is off, You're late", category='warning')
            return (redirect(url_for('student_homepage')))
    return render_template('mark_attendance.html')


@app.route('/turn_on_attendance', methods=['POST', 'GET'])
def turn_on_attendance():
    if request.method == 'POST':
        subject = request.form.get('select_widget')
        professor_id = session['professor_id']
        professor_name = session['professor_name']
        status = 'open'
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM att_tracker WHERE id_teacher = "'+str(professor_id) +
                    '"AND teacher_name = "'+professor_name+'"AND status ="'+status+'"AND course = "'+subject+'"')
        is_open = cur.fetchall()
        if len(is_open) > 0:
            flash("Attendance for {} is already open".format(
                subject), category='info')
            return redirect(url_for('admin_homepage'))
        else:
            cur = mysql.connection.cursor()
            q1 = 'INSERT INTO att_tracker (id_teacher, teacher_name, status, course, on_time, off_time, date)'
            q2 = 'VALUES("'+str(professor_id)+'","'+professor_name + \
                '","'+status+'","'+subject+'",now(), now(), CURDATE())'
            cur.execute(q1+q2)
            mysql.connection.commit()
            cur.close()
            flash("Attendance turned on successfully for {}".format(
                subject.replace('_', ' ').upper()), category='success')
            return redirect(url_for('admin_homepage'))
    return render_template('turn_on_attendance.html')


@app.route('/turn_off_attendance', methods=['POST', 'GET'])
def turn_off_attendance():
    if request.method == 'POST':
        professor_name = session['professor_name']
        professor_id = session['professor_id']
        subject = request.form.get('select_widget')
        check_status = 'open'
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM att_tracker WHERE id_teacher = "'+str(professor_id) +
                    '"AND teacher_name = "'+professor_name+'"AND status ="'+check_status+'"AND course = "'+subject+'"')
        is_close = cur.fetchall()
        print(is_close)
        if len(is_close) > 0:
            status = 'close'
            cur = mysql.connection.cursor()
            q1 = 'UPDATE att_tracker SET status = "'+status+'", off_time = now() WHERE id_teacher ="' + \
                str(professor_id)+'" AND course ="'+subject+'"'
            cur.execute(q1)
            mysql.connection.commit()
            cur.close()
            flash("Attendance for {} closed successfully".format(
                subject.replace('_', ' ').upper()), category='success')
            return redirect(url_for('admin_homepage'))
        else:
            flash("Attendance for {} is already closed".format(
                subject.replace('_', ' ').upper()), category='info')
            return redirect(url_for('admin_homepage'))
    return render_template('turn_on_attendance.html')


@app.route('/view_records_teacher')
def view_records_teacher():
    cur = mysql.connection.cursor()
    cur.execute('Select * from cloud_computing_lab')
    results = cur.fetchall()
    return render_template('view_records_teacher.html', results=results)


@app.route('/view_records_student', methods=['POST', 'GET'])
def view_records_student():
    student_name = session['student_name']
    student_id = session['student_id']
    course_list = ['cloud_computing_lab', 'human_machine_interaction',
                   'project_management', 'distributed_computing']
    sql_data_list = []
    for course in course_list:
        cur = mysql.connection.cursor()
        cur.execute('SELECT  DAYNAME(marking_date), marking_date, marking_time FROM ' +
                    course+' WHERE student_id = "'+str(student_id)+'"')
        result = cur.fetchall()
        sql_data_list.append(result)
        print(sql_data_list)
    if request.method == 'POST':
        subject = request.form.get('select_widget')
        print(subject)
        index = course_list.index(subject)
        print(sql_data_list[index])
        return render_template('view_records_student.html', results=sql_data_list[index], sub_name=subject.replace('_', ' ').capitalize())
    return render_template('view_records_student.html')

# TODO: #1 Create 'All records for student'
    # 2 Use the same code for Professor records
    # 3 Work on index page


# @app.route('/student_homepage<name>', methods=['POST', 'GET'])
# def student_homepage(name):
#     return render_template('student_homepage.html', name = name)

if __name__ == '__main__':
    app.run(debug=True)
app.run(host='127.0.0.1', port='8080', debug=True)
