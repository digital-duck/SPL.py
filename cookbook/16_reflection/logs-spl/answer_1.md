Here is an example design for a URL shortener system:

**System Requirements**

*   Unique Shortened URLs: Each original URL should be mapped to a unique shortened URL.
*   Redirects: When a user clicks on a shortened URL, they should be redirected to the corresponding original URL.
*   Stats and Analytics: Provide basic statistics about how often each shortened URL is clicked.

**System Design**

The system will consist of three main components:

1.  **Database**: This will store information about all URLs, including the shortened URLs and their corresponding original URLs.
2.  **URL Shortener Service**: This service will be responsible for shortening URLs, generating unique shortened URLs, and storing them in the database.
3.  **Redirect Service**: This service will redirect users to the correct original URL based on the shortened URL.

**Flow**

Here's a high-level overview of how the system works:

1.  When a user submits a new URL for shortening, it's processed by the URL Shortener Service.
2.  The service generates a unique shortened URL and stores this information in the database along with the corresponding original URL.
3.  When a user clicks on a shortened URL, it's intercepted by the Redirect Service.
4.  The service retrieves the original URL from the database based on the shortened URL and redirects the user to the correct location.

**Scalability**

To ensure our system can handle high traffic and maintain performance, we'll use the following strategies:

*   **Distributed Database**: Use a distributed database that's designed for horizontal scaling. This allows us to add more nodes as needed to support increased load.
*   **Load Balancing**: Implement load balancing to distribute incoming requests across multiple instances of our URL Shortener Service and Redirect Service.

**Code Implementation**

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
    
    if not original_url:
        return {'error': 'Missing URL'}, 400
    
    shortened_url = generate_shortened_url()
    
    # Store the mapping between the shortened URL and the original URL in the database.
    database[shortened_url] = original_url
    
    return {'original_url': original_url, 'shortened_url': shortened_url}

@app.route('/click', methods=['POST'])
def click_shortened_url():
    shortened_url = request.form.get('url')
    
    if not shortened_url:
        return {'error': 'Missing URL'}, 400
    
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

**API Documentation**

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

Example Response:

```bash
http://example.com/short/abc123
```

### Stats

Example Response:

```json
{
    "stats": {
        "num_clicks": 10,
        "last_updated": "2023-02-20T14:30:00.000000"
    }
}
```

This is a basic implementation of an in-memory database and doesn't account for things like handling duplicate URLs, caching, etc. However, it should give you a starting point to build upon.