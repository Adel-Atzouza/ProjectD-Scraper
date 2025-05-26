import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def get_dynamic_content(url: str) -> str:
    """Laad een pagina volledig (inclusief JavaScript) en geef de HTML terug."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)  # wacht op JavaScript-rendering
        html = page.content()
        browser.close()
        return html

def genereer_samenvatting(html: str, uitvoerpad: str = "samenvatting.txt") -> None:
    """Haal tekst uit HTML en laat deze samenvatten door een lokaal AI-model."""
    soup = BeautifulSoup(html, "html.parser")
    tekst = soup.get_text(separator="\n", strip=True)

    if not tekst.strip():
        print("⚠️ Geen bruikbare tekst gevonden op de pagina.")
        return

    prompt = (
    "Lees onderstaande tekst en geef een duidelijke en volledige samenvatting in bullet points. "
    "Richt je op de volgende onderdelen:\n"
    "- De namen van alle sportparken\n"
    "- Per sportpark: het adres en de aanwezige sportvoorzieningen (zoals voetbalvelden, handbalvelden, etc.)\n"
    "- Geef ook de contactgegevens van de organisatie (zoals naam contactpersoon, telefoonnummer en e-mailadres)\n"
    "Voeg geen onnodige informatie toe buiten deze onderdelen. Gebruik alleen de tekst die hieronder volgt:\n\n"
    )

    volledige_prompt = prompt + tekst

    # Sla het prompt tijdelijk op in een bestand
    with open("temp_input.txt", "w", encoding="utf-8") as f:
        f.write(volledige_prompt)

    # Roep Ollama aan en schrijf naar uitvoerbestand
    os.system(f"ollama run llama3.2:1b < temp_input.txt > {uitvoerpad}")
    os.remove("temp_input.txt")
    print(f"✅ Samenvatting opgeslagen in: {uitvoerpad}")

if __name__ == "__main__":
    url = "https://www.sportpuntgouda.nl/sportparken"
    print(f"🌐 Pagina laden: {url}")
    html = get_dynamic_content(url)
    print("📄 Pagina gedownload. Samenvatting wordt gegenereerd...")
    genereer_samenvatting(html)