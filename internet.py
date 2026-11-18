import base64
import json
import ipaddress
import re
import socket
import time

from urllib.parse import (
    parse_qs,
    unquote,
    urljoin,
    urlparse,
    urlencode,
    urlunparse,
)

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

TIMEOUT = 60
RETRIES = 2

YOU_SEARCH_URL = "https://api.you.com/mcp?profile=free"

DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"
BING_URL = "https://www.bing.com/search"

MCP_PROTOCOL_VERSION = "2026-07-28"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "application/json, text/event-stream"
    ),
    "Content-Type": "application/json",
    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
    "Mcp-Method": "tools/call",
    "Mcp-Name": "you-search",
}

WEB_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
}


# ============================================================
# INTERNET CONNECTION
# ============================================================

def internet_available():
    try:
        response = requests.get(
            "https://www.google.com",
            headers=WEB_HEADERS,
            timeout=10,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


# ============================================================
# URL NORMALIZATION
# ============================================================

def decode_bing_url(url):
    if not isinstance(url, str):
        return None

    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    hostname = (parsed.hostname or "").lower()

    if not (
        hostname == "bing.com"
        or hostname.endswith(".bing.com")
    ):
        return url

    parameters = parse_qs(parsed.query)
    values = parameters.get("u", [])

    if not values:
        return None

    encoded = values[0].strip()

    if encoded.startswith("a1"):
        encoded = encoded[2:]

    if not encoded:
        return None

    try:
        padding = "=" * (-len(encoded) % 4)

        decoded = base64.urlsafe_b64decode(
            encoded + padding
        ).decode("utf-8", errors="strict")

        return unquote(decoded.strip())

    except (
        ValueError,
        UnicodeDecodeError,
    ):
        return None


def is_safe_public_http_url(url):
    if not isinstance(url, str) or not url.strip():
        return False

    try:
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").rstrip(".").lower()
        port = parsed.port
    except (TypeError, ValueError):
        return False

    if scheme not in {"http", "https"} or not hostname:
        return False

    if parsed.username is not None or parsed.password is not None:
        return False

    expected_port = 443 if scheme == "https" else 80
    if port is not None and port != expected_port:
        return False

    blocked_suffixes = (
        ".localhost", ".local", ".internal", ".test",
        ".invalid", ".example", ".home", ".lan", ".corp", ".arpa",
    )

    if hostname == "localhost" or hostname.endswith(blocked_suffixes):
        return False

    if "." not in hostname and not hostname.startswith("["):
        return False

    if "%" in hostname:
        return False

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            records = socket.getaddrinfo(
                hostname,
                port or expected_port,
                type=socket.SOCK_STREAM,
            )
        except (OSError, UnicodeError):
            return False

        addresses = {record[4][0].split("%", 1)[0] for record in records}
        if not addresses:
            return False

        for item in addresses:
            try:
                address = ipaddress.ip_address(item)
            except ValueError:
                return False

            if address.version == 6 and address.ipv4_mapped:
                address = address.ipv4_mapped

            if not address.is_global:
                return False

        return True

    if address.version == 6 and address.ipv4_mapped:
        address = address.ipv4_mapped

    return address.is_global


def normalize_result_url(url):
    if not isinstance(url, str) or not url.strip():
        return None

    url = urljoin(
        "https://html.duckduckgo.com",
        url.strip(),
    )

    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    hostname = (parsed.hostname or "").lower()

    if (
        hostname == "duckduckgo.com"
        or hostname.endswith(".duckduckgo.com")
    ):
        parameters = parse_qs(parsed.query)
        redirect_values = parameters.get("uddg", [])

        if not redirect_values:
            return None

        url = unquote(redirect_values[0])

    url = decode_bing_url(url)

    if not url:
        return None

    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()

    if scheme not in {"http", "https"} or not hostname:
        return None

    blocked_hosts = {
        "bing.com",
        "www.bing.com",
        "duckduckgo.com",
        "www.duckduckgo.com",
        "google.com",
        "www.google.com",
    }

    if hostname in blocked_hosts:
        return None

    if hostname == "localhost" or hostname.endswith(".localhost"):
        return None

    tracking_parameters = {
        "fbclid",
        "gclid",
        "msclkid",
        "msockid",
    }

    query_items = []

    for key, values in parse_qs(
        parsed.query,
        keep_blank_values=True,
    ).items():

        if key.lower() in tracking_parameters:
            continue

        if key.lower().startswith("utm_"):
            continue

        for value in values:
            query_items.append((key, value))

    clean_query = urlencode(query_items)

    clean_url = urlunparse((
        scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        clean_query,
        "",
    ))

    if not is_safe_public_http_url(clean_url):
        return None

    return clean_url


# ============================================================
# YOU.COM SEARCH
# ============================================================

def search_you(query, max_results=10):
    """
    Поиск через You.com MCP.

    Возвращает список результатов:
    title, url, snippet, source.
    """

    if not isinstance(query, str) or not query.strip():
        return []

    query = query.strip()

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "you-search",
            "arguments": {
                "query": query,
                "count": max_results,
            },
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": (
                    MCP_PROTOCOL_VERSION
                ),
                "io.modelcontextprotocol/clientInfo": {
                    "name": "armitage",
                    "version": "1.0",
                },
                "io.modelcontextprotocol/clientCapabilities": {},
            },
        },
    }

    headers = dict(HEADERS)

    for attempt in range(RETRIES + 1):
        try:
            response = requests.post(
                YOU_SEARCH_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT,
            )

            if response.status_code != 200:
                print(
                    f"You.com: HTTP {response.status_code}"
                )

                if attempt < RETRIES:
                    time.sleep(1)

                continue

            data = response.json()

            result = data.get("result", {})

            if not isinstance(result, dict):
                print("You.com: некорректный ответ сервера.")
                return []

            content = result.get("content", [])

            if not isinstance(content, list):
                return []

            results = []

            for block in content:
                if not isinstance(block, dict):
                    continue

                if block.get("type") != "text":
                    continue

                raw_text = block.get("text", "")

                if not raw_text:
                    continue

                try:
                    parsed_data = json.loads(raw_text)
                except (ValueError, TypeError):
                    continue

                web_results = (
                    parsed_data
                    .get("results", {})
                    .get("web", [])
                )

                if not isinstance(web_results, list):
                    continue

                for item in web_results:
                    if not isinstance(item, dict):
                        continue

                    title = str(
                        item.get("title", "")
                    ).strip()

                    original_url = str(
                        item.get("url", "")
                    ).strip()

                    description = str(
                        item.get("description", "")
                    ).strip()

                    if not description:
                        contents = item.get(
                            "contents",
                            {},
                        )

                        highlights = contents.get(
                            "highlights",
                            [],
                        ) if isinstance(contents, dict) else []

                        if isinstance(highlights, list):
                            description = " ".join(
                                str(value)
                                for value in highlights
                                if value
                            )

                    clean_url = normalize_result_url(
                        original_url
                    )

                    if not title or not clean_url:
                        continue

                    results.append({
                        "title": title,
                        "url": clean_url,
                        "snippet": description[:1500],
                        "source": "You.com",
                    })

                    if len(results) >= max_results:
                        break

                if results:
                    return results

            return []

        except requests.RequestException as error:
            print(
                f"You.com: ошибка запроса, "
                f"попытка {attempt + 1}: {error}"
            )

            if attempt < RETRIES:
                time.sleep(1)

        except (ValueError, KeyError, TypeError) as error:
            print(
                f"You.com: ошибка обработки ответа: {error}"
            )
            return []

    return []


