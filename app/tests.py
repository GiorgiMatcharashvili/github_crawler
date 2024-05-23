import unittest
from unittest.mock import patch, MagicMock
from app import app, ProxyParser, GitHubCrawler
from schemas import InputSchema
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, ProxyError
from marshmallow.exceptions import ValidationError
from requests.exceptions import RequestException

# Load environment variables for the app
load_dotenv()


class ProxiesTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the Flask app and test client
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

    @patch('app.ProxyParser')
    def test_get_proxies_success(self, MockProxyParser):
        # Mock the ProxyParser and set the return value for get_proxies
        mock_proxies = MockProxyParser.return_value
        mock_proxies.get_proxies.return_value = ['proxy1', 'proxy2']

        # Make a GET request to the /proxies endpoint
        response = self.client.get('/proxies')

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        # Assert that the JSON response contains the expected proxies
        self.assertEqual(response.json, {"proxies": ['proxy1', 'proxy2']})

    @patch('app.ProxyParser')
    def test_get_proxies_connection_error(self, MockProxyParser):
        # Mock the ProxyParser to raise a ConnectionError when fetch_proxies is called
        mock_proxies = MockProxyParser.return_value
        mock_proxies.fetch_proxies.side_effect = ConnectionError("Unable to connect")

        # Make a GET request to the /proxies endpoint
        response = self.client.get('/proxies')

        # Assert that the response status code is 503 (Service Unavailable)
        self.assertEqual(response.status_code, 503)
        # Assert that the error message contains 'Service Unavailable'
        self.assertIn('Service Unavailable', response.json['error_message'])

    @patch('app.ProxyParser')
    def test_get_proxies_internal_error(self, MockProxyParser):
        # Mock the ProxyParser to raise a generic exception when fetch_proxies is called
        mock_proxies = MockProxyParser.return_value
        mock_proxies.fetch_proxies.side_effect = Exception("Some error")

        # Make a GET request to the /proxies endpoint
        response = self.client.get('/proxies')

        # Assert that the response status code is 500 (Internal Server Error)
        self.assertEqual(response.status_code, 500)
        # Assert that the error message contains 'Internal Server Error'
        self.assertIn('Internal Server Error', response.json['error_message'])


class CrawlerTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the Flask app and test client
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

    @patch('app.GitHubCrawler')
    @patch('app.InputSchema')
    def test_post_crawler_success(self, MockInputSchema, MockGitHubCrawler):
        # Mock the InputSchema to return valid data
        mock_schema = MockInputSchema.return_value
        mock_schema.load.return_value = {
            'proxies': ['proxy1'],
            'keywords': ['keyword1', 'keyword2'],
            'type': 'some_type'
        }
        # Mock the GitHubCrawler to return a successful result
        mock_crawler = MockGitHubCrawler.return_value
        mock_crawler.crawl.return_value = {"result": "some_result"}

        # Make a POST request to the /crawler endpoint with valid JSON data
        response = self.client.post('/crawler', json={
            'proxies': ['proxy1'],
            'keywords': ['keyword1', 'keyword2'],
            'type': 'some_type'
        })

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        # Assert that the JSON response contains the expected result
        self.assertEqual(response.json, {"result": "some_result"})

    @patch('app.InputSchema')
    def test_post_crawler_validation_error(self, MockInputSchema):
        # Mock the InputSchema to raise a ValidationError
        mock_schema = MockInputSchema.return_value
        mock_schema.load.side_effect = ValidationError("Invalid data")

        # Make a POST request to the /crawler endpoint with invalid JSON data
        response = self.client.post('/crawler', json={
            'proxies': ['proxy1'],
            'keywords': ['keyword1', 'keyword2'],
            'type': 'some_type'
        })

        # Assert that the response status code is 400 (Bad Request)
        self.assertEqual(response.status_code, 400)
        # Assert that the error message contains 'Bad Request'
        self.assertIn('Bad Request', response.json['error_message'])

    @patch('app.InputSchema')
    def test_post_crawler_internal_error(self, MockInputSchema):
        # Mock the InputSchema to raise a generic exception
        mock_schema = MockInputSchema.return_value
        mock_schema.load.side_effect = Exception("Some error")

        # Make a POST request to the /crawler endpoint
        response = self.client.post('/crawler', json={
            'proxies': ['proxy1'],
            'keywords': ['keyword1', 'keyword2'],
            'type': 'some_type'
        })

        # Assert that the response status code is 500 (Internal Server Error)
        self.assertEqual(response.status_code, 500)
        # Assert that the error message contains 'Internal Server Error'
        self.assertIn('Internal Server Error', response.json['error_message'])


