from flask import Flask, request, jsonify
from flask_restful import Resource, Api, abort
from marshmallow.exceptions import ValidationError
from requests.exceptions import ConnectionError

from process import ProxyParser, GitHubCrawler, PROXY_URL
from schemas import InputSchema


app = Flask(__name__)
api = Api(app)


class Proxies(Resource):
    def get(self):
        """
        Handle GET request to fetch proxies.
        """
        try:
            proxies = ProxyParser()
            proxies.fetch_proxies()
            return jsonify({"proxies": proxies.get_proxies()})
        except ConnectionError as e:
            abort(503, error_message={"Service Unavailable": f"Unable to connect to {PROXY_URL}: {e}"})
        except Exception as e:
            abort(500, error_message={"Internal Server Error": str(e)})


class Crawler(Resource):
    def post(self):
        """
        Handle POST request to start the GitHub crawler.
        """
        request_json = request.get_json()

        # Validate and deserialize input
        schema = InputSchema()
        try:
            data = schema.load(request_json)
            crawler = GitHubCrawler(data['proxies'])

            # Execute crawling with provided keywords and type
            result = crawler.crawl(data['keywords'], data['type'])
            return jsonify(result)
        except ValidationError as e:
            # Handle validation errors
            abort(400, error_message={"Bad Request": e.messages})
        except Exception as e:
            abort(500, error_message={"Internal Server Error": str(e)})


# Define the API resources
api.add_resource(Proxies, "/proxies")
api.add_resource(Crawler, "/crawler")
