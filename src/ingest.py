import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import json
import re


KNOWLEDGE_BASE = Path("../data/knowledge_base")
KNOWLEDGE_BASE.mkdir(parents=True, exist_ok=True)


SOURCES = [
    {
        "url": "https://www.nist.gov/itl/smallbusinesscyber/guidance-topic/phishing",
        "organization": "NIST",
        "topic": "phishing",
        "authority": 1.0,
    },

    {
        "url": "https://consumer.ftc.gov/articles/how-recognize-avoid-phishing-scams",
        "organization": "FTC",
        "topic": "phishing",
        "authority": 1.0,
    },

    {
        "url": "https://www.ftc.gov/business-guidance/small-businesses/cybersecurity",
        "organization": "FTC",
        "topic": "cybersecurity",
        "authority": 1.0,
    },

    {
        "url": "https://www.ftc.gov/business-guidance/blog/2018/12/cybersecurity-small-business-business-email-imposters",
        "organization": "FTC",
        "topic": "business_email_compromise",
        "authority": 1.0,
    },

    {
        "url": "https://www.ftc.gov/business-guidance/blog/2019/02/cybersecurity-small-business-email-authentication",
        "organization": "FTC",
        "topic": "email_authentication",
        "authority": 1.0,
    },

    {
        "url": "https://www.ftc.gov/business-guidance/resources/scams-your-small-business-guide-business",
        "organization": "FTC",
        "topic": "social_engineering",
        "authority": 1.0,
    },

    {
        "url": "https://www.nist.gov/publications/nist-phish-scale-user-guide",
        "organization": "NIST",
        "topic": "phishing_detection",
        "authority": 1.0,
    },
]


def download_page(url):
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Trace-RAG-Research/1.0"
            },
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:
        print(f"Failed to download {url}")
        print(error)

        return None


def extract_content(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove elements that are generally not useful knowledge.
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "form",
        ]
    ):
        tag.decompose()

    # Prefer the actual main content of the page.
    main_content = soup.find("main")

    if main_content is None:
        main_content = soup.find("article")

    if main_content is None:
        main_content = soup.body

    if main_content is None:
        return "Unknown", ""

    # Get title from the page.
    heading = main_content.find("h1")

    if heading:
        title = heading.get_text(" ", strip=True)
    elif soup.title:
        title = soup.title.get_text(" ", strip=True)
    else:
        title = "Unknown"

    # Remove additional non-content elements inside main.
    for tag in main_content.find_all(
        ["script", "style", "nav", "form", "aside"]
    ):
        tag.decompose()

    text = main_content.get_text(
        "\n",
        strip=True
    )

    # Clean excessive whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return title, text.strip()


def create_filename(source, title):
    organization = source["organization"].lower()

    clean_title = title.lower()

    clean_title = re.sub(
        r"[^a-z0-9]+",
        "_",
        clean_title
    )

    clean_title = clean_title.strip("_")

    return f"{organization}_{clean_title[:70]}.txt"


def save_document(source, title, text):
    filename = create_filename(source, title)

    document_path = KNOWLEDGE_BASE / filename

    document_path.write_text(
        text,
        encoding="utf-8"
    )

    metadata = {
        "title": title,
        "source_url": source["url"],
        "organization": source["organization"],
        "topic": source["topic"],
        "authority": source["authority"],
        "file": filename,
    }

    metadata_path = document_path.with_suffix(".json")

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )

    print(f"Saved: {document_path}")


def ingest_source(source):
    print(f"\nDownloading: {source['url']}")

    html = download_page(source["url"])

    if html is None:
        return False

    title, text = extract_content(html)

    if not text:
        print("No usable text found.")
        return False

    save_document(
        source,
        title,
        text
    )

    return True


def ingest_all():
    successful = 0

    for source in SOURCES:

        try:
            if ingest_source(source):
                successful += 1

        except Exception as error:
            print(
                f"Error processing {source['url']}: {error}"
            )

    print(
        f"\nFinished processing "
        f"{successful}/{len(SOURCES)} sources."
    )


if __name__ == "__main__":
    ingest_all()