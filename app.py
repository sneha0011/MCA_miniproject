from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql
from db import iud, selectone, selectall
from db import get_db_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    if 'username' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_home'))  # Redirect to Admin homepage
        elif role == 'staff':
            return redirect(url_for('staff_home'))  # Redirect to Staff homepage
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
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    sql_query = f"""
    SELECT * FROM students WHERE reg_id LIKE %s OR student_name LIKE %s
    """  # Replace 'student_id' with 'reg_id' if that's the correct column
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
        
        # Fetch user data from database
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

        return render_template('student_home.html', student=student_data)
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
