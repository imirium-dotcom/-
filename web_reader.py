import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from internet import is_safe_public_http_url


DEFAULT_MAX_CHARS = 20000
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_TIMEOUT = 15
DEFAULT_MAX_REDIRECTS = 5

WEB_READER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,text/plain",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "identity",
    "Connection": "close",
}


class WebReaderError(Exception):
    pass


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, port, address, timeout):
        super().__init__(host, port, timeout=timeout)
        self.connect_address = address

    def connect(self):
        self.sock = socket.create_connection(
            (self.connect_address, self.port),
            self.timeout,
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, address, timeout, context):
        super().__init__(
            host,
            port,
            timeout=timeout,
            context=context,
        )
        self.connect_address = address

    def connect(self):
        raw_socket = socket.create_connection(
            (self.connect_address, self.port),
            self.timeout,
        )

        try:
            self.sock = self._context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )
        except Exception:
            raw_socket.close()
            raise


def _resolve_public_address(host, port):
    if not host or "%" in host:
        raise WebReaderError("Недопустимое имя хоста.")

    try:
        direct_ip = ipaddress.ip_address(host)
        raw_addresses = [str(direct_ip)]
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            )
        except (OSError, UnicodeError) as error:
            raise WebReaderError(
                f"Не удалось определить IP-адрес: {error}"
            ) from error

        raw_addresses = list({
            record[4][0].split("%", 1)[0]
            for record in records
        })

    if not raw_addresses:
        raise WebReaderError("DNS не вернул IP-адреса.")

    public_addresses = []

    for raw_address in raw_addresses:
        try:
            address = ipaddress.ip_address(raw_address)
        except ValueError as error:
            raise WebReaderError(
                "DNS вернул некорректный IP-адрес."
            ) from error

        if address.version == 6 and address.ipv4_mapped:
            address = address.ipv4_mapped

        if not address.is_global:
            raise WebReaderError(
                f"Заблокирован непубличный IP-адрес: {address}"
            )

        public_addresses.append(str(address))

    return public_addresses[0]


def _build_connection(parsed, address):
    scheme = parsed.scheme.lower()
    host = parsed.hostname
    port = parsed.port or (443 if scheme == "https" else 80)

    if scheme == "https":
        return _PinnedHTTPSConnection(
            host,
            port,
            address,
            DEFAULT_TIMEOUT,
            ssl.create_default_context(),
        )

    return _PinnedHTTPConnection(
        host,
        port,
        address,
        DEFAULT_TIMEOUT,
    )


def _read_response_body(response, max_bytes):
    content_length = response.getheader("Content-Length")

    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise WebReaderError(
                    "Страница превышает допустимый размер загрузки."
                )
        except ValueError:
            raise WebReaderError(
                "Некорректный Content-Length."
            )

    chunks = []
    total = 0
    truncated = False

    while total <= max_bytes:
        remaining = max_bytes + 1 - total
        chunk = response.read(min(65536, remaining))

        if not chunk:
            break

        chunks.append(chunk)
        total += len(chunk)

        if total > max_bytes:
            truncated = True
            break

    body = b"".join(chunks)

    if truncated:
        body = body[:max_bytes]

    return body, truncated


def _clean_html(content):
    soup = BeautifulSoup(content, "html.parser")

    title = ""

    if soup.title:
        title = soup.title.get_text(" ", strip=True)

    for tag in soup([
        "script",
        "style",
        "noscript",
        "iframe",
        "svg",
        "canvas",
        "form",
        "nav",
        "footer",
        "aside",
        "button",
        "input",
    ]):
        tag.decompose()

    main = (
        soup.find("main")
        or soup.find("article")
        or soup.body
        or soup
    )

    text = main.get_text("\n", strip=True)

    lines = []

    for line in text.splitlines():
        cleaned = " ".join(line.split())

        if cleaned:
            lines.append(cleaned)

    return title, "\n".join(lines)


