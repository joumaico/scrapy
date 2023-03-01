import os
import pathlib
import shutil
import spider

from scrapy.crawler import CrawlerProcess


def test_index():
    process = CrawlerProcess()
    process.crawl(spider.IndexSpider)
    process.start()
    # sanity check if /output directory contains three files
    PATH_OUT = f"{pathlib.Path(__file__).resolve().parents[1]}/output"
    assert len(os.listdir(PATH_OUT)) == 3
    shutil.rmtree(PATH_OUT, ignore_errors=True)
