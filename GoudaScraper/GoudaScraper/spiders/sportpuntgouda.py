import scrapy
import csv


class SportpuntGoudaSpider(scrapy.Spider):
    name = "sportpuntgouda_rooster"
    start_urls = [
        "https://www.sportpuntgouda.nl/rooster?WarehouseID=&start=23-04-2025&end=22-05-2029"
    ]

    def parse(self, response):
        with open(
            "Zwemrooster_Groenhovenbad.csv", mode="w", newline="", encoding="utf-8"
        ) as csv_file:
            fieldnames = ["Date", "Time", "Activity", "Facility"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            current_date = None

            rows = response.xpath('//tr[@class="d-none d-md-table-row"]')
            for row in rows:
                if row == rows[1000]:
                    break
                time_text = row.xpath('.//td[@class="text-nowrap"]/text()[1]').get()
                if time_text:
                    time_text = time_text.strip()
                else:
                    continue

                activity = row.xpath(
                    './/td[contains(@class, "col-sm-5")]//a/text()'
                ).get()
                if activity:
                    activity = activity.strip()
                else:
                    continue

                facility = row.xpath(
                    './/td[contains(@class, "d-none d-sm-table-cell")][1]/text()'
                ).get()
                if facility:
                    facility = facility.strip()
                else:
                    continue

                date_row = row.xpath(
                    './/preceding::tr[1][@style="pointer-events: none"]'
                )
                if date_row:
                    current_date = date_row.xpath(".//th/text()").get().strip()

                if current_date:
                    writer.writerow(
                        {
                            "Date": current_date,
                            "Time": time_text,
                            "Activity": activity,
                            "Facility": facility,
                        }
                    )
