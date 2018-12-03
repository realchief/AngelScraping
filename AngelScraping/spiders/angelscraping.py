from scrapy.conf import settings
from urllib import urlencode
from scrapy import Request
from lxml import html

import scrapy
from scrapy.item import Item, Field
import re
import json


class SiteProductItem(Item):
    Company_Name = Field()
    Names_of_Founders = Field()
    Email_Address = Field()
    Linkedin_URL = Field()
    Sales_Positions = Field()
    Location = Field()


class AngelScraper (scrapy.Spider):
    name = "scrapingdata"
    allowed_domains = ['angel.co']
    START_URL = 'https://angel.co/jobs'
    DOMAIN_URL = 'https://angel.co'
    settings.overrides['ROBOTSTXT_OBEY'] = False
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/70.0.3538.102 Safari/537.36"}

    def start_requests(self):
        yield Request(url=self.START_URL,
                      callback=self.parse_page,
                      dont_filter=True,
                      headers=self.headers
                      )

    def parse_page(self, response):

        col_links = response.xpath('//a[@class="u-unstyledLink"]/@href').extract()

        for c_link in col_links:
            if 'https' in c_link:
                sub_link = c_link
            else:
                sub_link = self.DOMAIN_URL + c_link
            yield Request(url=sub_link, callback=self.parse_company, dont_filter=True, headers=self.headers)

    def parse_company(self, response):

        company_links = response.xpath('//h3//a/@href').extract()

        for c_link in company_links:
            if 'https' in c_link:
                sub_link = c_link
            else:
                sub_link = self.DOMAIN_URL + c_link
            yield Request(url=sub_link, callback=self.parse_founder, dont_filter=True, headers=self.headers)

    def parse_founder(self, response):

        founder_links = response.xpath('//a[@class="profile-link"]/@href').extract()
        company_name = response.xpath('//h1//text()').extract()[0]
        meta = {'company_name': company_name}

        for f_link in founder_links:
            if 'https' in f_link:
                sub_link = f_link
            else:
                sub_link = self.DOMAIN_URL + f_link
            yield Request(url=sub_link, callback=self.parse_product_detail,
                          dont_filter=True, meta=meta, headers=self.headers)

    def parse_product_detail(self, response):
        product = SiteProductItem()

        company_name = self._parse_company_name(response)
        product['Company_Name'] = company_name

        founder_name = self._parse_founder_name(response)
        product['Names_of_Founders'] = founder_name

        email = self._parse_email(response)
        product['Email_Address'] = email

        linked_in = self._parse_linkedin(response)
        product['Linkedin_URL'] = linked_in

        yield product

    @staticmethod
    def _parse_company_name(response):
        company_name = response.meta['company_name']
        return company_name[0].strip() if company_name else None

    def _parse_founder_name(self, response):

        asset_images = response.xpath('//div[@class="frameImg"]//img/@data-lazy').extract()
        if asset_images:
            for image in asset_images:
                image = self.DOMAIN_URL + image
                images.append(image)
        return images

    @staticmethod
    def _parse_email(response):
        features = response.xpath('//div[contains(@id,"Features")]//a[contains(@class, "btn-gold")]//text()').extract()
        return features

    def _parse_linkedin(self, response):
        result = []
        t_header = response.xpath('//table[contains(@class, "table-striped")]/thead/tr/th/text()').extract()
        t_body = response.xpath('//table[contains(@class, "table-striped")]/div[contains(@class, "tablePar")]//tr').extract()
        if len(t_header) > 0:
            for body in t_body:
                spec = {}
                tree_body = html.fromstring(body)
                spec_body_vals = tree_body.xpath('//tr/td/text()')

                for i in range(0, len(t_header) - 1):
                    spec_header = self._clean_text(t_header[i])
                    if spec_body_vals:
                        spec_body = self._clean_text(spec_body_vals[i])
                        spec[spec_header] = spec_body
                result.append(spec)
        return result


    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)