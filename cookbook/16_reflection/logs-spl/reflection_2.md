**URL Shortener System Design**

The goal of this project is to design an efficient and scalable URL shortener system that can handle high traffic and provide basic statistics about how often each shortened URL is clicked.

**System Components**

1.  **Database**: A PostgreSQL database with the following tables:
    *   `urls`: stores information about all URLs, including the shortened URLs and their corresponding original URLs.
2.  **URL Shortener Service**: a Flask API that shortens URLs, generates unique shortened URLs, and stores them in the database.
3.  **Redirect Service**: a Flask API that redirects users to the correct original URL based on the shortened URL.

**System Flow**

1.  When a user submits a new URL for shortening, it's processed by the URL Shortener Service.
2.  The service generates a unique shortened URL and stores this information in the database along with the corresponding original URL.
3.  When a user clicks on a shortened URL, it's intercepted by the Redirect Service.
4.  The service retrieves the original URL from the database based on the shortened URL and redirects the user to the correct location.

**Scalability Strategies**

1.  **Distributed Database**: Use a distributed PostgreSQL database with multiple nodes to handle high traffic and improve performance.
2.  **Load Balancing**: Implement load balancing using HAProxy or NGINX to distribute incoming requests across multiple instances of the URL Shortener Service and Redirect Service.

**Security Measures**

1.  **HTTPS**: Secure the server with HTTPS using SSL/TLS certificates to protect user data.
2.  **Password Hashing**: Use password hashing libraries like Werkzeug to securely store passwords for administrators.
3.  **Input Validation**: Validate user input data, including URLs and shortened URLs, to prevent SQL injection and other attacks.

**Code Implementation**

Below is an example code implementation in Python:

```python
import os
from flask import Flask, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@host:port/dbname'
db = SQLAlchemy(app)

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(200), unique=True, nullable=False)
    shortened_url = db.Column(db.String(20), unique=True, nullable=False)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if 'url' not in data:
        return jsonify({'error': 'Missing URL'}), 400
    
    original_url = data['url']
    
    # Validate the input URL
    try:
        url = urlparse(original_url)
        if not all([url.scheme, url.netloc]):
            raise ValueError("Invalid URL")
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    shortened_url = generate_shortened_url()
    
    # Create a new URL entry in the database
    try:
        url_entry = URL(original_url=original_url, shortened_url=shortened_url)
        db.session.add(url_entry)
        db.session.commit()
        
        return {'original_url': original_url, 'shortened_url': shortened_url}
    except Exception as e:
        # Log any errors that occur during database operations
        app.logger.error(str(e))
        return jsonify({'error': 'Failed to shorten URL'}), 500

@app.route('/click', methods=['POST'])
def click_shortened_url():
    data = request.get_json()
    if 'url' not in data:
        return jsonify({'error': 'Missing URL'}), 400
    
    shortened_url = data['url']
    
    try:
        url_entry = URL.query.filter_by(shortened_url=shortened_url).first()
        if url_entry and url_entry.original_url == shortened_url:
            # Redirect to the original URL
            return redirect(url_for('original_url', url=shortened_url))
        
        return jsonify({'error': 'URL not found'}), 404
    except Exception as e:
        app.logger.error(str(e))
        return jsonify({'error': 'Failed to click URL'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    stats = {'num_clicks': URL.query.count(), 'last_updated': datetime.now()}
    
    # Calculate the last updated time to improve performance
    recent_urls = URL.query.order_by(URL.id.desc()).limit(10).all()
    for url in recent_urls:
        try:
            stats['num_clicks'] += 1
        except Exception as e:
            app.logger.error(str(e))
    
    return jsonify({'stats