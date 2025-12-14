import scrapy
from datetime import datetime
from urllib.parse import urlencode


class WorkplacespiderSpider(scrapy.Spider):
    name = "workplacespider"
    allowed_domains = ["www.workplacerelations.ie"]

    def start_requests(self):
        params = {
            "decisions": 1,
            "from": "15/11/2025",
            "to": "14/12/2025",
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

        # Stop if no results
        if not items:
            self.logger.info("No more results found. Pagination complete.")
            return

        # Extract records
        for item in items:
            yield {
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
                "partition_date": response.meta["partition_date"]
            }

        # Paginate if page is full (10 items)
        if len(items) == 10:
            next_page = response.meta["page"] + 1

            params = {
                "decisions": 1,
                "from": "1/12/2025",
                "to": "14/12/2025",
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
