import pytest
from Crawlscraper import is_excluded, clean_text

def test_is_excluded_true():
    assert is_excluded("https://example.com/file.pdf")
    assert is_excluded("https://example.com/file.DOCX")
    assert is_excluded("https://example.com/archive.zip")
    assert is_excluded("https://example.com/presentation.pptx")

def test_is_excluded_false():
    assert not is_excluded("https://example.com/index.html")
    assert not is_excluded("https://example.com/image.jpg")
    assert not is_excluded("https://example.com/about")

def test_clean_text_removes_table_lines():
    md = "Header1 | Header2 | Header3\nRow1 | Row2 | Row3\nSome text."
    result = clean_text(md)
    assert "Header1" not in result
    assert "Row1" not in result
    assert "Some text." in result

def test_clean_text_removes_markdown_links():
    md = "This is a [link](https://example.com) in text."
    result = clean_text(md)
    assert "[link]" not in result
    assert "(https://example.com)" not in result
    assert "link" in result

def test_clean_text_removes_headers():
    md = "# Title\n## Subtitle\nContent here."
    result = clean_text(md)
    assert "#" not in result
    assert "Title" in result
    assert "Subtitle" in result

def test_clean_text_limits_to_five_sentences():
    md = "One. Two! Three? Four. Five. Six. Seven."
    result = clean_text(md)
    assert result.count('.') + result.count('!') + result.count('?') <= 5
    assert result.startswith("One.")

def test_clean_text_trims_and_reduces_newlines():
    md = "\n\n\nFirst line.\n\n\nSecond line.\n\n\n"
    result = clean_text(md)
    assert result.startswith("First line.")
    assert "Second line." in result