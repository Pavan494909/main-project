from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import re
from werkzeug.security import generate_password_hash, check_password_hash
# Add new imports for sentiment analysis
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
nltk.download('vader_lexicon', quiet=True)

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # replace with your MySQL username
app.config['MYSQL_PASSWORD'] = 'Usman@786'  # replace with your MySQL password
app.config['MYSQL_DB'] = 'login_system'  # replace with your database name

# Initialize MySQL and Sentiment Analyzer
mysql = MySQL(app)
sia = SentimentIntensityAnalyzer()

# Add sentiment analysis function
def analyze_sentiment(text):
    # Get sentiment scores
    scores = sia.polarity_scores(text)
    
    # Determine sentiment based on compound score
    if scores['compound'] >= 0.05:
        sentiment = 'Positive'
    elif scores['compound'] <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    
    return {
        'sentiment': sentiment,
        'confidence': abs(scores['compound']) * 100,
        'scores': {
            'positive': scores['pos'] * 100,
            'negative': scores['neg'] * 100,
            'neutral': scores['neu'] * 100,
            'compound': scores['compound']
        }
    }

# Existing routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user[3], password):
            session['loggedin'] = True
            session['id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            flash('Incorrect email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Input validation
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address', 'error')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers', 'error')
        elif not username or not email or not password:
            flash('Please fill out the form', 'error')
        else:
            # Check if user already exists
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            
            if user:
                flash('Account already exists with this email', 'error')
            else:
                hashed_password = generate_password_hash(password)
                cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                           (username, email, hashed_password))
                mysql.connection.commit()
                flash('You have successfully registered', 'success')
                return redirect(url_for('login'))
            
            cur.close()
    
    return render_template('register.html')

@app.route('/home')
def home():
    # Check if user is logged in
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

# Updated sentiment analysis route
@app.route('/sentiment_analysis', methods=['GET', 'POST'])
def sentiment_analysis():
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    result = None
    review = ''
    
    if request.method == 'POST':
        review = request.form['review']
        if review:
            # Get sentiment analysis results
            result = analyze_sentiment(review)
    
    return render_template('sentiment_analysis.html', username=session['username'], 
                         review=review, result=result)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)