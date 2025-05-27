# prompt = "Geef een uitgebreide samenvatting in bullet points van deze tekst. \t"

def parse(content: str) -> str:

    prompt = (
        f"Je krijgt de taak om specifieke informatie te extraheren uit de volgende tekstinhoud: {content}. "
        "Volg deze instructies zorgvuldig: \n\n"
        "1. **Informatie Extraheren:** Extraheer alleen relevante informatie. "
        "2. **Geen Extra Inhoud:** Voeg geen extra tekst, opmerkingen of uitleg toe aan je antwoord. "
        "3. **Lege Reactie:** Als er geen informatie overeenkomt met de beschrijving, retourneer dan een lege string ('')."
        "4. **Alleen Gevraagde Gegevens:** Je output mag uitsluitend de expliciet gevraagde gegevens bevatten, zonder andere tekst."
    )


    args = [
        "ollama",
        "run",
        "llama3.2:1b",
        f'"{prompt}"',
        ">",
        "samenvatting.txt",
    ]
    os.system(" ".join(args))
    print("Samenvatting opgeslagen.")