# ============================================================
# DUCKDUCKGO PARSER
# ============================================================

def parse_duckduckgo(html, max_results):
    soup = BeautifulSoup(html, "html.parser")

    results = []
    seen = set()

    items = soup.select(".result")

    if not items:
        items = soup.select(".web-result")

    for item in items:
        link = item.select_one("a.result__a")

        if not link:
            link = item.select_one("h2 a")

        if not link:
            continue

        title = link.get_text(" ", strip=True)
        href = link.get("href")

        if not title or not href:
            continue

        clean_url = normalize_result_url(href)

        if not clean_url:
            continue

        key = clean_url.casefold()

        if key in seen:
            continue

        seen.add(key)

        snippet_element = item.select_one(
            ".result__snippet"
        )

        snippet = (
            snippet_element.get_text(" ", strip=True)
            if snippet_element
            else ""
        )

        results.append({
            "title": title,
            "url": clean_url,
            "snippet": snippet,
            "source": "DuckDuckGo",
        })

        if len(results) >= max_results:
            break

    return results


# ============================================================
# BING PARSER
# ============================================================

def parse_bing(html, max_results):
    soup = BeautifulSoup(html, "html.parser")

    results = []
    seen = set()

    for item in soup.select("li.b_algo"):
        link = item.select_one("h2 a")

        if not link:
            continue

        title = link.get_text(" ", strip=True)
        href = link.get("href")

        if not title or not href:
            continue

        clean_url = normalize_result_url(href)

        if not clean_url:
            continue

        key = clean_url.casefold()

        if key in seen:
            continue

        seen.add(key)

        snippet_element = item.select_one(
            ".b_caption p"
        )

        if not snippet_element:
            snippet_element = item.select_one("p")

        snippet = (
            snippet_element.get_text(" ", strip=True)
            if snippet_element
            else ""
        )

        results.append({
            "title": title,
            "url": clean_url,
            "snippet": snippet,
            "source": "Bing",
        })

        if len(results) >= max_results:
            break

    return results