def _decode_content(body, response):
    charset = response.headers.get_content_charset() or "utf-8"

    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def read_webpage(
    url,
    max_chars=DEFAULT_MAX_CHARS,
    max_bytes=DEFAULT_MAX_BYTES,
    max_redirects=DEFAULT_MAX_REDIRECTS,
):
    """
    Безопасно загружает публичную HTML/XHTML/TXT-страницу.

    Не выполняет JavaScript, команды или код страницы.
    Не загружает изображения, архивы и другие бинарные файлы.
    Проверяет DNS и подключается непосредственно к проверенному IP.
    Проверяет каждый адрес перенаправления.
    """

    current_url = str(url).strip() if url is not None else ""

    try:
        max_chars = max(100, min(int(max_chars), 50000))
        max_bytes = max(10000, min(int(max_bytes), 2_000_000))
        max_redirects = max(0, min(int(max_redirects), 5))

        if not current_url:
            raise WebReaderError("URL не указан.")

        redirects = 0

        while True:
            if not is_safe_public_http_url(current_url):
                raise WebReaderError(
                    "Адрес заблокирован проверкой безопасности."
                )

            try:
                parsed = urlparse(current_url)
                hostname = parsed.hostname
                scheme = parsed.scheme.lower()
                port = parsed.port or (
                    443 if scheme == "https" else 80
                )
            except ValueError as error:
                raise WebReaderError(
                    "Некорректный URL."
                ) from error

            address = _resolve_public_address(hostname, port)

            connection = _build_connection(parsed, address)

            try:
                request_target = parsed.path or "/"

                if parsed.params:
                    request_target += ";" + parsed.params

                if parsed.query:
                    request_target += "?" + parsed.query

                connection.putrequest(
                    "GET",
                    request_target,
                    skip_host=True,
                )

                connection.putheader("Host", parsed.netloc)

                for key, value in WEB_READER_HEADERS.items():
                    connection.putheader(key, value)

                connection.endheaders()

                response = connection.getresponse()

                if response.status in {301, 302, 303, 307, 308}:
                    location = response.getheader("Location")

                    if not location:
                        raise WebReaderError(
                            "Перенаправление не содержит Location."
                        )

                    if redirects >= max_redirects:
                        raise WebReaderError(
                            "Превышено количество перенаправлений."
                        )

                    current_url = urljoin(
                        current_url,
                        location,
                    )

                    redirects += 1
                    continue

                if response.status != 200:
                    raise WebReaderError(
                        f"Сервер вернул HTTP {response.status}."
                    )

                content_type = (
                    response.headers.get_content_type().lower()
                )

                allowed_types = {
                    "text/html",
                    "application/xhtml+xml",
                    "text/plain",
                }

                if content_type not in allowed_types:
                    raise WebReaderError(
                        f"Тип содержимого не поддерживается: "
                        f"{content_type}"
                    )

                body, byte_truncated = _read_response_body(
                    response,
                    max_bytes,
                )

                decoded = _decode_content(body, response)

                if content_type == "text/plain":
                    title = ""
                    page_text = "\n".join(
                        line.strip()
                        for line in decoded.splitlines()
                        if line.strip()
                    )
                else:
                    title, page_text = _clean_html(decoded)

                if not page_text.strip():
                    raise WebReaderError(
                        "На странице не найден текст."
                    )

                char_truncated = len(page_text) > max_chars
                page_text = page_text[:max_chars]

                return {
                    "status": "success",
                    "url": current_url,
                    "title": title,
                    "text": page_text,
                    "content_type": content_type,
                    "chars": len(page_text),
                    "truncated": (
                        byte_truncated or char_truncated
                    ),
                    "redirects": redirects,
                    "verified": True,
                    "message": "Страница успешно прочитана.",
                }

            finally:
                connection.close()

    except WebReaderError as error:
        return {
            "status": "failed",
            "url": current_url,
            "title": "",
            "text": "",
            "verified": False,
            "message": str(error),
        }

    except (
        OSError,
        http.client.HTTPException,
        ssl.SSLError,
        UnicodeError,
        ValueError,
    ) as error:
        return {
            "status": "failed",
            "url": current_url,
            "title": "",
            "text": "",
            "verified": False,
            "message": f"Ошибка загрузки страницы: {error}",
        }