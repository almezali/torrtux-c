#!/usr/bin/env python3
"""
Torrtux v1.0.3 - Professional Torrent Search Tool
"""

import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
from termcolor import colored
import time
import re
from urllib.parse import urljoin, quote
import logging
import csv
import json
from concurrent.futures import ThreadPoolExecutor

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
import threading
import itertools
import time

ASCII_ART = """


 ████████╗ ██████╗ ██████╗ ██████╗ ████████╗██╗   ██╗██╗  ██╗
 ╚══██╔══╝██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝██║   ██║╚██╗██╔╝
    ██║   ██║   ██║██████╔╝██████╔╝   ██║   ██║   ██║ ╚███╔╝ 
    ██║   ██║   ██║██╔══██╗██╔══██╗   ██║   ██║   ██║ ██╔██╗ 
    ██║   ╚██████╔╝██║  ██║██║  ██║   ██║   ╚██████╔╝██╔╝ ██╗
    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝


                                v1.0.3
"""

class TorrentSite:
    """Base class for torrent sites"""
    def __init__(self, name, base_urls, search_path="", result_selector=""):
        self.name = name
        self.base_urls = base_urls if isinstance(base_urls, list) else [base_urls]
        self.search_path = search_path
        self.result_selector = result_selector
        self.working_url = None
    
    def test_connection(self):
        """Test if any of the base URLs are working"""
        for url in self.base_urls:
            try:
                response = requests.get(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    self.working_url = url
                    return True
            except:
                continue
        return False
    
    def search(self, query, page=0):
        """Search for torrents on this site"""
        if not self.working_url:
            return []
        
        try:
            search_url = self.build_search_url(query, page)
            response = requests.get(search_url, timeout=15)
            if response.status_code == 200:
                return self.parse_results(response.content, query)
        except Exception as e:
            print(colored(f"Error searching {self.name}: {e}", "red"))
        
        return []
    
    def build_search_url(self, query, page=0):
        """Build search URL - to be implemented by subclasses"""
        raise NotImplementedError
    
    def parse_results(self, content, query):
        """Parse search results - to be implemented by subclasses"""
        raise NotImplementedError

    def get_magnet_link(self, detail_url):
        """Get magnet link from detail page"""
        try:
            response = requests.get(detail_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml")
                for a in soup.find_all("a", href=True):
                    if a["href"].startswith("magnet:"):
                        return a["href"]
        except Exception as e:
            print(colored(f"Error getting magnet link from {self.name}: {e}", "red"))
        return None

    def build_latest_url(self, page=0):
        # By default, fallback to search for empty query or a special latest page if site supports it
        try:
            return self.build_search_url("", page)
        except:
            return None

class PirateBay(TorrentSite):
    def __init__(self):
        super().__init__(
            "The Pirate Bay",
            [
                "https://thepiratebay.org",
                "https://tpb.party",
                "https://pirateproxy.live",
                "https://thehiddenbay.com",
                "https://piratebay.live",
                "https://thepiratebay.rocks",
                "https://tpb.pm",
                "https://piratebay.ink",
                "https://piratebayproxy.net",
                "https://thepiratebay10.org",
                "https://thepiratebay3.to"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/s/?q={quote(query)}&page={page}&orderby=99"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", id="searchResult")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                name_cell = row.find("a", class_="detLink")
                name = name_cell.get_text(strip=True) if name_cell else "-"
                detail_url = urljoin(self.working_url, name_cell["href"]) if name_cell else None
                magnet_link = row.find("a", href=lambda href: href and href.startswith("magnet:"))
                magnet = magnet_link["href"] if magnet_link else (self.get_magnet_link(detail_url) if detail_url else "")
                desc_cell = row.find("font", class_="detDesc")
                desc_text = desc_cell.get_text().split(",") if desc_cell else []
                date = desc_text[0].replace("Uploaded ", "").strip() if len(desc_text) > 0 else "-"
                size = desc_text[1].replace("Size ", "").strip() if len(desc_text) > 1 else "-"
                seed_leeches = row.find_all("td", align="right")
                seeds = seed_leeches[0].get_text() if len(seed_leeches) > 0 else "-"
                leeches = seed_leeches[1].get_text() if len(seed_leeches) > 1 else "-"
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except Exception as e:
                continue
        return results

class X1337(TorrentSite):
    def __init__(self):
        super().__init__(
            "1337x",
            [
                "https://1337x.to",
                "https://1337x.st",
                "https://x1337x.ws",
                "https://1337x.gd",
                "https://1337x.is",
                "https://1337x.unblockit.boo"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search/{quote(query)}/{page+1}/"

    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="table-list")
        if not table:
            return results

        for row in table.find_all("tr")[1:]:
            try:
                name_cell = row.find("td", class_="name").find_all("a")[1]
                name = name_cell.text
                detail_url = urljoin(self.working_url, name_cell["href"])
                seeds = row.find("td", class_="seeds").text
                leeches = row.find("td", class_="leeches").text
                size = row.find("td", class_="size").text.split("B")[0] + "B"
                date = row.find("td", class_="coll-date").text

                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": self.get_magnet_link(detail_url),
                    "site": self.name
                })
            except:
                continue
        return results

class YTS(TorrentSite):
    def __init__(self):
        super().__init__(
            "YTS",
            [
                "https://yts.mx",
                "https://yts.rs",
                "https://yts.lt"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/browse-movies/{quote(query)}/all/all/0/latest"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for movie in soup.select(".browse-movie-wrap"):
            try:
                name = movie.select_one(".browse-movie-title").text.strip()
                year = movie.select_one(".browse-movie-year").text.strip()
                detail_url = movie.select_one("a")['href']
                seeds = "-"
                leeches = "-"
                size = "-"
                date = year
                magnet = None
                # Get magnet from detail page
                try:
                    magnet = self.get_magnet_link(detail_url)
                except:
                    pass
                results.append({
                    "name": f"{name} ({year})",
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class Nyaa(TorrentSite):
    def __init__(self):
        super().__init__(
            "Nyaa",
            [
                "https://nyaa.si",
                "https://nyaa.net"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/?f=0&c=0_0&q={quote(query)}&p={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="torrent-list")
        if not table:
            table = soup.find("table", class_="table")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[1].find("a", href=True).text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a", href=True)["href"])
                size = cols[3].text.strip()
                date = cols[4].text.strip()
                seeds = cols[5].text.strip()
                leeches = cols[6].text.strip()
                magnet = cols[2].find("a", href=lambda h: h and h.startswith("magnet:"))
                magnet = magnet["href"] if magnet else self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class EZTV(TorrentSite):
    def __init__(self):
        super().__init__(
            "EZTV",
            [
                "https://eztv.re",
                "https://eztv.wf",
                "https://eztv.unblockit.boo"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search/{quote(query)}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="forum_header_border")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue
                name = cols[1].get_text(strip=True)
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[3].get_text(strip=True)
                date = cols[4].get_text(strip=True)
                seeds = "-"
                leeches = "-"
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class TorrentGalaxy(TorrentSite):
    def __init__(self):
        super().__init__(
            "TorrentGalaxy",
            [
                "https://torrentgalaxy.to",
                "https://tgx.rs"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/torrents.php?search={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="tgxtable")
        if not table:
            return results
        for row in table.find_all("tr", class_="tgxtablerow"):
            try:
                cols = row.find_all("td")
                if len(cols) < 10:
                    continue
                name = cols[1].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[5].text.strip()
                seeds = cols[7].text.strip()
                leeches = cols[8].text.strip()
                date = cols[4].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class LimeTorrents(TorrentSite):
    def __init__(self):
        super().__init__(
            "LimeTorrents",
            [
                "https://www.limetorrents.lol",
                "https://www.limetorrents.pro",
                "https://www.limetorrents.cyou",
                "https://www.limetorrents.zone"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search/all/{quote(query)}/seeds/{page+1}/"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", id="table2")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 6:
                    continue
                name = cols[0].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[0].find("a")["href"])
                size = cols[1].text.strip()
                date = cols[2].text.strip()
                seeds = cols[3].text.strip()
                leeches = cols[4].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class TorrentDownloads(TorrentSite):
    def __init__(self):
        super().__init__(
            "TorrentDownloads",
            [
                "https://www.torrentdownloads.pro",
                "https://www.torrentdownloads.me",
                "https://www.torrentdownloads.unblockit.boo"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search/?search={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="torrent_table")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue
                name = cols[0].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[0].find("a")["href"])
                size = cols[1].text.strip()
                date = cols[2].text.strip()
                seeds = cols[3].text.strip()
                leeches = cols[4].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class Torlock(TorrentSite):
    def __init__(self):
        super().__init__(
            "Torlock",
            [
                "https://www.torlock.com",
                "https://torlock.unblocked.lol"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/all/torrents/{quote(query)}.html?page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", id="torrenttable")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[0].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[0].find("a")["href"])
                size = cols[3].text.strip()
                date = cols[4].text.strip()
                seeds = cols[5].text.strip()
                leeches = cols[6].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class Zooqle(TorrentSite):
    def __init__(self):
        super().__init__(
            "Zooqle",
            [
                "https://zooqle.com",
                "https://zooqle.unblockit.boo"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search?q={quote(query)}&pg={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for row in soup.select(".torrent-list tbody tr"):
            try:
                cols = row.find_all("td")
                if len(cols) < 8:
                    continue
                name = cols[1].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[5].text.strip()
                seeds = cols[6].text.strip()
                leeches = cols[7].text.strip()
                date = "-"
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class TorrentFunk(TorrentSite):
    def __init__(self):
        super().__init__(
            "TorrentFunk",
            [
                "https://www.torrentfunk.com"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search/all/{quote(query)}/"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for row in soup.select(".search-results .odd, .search-results .even"):
            try:
                name = row.find("a", class_="torrent-name").text.strip()
                detail_url = urljoin(self.working_url, row.find("a", class_="torrent-name")["href"])
                size = row.find("td", class_="size").text.strip()
                seeds = row.find("td", class_="seeds").text.strip()
                leeches = row.find("td", class_="leeches").text.strip()
                date = "-"
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class ETTV(TorrentSite):
    def __init__(self):
        super().__init__(
            "ETTV",
            [
                "https://www.ettvdl.com",
                "https://ettvcentral.com"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/torrents-search.php?search={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="table")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[1].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[2].text.strip()
                seeds = cols[5].text.strip()
                leeches = cols[6].text.strip()
                date = cols[3].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class Bitsearch(TorrentSite):
    def __init__(self):
        super().__init__(
            "Bitsearch",
            [
                "https://bitsearch.to"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search?q={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for row in soup.select(".search-results .result"):
            try:
                name = row.find("a", class_="name").text.strip()
                detail_url = urljoin(self.working_url, row.find("a", class_="name")["href"])
                size = row.find("span", class_="size").text.strip()
                seeds = row.find("span", class_="seeds").text.strip()
                leeches = row.find("span", class_="leeches").text.strip()
                date = "-"
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class Glodls(TorrentSite):
    def __init__(self):
        super().__init__(
            "Glodls",
            [
                "https://glodls.to"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search_results.php?search={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="table")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[1].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[2].text.strip()
                seeds = cols[5].text.strip()
                leeches = cols[6].text.strip()
                date = cols[3].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class TorrentProject(TorrentSite):
    def __init__(self):
        super().__init__(
            "TorrentProject",
            [
                "https://torrentproject2.com",
                "https://torrentproject.se"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/?t={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for row in soup.select(".table tr"):
            try:
                cols = row.find_all("td")
                if len(cols) < 6:
                    continue
                name = cols[0].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[0].find("a")["href"])
                size = cols[2].text.strip()
                seeds = cols[3].text.strip()
                leeches = cols[4].text.strip()
                date = cols[1].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class SkyTorrents(TorrentSite):
    def __init__(self):
        super().__init__(
            "SkyTorrents",
            [
                "https://www.skytorrents.lol",
                "https://skytorrents.unblockit.boo"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search/all/{quote(query)}/page/{page+1}/"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="table")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[1].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[2].text.strip()
                seeds = cols[5].text.strip()
                leeches = cols[6].text.strip()
                date = cols[3].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class YourBittorrent(TorrentSite):
    def __init__(self):
        super().__init__(
            "YourBittorrent",
            [
                "https://yourbittorrent.com"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/?q={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for row in soup.select(".search-result .row"):
            try:
                name = row.find("a", class_="torrent-name").text.strip()
                detail_url = urljoin(self.working_url, row.find("a", class_="torrent-name")["href"])
                size = row.find("span", class_="size").text.strip()
                seeds = row.find("span", class_="seeds").text.strip()
                leeches = row.find("span", class_="leeches").text.strip()
                date = "-"
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class KickassTorrents(TorrentSite):
    def __init__(self):
        super().__init__(
            "KickassTorrents",
            [
                "https://kickasstorrents.to",
                "https://katcr.to",
                "https://kickasstorrents.bz"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/usearch/{quote(query)}/{page+1}/"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="data")
        if not table:
            return results
        for row in table.find_all("tr", class_="odd") + table.find_all("tr", class_="even"):
            try:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue
                name = cols[0].find("a", class_="cellMainLink").text.strip()
                detail_url = urljoin(self.working_url, cols[0].find("a", class_="cellMainLink")["href"])
                size = cols[1].text.strip()
                seeds = cols[2].text.strip()
                leeches = cols[3].text.strip()
                date = cols[4].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class Torrentz2(TorrentSite):
    def __init__(self):
        super().__init__(
            "Torrentz2",
            [
                "https://torrentz2.nz",
                "https://torrentz2.is",
                "https://torrentz2.eu"
            ]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search?f={quote(query)}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for row in soup.select(".results dl"):
            try:
                name = row.find("a").text.strip()
                detail_url = urljoin(self.working_url, row.find("a")["href"])
                # Torrentz2 does not provide size/seeds/leeches directly
                size = "-"
                seeds = "-"
                leeches = "-"
                date = "-"
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class RARBG(TorrentSite):
    def __init__(self):
        super().__init__(
            "RARBG",
            [
                "https://rarbgmirror.com",
                "https://rarbgprx.org"
            ]
        )
    def build_search_url(self, query, page=0):
        # Archive only, no real search, so return None
        return None
    def parse_results(self, content, query):
        print(colored("RARBG is closed. Archive mirrors only, no real search.", "red"))
        return []

class MagnetDL(TorrentSite):
    def __init__(self):
        super().__init__(
            "MagnetDL",
            [
                "https://www.magnetdl.com",
                "https://magnetdl.unblockit.boo"
            ]
        )
    def build_search_url(self, query, page=0):
        # MagnetDL uses the first letter of the query in the URL path
        first_letter = query[0].lower() if query else 'a'
        return f"{self.working_url}/{first_letter}/{quote(query)}/?page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="download")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[0].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[0].find("a")["href"])
                size = cols[3].text.strip()
                seeds = cols[4].text.strip()
                leeches = cols[5].text.strip()
                date = cols[2].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class GoodTorrent(TorrentSite):
    def __init__(self):
        super().__init__(
            "Good-Torrent",
            ["https://good-torrent.com"]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/search/{quote(query)}"
    def parse_results(self, content, query):
        # Initial: No detailed parsing yet, to be improved after site structure analysis.
        soup = BeautifulSoup(content, "lxml")
        results = []
        # Can be improved later
        return results

class ArabTorrents(TorrentSite):
    def __init__(self):
        super().__init__(
            "Arab-Torrents",
            ["https://www.arab-torrents.net"]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/torrents-search.php?search={quote(query)}&page={page+1}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="table")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[1].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[2].text.strip()
                seeds = cols[5].text.strip()
                leeches = cols[6].text.strip()
                date = cols[3].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class FitGirlRepacks(TorrentSite):
    def __init__(self):
        super().__init__(
            "FitGirl Repacks",
            ["https://fitgirl-repacks.site"]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/?s={quote(query)}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        for post in soup.select(".post"):
            try:
                name = post.find("h1", class_="post-title").text.strip()
                detail_url = post.find("a")["href"]
                size = "-"
                seeds = "-"
                leeches = "-"
                date = "-"
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class LinuxTracker(TorrentSite):
    def __init__(self):
        super().__init__(
            "LinuxTracker",
            ["https://linuxtracker.org"]
        )
    def build_search_url(self, query, page=0):
        return f"{self.working_url}/index.php?page=torrents&search={quote(query)}"
    def parse_results(self, content, query):
        soup = BeautifulSoup(content, "lxml")
        results = []
        table = soup.find("table", class_="torrents")
        if not table:
            return results
        for row in table.find_all("tr")[1:]:
            try:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                name = cols[1].find("a").text.strip()
                detail_url = urljoin(self.working_url, cols[1].find("a")["href"])
                size = cols[4].text.strip()
                seeds = cols[5].text.strip()
                leeches = cols[6].text.strip()
                date = cols[3].text.strip()
                magnet = self.get_magnet_link(detail_url)
                results.append({
                    "name": name,
                    "size": size,
                    "seeds": seeds,
                    "leeches": leeches,
                    "date": date,
                    "magnet": magnet,
                    "site": self.name
                })
            except:
                continue
        return results

class TorrentSearcher:
    def __init__(self):
        self.sites = [
            PirateBay(),
            X1337(),
            KickassTorrents(),
            YTS(),
            Nyaa(),
            EZTV(),
            TorrentGalaxy(),
            LimeTorrents(),
            TorrentDownloads(),
            Torlock(),
            Zooqle(),
            TorrentFunk(),
            ETTV(),
            MagnetDL(),
            Bitsearch(),
            Glodls(),
            TorrentProject(),
            SkyTorrents(),
            YourBittorrent(),
            GoodTorrent(),
            Torrentz2(),
            RARBG(),
            ArabTorrents(),
            FitGirlRepacks(),
            LinuxTracker(),
        ]
        self.working_sites = []
    
    def test_sites(self):
        """Test which sites are working"""
        print(colored("Testing torrent sites...", "cyan"))
        
        for site in self.sites:
            print(f"Testing {site.name}...", end=" ")
            if site.test_connection():
                self.working_sites.append(site)
                print(colored("✓ Working", "green"))
            else:
                print(colored("✗ Not accessible", "red"))
        
        if not self.working_sites:
            print(colored("No working torrent sites found!", "red"))
            return False
        
        print(colored(f"\nFound {len(self.working_sites)} working sites", "green"))
        return True
    
    def search_all_sites(self, query, page_limit=1, show_progress=False, verbose=False):
        """Search all working sites"""
        all_results = []
        
        for site in self.working_sites:
            spinner = Spinner(f"Searching {site.name}") if show_progress else None
            if show_progress:
                spinner.start()
            elif verbose:
                print(colored(f"\nSearching {site.name}...", "yellow"))
            try:
                for page in range(page_limit):
                    search_url = None
                    try:
                        search_url = site.build_search_url(query, page)
                    except Exception as e:
                        if show_progress:
                            spinner.stop(colored(f"✗ Error", "red"))
                        elif verbose:
                            print(colored(f"Error building search URL for {site.name}: {e}", "red"))
                        break
                    if not search_url or not isinstance(search_url, str) or not search_url.startswith("http"):
                        if show_progress:
                            spinner.stop(colored(f"✗ Skipped", "magenta"))
                        elif verbose:
                            print(colored(f"Skipping {site.name}: No valid search URL.", "magenta"))
                        break
                    try:
                        response = requests.get(search_url, timeout=15)
                        if response.status_code == 200:
                            results = site.parse_results(response.content, query)
                            if results:
                                all_results.extend(results)
                                if show_progress:
                                    spinner.stop(colored(f"✓ {len(results)} results", "green"))
                                elif verbose:
                                    print(colored(f"Found {len(results)} results from {site.name} (page {page + 1})", "green"))
                            else:
                                if show_progress:
                                    spinner.stop(colored(f"- No results", "magenta"))
                                elif verbose:
                                    print(colored(f"No results found from {site.name} (page {page + 1})", "magenta"))
                                break
                        elif response.status_code == 403:
                            if show_progress:
                                spinner.stop(colored(f"✗ 403", "red"))
                            elif verbose:
                                print(colored(f"{site.name} returned status code 403 (Forbidden/Blocked). Skipping site.", "red"))
                            break
                        elif response.status_code == 404:
                            if show_progress:
                                spinner.stop(colored(f"✗ 404", "red"))
                            elif verbose:
                                print(colored(f"{site.name} returned status code 404 (Not Found). Skipping site.", "red"))
                            break
                        elif response.status_code == 500:
                            if show_progress:
                                spinner.stop(colored(f"✗ 500", "red"))
                            elif verbose:
                                print(colored(f"{site.name} returned status code 500 (Internal Server Error). Skipping site.", "red"))
                            break
                        else:
                            if show_progress:
                                spinner.stop(colored(f"✗ {response.status_code}", "red"))
                            elif verbose:
                                print(colored(f"{site.name} returned status code {response.status_code}. Skipping site.", "red"))
                            break
                    except requests.exceptions.Timeout:
                        if show_progress:
                            spinner.stop(colored(f"✗ Timeout", "red"))
                        elif verbose:
                            print(colored(f"Timeout while searching {site.name} (page {page + 1})", "red"))
                        break
                    except requests.exceptions.RequestException as e:
                        if show_progress:
                            spinner.stop(colored(f"✗ ConnErr", "red"))
                        elif verbose:
                            print(colored(f"Connection error while searching {site.name}: {e}", "red"))
                        break
                    except Exception as e:
                        if show_progress:
                            spinner.stop(colored(f"✗ Error", "red"))
                        elif verbose:
                            print(colored(f"Unexpected error while searching {site.name}: {e}", "red"))
                        break
            except Exception as e:
                if show_progress:
                    spinner.stop(colored(f"✗ Error", "red"))
                elif verbose:
                    print(colored(f"Error searching {site.name}: {e}", "red"))
        if not all_results:
            print(colored("\nNo results found from any site. Try a different search term.", "red"))
        return all_results
    
    def search_latest_sites(self, page_limit=1, show_progress=False, verbose=False):
        all_results = []
        for site in self.working_sites:
            spinner = Spinner(f"Fetching {site.name}") if show_progress else None
            if show_progress:
                spinner.start()
            elif verbose:
                print(colored(f"\nFetching latest torrents from {site.name}...", "yellow"))
            try:
                for page in range(page_limit):
                    latest_url = None
                    try:
                        latest_url = site.build_latest_url(page)
                    except Exception as e:
                        if show_progress:
                            spinner.stop(colored(f"✗ Error", "red"))
                        elif verbose:
                            print(colored(f"Error building latest URL for {site.name}: {e}", "red"))
                        continue
                    if not latest_url or not isinstance(latest_url, str) or not latest_url.startswith("http"):
                        if show_progress:
                            spinner.stop(colored(f"✗ Skipped", "magenta"))
                        elif verbose:
                            print(colored(f"Skipping {site.name}: No valid latest URL.", "magenta"))
                        break
                    try:
                        response = requests.get(latest_url, timeout=15)
                        if response.status_code == 200:
                            results = site.parse_results(response.content, "")
                            if results:
                                all_results.extend(results)
                                if show_progress:
                                    spinner.stop(colored(f"✓ {len(results)} results", "green"))
                                elif verbose:
                                    print(colored(f"Found {len(results)} latest torrents from {site.name} (page {page + 1})", "green"))
                            else:
                                if show_progress:
                                    spinner.stop(colored(f"- No results", "magenta"))
                                elif verbose:
                                    print(colored(f"No latest torrents found from {site.name} (page {page + 1})", "magenta"))
                                break
                        else:
                            if show_progress:
                                spinner.stop(colored(f"✗ {response.status_code}", "red"))
                            elif verbose:
                                print(colored(f"{site.name} returned status code {response.status_code}", "red"))
                            break
                    except Exception as e:
                        if show_progress:
                            spinner.stop(colored(f"✗ Error", "red"))
                        elif verbose:
                            print(colored(f"Error fetching latest from {site.name}: {e}", "red"))
                        break
            except Exception as e:
                if show_progress:
                    spinner.stop(colored(f"✗ Error", "red"))
                elif verbose:
                    print(colored(f"Error fetching latest from {site.name}: {e}", "red"))
        return all_results
    
    def format_results(self, results):
        """Format results for display with truncation for neat columns"""
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append([
                i,
                truncate(result["site"], 14),
                truncate(result["name"], 40),
                truncate(result["size"], 12),
                truncate(result["seeds"], 8),
                truncate(result["leeches"], 8),
                truncate(result["date"], 16),
            ])
        return formatted_results

def parse_size(size_str):
    # Convert size string like '1.2 GB' to bytes
    try:
        size_str = size_str.strip().upper()
        if size_str.endswith('GB'):
            return float(size_str.replace('GB','').strip()) * 1024**3
        elif size_str.endswith('MB'):
            return float(size_str.replace('MB','').strip()) * 1024**2
        elif size_str.endswith('KB'):
            return float(size_str.replace('KB','').strip()) * 1024
        elif size_str.endswith('B'):
            return float(size_str.replace('B','').strip())
        else:
            return float(size_str)
    except:
        return 0

def truncate(text, maxlen):
    text = str(text)
    return text if len(text) <= maxlen else text[:maxlen-3] + '...'

# Spinner utility
class Spinner:
    def __init__(self, message="Loading"):
        self.spinner = itertools.cycle(['|', '/', '-', '\\'])
        self.stop_running = False
        self.message = message
        self.thread = None
    def start(self):
        def run():
            while not self.stop_running:
                print(f"\r{self.message} {next(self.spinner)}", end="", flush=True)
                time.sleep(0.1)
        self.thread = threading.Thread(target=run)
        self.thread.start()
    def stop(self, end_message=None):
        self.stop_running = True
        if self.thread:
            self.thread.join()
        print("\r" + (end_message or "").ljust(40))

# Update main() to add new arguments and logic

def main():
    parser = argparse.ArgumentParser(
        description="Torrtux - Professional Torrent Search Tool"
    )
    parser.add_argument(
        "search",
        help="Search query",
        nargs="?",
        default=None,
        metavar="QUERY"
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        help="Number of pages to search per site (default: 1)",
        default=1,
        metavar="N"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        help="Maximum number of results to display (default: unlimited)",
        default=None,
        metavar="N"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="Torrtux v1.0.3"
    )
    parser.add_argument(
        "--sites",
        type=str,
        help="Comma-separated list of sites to search (e.g. '1337x,The Pirate Bay,Nyaa')",
        default=None
    )
    parser.add_argument(
        "--min-size",
        type=str,
        help="Minimum torrent size (e.g. 500MB)",
        default=None
    )
    parser.add_argument(
        "--max-size",
        type=str,
        help="Maximum torrent size (e.g. 2GB)",
        default=None
    )
    parser.add_argument(
        "--min-seeds",
        type=int,
        help="Minimum number of seeds",
        default=None
    )
    parser.add_argument(
        "--max-seeds",
        type=int,
        help="Maximum number of seeds",
        default=None
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        help="Export results to CSV file"
    )
    parser.add_argument(
        "--export-json",
        type=str,
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--magnets-only",
        action="store_true",
        help="Show only magnet links in output"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress ASCII art and extra messages"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Filter by content type (if supported by site)",
        default=None
    )
    parser.add_argument(
        "--lang",
        type=str,
        help="Filter by language (if supported by site)",
        default=None
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel search across sites"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Show latest torrents from all or selected sites"
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show a loading spinner/progress indicator while fetching results"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed fetching messages"
    )

    args = parser.parse_args()

    if not args.quiet:
        print(colored(ASCII_ART, "cyan", attrs=["bold"]))

    if not args.search and not args.latest:
        parser.print_help()
        sys.exit(1)

    if args.pages <= 0 or args.pages > 10:
        print(colored("Page limit must be between 1 and 10", "red"))
        sys.exit(1)

    searcher = TorrentSearcher()

    if not searcher.test_sites():
        print(colored("No working torrent sites available. Please check your internet connection or try using a VPN.", "red"))
        sys.exit(1)

    # Filter sites if --sites is used
    if args.sites:
        selected_sites = [s.strip().lower() for s in args.sites.split(",")]
        searcher.working_sites = [site for site in searcher.working_sites if site.name.lower() in selected_sites]
        if not searcher.working_sites:
            print(colored("No matching sites found for your selection.", "red"))
            sys.exit(1)

    if not args.quiet:
        if args.search:
            print(colored(f"\nSearching for: '{args.search}'", "yellow", attrs=["bold"]))
        else:
            print(colored("\nFetching latest torrents...", "yellow", attrs=["bold"]))

    # Parallel search if --parallel
    if args.parallel:
        all_results = []
        def search_site(site):
            results = []
            try:
                for page in range(args.pages):
                    search_url = site.build_search_url(args.search, page)
                    if not search_url or not isinstance(search_url, str) or not search_url.startswith("http"):
                        break
                    response = requests.get(search_url, timeout=15)
                    if response.status_code == 200:
                        results += site.parse_results(response.content, args.search)
                    else:
                        break
            except Exception as e:
                pass
            return results
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(search_site, site) for site in searcher.working_sites]
            for future in futures:
                all_results += future.result()
        results = all_results
    elif args.latest:
        results = searcher.search_latest_sites(args.pages, show_progress=args.progress, verbose=args.verbose)
    else:
        results = searcher.search_all_sites(args.search, args.pages, show_progress=args.progress, verbose=args.verbose)

    # Filtering by seeds/size
    if args.min_seeds is not None:
        results = [r for r in results if r["seeds"] != '-' and r["seeds"].isdigit() and int(r["seeds"]) >= args.min_seeds]
    if args.max_seeds is not None:
        results = [r for r in results if r["seeds"] != '-' and r["seeds"].isdigit() and int(r["seeds"]) <= args.max_seeds]
    if args.min_size is not None:
        min_bytes = parse_size(args.min_size)
        results = [r for r in results if r["size"] != '-' and parse_size(r["size"]) >= min_bytes]
    if args.max_size is not None:
        max_bytes = parse_size(args.max_size)
        results = [r for r in results if r["size"] != '-' and parse_size(r["size"]) <= max_bytes]

    # Filter by category/lang if supported (future extension)
    # ...

    if args.limit:
        results = results[:args.limit]

    if not results:
        print(colored("No results found!", "red"))
        sys.exit(0)

    if args.export_csv:
        with open(args.export_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["site", "name", "size", "seeds", "leeches", "date", "magnet"])
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print(colored(f"Results exported to {args.export_csv}", "green"))

    if args.export_json:
        with open(args.export_json, "w") as f:
            json.dump(results, f, indent=2)
        print(colored(f"Results exported to {args.export_json}", "green"))

    if args.magnets_only:
        for r in results:
            if r["magnet"]:
                print(r["magnet"])
        print(colored(f"\nTotal magnet links: {len([r for r in results if r['magnet']])}", "green", attrs=["bold"]))
        sys.exit(0)

    if not args.quiet:
        print(colored("\n" + "=" * 80, "cyan"))
        print(colored("SEARCH RESULTS", "cyan", attrs=["bold"]))
        print(colored("=" * 80, "cyan"))

    headers = ["#", "Site", "Name", "Size", "Seeds", "Leeches", "Date"]
    formatted_results = searcher.format_results(results)
    table = tabulate(formatted_results, headers=headers, tablefmt="fancy_grid", stralign="left", numalign="right")
    print(table)

    print(colored(f"\nTotal results: {len(results)}", "green", attrs=["bold"]))

    if args.quiet:
        sys.exit(0)

    while True:
        try:
            choice = input(colored("\nEnter torrent number to get magnet link (0 to exit): ", "blue")).strip()
            if choice == "0" or choice.lower() == "exit":
                break
            try:
                index = int(choice) - 1
                if 0 <= index < len(results):
                    result = results[index]
                    magnet_link = result.get("magnet")
                    if magnet_link:
                        print(colored("\nMagnet Link:", "yellow", attrs=["bold"]))
                        print(magnet_link)
                    else:
                        print(colored("Magnet link not found for this torrent.", "red"))
                else:
                    print(colored("Invalid number! Please try again.", "red"))
            except ValueError:
                print(colored("Please enter a valid number!", "red"))
        except KeyboardInterrupt:
            break
    print(colored("\nThank you for using Torrtux!", "green", attrs=["bold"]))

if __name__ == "__main__":
    # Setup error logging
    logging.basicConfig(filename='torrtux_errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')
    main()


