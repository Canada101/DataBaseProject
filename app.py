from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import pandas as pd
import os
from config import MYSQL_CONFIG

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

@app.route('/show_table', methods=['POST'])
def show_table():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM parts')
    myresults = cursor.fetchall()
    connection.commit()
    cursor.close()
    connection.close()
    
    # Create DataFrame and convert to HTML
    df = pd.DataFrame(myresults, columns=['ID', 'Type', 'Length', 'Width', 'Height', 'Manufacturer'])
    table_html = df.to_html(index=False)
    
    return render_template('data_table.html', data_table=table_html)

@app.route('/search_part', methods=['GET'])
def search_part():
    part_id = request.args.get('id')

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM parts WHERE id = %s', (part_id,))
    result = cursor.fetchone()
    connection.close()

    if result:
        df = pd.DataFrame([result], columns=['ID', 'Type', 'Length', 'Width', 'Height', 'Manufacturer'])
        table_html = df.to_html(index=False)
    else:
        table_html = "<p>Part with entered ID couldn't be found</p>"

    return render_template('data_table.html', data_table=table_html)

@app.route('/upload_invoice', methods=['GET', 'POST'])
def upload_invoice():
    if request.method == 'POST':
        file = request.files['invoice']
        if file and file.filename.endswith('.txt'):
            # Save the uploaded file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            connection = get_db_connection()
            cursor = connection.cursor()

            # Insert invoice details
            cursor.execute('INSERT INTO invoices (invoice_name) VALUES (%s)', (file.filename,))
            connection.commit()
            invoice_id = cursor.lastrowid

            # Parse file and add parts
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()  # Remove leading/trailing whitespace
                    if line:  # Ensure the line is not empty
                        attributes = [x.strip() for x in line.split(',')]  # Strip each part
                        
                        if len(attributes) == 6:  # Ensure there are exactly 6 attributes
                            part_id, part_type, length, width, height, manufacturer = attributes
                            
                            try:
                                part_id = int(part_id)
                                length, width, height = float(length), float(width), float(height)
                            except ValueError:
                                return f"Invalid number format in line: {line}", 400

                            # Insert part into the database if it doesn't already exist
                            cursor.execute(
                                'INSERT IGNORE INTO parts (id, type, length, width, height, manufacturer) '
                                'VALUES (%s, %s, %s, %s, %s, %s)',
                                (part_id, part_type, length, width, height, manufacturer)
                            )

                            # Link part to the invoice
                            cursor.execute(
                                'INSERT INTO invoice_parts (invoice_id, part_id) VALUES (%s, %s)',
                                (invoice_id, part_id)
                            )
                        else:
                            return f"Invalid line format: {line}. It must contain 6 values.", 400
            connection.commit()
            cursor.close()
            connection.close()

            return redirect(url_for('index'))
        else:
            return "Invalid file type. Please upload a .txt file.", 400
    return render_template('upload_invoice.html')

@app.route('/search_invoice', methods=['GET'])
def search_invoice():
    invoice_id = request.args.get('invoice_id')

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT p.id, p.type, p.length, p.width, p.height, p.manufacturer
        FROM parts p
        INNER JOIN invoice_parts ip ON p.id = ip.part_id
        WHERE ip.invoice_id = %s
    ''', (invoice_id,))
    results = cursor.fetchall()
    connection.close()

    if results:
        df = pd.DataFrame(results, columns=['ID', 'Type', 'Length', 'Width', 'Height', 'Manufacturer'])
        table_html = df.to_html(index=False)
    else:
        table_html = "<p>No parts found for this invoice.</p>"

    return render_template('data_table.html', data_table=table_html)

if __name__ == '__main__':
    app.run(debug=True)
