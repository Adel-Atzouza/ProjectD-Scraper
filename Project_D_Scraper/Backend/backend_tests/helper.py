
# Mocked scraper module with utility functions

def extract_phone_number(text):
    return "123-456-7890" if "phone" in text.lower() else None

def clean_html_tags(html):
    import re
    return re.sub(r'<[^>]*>', '', html)

def validate_required_fields(data, required_fields):
    return all(field in data and data[field] for field in required_fields)

def normalize_link(link):
    return link.strip().lower()

def is_duplicate_footer(text, threshold=0.9):
    return "footer" in text.lower()

def is_visible_with_javascript(html_element):
    return "visible" in html_element

def measure_scrape_duration(start_time, end_time):
    return end_time - start_time