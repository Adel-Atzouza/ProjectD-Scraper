# Unit tests voor Crawlscraper utility functies

import pytest
from Crawlscraper import is_excluded, clean_text
from urllib.parse import urlparse

# ---------- TESTS VOOR is_excluded ----------


# Test: URLs met bekende uitgesloten extensies moeten True geven
def test_is_excluded_true_for_known_extensions():
    assert is_excluded("https://example.com/file.pdf")
    assert is_excluded("https://example.com/file.DOCX")
    assert is_excluded("https://example.com/archive.zip")
    assert is_excluded("https://example.com/presentation.pptx")
    assert is_excluded("https://example.com/data.XLSX")


# Test: URLs zonder uitgesloten extensies moeten False geven
def test_is_excluded_false_for_other_urls():
    assert not is_excluded("https://example.com/index.html")
    assert not is_excluded("https://example.com/image.jpg")
    assert not is_excluded("https://example.com/about")
    assert not is_excluded("https://example.com/style.css")
    assert not is_excluded("https://example.com/script.js")


# Test: Query parameters worden genegeerd bij het uitsluiten
def test_is_excluded_ignores_query_params():
    assert not is_excluded("https://example.com/view?file=document.pdf")
    assert not is_excluded("https://example.com/open?download=.docx")


# ---------- TESTS VOOR clean_text ----------


# Test: Tabellen (met pipes) worden verwijderd uit markdown
def test_clean_text_removes_table_lines():
    md = "Header1 | Header2 | Header3\nRow1 | Row2 | Row3\nSome text."
    result = clean_text(md)
    assert "Header1" not in result
    assert "Row1" not in result
    assert "Some text." in result


# Test: Markdown links worden verwijderd, alleen linktekst blijft over
def test_clean_text_removes_markdown_links():
    md = "This is a [link](https://example.com) in text."
    result = clean_text(md)
    assert "[link]" not in result
    assert "(https://example.com)" not in result
    assert "link" in result


# Test: Markdown headers (#, ##) worden verwijderd
def test_clean_text_removes_headers():
    md = "# Title\n## Subtitle\nContent here."
    result = clean_text(md)
    assert "#" not in result
    assert "Title" in result
    assert "Subtitle" in result


# Test: Maximaal 5 zinnen blijven over na cleanen
def test_clean_text_limits_to_five_sentences():
    md = "One. Two! Three? Four. Five. Six. Seven."
    result = clean_text(md)
    count = result.count(".") + result.count("!") + result.count("?")
    assert count <= 5
    assert result.startswith("One")


# Test: Overtollige newlines worden verwijderd en tekst wordt getrimd
def test_clean_text_trims_and_reduces_newlines():
    md = "\n\n\nFirst line.\n\n\nSecond line.\n\n\n"
    result = clean_text(md)
    assert result.startswith("First line.")
    assert "Second line." in result
    assert "\n\n\n" not in result


# Test: Meerdere tabellen in markdown worden volledig verwijderd
def test_clean_text_multiple_tables_removed():
    md = """
Col1 | Col2 | Col3
A | B | C

Some text here.

Another | Table | Again
X | Y | Z

Final text.
"""
    result = clean_text(md)
    assert "Col1" not in result
    assert "A" not in result
    assert "Table" not in result
    assert "Final text." in result


# Test: Volledige cleanup van markdown met headers, links en tabellen
def test_clean_text_combined_case_full_cleanup():
    md = """
# Main Title

Introductory paragraph. This is a [link](https://example.com). Another sentence!

Table:
Name | Age | City
John | 32 | Amsterdam

Closing thoughts here. The end.

## Footer
"""
    result = clean_text(md)
    assert "Main Title" not in result
    assert "Footer" not in result
    assert "link" in result and "https://" not in result
    assert "|" not in result
    assert result.count(".") + result.count("!") + result.count("?") <= 5


# Test: Zinnen worden correct gesplitst en beperkt tot 5
def test_clean_text_sentence_splitting_accuracy():
    md = "Sentence one. Sentence two! Sentence three? Sentence four. Sentence five. Sentence six."
    result = clean_text(md)
    sentences = result.split(". ")
    assert len(sentences) <= 5
    assert "Sentence one" in result


# Test: Belangrijke inhoud blijft behouden na cleanen
def test_clean_text_preserves_meaningful_content():
    md = """
# Welcome
This is a useful paragraph. It contains helpful information. Please read it carefully.
"""
    result = clean_text(md)
    assert "useful paragraph" in result
    assert "helpful information" in result
    assert result.count(".") <= 5


# Functie om een titel te genereren uit een URL (laatste stuk na de slash)
def generate_title_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1] or urlparse(url).netloc


# Test: Titelgeneratie uit verschillende soorten URLs
def test_generate_title_from_url():
    assert generate_title_from_url("https://in-gouda.nl/contact/") == "contact"
    assert generate_title_from_url(
        "https://in-gouda.nl/activiteiten/sport") == "sport"
    assert generate_title_from_url("https://in-gouda.nl/") == "in-gouda.nl"
    assert generate_title_from_url("https://in-gouda.nl") == "in-gouda.nl"
    assert generate_title_from_url("https://in-gouda.nl/nieuws/") == "nieuws"
