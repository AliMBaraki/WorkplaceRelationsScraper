import hashlib
import os
import scrapy
from datetime import datetime
from urllib.parse import urlencode

DOWNLOAD_DIR = "downloads"

class WorkplacespiderSpider(scrapy.Spider):
    name = "workplacespider"
    allowed_domains = ["www.workplacerelations.ie"]

    def start_requests(self):
        self.from_date = "15/9/2025"
        self.to_date = "14/12/2025"
        params = {
            "decisions": 1,
            "from": self.from_date,
            "to": self.to_date,
            "pageNumber": 1
        }

        url = f"https://www.workplacerelations.ie/en/search/?{urlencode(params)}"

        yield scrapy.Request(
            url=url,
            callback=self.parse,
            meta={
                "page": 1,
                "partition_date": datetime.utcnow().date().isoformat()
            }
        )

    def parse(self, response):
        items = response.css('li.each-item')

        if not items:
            self.logger.info("No more results found. Pagination complete.")
            return

        for item in items:
            record =  {
                "title": item.css('h2.title a::text').get(),
                "identifier": item.css('span.refNO::text').get(),
                "decision_date": datetime.strptime(
                    item.css('span.date::text').get(), '%d/%m/%Y'
                ).date().isoformat(),
                "description": ' '.join(
                    t.strip()
                    for t in item.css('p.description::text').getall()
                    if t.strip()
                ),
                "link": response.urljoin(
                    item.css('a.btn.btn-primary::attr(href)').get()
                ),
                "partition_date": response.meta["partition_date"],
                "start_date": self.from_date,
                "end_date": self.to_date
            }
            yield scrapy.Request(
            url=record["link"],
            callback=self.parse_link,
            meta={"record": record},
            dont_filter=True
            )

        if len(items) == 10:
            next_page = response.meta["page"] + 1

            params = {
                "decisions": 1,
                "from": self.from_date,
                "to": self.to_date,
                "pageNumber": next_page
            }

            next_url = f"https://www.workplacerelations.ie/en/search/?{urlencode(params)}"

            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={
                    "page": next_page,
                    "partition_date": response.meta["partition_date"]
                }
            )
    def parse_link(self, response):
        record = response.meta["record"]
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        content_type = response.headers.get('Content-Type', b'').decode('utf-8')

        if "pdf" in content_type:
            ext = ".pdf"
        elif "msword" in content_type or "word" in content_type:
            ext = ".doc"
        else:
            ext = ".html"

        filename = f"{record['identifier']}{ext}"
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(response.body)

        file_hash = hashlib.sha256(response.body).hexdigest()

        record["file_path"] = file_path
        record["file_hash"] = file_hash

        yield record