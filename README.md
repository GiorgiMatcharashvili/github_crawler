# GitHub Crawler

## Introduction
This project is a GitHub crawler implemented in Python. The crawler allows users to perform GitHub searches and retrieve all the links from the search results. It emphasizes efficiency in terms of speed, low memory usage, and low CPU usage. The requisites for the project are:

- Implemented in Python 3
- Efficient crawler
- Supports search with Unicode characters
- Utilizes proxies for HTTP requests
- Supports searching for different types of objects such as Repositories, Issues, and Wikis

## Usage
To use this project, follow these steps:

1. Install Docker and Docker Compose.
2. Install requirements by navigating to the app directory and running:
    ```
    pip install -r requirements.txt
    ```
3. Build the Docker containers with:
    ```
    docker-compose build
    ```
4. Start the containers with:
    ```
    docker-compose up
    ```
5. Optionally, run tests with:
    ```
    coverage run -m tests
    ```

## Technologies
Using the following technologies is beneficial for this project:

- Flask and Flask-RESTful for building the API
- Multiprocessing for efficient crawling
- Docker for containerization
- Gunicorn for deployment
- BeautifulSoup4 for HTML parsing
- Marshmallow for data validation
- Coverage for code coverage analysis
- python-dotenv for managing environment variables

## Endpoints
This API provides two endpoints:

1. **/proxies** (GET):
   - Description: Parses https://free-proxy-list.net/ and returns proxies.
   - Usage: Send a GET request to `/proxies` endpoint.
   - Example:
     ```bash
     curl http://localhost:5000/proxies
     ```
   - Response:
     ```json
     {
         "proxies": [
             "123.456.789:000",
             "123.456.789:001"
         ]
     }
     ```

2. **/crawler** (POST):
   - Description: Crawls GitHub website based on search parameters and returns search results.
   - Usage: Send a POST request to `/crawler` endpoint with request body containing keywords, proxies, and type of search.
   - Request Body:
     ```json
     {
         "keywords": ["keyword1", "keyword2"],
         "proxies": ["proxy1", "proxy2"],
         "type": "type_of_search"
     }
     ```
   - Response:
     - For Wikis and Issues types:
       ```json
       [
           {
               "url": "https://github.com/user/repo"
           }
       ]
       ```
     - For Repositories type (with extra information):
       ```json
       [
           {
               "url": "https://github.com/user/repo",
               "extra": {
                   "owner": "user",
                   "language_stats": {
                       "CSS": 52.0,
                       "JavaScript": 47.2,
                       "HTML": 0.8
                   }
               }
           }
       ]
       ```

## Unit Tests
This project includes a total of 22 tests with a coverage of 92%.

