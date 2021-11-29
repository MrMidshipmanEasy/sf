from yaml import load, dump, Loader
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Optional

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import dateparser
import warnings
warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


@dataclass
class RestaurantInfo:
    exist: bool = False
    reviews_count: Optional[int] = None
    last_reviews: Optional[str] = None
    price: Optional[str] = None
    cuisines: Optional[str] = None

    def __repr__(self):
        return f"[{'+' if self.exist else ' '}] {self.cuisines} {self.reviews_count} {self.price} {self.last_reviews}"


class TripAdvisorScrubber:
    base_url = "https://www.tripadvisor.com"
    cache_dir = "scrubber_cache"
    headers = {
        "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': 'www.tripadvisor.com',
        "Upgrade-Insecure-Requests": "1",
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:96.0) Gecko/20100101 Firefox/96.0',
        'TE': 'trailers'}

    @classmethod
    def cleanup(cls):
        shutil.rmtree(cls.cache_dir)

    def __init__(self, path):
        self.r = requests.Session()
        self.r.headers = self.headers
        self.soup = None
        self.path = path
        self.refer = None
        self.info = None

        cache = Path(self.cache_dir)
        if not cache.is_dir():
            cache.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache / path[1:].replace("&", "-").replace("?", '-')

    def grab(self, path):
        url = self.base_url + path
        if self.refer:
            self.r.headers.update({"Referer": self.refer})
            self.refer = url
        self.cache_file = Path(self.cache_dir) / path[1:].replace("&", "-").replace("?", '-')
        if not self.cache_file.is_file():
            resp = self.r.get(url, timeout=200, verify=False)
            print('.', end=" ")
            if resp.ok:
                html_doc = resp.text
                self.cache_file.write_text(html_doc)
                return html_doc
            else:
                print(resp)
        else:
            return self.cache_file.read_text()

    def build_info(self):
        def unlink():
            if self.cache_file.is_file():
                self.cache_file.unlink()

        data_cache = Path(str(self.cache_file)+'.yaml')
        if data_cache.is_file():
            unlink()
            return load(data_cache.read_text(), Loader)

        html_doc = self.grab(self.path)
        self.soup = BeautifulSoup(html_doc, 'html.parser')

        info = RestaurantInfo(exist=self.page_exist())
        if not info.exist:
            unlink()
            data_cache.write_text(dump(info))
            return info

        info.reviews_count = self.get_review_count()
        info.last_reviews = self.get_last_reviews()
        info.price = self.get_price()
        info.cuisines = self.get_cuisines()

        data_cache.write_text(dump(info))
        unlink()

        return info

    def page_exist(self):
        return len(self.soup.select("h1#HEADING")) == 0

    def get_review_count(self):
        review_count_selector = ".eBTWs"
        els = self.soup.select(f"{review_count_selector}")
        if len(els):
            return int(els[0].text.split()[0].replace(',',''))  # 50 reviews

    def get_last_reviews(self):
        reviews_selector = ".reviewSelector"
        reviews_els = self.soup.select(reviews_selector)
        reviews = []
        dates = []
        for r in reviews_els[:min(2, len(reviews_els))]:
            human_date = r.select('.ratingDate')[0].text.strip().replace("Reviewed ","")
            dates.append(dateparser.parse(human_date).strftime('%m/%d/%y'))
            text = r.select('.noQuotes')[0].text.strip()
            if text == '':
                gtrans = r.select('.ui_button.secondary.small')
                if len(gtrans) > 0:
                    link = gtrans[0].attrs['data-url']
                    html = self.grab(link)
                    s = BeautifulSoup(html, 'html.parser')
                    q = s.select(".quote")
                    if len(q) > 0:
                        text = s.select(".quote")[0].text.strip('"').strip("\n")

            reviews.append(text)
        return [reviews, dates]

    def get_price(self):
        price_selector = "#taplc_top_info_0 a.drUyy:nth-child(1)"
        price = self.soup.select(price_selector)
        if len(price):
            price = price[0].text.strip()
            return price if price in ['$', '$$$$', '$$ - $$$'] else None

    def get_cuisines(self):
        els = self.soup.select(".cfvAV")
        if len(els) == 0:
            return None
        cuisines = els[0].text.split(',')
        if cuisines[0].startswith('UAH'):
            return None
        cuisines = str(list(map(str.strip, cuisines)))
        return cuisines


if __name__ == "__main__":
    #
    path = "/Restaurant_Review-g189180-d12503536-Reviews-Dick_s_Bar-Porto_Porto_District_Northern_Portugal.html"
    # path = "/Restaurant_Review-g187514-d10058810-Reviews-Bar_Restaurante_El_Diezy7-Madrid.html"
    # # path = "/Restaurant_Review-g189852-d7992032-Reviews-Buddha_Nepal-Stockholm.html"
    # path = "/Restaurant_Review-g187323-d1358776-Reviews-Esplanade-Berlin.html"
    #
    # path = "/Restaurant_Review-g274887-d13197631-Reviews-Le_Poulet-Budapest_Central_Hungary.html"
    # path = '/Restaurant_Review-g187849-d1319744-Reviews-Le_Biciclette-Milan_Lombardy.html'
    # path = '/Restaurant_Review-g187849-d12447161-Reviews-Le_Biciclette_Art_Bar_Bistrot-Milan_Lombardy.html'
    # path = '/Restaurant_Review-g187514-d10058810-Reviews-Bar_Restaurante_El_Diezy7-Madrid.html'
    # path = '/Restaurant_Review-g187147-d5776778-Reviews-Fujiwara-Paris_Ile_de_France.html'

    # TripAdvisorScrubber.cleanup()

    # print('-'.join(path.split('-')[4:6]))
    # path = '/Restaurants-g187849-Milan_Lombardy.html'
    s = TripAdvisorScrubber(path)
    #
    info = s.build_info()
    # print(s.id)
    # print(info)
