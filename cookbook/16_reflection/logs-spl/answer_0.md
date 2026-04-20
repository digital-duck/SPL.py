# URL Shortener System Design

## Overview

A URL shortener is a service that takes a long, unwieldy URL and reduces it to a shorter, more manageable version. This can be useful for several reasons:

*   **Shorter URLs are easier to type**: People often struggle with typing out long URLs, especially on mobile devices or when sharing links via text message.
*   **Long URLs can lead to duplicate clicks**: When the same URL is shared multiple times, it's possible that some users may click on the link more than once. A URL shortener can help avoid this by providing a unique shortened version of each original URL.

## System Requirements

The following are the key requirements for our URL shortener system:

*   **Unique Shortened URLs**: Each original URL should be mapped to a unique shortened URL.
*     **Redirects**: When a user clicks on a shortened URL, they should be redirected to the corresponding original URL.
*   **Stats and Analytics**: Provide basic statistics about how often each shortened URL is clicked.

## System Design

Here's an overview of our system design:

### Components

1.  **Database**
    *   Stores information about all URLs, including the shortened URLs and their corresponding original URLs.
2.  **URL Shortener Service**
    *   Responsible for shortening URLs, generating unique shortened URLs, and storing them in the database.
3.  **Redirect Service**
    *   Redirects users to the correct original URL based on the shortened URL.

### Flow

Here's a high-level overview of how our system works:

1.  When a user submits a new URL for shortening, it's processed by the URL Shortener Service.
2.  The service generates a unique shortened URL and stores this information in the database along with the corresponding original URL.
3.  When a user clicks on a shortened URL, it's intercepted by the Redirect Service.
4.  The service retrieves the original URL from the database based on the shortened URL and redirects the user to the correct location.

### Scalability

To ensure our system can handle high traffic and maintain performance, we'll use the following strategies:

*   **Distributed Database**: Use a distributed database that's designed for horizontal scaling. This allows us to add more nodes as needed to support increased load.
*   **Load Balancing**: Implement load balancing to distribute incoming requests across multiple instances of our URL Shortener Service and Redirect Service.

### Code Implementation

Below is an example code implementation in Python:

```python
import uuid
from flask import Flask, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# In-memory database for demonstration purposes only. 
# In a real-world application, you'd want to use a production-ready database.

database = {}

@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form.get('url')
    shortened_url = generate_shortened_url()
    
    # Store the mapping between the shortened URL and the original URL in the database.
    database[shortened_url] = original_url
    
    return {'original_url': original_url, 'shortened_url': shortened_url}

@app.route('/click', methods=['POST'])
def click_shortened_url():
    shortened_url = request.form.get('url')
    
    # Retrieve the original URL from the database based on the shortened URL.
    original_url = database[shortened_url]
    
    # Redirect the user to the correct location.
    return redirect(original_url)

@app.route('/stats', methods=['GET'])
def get_stats():
    stats = {'num_clicks': 0, 'last_updated': datetime.now()}
    
    # Retrieve the mappings between shortened URLs and original URLs from the database.
    for shortened_url, original_url in database.items():
        stats['num_clicks'] += 1
    
    return {'stats': stats}

# Function to generate a unique shortened URL.
def generate_shortened_url():
    return f'http://example.com/short/{uuid.uuid4().hex[:6]}'

if __name__ == '__main__':
    app.run(debug=True)
```

This is a basic implementation of an in-memory database and doesn't account for things like handling duplicate URLs, caching, etc. However, it should give you a starting point to build upon.

## API Documentation

Here's some sample API documentation for our URL shortener system:

### Shorten URL Endpoint

*   `POST /shorten`
    *   Request Body:
        +   `url`: The original URL to be shortened.
    *   Response: A JSON object containing the shortened URL and the original URL.

Example Request:

```bash
curl -X POST \
  http://localhost:5000/shorten \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'url=https://www.example.com'
```

### Click