from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag
import requests


HEBREW_WIKIPEDIA_API = "https://he.wikipedia.org/w/api.php"
MAIN_PAGE_URL = "https://he.wikipedia.org/wiki/%D7%A2%D7%9E%D7%95%D7%93_%D7%A8%D7%90%D7%A9%D7%99"


@dataclass(frozen=True)
class DidYouKnowItem:
    text: str
    image_url: str | None
    source_url: str = MAIN_PAGE_URL
    html_text: str | None = None


class WikipediaFetchError(RuntimeError):
    pass


def fetch_daily_did_you_know(user_agent: str) -> DidYouKnowItem:
    response = requests.get(
        HEBREW_WIKIPEDIA_API,
        params={
            "action": "parse",
            "page": "עמוד ראשי",
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        },
        headers={"User-Agent": user_agent},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    try:
        html = data["parse"]["text"]
    except KeyError as exc:
        raise WikipediaFetchError("Unexpected response from Hebrew Wikipedia") from exc

    return parse_did_you_know_html(html)


def parse_did_you_know_html(html: str) -> DidYouKnowItem:
    soup = BeautifulSoup(html, "html.parser")
    section = _find_did_you_know_section(soup)
    if section is None:
        raise WikipediaFetchError('Could not find the Hebrew Wikipedia "הידעת" section')

    image_url = _find_content_image(section)
    source_url = _find_source_url(section)
    text, html_text = _extract_section_content(section)
    if not text:
        raise WikipediaFetchError('The Hebrew Wikipedia "הידעת" section did not contain text')

    return DidYouKnowItem(text=text, image_url=image_url, source_url=source_url, html_text=html_text)


def _find_did_you_know_section(soup: BeautifulSoup):
    for headline in soup.find_all(["h2", "h3"]):
        if "הידעת" not in headline.get_text(" ", strip=True):
            continue

        container = headline.find_parent(["section", "div", "td"])
        if container is not None:
            return container

        nodes = []
        for sibling in headline.next_siblings:
            if getattr(sibling, "name", None) in {"h2", "h3"}:
                break
            nodes.append(sibling)
        return BeautifulSoup("".join(str(node) for node in nodes), "html.parser")

    return None


def _find_content_image(section) -> str | None:
    for image in section.find_all("img"):
        alt = image.get("alt", "")
        src = image.get("src", "")
        if "הידעת" in alt:
            continue
        if not src:
            continue
        return urljoin("https:", src)
    return None


def _find_source_url(section) -> str:
    headline = section.find(["h2", "h3"])
    if headline is not None:
        link = headline.find("a", href=True)
        if link is not None:
            return urljoin("https://he.wikipedia.org", link["href"])

    return MAIN_PAGE_URL


def _extract_section_content(section) -> tuple[str, str]:
    section = BeautifulSoup(str(section), "html.parser")

    for unwanted in section.select("style, script, h2, h3, figure, .mw-editsection, .noprint"):
        unwanted.decompose()

    for div in section.find_all("div"):
        style = div.get("style", "")
        if "float:" in style or "clear:" in style:
            div.decompose()

    for link in section.find_all("a"):
        next_sibling = link.next_sibling
        while next_sibling is not None and not str(next_sibling).strip():
            next_sibling = next_sibling.next_sibling
        if getattr(next_sibling, "name", None) == "a":
            link.insert_after(" ")

    text = section.get_text("", strip=False)
    text = _normalize_text(text)

    html_text = _render_telegram_html(section)
    html_text = _normalize_text(html_text)
    html_text = re.sub(r"\s+</a>", "</a>", html_text)
    html_text = re.sub(r"<a ([^>]+)>\s+", r"<a \1>", html_text)

    return text, html_text


def _render_telegram_html(node) -> str:
    parts = []
    for child in node.children:
        if isinstance(child, NavigableString):
            parts.append(escape(str(child), quote=False))
            continue

        if not isinstance(child, Tag):
            continue

        if child.name == "a" and child.get("href"):
            href = urljoin("https://he.wikipedia.org", child["href"])
            label = _normalize_text(child.get_text("", strip=False))
            if label:
                parts.append(f'<a href="{escape(href, quote=True)}">{escape(label, quote=False)}</a>')
            continue

        parts.append(_render_telegram_html(child))

    return "".join(parts)


def _normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", text)
