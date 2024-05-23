import json
import os
import random
import uuid
from typing import List, Any, Dict

import multiprocessing as mp
import requests
from bs4 import BeautifulSoup

# Constants for environment variables
PROXY_URL = os.environ.get('PROXY_URL', 'https://free-proxy-list.net/')
GITHUB_URL = os.environ.get('GITHUB_URL', 'https://github.com')

# Setting up headers for requests
try:
    HEADERS = json.loads(os.environ.get('HEADERS'))
except:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/58.0.3029.110 Safari/537.3",
        "Accept": "text/html"
    }


class ProxyParser:
    """Class to fetch and parse proxy addresses."""

    def __init__(self):
        self.proxies = []

    def fetch_proxies(self) -> None:
        """Fetches proxy addresses from the proxy URL."""
        try:
            response = requests.get(url=PROXY_URL)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching proxies: {e}")

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table table-striped table-bordered')
        ip_addresses = table.find_all('tr')[1:]

        for ip_address in ip_addresses:
            proxy = ip_address.find_all('td')[0].text
            self.proxies.append(proxy)

    def get_proxies(self) -> List[str]:
        """Returns the list of fetched proxy addresses."""
        return self.proxies


class GitHubCrawler:
    """Class to crawl GitHub using provided proxies."""

    def __init__(self, proxies: List[str]):
        self.proxies = proxies

    def crawl(self, keywords: List[str], search_type: str) -> List[Dict[str, Any]]:
        """Crawls GitHub for the given keywords and search type, and returns a list of results."""
        url = f"{GITHUB_URL}/search?q={'+'.join(keywords)}&type={search_type}"
        proxy = self._get_valid_proxy()

        manager = mp.Manager()
        return_dict = manager.dict()
        jobs = []

        try:
            response = requests.get(url=url, headers=HEADERS, proxies={"http": proxy, "https": proxy})
            response.raise_for_status()
        except (requests.exceptions.ProxyError, requests.exceptions.RequestException) as e:
            raise Exception(f"Error fetching data from GitHub: {e}")

        soup = BeautifulSoup(response.content, 'html.parser')
        div = soup.find('div', class_="Box-sc-g0xbh4-0 kXssRI")
        divs = div.find_all('div', class_="Box-sc-g0xbh4-0 bDcVHV")

        results = []
        for div in divs:
            a = div.find('a', class_="Link__StyledLink-sc-14289xe-0 dheQRw")
            repo_url = f"{GITHUB_URL}{a['href']}"
            final_data = {'url': repo_url}
            if search_type == 'Repositories':
                process = mp.Process(target=self._get_extra_info,
                                     args=(repo_url, {"http": proxy, "https": proxy}, final_data, return_dict,))
                jobs.append(process)
                process.start()
            else:
                results.append(final_data)

        for job in jobs:
            job.join()

        if search_type == 'Repositories':
            return list(return_dict.values())
        return results

    def _get_valid_proxy(self) -> str:
        """Returns a valid proxy from the list of proxies."""
        if not self.proxies:
            raise Exception("No valid proxies available")
        return random.choice(self.proxies)

    @staticmethod
    def _get_extra_info(url: str, proxies: Dict[str, str], final_data: Dict[str, Any],
                        return_dict: Dict[str, Any]) -> None:
        """Fetches additional information about the repository and updates the shared dictionary."""
        result = {"language_stats": {}}

        try:
            response = requests.get(url=url, headers=HEADERS, proxies=proxies)
            response.raise_for_status()
        except (requests.exceptions.ProxyError, requests.exceptions.RequestException) as e:
            raise Exception(f"Error fetching extra info from GitHub: {e}")

        soup = BeautifulSoup(response.content, 'html.parser')
        name_a = soup.find('a', class_="url fn")
        name = name_a.text.strip().replace('\n', '')
        result["owner"] = name

        divs = soup.find('div', class_="BorderGrid about-margin")
        languages_div = divs.find_all('div', class_="BorderGrid-row")[-1]

        languages_a = languages_div.find_all('a',
                                             class_="d-inline-flex flex-items-center flex-nowrap Link--secondary no-underline text-small mr-3")

        for language_a in languages_a:
            languages_span = language_a.find_all('span')
            language = languages_span[0].text
            stat = float(languages_span[1].text.replace('%', ''))
            result["language_stats"][language] = stat

        final_data["extra"] = result
        return_dict[uuid.uuid4().hex] = final_data
