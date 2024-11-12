from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from config import MYSQL_CONFIG

app = Flask(__name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_part', methods=['POST'])
def add_part():
    part_type = request.form['type']
    length = float(request.form['length'])
    width = float(request.form['width'])
    height = float(request.form['height'])
    manufacturer = request.form['manufacturer']
    part_id = int(request.form['id'])

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO parts (id, type, length, width, height, manufacturer) VALUES (%s, %s, %s, %s, %s, %s)',
                   (part_id, part_type, length, width, height, manufacturer))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('index'))

@app.route('/remove_part', methods=['POST'])
def remove_part():
    part_id = int(request.form['id'])

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM parts WHERE id = %s', (part_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
