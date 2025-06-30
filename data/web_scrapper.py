import requests
from bs4 import BeautifulSoup
from langchain.schema import Document

def scrape_web_pages(urls: list):
    docs = []
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            cleaned = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
            docs.append(Document(page_content=cleaned, metadata={"source": url}))
        except Exception as e:
            print(f" Failed to scrape {url}: {e}")
    return docs
