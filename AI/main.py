import os
import requests
import subprocess
from bs4 import BeautifulSoup


def get_page(url: str) -> None:
    root = requests.get(url).content
    soup = BeautifulSoup(root, "html.parser")

    for x in soup.find_all("a", href=True):
        depth_1 = requests.get("https://goudawijzer.nl" + x["href"]).content
        depth_1 = BeautifulSoup(depth_1, "html.parser")

        print(depth_1.get_text())


def voorbeeld():
    print(
        "https://www.goudawijzer.nl/is/een-vraag-over/wonen-en-huishouden/woningen-en-woonvormen/seniorenwoningen"
    )
    root = requests.get(
        "https://www.goudawijzer.nl/is/een-vraag-over/wonen-en-huishouden/woningen-en-woonvormen/seniorenwoningen"
    ).content

    print("Page Downloaded")
    print("---------------", end="\n\n")

    root = BeautifulSoup(root, "html.parser")

    root = root.get_text()

    # prompt = "Vat deze tekst samen en voeg geen extra tekst toe in de output van dit prompt verzoek. geef alleen de samenvatting terug. \t"
    prompt = "Geef een uitgebreide samenvatting in bullet points van deze tekst. \t"
    args = [
        "ollama",
        "run",
        "llama3.2:1b",
        f'"{prompt + root}"',
        ">",
        "samenvatting.txt",
    ]
    os.system(" ".join(args))
    print("Samenvatting opgeslagen.")


if __name__ == "__main__":
    # content = get_page("https://www.goudawijzer.nl/is/een-vraag-over")
    voorbeeld()
