# app.py

from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Configuration ---
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '1234')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'school_db')
app.config['MYSQL_CURSORCLASS'] = os.environ.get('MYSQL_CURSORCLASS', 'DictCursor')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))
CORS(app)
mysql = MySQL(app)

# --- API Endpoints for Students and Marks ---

# CREATE a new student (POST /api/students)
@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        name = data['name']
        student_class = data['class']
        email = data['email']
        roll_number = data['roll_number']
        marks_list = data['marks']  # [{subject, marks}, ...]
        
        # Calculate percentage
        total_marks = sum([float(m['marks']) for m in marks_list])
        percentage = total_marks / len(marks_list) if marks_list else 0

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO students (name, class, email, roll_number, percentage) VALUES (%s, %s, %s, %s, %s)",
                    (name, student_class, email, roll_number, percentage))
        student_id = cur.lastrowid
        # Insert marks
        for m in marks_list:
            cur.execute("INSERT INTO marks (student_id, subject, marks) VALUES (%s, %s, %s)",
                        (student_id, m['subject'], m['marks']))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Student added successfully', 'id': student_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# READ all students (GET /api/students)
@app.route('/api/students', methods=['GET'])
def get_all_students():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students")
        students = cur.fetchall()
        # Get marks for each student
        for s in students:
            cur.execute("SELECT subject, marks FROM marks WHERE student_id = %s", (s['id'],))
            s['marks'] = cur.fetchall()
        cur.close()
        return jsonify(students)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# READ a single student (GET /api/students/<id>)
@app.route('/api/students/<int:id>', methods=['GET'])
def get_student(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cur.fetchone()
        if student:
            cur.execute("SELECT subject, marks FROM marks WHERE student_id = %s", (id,))
            student['marks'] = cur.fetchall()
            cur.close()
            return jsonify(student)
        else:
            cur.close()
            return jsonify({'message': 'Student not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# UPDATE a student (PUT /api/students/<id>)
@app.route('/api/students/<int:id>', methods=['PUT', 'PATCH'])
def update_student(id):
    try:
        data = request.get_json()
        name = data['name']
        student_class = data['class']
        email = data['email']
        roll_number = data['roll_number']
        marks_list = data['marks']
        total_marks = sum([float(m['marks']) for m in marks_list])
        percentage = total_marks / len(marks_list) if marks_list else 0
        cur = mysql.connection.cursor()
        cur.execute("UPDATE students SET name=%s, class=%s, email=%s, roll_number=%s, percentage=%s WHERE id=%s",
                    (name, student_class, email, roll_number, percentage, id))
        # Remove old marks
        cur.execute("DELETE FROM marks WHERE student_id=%s", (id,))
        # Insert new marks
        for m in marks_list:
            cur.execute("INSERT INTO marks (student_id, subject, marks) VALUES (%s, %s, %s)",
                        (id, m['subject'], m['marks']))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Student updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# DELETE a student (DELETE /api/students/<id>)
@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM students WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Student deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
