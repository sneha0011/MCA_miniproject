from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import pymysql
from db import iud, selectone, selectall, selectall2
from db import get_db_connection
from datetime import datetime

import razorpay

import random

from flask_mail import *


app = Flask(__name__)
app.secret_key = '68444982465546' 


app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use the server for your mail service
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'duetrackermp@gmail.com'  # Your email address
app.config['MAIL_PASSWORD'] = 'tzjm pmpz ibkl kzyi'  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = ('Due_Tracker', 'duetrackermp@gmail.com')

mail = Mail(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/forgot_password')
def forgot_password():
    return render_template("forgot_password.html")


@app.route('/forgot_password2', methods=['post'])
def forgot_password2():

    email = request.form['textfield']
    session['email'] = email

    qry = "SELECT * FROM `login` WHERE `username`=%s"

    res = selectone(qry, email)

    print(res)

    if res is None:
        return ''''<script>alert("Invalid email address");window.location="/forgot_password"</script>'''
    else:

        random_number = random.randint(1000, 9999)

        print(random_number)

        s = random_number
        session['otp'] = random_number

        def mail(s, email):
            try:
                print("ïm hereeeee")
                gmail = smtplib.SMTP('smtp.gmail.com', 587)
                gmail.ehlo()
                gmail.starttls()
                gmail.login('duetrackermp@gmail.com', 'tzjm pmpz ibkl kzyi')
                print("okkkkkk")
            except Exception as e:
                print("Couldn't setup email!!" + str(e))
            msg = MIMEText("Your OTP to verify Email: " + str(s)+ " Dont share your OTP")
            print(msg)
            msg['Subject'] = 'Verify your email'
            msg['To'] = email
            msg['From'] = 'duetrackermp@gmail.com'
            try:
                gmail.send_message(msg)
                print("Done =====================")
                  

            except Exception as e:
                print("COULDN'T SEND EMAIL", str(e))
                return ''''<script>alert("COULDN'T SEND EMAIL");window.location="/forgot_password"</script>'''
        
        mail(s,email)
        return render_template("otp.html")

     
@app.route("/verify_otp", methods=['post'])
def verify_otp():
    otp = request.form['textfield']
    print("otpp",otp)
    print("session otp", session['otp'])
    if int(otp) == int(session['otp']):
        return render_template("new_password.html")
    else:
        return ''''<script>alert("OTP missmatch. Please Enter the valid otp");window.location="/forgot_password"</script>'''

     
@app.route("/new_password", methods=['post'])
def new_password():
    new_password = request.form['textfield']
    qry = "UPDATE `login` SET `password`=%s WHERE `username`=%s"
    iud(qry,(new_password,session['email']))
    return ''''<script>alert("Password Changed Successfully");window.location="/"</script>'''


@app.route('/home')
def home():
    if 'username' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_home')) 
        elif role == 'staff':
            staff_type = session.get('staff_type')
            if staff_type == 'Hostel':
                return redirect(url_for('hostel_home'))
            elif staff_type == 'Office':
                return redirect(url_for('office_home'))
            elif staff_type == 'Department':
                return redirect(url_for('department_home'))
            elif staff_type == 'Library':
                return redirect(url_for('library_home'))
            else:
                return "Invalid staff type."
        elif role == 'student':
            return redirect(url_for('student_home'))  # Redirect to Student homepage
        else:
            return "Unauthorized access"
    return redirect(url_for('login'))


@app.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        # Retrieve form data
        staff_id = request.form['staff_id']
        staff_name = request.form['staff_name']
        role = request.form['role']
        dob = request.form['dob']
        email = request.form['email']
        password = request.form['password']
        
        existing_staff = selectone("SELECT * FROM staff WHERE staff_id=%s OR email=%s", (staff_id, email))
        if existing_staff:
            # Handle duplicate case
            return "Staff member with this ID or Email already exists."

        # Insert into login table
        sql_login = "INSERT INTO login (username, password, role) VALUES (%s, %s, %s)"
        login_values = (email, password, 'staff')
        iud(sql_login, login_values)

        # Retrieve the ID generated in the login table
        login_id = selectone("SELECT id FROM login WHERE username=%s", (email,))

        # Insert into staff table
        sql_staff = "INSERT INTO staff (id, staff_id, staff_name, role, dob, email) VALUES (%s, %s, %s, %s, %s, %s)"
        staff_values = (login_id['id'], staff_id, staff_name, role, dob, email)
        iud(sql_staff, staff_values)

        return redirect(url_for('admin_home'))

    return render_template('add_staff.html')


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' in session and session.get('role') == 'admin':
        if request.method == 'POST':
            reg_id = request.form['reg_id']
            student_name = request.form['student_name']
            department = request.form['department']
            semester = request.form['semester']
            contact_no = request.form['contact_no']
            email = request.form['email']
            dob = request.form['dob']
            hostel = request.form['hostel']
            password = request.form['password']
            
            # Insert into the 'login' table
            qry_login = "INSERT INTO login (username, password, role) VALUES (%s, %s, 'student')"
            login_id = iud(qry_login, (email, password))
            
            # Insert into the 'students' table
            qry_student = """
            INSERT INTO students (id, reg_id, student_name, department, semester, contact_no, email, dob, hostel)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            iud(qry_student, (login_id, reg_id, student_name, department, semester, contact_no, email, dob, hostel))
            
            return redirect(url_for('admin_home'))  # Redirect to Admin homepage after adding
        return render_template('add_student.html')
    return redirect(url_for('login'))

@app.route('/search_staff', methods=['GET'])
def search_staff():
    search_query = request.args.get('query', '')
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    sql_query = f"""
    SELECT * FROM staff WHERE staff_id LIKE %s OR staff_name LIKE %s
    """
    cursor.execute(sql_query, (f'%{search_query}%', f'%{search_query}%'))
    results = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return jsonify(results)

@app.route('/search_students', methods=['GET'])
def search_students():
    search_query = request.args.get('query', '')
    display_type = request.args.get('type', 'default')  # New parameter to control what details to fetch
    
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    if display_type == 'due_details':
        # Fetching student details along with their due details
        sql_query = """
        SELECT s.reg_id, s.student_name, h.amount, h.due_date, h.status 
        FROM students s 
        JOIN hostel_fees h ON s.reg_id = h.reg_id 
        WHERE s.reg_id LIKE %s OR s.student_name LIKE %s
        """
    else:
        # Fetching basic student details
        sql_query = """
        SELECT * FROM students WHERE reg_id LIKE %s OR student_name LIKE %s
        """
    
    cursor.execute(sql_query, (f'%{search_query}%', f'%{search_query}%'))
    results = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return jsonify(results)


@app.route('/edit_staff/<staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    if request.method == 'POST':
        # Update staff details in the database
        staff_name = request.form['staff_name']
        role = request.form['role']
        dob = request.form['dob']
        email = request.form['email']
        
        # Update the staff record
        sql_update = "UPDATE staff SET staff_name=%s, role=%s, dob=%s, email=%s WHERE staff_id=%s"
        iud(sql_update, (staff_name, role, dob, email, staff_id))

        return redirect(url_for('admin_home'))  # Redirect to Admin homepage

    # Fetch staff details to display in the edit form
    staff = selectone("SELECT * FROM staff WHERE staff_id=%s", (staff_id,))
    if not staff:
        return "Staff member not found", 404
    
    return render_template('edit_staff.html', staff=staff)

@app.route('/delete_staff/<staff_id>', methods=['POST'])
def delete_staff(staff_id):
    # Delete the staff member from the database
    iud("DELETE FROM staff WHERE staff_id=%s", (staff_id,))
    return redirect(url_for('admin_home'))

@app.route('/edit_student/<reg_id>', methods=['GET', 'POST'])
def edit_student(reg_id):
    if request.method == 'POST':
        student_name = request.form['student_name']
        department = request.form['department']
        semester = request.form['semester']
        contact_no = request.form['contact_no']
        email = request.form['email']
        dob = request.form['dob']
        hostel = request.form['hostel']

        # Update student details in the database
        update_query = """
            UPDATE students 
            SET student_name=%s, department=%s, semester=%s, contact_no=%s, email=%s, dob=%s, hostel=%s 
            WHERE reg_id=%s
        """
        iud(update_query, (student_name, department, semester, contact_no, email, dob, hostel, reg_id))
        return redirect(url_for('admin_home'))  # Corrected redirect

    # Fetch student details to display in the edit form
    student = selectone("SELECT * FROM students WHERE reg_id=%s", (reg_id,))
    if not student:
        return "Student not found", 404

    return render_template('edit_student.html', student=student)


@app.route('/delete_student/<reg_id>', methods=['POST'])
def delete_student(reg_id):
    # Delete the student from the database
    iud("DELETE FROM students WHERE reg_id=%s", (reg_id,))
    return redirect(url_for('admin_home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Fetch user data from the login table
        qry = "SELECT * FROM login WHERE username=%s"
        user = selectone(qry, (username,))
        
        if user:
            # Check password
            if password == user['password']:
                # Password matches, set session
                session['username'] = username
                session['role'] = user['role']
                
                if user['role'] == 'student':
                    # Fetch the student ID from the students table
                    qry_student = "SELECT stu_id FROM students WHERE email=%s"
                    student = selectone(qry_student, (username,))
                    
                    if student:
                        session['stu_id'] = student['stu_id']  # Set the student ID in session
                
                elif user['role'] == 'staff':
                    # Fetch the staff type (role) from the staff table
                    qry_staff = "SELECT role FROM staff WHERE email=%s"
                    staff = selectone(qry_staff, (username,))
                    
                    if staff:
                        session['staff_type'] = staff['role']  # Set the staff type in session
                    else:
                        return "Staff member not found."
                
                return redirect(url_for('home'))
            else:
                return "Invalid credentials. Please try again."
        else:
            return "User does not exist."
    return render_template('login.html')



@app.route('/admin_home')
def admin_home():
    if 'username' in session and session.get('role') == 'admin':
        staff_list = selectall("SELECT * FROM staff")
        return render_template('admin_home.html', staff_list=staff_list)
    return redirect(url_for('login'))

@app.route('/staff_home')
def staff_home():
    if 'username' in session and session.get('role') == 'staff':
        return render_template('staff_home.html')
    return redirect(url_for('login'))


@app.route('/hostel_home')
def hostel_home():
    if 'username' in session and session.get('role') == 'staff' and session.get('staff_type') == 'Hostel':
        # Fetch and display data relevant to hostel staff
        return render_template('hostel_home.html')
    return redirect(url_for('login'))

@app.route('/office_home')
def office_home():
    if 'username' in session and session.get('role') == 'staff' and session.get('staff_type') == 'Office':
        # Fetch and display data relevant to office staff
        return render_template('office_home.html')
    return redirect(url_for('login'))

@app.route('/department_home')
def department_home():
    if 'username' in session and session.get('role') == 'staff' and session.get('staff_type') == 'Department':
        # Fetch and display data relevant to department staff
        return render_template('department_home.html')
    return redirect(url_for('login'))

@app.route('/library_home')
def library_home():
    if 'username' in session and session.get('role') == 'staff' and session.get('staff_type') == 'Library':
        # Fetch and display data relevant to library staff
        return render_template('library_home.html')
    return redirect(url_for('login'))

@app.route('/student_home')
def student_home():
    student_id = session.get('stu_id')

    if student_id:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch personal information
        cursor.execute("SELECT * FROM students WHERE stu_id = %s", (student_id,))
        student_data = cursor.fetchone()

        connection.close()

        return render_template('student_home.html', student=student_data, stu_id=student_id)
    else:
        return redirect('/login')

@app.route('/add_hostel_fee', methods=['GET', 'POST'])
def add_hostel_fee():
    if request.method == 'POST':
        reg_id = request.form['reg_id']
        
        # Fetch the student ID based on the registration ID
        student = selectone("SELECT stu_id FROM students WHERE reg_id=%s", (reg_id,))
        
        if not student:
            return "Student not found", 404
        
        stu_id = student['stu_id']
        fee_type = request.form['fee_type']
        amount = request.form['amount']
        due_date = request.form['due_date']
        status = request.form.get('status', 'Unpaid')
        description = request.form.get('description', '')

        # Insert the fee record into the hostel_fees table
        sql_query = """
        INSERT INTO hostel_fees (stu_id, reg_id, fee_type, amount, due_date, status, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        iud(sql_query, (stu_id, reg_id, fee_type, amount, due_date, status, description))
        
        return redirect(url_for('hostel_home'))

    return render_template('add_hostel_fee.html')

@app.route('/search_hostel_dues', methods=['GET'])
def search_hostel_dues():
    search_query = request.args.get('query', '')
    
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    sql_query = """
    SELECT s.reg_id, s.student_name, h.fee_type, h.amount, h.due_date, h.status, h.description 
    FROM students s 
    JOIN hostel_fees h ON s.reg_id = h.reg_id 
    WHERE s.reg_id LIKE %s OR s.student_name LIKE %s
    """
    
    cursor.execute(sql_query, (f'%{search_query}%', f'%{search_query}%'))
    results = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return jsonify(results)

@app.route('/edit_hostel_fee/<reg_id>', methods=['GET', 'POST'])
def edit_hostel_fee(reg_id):
    if request.method == 'POST':
        # Get updated data from the form
        fee_type = request.form['fee_type']
        amount = request.form['amount']
        due_date = request.form['due_date']
        description = request.form['description']
        status = request.form['status']
        
        # Update query
        qry = """UPDATE hostel_fees 
                 SET fee_type = %s, amount = %s, due_date = %s, description = %s, status = %s 
                 WHERE reg_id = %s"""
        val = (fee_type, amount, due_date, description, status, reg_id)
        
        # Execute the update
        iud(qry, val)
        
        flash('Hostel fee updated successfully', 'success')
        return redirect(url_for('hostel_home'))
    else:
        # Retrieve the existing data for the specified reg_id
        qry = "SELECT * FROM hostel_fees WHERE reg_id = %s"
        hostel_fees = selectone(qry, reg_id)
        
        if hostel_fees:
            # Pass the existing data to the template
            return render_template('edit_hostel_fee.html', hostel_fees=hostel_fees)
        else:
            flash('Hostel fee not found', 'danger')
            return redirect(url_for('hostel_home'))

@app.route('/delete_hostel_fee/<reg_id>', methods=['POST'])
def delete_hostel_fee(reg_id):
    # Delete the student from the database
    iud("DELETE FROM hostel_fees WHERE reg_id=%s", (reg_id,))
    return redirect(url_for('hostel_home'))

@app.route('/add_library_fee', methods=['GET', 'POST'])
def add_library_fee():
    if request.method == 'POST':
        reg_id = request.form['reg_id']
        
        # Fetch the student ID based on the registration ID
        student = selectone("SELECT stu_id FROM students WHERE reg_id=%s", (reg_id,))
        
        if not student:
            return "Student not found", 404
        
        stu_id = student['stu_id']
        book_id = request.form['book_id']
        due_date = request.form['due_date']
        return_date = request.form.get('return_date', None)
        fine_per_day = request.form['fine_per_day']
        total_fine = request.form.get('total_fine', '0.00')
        status = request.form.get('status', 'Unpaid')

        # Insert the fee record into the library_fees table
        sql_query = """
        INSERT INTO library_fees (reg_id, book_id, due_date, return_date, fine_per_day, total_fine, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        iud(sql_query, (reg_id, book_id, due_date, return_date, fine_per_day, total_fine, status))
        
        return redirect(url_for('library_home'))

    return render_template('add_library_fee.html')
@app.route('/search_library_fees', methods=['GET'])
def search_library_fees():
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify([])  # Return an empty list if no query is provided
    
    # Search for library fees based on the provided registration ID
    sql_query = f"SELECT reg_id, book_id, due_date, return_date, fine_per_day, total_fine, status FROM library_fees WHERE reg_id = '{query}'"
    fees = selectall(sql_query)  
    return jsonify(fees)

@app.route('/edit_library_fee/<reg_id>', methods=['GET', 'POST'])
def edit_library_fee(reg_id):
    if request.method == 'POST':
        book_id = request.form['book_id']
        due_date = request.form['due_date']
        return_date = request.form.get('return_date', None)
        fine_per_day = float(request.form['fine_per_day'])
        status = request.form['status']

        # Calculate the total fine if return_date is provided
        total_fine = 0
        if return_date:
            due_date_dt = datetime.strptime(due_date, '%Y-%m-%d')
            return_date_dt = datetime.strptime(return_date, '%Y-%m-%d')
            overdue_days = (return_date_dt - due_date_dt).days

            if overdue_days > 0:
                total_fine = overdue_days * fine_per_day

        # Update the library fee record
        sql_query = """
        UPDATE library_fees
        SET book_id=%s, due_date=%s, return_date=%s, fine_per_day=%s, total_fine=%s, status=%s
        WHERE reg_id=%s
        """
        iud(sql_query, (book_id, due_date, return_date, fine_per_day, total_fine, status, reg_id))

        return redirect(url_for('library_home'))

    # Fetch the existing data for the library fee
    fee = selectone("SELECT * FROM library_fees WHERE reg_id=%s", (reg_id,))
    if not fee:
        return "Fee record not found", 404

    return render_template('edit_library_fee.html', fee=fee)

@app.route('/delete_library_fee/<reg_id>', methods=['POST'])
def delete_library_fee(reg_id):
    # SQL query to delete the fee record
    sql_query = "DELETE FROM library_fees WHERE reg_id=%s"
    iud(sql_query, (reg_id,))  # Execute the delete query

    return redirect(url_for('library_home'))  # Redirect to the library home after deletion

@app.route('/add_department_fee', methods=['GET', 'POST'])
def add_department_fee():
    if request.method == 'POST':
        reg_id = request.form['reg_id']
        
        # Fetch the student ID based on the registration ID
        student = selectone("SELECT stu_id FROM students WHERE reg_id=%s", (reg_id,))
        
        if not student:
            return "Student not found", 404
        
        stu_id = student['stu_id']
        dept_name = request.form['dept_name']
        fee_type=request.form['fee_type']
        amount = request.form['amount']
        due_date = request.form['due_date']
        status = request.form.get('status', 'Unpaid')
        description = request.form.get('description', '')

        # Insert the fee record into the department_fees table
        sql_query = """
        INSERT INTO department_fees (stu_id, reg_id, fee_type, dept_name, amount, due_date, status, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        iud(sql_query, (stu_id, reg_id, fee_type, dept_name, amount, due_date, status, description))
        
        return redirect(url_for('department_home'))

    return render_template('add_department_fee.html')
@app.route('/search_department_fees')
def search_department_fees():
    query = request.args.get('query')
    
    # Assuming you're using pymysql
    sql = """
        SELECT * FROM department_fees 
        WHERE reg_id LIKE %s OR dept_name LIKE %s
    """
    values = ('%' + query + '%', '%' + query + '%')
    
    results = selectall2(sql, values)
    
    return jsonify(results)
@app.route('/edit_department_fee/<reg_id>', methods=['GET', 'POST'])
def edit_department_fee(reg_id):
    if request.method == 'POST':
        # Get updated data from the form
        dept_name = request.form['dept_name']
        fee_type = request.form['fee_type']
        amount = request.form['amount']
        due_date = request.form['due_date']
        description = request.form['description']
        status = request.form['status']
        
        # Update query
        qry = """UPDATE department_fees 
                 SET dept_name = %s, fee_type = %s, amount = %s, due_date = %s, description = %s, status = %s 
                 WHERE reg_id = %s"""
        val = (dept_name, fee_type, amount, due_date, description, status, reg_id)
        
        # Execute the update
        iud(qry, val)
        
        flash('Department fee updated successfully', 'success')
        return redirect(url_for('department_home'))
    else:
        # Retrieve the existing data for the specified reg_id
        qry = "SELECT * FROM department_fees WHERE reg_id = %s"
        department_fee = selectone(qry, reg_id)
        
        if department_fee:
            # Pass the existing data to the template
            return render_template('edit_department_fee.html', department_fee=department_fee)
        else:
            flash('Department fee not found', 'danger')
            return redirect(url_for('department_home'))
@app.route('/delete_department_fee/<reg_id>', methods=['POST'])
def delete_department_fee(reg_id):
    # Delete query
    qry = "DELETE FROM department_fees WHERE reg_id = %s"
    val = (reg_id,)
    
    # Execute the delete query
    iud(qry, val)
    
    flash('Department fee deleted successfully', 'success')
    return redirect(url_for('department_home'))
@app.route('/add_office_fee', methods=['GET', 'POST'])
def add_office_fee():
    if request.method == 'POST':
        reg_id = request.form['reg_id']
        
        # Fetch the student ID based on the registration ID
        student = selectone("SELECT stu_id FROM students WHERE reg_id=%s", (reg_id,))
        
        if not student:
            return "Student not found", 404
        
        stu_id = student['stu_id']

        fee_type = request.form['fee_type']
        due_date = request.form['due_date']
        description = request.form.get('description', '')
        installment = request.form.get('installment', False)  # Check if installment option is selected
        installment_amount = request.form.get('installment_amount', None)
        installment_due_date = request.form.get('installment_due_date', None)
        num_installments = request.form.get('num_installments', None)

        # Insert the fee record into the office_fees table
        sql_query = """
        INSERT INTO office_fees (stu_id, reg_id, fee_type, due_date, description, 
        installment, installment_amount, installment_due_date, num_installments)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        iud(sql_query, (stu_id, reg_id, fee_type, due_date, description, 
                        installment, installment_amount, installment_due_date, num_installments))
        
        return redirect(url_for('office_home'))

    return render_template('add_office_fee.html')

@app.route('/search_office_dues', methods=['GET'])
def search_office_dues():
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify([])  # Return an empty list if no query is provided
    
    # Search for office fees based on the provided registration ID
    sql_query = f"""
    SELECT 
        reg_id, 
        fee_type, 
        amount, 
        due_date, 
        description, 
        installment 
    FROM office_fees 
    WHERE reg_id = '{query}'
    """
    fees = selectall(sql_query)
    return jsonify(fees)
@app.route('/edit_office_fee/<reg_id>', methods=['GET', 'POST'])
def edit_office_fee(reg_id):
    if request.method == 'POST':
        # Capture form data
        fee_type = request.form['fee_type']
        amount = request.form['amount']
        due_date = request.form['due_date']
        description = request.form['description']

        # Checkbox handling
        installment = 'installment' in request.form
        installment_amount = request.form.get('installment_amount', 0) if installment else 0
        installment_due_date = request.form.get('installment_due_date', None) if installment else None
        num_installments = request.form.get('num_installments', 0) if installment else 0
        amount = request.form['amount']
        # Update the database
        query = """UPDATE office_fees SET fee_type=%s, due_date=%s, description=%s, 
                   installment=%s, installment_amount=%s, installment_due_date=%s, num_installments=%s, amount=%s 
                   WHERE reg_id=%s"""
        values = (fee_type, due_date, description, int(installment), 
                  installment_amount, installment_due_date, num_installments, amount, reg_id)
        iud(query, values)  # Ensure iud function handles None correctly

        return redirect(url_for('office_home'))

    # Fetch existing data
    query = "SELECT * FROM office_fees WHERE reg_id=%s"
    office_fee = selectone(query, (reg_id,))

    if not office_fee:
        return "Office fee record not found", 404

    return render_template('edit_office_fee.html', office_fee=office_fee)
@app.route('/delete_office_fee/<reg_id>', methods=['POST'])
def delete_office_fee(reg_id):
    # Delete query
    qry = "DELETE FROM office_fees WHERE reg_id = %s"
    val = (reg_id,)
    
    # Execute the delete query
    iud(qry, val)

    return redirect(url_for('office_home'))
    
@app.route('/test_fetch_fees')
def test_fetch_fees():
    return render_template('test_fetch_fees.html')


@app.route('/fetch_all_fees')
def fetch_all_fees():
    reg_id = request.args.get('reg_id')

    if reg_id:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query for hostel fees
        cursor.execute("SELECT 'Hostel' AS source, fee_id, reg_id, fee_type, description, amount, due_date, status FROM hostel_fees WHERE reg_id = %s", (reg_id,))
        hostel_fees = cursor.fetchall()

        # Query for office fees
        cursor.execute("SELECT 'Office' AS source,  fee_id, reg_id, fee_type, description, amount, due_date, status FROM office_fees WHERE reg_id = %s", (reg_id,))
        office_fees = cursor.fetchall()

        # Query for department fees
        cursor.execute("SELECT 'Department' AS source,  fee_id, reg_id, fee_type, description, amount, due_date, status FROM department_fees WHERE reg_id = %s", (reg_id,))
        department_fees = cursor.fetchall()

        # Query for library fees (fixed)
        cursor.execute("SELECT 'Library' AS source, 'Book fine' AS fee_type, book_id AS description, total_fine AS amount, fee_id, reg_id, due_date, status FROM library_fees WHERE reg_id = %s", (reg_id,))
        library_fees = cursor.fetchall()
        
        hostel_fees = list(hostel_fees) if not isinstance(hostel_fees, list) else hostel_fees
        office_fees = list(office_fees) if not isinstance(office_fees, list) else office_fees
        department_fees = list(department_fees) if not isinstance(department_fees, list) else department_fees
        library_fees = list(library_fees) if not isinstance(library_fees, list) else library_fees


        # Combine all fees
        all_fees = hostel_fees + office_fees + department_fees + library_fees

        connection.close()

        # Return all fees as JSON
        return jsonify(all_fees)
    else:
        return jsonify([])  # Return an empty list if no reg_id is provided


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route("/student_pay_due")
def student_pay_due():
    amt = request.args.get('amt')

    session['amt']  = int(float(amt))
    id = request.args.get('fee_id')

    session['due_id'] = id

    std_id = request.args.get('std_id')

    session['std_id'] = std_id

    source = request.args.get('fee_type')

    session['due_type'] = source


    return redirect("/user_pay_proceed")


@app.route('/user_pay_proceed')
def user_pay_proceed():
    client = razorpay.Client(auth=("rzp_test_edrzdb8Gbx5U5M", "XgwjnFvJQNG6cS7Q13aHKDJj"))
    print(client)
    payment = client.order.create({'amount': int(float(session['amt']*100)), 'currency': "INR", 'payment_capture': '1'})
    return render_template('UserPayProceed.html',p=payment)
@app.route('/user_pay_complete', methods=['POST'])
def user_pay_complete():
    print(request.form)
    pid = request.form['razorpay_payment_id']
    fee_type = session.get('due_type')  # This will hold which fee type (office, library, department, or hostel)
    due_id = session.get('due_id')  # The specific fee entry to be updated
    amt = session.get('amt')
   
    # Fetch the student's email from the session
    qry = "SELECT `email` FROM `students` WHERE `reg_id`=%s"
    res = selectone(qry, session['std_id'])  # Assuming reg_id is in session
    email = res['email']
    
    # Sending confirmation email
    try:
        gmail = smtplib.SMTP('smtp.gmail.com', 587)
        gmail.ehlo()
        gmail.starttls()
        gmail.login('duetrackermp@gmail.com', 'your-email-password')
    except Exception as e:
        print("Couldn't setup email!!" + str(e))
    
    msg = MIMEText(f"Hello\nYour payment was successful for Fee Type: {fee_type.capitalize()}\nAmount: {amt}\nPayment ID: {pid}\nYou can login to view payment details.")
    msg['Subject'] = 'Payment Confirmation'
    msg['To'] = email
    msg['From'] = 'duetrackermp@gmail.com'
    
    try:
        gmail.send_message(msg)
    except Exception as e:
        print("Couldn't send email: ", str(e))

    # Update the payment status in the respective table based on fee_type
    if fee_type == 'Office':
        qry = "UPDATE `office_fees` SET `status`='Paid', `payment_id`=%s WHERE `fee_id`=%s"
    elif fee_type == 'Library':
        qry = "UPDATE `library_fees` SET `status`='Paid', `payment_id`=%s WHERE `fee_id`=%s"
    elif fee_type == 'Department':
        qry = "UPDATE `department_fees` SET `status`='Paid', `payment_id`=%s WHERE `fee_id`=%s"
    elif fee_type == 'Hostel':
        qry = "UPDATE `hostel_fees` SET `status`='Paid', `payment_id`=%s WHERE `fee_id`=%s"
    else:
        return '''<script>alert("Invalid Fee Type!",fee_type);window.location="student_home"</script>'''

    # Execute the update query
    iud(qry, (pid, due_id))


    return '''<script>alert("Payment successful!");window.location="student_home"</script>'''
	
if __name__ == '__main__':
    app.run(debug=True)
