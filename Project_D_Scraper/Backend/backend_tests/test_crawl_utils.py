import pytest
from urllib.parse import urlparse

import os, sys

# Get the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add parent directory to sys.path
sys.path.append(parent_dir)

from Crawlscraper import is_excluded, clean_text


# ---------- TESTS FOR is_excluded FUNCTION ----------


def test_is_excluded_true_for_known_extensions():
    """Test that known file extensions are properly excluded from crawling"""
    assert is_excluded("https://example.com/file.pdf")
    assert is_excluded("https://example.com/file.DOCX")      # Case insensitive
    assert is_excluded("https://example.com/archive.zip")
    assert is_excluded("https://example.com/presentation.pptx")
    assert is_excluded("https://example.com/data.XLSX")


def test_is_excluded_false_for_other_urls():
    """Test that web pages and other content types are not excluded"""
    assert not is_excluded("https://example.com/index.html")
    assert not is_excluded("https://example.com/image.jpg")
    assert not is_excluded("https://example.com/about")        # No extension
    assert not is_excluded("https://example.com/style.css")
    assert not is_excluded("https://example.com/script.js")


def test_is_excluded_ignores_query_params():
    """Test that query parameters don't affect exclusion logic"""
    assert not is_excluded("https://example.com/view?file=document.pdf")
    assert not is_excluded("https://example.com/open?download=.docx")


# ---------- TESTS FOR clean_text FUNCTION ----------


def test_clean_text_removes_table_lines():
    """Test that markdown table rows are removed from text"""
    md = "Header1 | Header2 | Header3\nRow1 | Row2 | Row3\nSome text."
    result = clean_text(md)
    assert "Header1" not in result
    assert "Row1" not in result
    assert "Some text." in result


def test_clean_text_removes_markdown_links():
    """Test that markdown link syntax is converted to plain text"""
    md = "This is a [link](https://example.com) in text."
    result = clean_text(md)
    assert "[link]" not in result
    assert "(https://example.com)" not in result
    assert "link" in result  # Link text should remain


def test_clean_text_removes_headers():
    """Test that markdown headers are removed from text"""
    md = "# Title\n## Subtitle\nContent here."
    result = clean_text(md)
    assert "#" not in result
    assert "Title" not in result
    assert "Subtitle" not in result


def test_clean_text_limits_to_five_sentences():
    """Test that text is properly limited to maximum 5 sentences"""
    md = "One. Two! Three? Four. Five. Six. Seven."
    result = clean_text(md)
    count = result.count(".") + result.count("!") + result.count("?")
    assert count <= 5
    assert result.startswith("One")


def test_clean_text_trims_and_reduces_newlines():
    """Test that excessive newlines are reduced and text is trimmed"""
    md = "\n\n\nFirst line.\n\n\nSecond line.\n\n\n"
    result = clean_text(md)
    assert result.startswith("First line.")
    assert "Second line." in result
    assert "\n\n\n" not in result  # No triple newlines should remain


def test_clean_text_multiple_tables_removed():
    """Test that multiple tables throughout the text are all removed"""
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


def test_clean_text_combined_case_full_cleanup():
    """Test comprehensive text cleaning with all features combined"""
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
    # Headers should be removed
    assert "Main Title" not in result
    assert "Footer" not in result
    # Tables should be removed
    assert "|" not in result
    # Links should be converted to plain text
    assert "link" in result and "https://" not in result
    # Should be limited to 5 sentences
    assert result.count(".") + result.count("!") + result.count("?") <= 5


def test_clean_text_sentence_splitting_accuracy():
    """Test that sentence splitting works correctly for sentence limiting"""
    md = "Sentence one. Sentence two! Sentence three? Sentence four. Sentence five. Sentence six."
    result = clean_text(md)
    sentences = result.split(". ")
    assert len(sentences) <= 5
    assert "Sentence one" in result


def test_clean_text_preserves_meaningful_content():
    """Test that meaningful content is preserved after cleaning"""
    md = """
# Welcome
This is a useful paragraph. It contains helpful information. Please read it carefully.
"""
    result = clean_text(md)
    assert "useful paragraph" in result
    assert "helpful information" in result
    assert result.count(".") <= 5


# ---------- TEST FOR URL TITLE GENERATION ----------


def generate_title_from_url(url: str) -> str:
    """
    Generate a title from a URL by using the last path segment or domain
    
    Args:
        url: The URL to generate a title from
        
    Returns:
        str: Generated title (last path segment or domain name)
    """
    return url.rstrip("/").split("/")[-1] or urlparse(url).netloc


def test_generate_title_from_url():
    """Test URL-to-title conversion for various URL formats"""
    assert generate_title_from_url("https://in-gouda.nl/contact/") == "contact"
    assert generate_title_from_url("https://in-gouda.nl/activiteiten/sport") == "sport"
    assert generate_title_from_url("https://in-gouda.nl/") == "in-gouda.nl"      # Root URL
    assert generate_title_from_url("https://in-gouda.nl") == "in-gouda.nl"       # No trailing slash
    assert generate_title_from_url("https://in-gouda.nl/nieuws/") == "nieuws"
