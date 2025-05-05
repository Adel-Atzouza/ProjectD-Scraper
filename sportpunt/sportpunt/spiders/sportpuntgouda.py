import scrapy
import csv


class SportpuntGoudaSpider(scrapy.Spider):
    name = 'sportpuntgouda_rooster'
    start_urls = [
        'https://www.sportpuntgouda.nl/rooster?WarehouseID=&start=23-04-2025&end=22-05-2029'
    ]

    def parse(self, response):
        # Open the CSV file in write mode
        with open('Zwemrooster_Groenhovenbad.csv', mode='w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Date', 'Time', 'Activity', 'Facility']  # Column headers
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()  # Write the header row

            current_date = None

            # Loop through all rows with the class 'd-none d-md-table-row' (event rows)
            rows = response.xpath('//tr[@class="d-none d-md-table-row"]')
            for row in rows:
                # Get time (in the first <td>)
                if row == rows[1000]:
                    break
                time_text = row.xpath('.//td[@class="text-nowrap"]/text()[1]').get()
                if time_text:
                    time_text = time_text.strip()
                else:
                    continue

                # Get activity (in the second <td> containing an <a> tag)
                activity = row.xpath('.//td[contains(@class, "col-sm-5")]//a/text()').get()
                if activity:
                    activity = activity.strip()
                else:
                    continue

                # Get facility (in the third <td>)
                facility = row.xpath('.//td[contains(@class, "d-none d-sm-table-cell")][1]/text()').get()
                if facility:
                    facility = facility.strip()
                else:
                    continue

                # Check if a date row exists (where the date is mentioned)
                date_row = row.xpath('.//preceding::tr[1][@style="pointer-events: none"]')
                if date_row:
                    current_date = date_row.xpath('.//th/text()').get().strip()

                # Write each event's data into the CSV file with the date
                if current_date:
                    writer.writerow({
                        'Date': current_date,
                        'Time': time_text,
                        'Activity': activity,
                        'Facility': facility
                    })