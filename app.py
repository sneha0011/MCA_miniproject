from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from db import iud, selectone

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key

@app.route('/')
def home():
    if 'username' in session:
        role = session.get('role')
        if role == 'admin':
            return render_template('admin1.html')  # Admin homepage
        elif role == 'staff':
            return render_template('staff_home.html')  # Staff homepage
        elif role == 'student':
            return render_template('student_home.html')  # Student homepage
        else:
            return "Unauthorized"
    return redirect(url_for('login'))

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
                return redirect(url_for('home'))
            else:
                return "Invalid credentials. Please try again."
        else:
            return "User does not exist."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
