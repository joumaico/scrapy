import os
import pandas as pd
import scrapy

from datetime import datetime
from pathlib import Path
from scrapy.selector import Selector


BASE_URL = 'https://rewardsforjustice.net'
PATH_OUT = f"{Path(__file__).resolve().parents[2]}/output"
FILE_URI = f"{PATH_OUT}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class IndexSpider(scrapy.Spider):

    name = 'index'
    custom_settings = {"FEEDS": {
        f"{FILE_URI}.json": {
            "format": "json",
        },
        f"{FILE_URI}.csv": {
            "format": "csv",
        }
    }, }

    def __init__(self):
        os.mkdir(PATH_OUT)

    def pagination(self, num: int) -> str:
        return f"{BASE_URL}/index/?jsf=jet-engine:rewards-grid&tax=crime-category:1070,1071,1073,1072,1074&pagenum={num}"

    def start_requests(self):
        url = self.pagination(1)
        formdata = {
            "action": "jet_engine_ajax",
            "handler": "get_listing",
            "page_settings[post_id]": "22076",
            "page_settings[queried_id]": "22076|WP_Post",
            "page_settings[element_id]": "ddd7ae9",
            "page_settings[page]": "1",
            "listing_type": "elementor",
            "isEditMode": "false",
            "addedPostCSS[]": "22078", }  # XHR
        yield scrapy.FormRequest(url, method="POST", formdata=formdata, callback=self.parse)

    def parse(self, response):
        data = response.json()
        html = data['data']['html']
        max_page = data['data']['filters_data']['props']['rewards-grid']['max_num_pages']

        for url in Selector(text=html).css("a::attr(href)").getall():
            yield scrapy.Request(url=url, callback=self.entry)

        for page in range(1, max_page + 1):
            url = self.pagination(page)
            formdata = {
                "action": "jet_engine_ajax",
                "handler": "get_listing",
                "page_settings[post_id]": "22076",
                "page_settings[queried_id]": "22076|WP_Post",
                "page_settings[element_id]": "ddd7ae9",
                "page_settings[page]": str(page),
                "listing_type": "elementor",
                "isEditMode": "false",
                "addedPostCSS[]": "22078", }
            yield scrapy.FormRequest(url, method="POST", formdata=formdata, callback=self.parse)

    def entry(self, response):
        sel = Selector(response)
        page_url = sel.css('link[rel="canonical"]::attr(href)').get()
        title = sel.css('div[data-id="f2eae65"] h2::text').get()
        if reward_amount := sel.css('div[data-id="5e60756"] h2::text').get():
            reward_amount = reward_amount.replace('Up to ', '')
        organization = sel.css('div[data-id="095ca34"] a::text').getall()
        if location := sel.css('div[data-id="0fa6be9"] span::text').getall():
            location = [i.strip() for i in location]
            location = ''.join(location).split(',')
        date_of_birth = []  # other entries have more than one date
        if dates := sel.css('div[data-id="9a896ea"] div::text').get():
            dates = dates.split(';')
            for date in dates:
                try:
                    date = datetime.strptime(date.strip(), '%B %d, %Y')
                    date_of_birth.append(date.strftime('%Y-%m-%d'))
                except ValueError:
                    date_of_birth.append(date.strip())
        if about := sel.css('div[data-id="52b1d20"] p::text').getall():
            about = '\n\n'.join(about)
        image = sel.css('div[data-id="a819a24"] a::attr(href)').getall()
        yield {
            "page_url": page_url,
            "title": title,
            "reward_amount": reward_amount,
            "organization": organization,
            "location": location,
            "date_of_birth": date_of_birth,
            "about": about,
            "images": image, }

    def closed(self, _):
        # convert csv to excel file
        df = pd.read_csv(f'{FILE_URI}.csv')
        df.to_excel(f'{FILE_URI}.xlsx', sheet_name="Index", index=False)