class ProxyParserTestCase(unittest.TestCase):

    @patch('requests.get')
    def test_fetch_proxies_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
            <html>
                <table class="table table-striped table-bordered">
                    <tr><th>IP</th></tr>
                    <tr><td>123.456.789.0</td></tr>
                    <tr><td>123.456.789.1</td></tr>
                </table>
            </html>
        """
        mock_get.return_value = mock_response

        parser = ProxyParser()
        parser.fetch_proxies()

        self.assertEqual(parser.get_proxies(), ['123.456.789.0', '123.456.789.1'])

    @patch('requests.get')
    def test_fetch_proxies_request_exception(self, mock_get):
        mock_get.side_effect = RequestException("Error fetching proxies")

        parser = ProxyParser()
        with self.assertRaises(Exception) as context:
            parser.fetch_proxies()

        self.assertIn("Error fetching proxies", str(context.exception))

    def test_get_proxies(self):
        parser = ProxyParser()
        parser.proxies = ['123.456.789.0', '123.456.789.1']

        self.assertEqual(parser.get_proxies(), ['123.456.789.0', '123.456.789.1'])


class GitHubCrawlerTestCase(unittest.TestCase):

    def setUp(self):
        self.proxies = ['http://123.456.789.0:8080', 'http://123.456.789.1:8080']
        self.crawler = GitHubCrawler(self.proxies)

    @patch('app.GitHubCrawler._get_extra_info')
    @patch('requests.get')
    @patch('multiprocessing.Process')
    def test_crawl_success(self, mock_process, mock_get, mock_get_extra_info):
        # Mock response for the initial GitHub search request
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = """
            <div class="Box-sc-g0xbh4-0 kXssRI">
                <div class="Box-sc-g0xbh4-0 bDcVHV">
                    <a class="Link__StyledLink-sc-14289xe-0 dheQRw" href="/user/repo"></a>
                </div>
            </div>
        """
        mock_get.return_value = mock_response

        # Mock the _get_extra_info method to avoid actual HTTP requests
        mock_get_extra_info.return_value = {}

        # Mock the process to avoid creating actual child processes
        mock_process.return_value = MagicMock()

        result = self.crawler.crawl(['test'], 'Wikis')
        expected_result = [{'url': 'https://github.com/user/repo'}]

        self.assertEqual(result, expected_result)

    @patch('requests.get')
    def test_crawl_proxy_error(self, mock_get):
        mock_get.side_effect = ProxyError("Proxy error")

        with self.assertRaises(Exception) as context:
            self.crawler.crawl(['test'], 'Repositories')

        self.assertIn("Error fetching data from GitHub", str(context.exception))

    @patch('requests.get')
    def test_crawl_request_exception(self, mock_get):
        mock_get.side_effect = RequestException("Request error")

        with self.assertRaises(Exception) as context:
            self.crawler.crawl(['test'], 'Repositories')

        self.assertIn("Error fetching data from GitHub", str(context.exception))

    def test__get_valid_proxy(self):
        proxy = self.crawler._get_valid_proxy()
        self.assertIn(proxy, self.proxies)

    def test__get_valid_proxy_no_proxies(self):
        crawler = GitHubCrawler([])
        with self.assertRaises(Exception) as context:
            crawler._get_valid_proxy()

        self.assertIn("No valid proxies available", str(context.exception))


class InputSchemaTestCase(unittest.TestCase):

    def setUp(self):
        self.schema = InputSchema()

    def test_valid_input(self):
        input_data = {
            "keywords": ["test", "example"],
            "proxies": ["http://proxy1", "http://proxy2"],
            "type": "Repositories"
        }
        result = self.schema.load(input_data)
        self.assertEqual(result, input_data)

    def test_empty_keywords(self):
        input_data = {
            "keywords": [],
            "proxies": ["http://proxy1", "http://proxy2"],
            "type": "Repositories"
        }
        with self.assertRaises(ValidationError) as context:
            self.schema.load(input_data)
        self.assertIn("keywords cannot be empty", str(context.exception))

    def test_empty_keyword_in_keywords(self):
        input_data = {
            "keywords": ["test", ""],
            "proxies": ["http://proxy1", "http://proxy2"],
            "type": "Repositories"
        }
        with self.assertRaises(ValidationError) as context:
            self.schema.load(input_data)
        self.assertIn("keyword cannot be empty", str(context.exception))

    def test_empty_proxies(self):
        input_data = {
            "keywords": ["test", "example"],
            "proxies": [],
            "type": "Repositories"
        }
        with self.assertRaises(ValidationError) as context:
            self.schema.load(input_data)
        self.assertIn("proxies cannot be empty", str(context.exception))

    def test_empty_proxy_in_proxies(self):
        input_data = {
            "keywords": ["test", "example"],
            "proxies": ["http://proxy1", ""],
            "type": "Repositories"
        }
        with self.assertRaises(ValidationError) as context:
            self.schema.load(input_data)
        self.assertIn("proxy cannot be empty", str(context.exception))

    def test_empty_type(self):
        input_data = {
            "keywords": ["test", "example"],
            "proxies": ["http://proxy1", "http://proxy2"],
            "type": ""
        }
        with self.assertRaises(ValidationError) as context:
            self.schema.load(input_data)
        self.assertIn("type cannot be empty", str(context.exception))

    def test_invalid_type(self):
        input_data = {
            "keywords": ["test", "example"],
            "proxies": ["http://proxy1", "http://proxy2"],
            "type": "InvalidType"
        }
        with self.assertRaises(ValidationError) as context:
            self.schema.load(input_data)
        self.assertIn("Unknown type: InvalidType", str(context.exception))

    def test_valid_types(self):
        for valid_type in ['Repositories', 'Issues', 'Wikis']:
            input_data = {
                "keywords": ["test", "example"],
                "proxies": ["http://proxy1", "http://proxy2"],
                "type": valid_type
            }
            result = self.schema.load(input_data)
            self.assertEqual(result, input_data)


if __name__ == '__main__':
    # Run the unittests
    unittest.main()
