import re
import csv

def clean_field(value):
    if not value:
        return ''
    value = re.sub(r'\s+', ' ', value)  # Collapse all whitespace (e.g. newlines/tabs) into one space
    value = value.replace('"', '').strip()  # Remove quotes and trim
    return value

class KwadraadEventsCsvPipeline:
    def open_spider(self, spider):
        self.file = open('kwadraad_events.csv', 'w', newline='', encoding='utf-8')
        self.exporter = csv.writer(self.file)
        self.exporter.writerow([
            'id', 'title', 'subtitle', 'date', 'time',
            'location', 'max_persons', 'contact_name',
            'contact_phone', 'contact_email'
        ])

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.writerow([
            clean_field(item.get('id')),
            clean_field(item.get('title')),
            clean_field(item.get('subtitle')),
            clean_field(item.get('date')),
            clean_field(item.get('time')),
            clean_field(item.get('location')),
            clean_field(item.get('max_persons')),
            clean_field(item.get('contact_name')),
            clean_field(item.get('contact_phone')),
            clean_field(item.get('contact_email')),
        ])
        return item
