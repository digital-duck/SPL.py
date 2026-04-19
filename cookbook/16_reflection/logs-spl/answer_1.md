Here is a design for a URL shortener system:

**Overview**

The URL shortener system will be designed to provide a simple and efficient way for users to shorten long URLs. The system will store shortened URLs in a database and provide an API for users to shorten URLs.

**Database Schema**

The database schema will consist of the following tables:

*   **Urls**: stores the shortened URLs
    *   `id` (primary key): unique identifier for each URL
    *   `original_url`: the original, long URL
    *   `short_code`: a unique short code for the URL
    *   `clicks`: the number of times the URL has been clicked

*   **Clicks**: stores the click history for each URL
    *   `id` (primary key): unique identifier for each click
    *   `url_id` (foreign key): references the `id` column in the `Urls` table
    *   `click_time`: the timestamp of when the URL was clicked

**API Endpoints**

The following API endpoints will be provided:

1.  **POST /urls**: creates a new shortened URL
    *   Request Body:
        ```json
{
  "original_url": "https://www.example.com/very-long-url"
}
```
    *   Response: the short code for the URL
    *   Example: `https://short.url/abc123`

2.  **GET /urls/{short_code}**: retrieves the original URL associated with a given short code
    *   Request Parameters:
        ```bash
?short_code=abc123
```
    *   Response: the original URL
    *   Example: `https://www.example.com/very-long-url`

3.  **GET /clicks**: retrieves the click history for all URLs
    *   Response: a list of click history for each URL
    *   Example:
        ```json
[
  {
    "url_id": 1,
    "click_time": "2023-03-01T12:00:00Z"
  },
  {
    "url_id": 2,
    "click_time": "2023-03-02T13:30:00Z"
  }
]
```

4.  **GET /urls/{short_code}/clicks**: logs a click for the URL associated with the given short code
    *   Request Parameters:
        ```bash
?short_code=abc123
```
    *   Response: `message` indicating that the click has been logged successfully

**System Architecture**

The system will be built using a microservices architecture, with each endpoint implemented as a separate service.

1.  **URL Shortener Service**: This service will handle the creation and management of shortened URLs. It will store data in the `Urls` table and provide API endpoints for creating and retrieving shortened URLs.
2.  **Click History Service**: This service will handle the logging of click history for each URL. It will store data in the `Clicks` table and provide API endpoints for storing and retrieving click history.

**Implementation**

The implementation will be written in a programming language such as Python, using a web framework such as Flask or Django.

Here is an example of how the system could be implemented:

```python
from flask import Flask, request, jsonify
import uuid
from datetime import datetime

app = Flask(__name__)

# In-memory database
urls = {}
clicks = {}

@app.route('/urls', methods=['POST'])
def create_url():
    original_url = request.json['original_url']
    short_code = str(uuid.uuid4())
    urls[short_code] = {'original_url': original_url, 'clicks': 0}
    return jsonify({'short_code': short_code})

@app.route('/urls/<string:short_code>', methods=['GET'])
def get_original_url(short_code):
    if short_code in urls:
        return jsonify(urls[short_code]['original_url'])
    else:
        return jsonify({'error': 'Invalid short code'}), 404

@app.route('/clicks', methods=['GET'])
def get_click_history():
    click_history = []
    for url_id, clicks_data in clicks.items():
        for click_time, _ in clicks_data:
            click_history.append({
                'url_id': url_id,
                'click_time': click_time
            })
    return jsonify(click_history)

@app.route('/urls/<string:short_code>/clicks', methods=['POST'])
def log_click(short_code):
    if short_code in urls:
        urls[short_code]['clicks'] += 1
        clicks[str(uuid.uuid4())] = [(datetime.now(), short_code)]
        return jsonify({'message': 'Click logged successfully'})
    else:
        return jsonify({'error': 'Invalid short code'}), 404

if __name__ == '__