# ============================================================
# SEARCH ENGINE REQUEST
# ============================================================

def request_search_engine(
    engine_name,
    url,
    query,
    parser,
    max_results,
):
    for attempt in range(RETRIES + 1):
        try:
            response = requests.get(
                url,
                params={"q": query},
                headers=WEB_HEADERS,
                timeout=15,
            )

            if response.status_code != 200:
                print(
                    f"{engine_name}: HTTP "
                    f"{response.status_code}"
                )

                if attempt < RETRIES:
                    time.sleep(1)

                continue

            results = parser(
                response.text,
                max_results,
            )

            if results:
                return results

            print(
                f"{engine_name}: подходящие ссылки не получены."
            )

            return []

        except requests.RequestException as error:
            print(
                f"Ошибка {engine_name}, "
                f"попытка {attempt + 1}: {error}"
            )

            if attempt < RETRIES:
                time.sleep(1)

    return []


# ============================================================
# INTERNET SEARCH
# ============================================================

def search_internet(query, max_results=10):
    """
    Основная функция интернет-поиска для Armitage.

    Приоритет:
    1. You.com MCP.
    2. DuckDuckGo.
    3. Bing.

    Формат совместим с core.py и Executor:
    title, url, snippet, source.
    """

    if not isinstance(query, str) or not query.strip():
        return []

    query = query.strip()

    try:
        max_results = int(max_results)
    except (TypeError, ValueError):
        max_results = 10

    max_results = max(1, min(max_results, 50))

    print(f"Интернет-поиск: {query}")

    if not internet_available():
        print("Интернет недоступен.")
        return []

    # --------------------------------------------------------
    # 1. YOU.COM
    # --------------------------------------------------------

    print("Поисковая система: You.com")

    results = search_you(
        query,
        max_results,
    )

    # --------------------------------------------------------
    # 2. DUCKDUCKGO
    # --------------------------------------------------------

    if not results:
        print(
            "You.com не вернул результаты. "
            "Пробую DuckDuckGo."
        )

        results = request_search_engine(
            "DuckDuckGo",
            DUCKDUCKGO_URL,
            query,
            parse_duckduckgo,
            max_results,
        )

    # --------------------------------------------------------
    # 3. BING
    # --------------------------------------------------------

    if not results:
        print(
            "DuckDuckGo не вернул результаты. "
            "Пробую Bing."
        )

        results = request_search_engine(
            "Bing",
            BING_URL,
            query,
            parse_bing,
            max_results,
        )

    # --------------------------------------------------------
    # 4. DEDUPLICATION
    # --------------------------------------------------------

    unique_results = []
    seen = set()

    for item in results:
        clean_url = normalize_result_url(
            item.get("url", "")
        )

        title = str(
            item.get("title", "")
        ).strip()

        if not clean_url or not title:
            continue

        key = clean_url.casefold()

        if key in seen:
            continue

        seen.add(key)

        unique_results.append({
            "title": title,
            "url": clean_url,
            "snippet": str(
                item.get("snippet", "")
            ).strip(),
            "source": item.get("source", ""),
        })

        if len(unique_results) >= max_results:
            break

    # --------------------------------------------------------
    # 5. OUTPUT
    # --------------------------------------------------------

    print(
        f"Найдено результатов: {len(unique_results)}"
    )

    for index, item in enumerate(
        unique_results,
        start=1,
    ):
        print(f"{index}. {item['title']}")
        print(f"   {item['url']}")

        if item["snippet"]:
            print(
                f"   {item['snippet'][:250]}"
            )

    return unique_results


# ============================================================
# COMPATIBILITY
# ============================================================

def search_web(query, max_results=10):
    return search_internet(
        query,
        max_results,
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("================================")
    print("       INTERNET TEST")
    print("================================")
    print()

    print(
        "Интернет:",
        "доступен"
        if internet_available()
        else "недоступен",
    )

    print()
    print("Тестовый поиск: Blender Python API")

    results = search_internet(
        "site:docs.blender.org/api/current Blender Python API bpy",
        max_results=5,
    )

    print()

    if results:
        print("Результаты получены.")
    else:
        print("Результатов нет.")

    print()
    print("================================")
    print("       TEST FINISHED")
    print("================================")