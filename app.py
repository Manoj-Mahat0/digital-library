from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import requests
from bs4 import BeautifulSoup
from functools import wraps



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

admin_logged_in = False

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not admin_logged_in:
            # Redirect to error page or any other action you prefer
            return render_template('error.html', message='Access denied. Please log in as admin.')
        return f(*args, **kwargs)
    return decorated_function

# Dummy user data (replace with your actual user authentication system)
# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'Libraryms'

mysql = MySQL(app)


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/error')
def error_page():
    return render_template('error.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shop')
def shop():
    # Render the shop.html template
    return render_template('shop.html')

@app.route('/addtocart', methods=['GET', 'POST'])
def addtocart():
    if request.method == 'POST':
        # Handle POST request to add item to cart
        # Logic to add item to cart
        return render_template('addtocart.html')  # Render the add_to_cart page after item is added
    else:
        # Handle GET request to access add_to_cart page directly (if needed)
        return redirect(url_for('books'))  # Redirect to books page or handle differently based on your application's logic



@app.route('/books')
def books():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of items per page

        cur = mysql.connection.cursor()
        cur.execute('SELECT COUNT(*) FROM lib_books')
        total_books = cur.fetchone()[0]

        cur.execute('SELECT * FROM lib_books LIMIT %s OFFSET %s', (per_page, (page - 1) * per_page))
        books = cur.fetchall()
        cur.close()

        return render_template('books.html', books=books, total_books=total_books, page=page, per_page=per_page)
    except Exception as e:
        print("Error fetching books:", e)
        return "An error occurred while fetching books."

@app.route('/addbook', methods=['GET', 'POST'])
def addbook():
    if request.method == 'POST':
        # Get form data
        book_name = request.form['book_name']
        publisher = request.form['publisher']
        book_author = request.form['book_author']
        isbn_no = request.form['isbn_no']
        registration_date = request.form['registration_date']
        available = request.form['available']
        price = request.form['price']
        
        # Create a cursor
        cur = mysql.connection.cursor()

        # Execute query to insert data into the database
        cur.execute("INSERT INTO lib_books (book_name, publisher, book_author, isbn_no, registration_date, available, price) VALUES (%s, %s, %s, %s, %s, %s, %s)", (book_name, publisher, book_author, isbn_no, registration_date, available, price))

        # Commit to database
        mysql.connection.commit()

        # Close cursor
        cur.close()

        # Redirect or render success page
        return render_template('addbook.html')
    else:
        return render_template('addbook.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/thanks')
def thanks():
    return render_template('thanks.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Error page
@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_msg = None  # Define with a default value

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print("Received form data:", username, password)  # Check if form data is received
        
        # Connect to the database
        cursor = mysql.connection.cursor()
        
        try:
            # Query the database to check if the credentials are valid
            cursor.execute("SELECT * FROM admin_login WHERE username = %s AND password = %s", (username, password))
            admin = cursor.fetchone()
            
            print("Fetched admin:", admin)  # Check if admin is fetched
            
            if admin:
                session['logged_in'] = True
                return redirect(url_for('admin'))
            else:
                error_msg = 'Invalid username or password. Please try again.'
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
        finally:
            cursor.close()

    # Move the render_template outside of the 'if' block
    return render_template('login.html', error=error_msg)



@app.route('/signup', methods=['GET', 'POST'])
@admin_required
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Connect to the database
        cur = mysql.connection.cursor()

        try:
            # Check if the username already exists in the database
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            existing_user = cur.fetchone()
            
            if existing_user:
                return render_template('signup.html', message='Username already exists. Please choose another username.')
            else:
                # Insert new user into the database
                cur.execute('INSERT INTO users (name, username, password) VALUES (%s, %s, %s)', (name, username, password))
                mysql.connection.commit()
                return redirect(url_for('login'))  # Redirect to the login page after successful signup
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            return render_template('signup.html', message=error_msg)
        finally:
            cur.close()
    
    return render_template('signup.html')



@app.route('/news')
def news():
    try:
        url = 'https://epaper.navbharattimes.com/?status=ssosigninsuccess&channel=nbtepaper&site=sso&ticketId=7HpoL5Ytj-JFdrDLxFZqcETYiCNqaB7wSA-jpl4DnzzhqI4Ac3TH3h4X8G67BsmL'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find elements with class "col-sm-4 mp-col" and then find elements with class "dtspan" within them
        dtspan_elements = soup.find_all(class_='col-sm-4 mp-col')[0].find_all(class_='dtspan')
        
        # Extracting the text content of dtspan elements
        dtspan_texts = [element.text for element in dtspan_elements]
        
        return render_template('news.html', dtspan_texts=dtspan_texts)
    except Exception as e:
        return render_template('error.html', message="An error occurred while fetching news.")

    
    
@app.route('/admin')
def admin():
    if 'logged_in' in session and session['logged_in']:
        return render_template('admin.html')
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
