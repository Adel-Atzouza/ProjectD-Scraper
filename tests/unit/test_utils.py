from Crawlscraper import clean_text, extract_title, is_excluded


def test_is_excluded():
    assert is_excluded("https://example.com/file.pdf") is True
    assert is_excluded("https://example.com/image.png") is False


def test_clean_text_removes_formatting():
    markdown = (
        "# Titel\n[Link](https://example.com)\nIntroductie tekst | kolom2 | kolom3"
    )
    result = clean_text(markdown)
    assert "Link" in result
    assert "|" not in result


def test_extract_title_with_h1():
    assert extract_title("# Hoofdtitel") == "Hoofdtitel"


def test_extract_title_with_h2():
    assert extract_title("## Subtitel") == "Subtitel"


def test_extract_title_fallback():
    assert extract_title("Geen koptekst hier.") == "Onbekend"
