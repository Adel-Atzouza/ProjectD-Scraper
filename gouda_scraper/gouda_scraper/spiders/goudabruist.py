import scrapy
import time

class GoudaBruistSpider(scrapy.Spider):
    name = 'goudabruist'
    start_urls = ['https://goudabruist.nl/activiteiten']
    base_url = 'https://goudabruist.nl/activiteiten'
    from_param = 0
    increment = 40
    start_time = None

    def parse(self, response):
        if self.start_time is None:
            self.start_time = time.time()

        yield from self.parse_activities(response)

        # Als er nog activiteiten zijn, doorgaan met pagineren
        if response.css('div.card-body'):
            self.from_param += self.increment
            yield scrapy.Request(
                url=f'{self.base_url}?from={self.from_param}&increment={self.increment}',
                method='POST',
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
                    'Accept': 'text/plain, */*; q=0.01',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://goudabruist.nl/activiteiten',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': 'https://goudabruist.nl',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'Pragma': 'no-cache',
                    'Cache-Control': 'no-cache',
                },
                callback=self.parse
            )
        else:
            total_time = time.time() - self.start_time
            print(f"Scraping voltooid. Totale tijd: {total_time:.2f} seconden")

    def parse_activities(self, response):
        activities = response.css('div.card-body')

        for activity in activities:
            day_name = activity.css('div.go_day-name-wrapper::text').get()
            day = activity.css('div.go_date-day-wrapper::text').get()
            month = activity.css('div.go_date-month-wrapper::text').get()
            time_event = activity.css('div.go_date-time-wrapper::text').get()
            title = activity.css('div.go_card-title-wrapper::text').get()
            source = activity.css('div.go_source-name-wrapper::text').get()
            description = activity.css('div.go_content-start-wrapper::text').get()

            if title:
                title = title.strip()
            if source:
                source = source.strip()
            if description:
                description = description.strip()

            yield {
                'Day': day_name,
                'Date': f'{day} {month}' if day and month else None,
                'Time': time_event,
                'Title': title,
                'Source': source,
                'Description': description
            }
