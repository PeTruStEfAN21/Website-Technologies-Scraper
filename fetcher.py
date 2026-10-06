import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()


class PageData:
    def __init__(self, url):
        self.url = url
        self.status_code = 0
        self.status = 0
        self.error = None
        self.html = ""
        self.headers = {}
        self.cookies = []
        self.scripts = []
        self.meta_tag = {}
        self.href = []


class Fetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
        })

    def fetch(self, domain):
        d = domain.replace("https://", "").replace("http://", "").strip("/")
        page = PageData(url="https://" + d)

        resp = None
        last_err = None

        tries = [
            ("https://" + d, True),
            ("https://" + d, False),
            ("http://" + d, False),
        ]

        for u, verify in tries:
            try:
                resp = self.session.get(u, timeout=10, verify=verify)
                break
            except Exception as e:
                last_err = e
                continue

        if resp is None:
            msg = str(last_err).lower() if last_err else ""

            if "nameresolutionerror" in msg or "failed to resolve" in msg or "getaddrinfo" in msg:
                page.error = "DNS_NOT_FOUND"
            elif "timeout" in msg:
                page.error = "TIMEOUT"
            elif "ssl" in msg or "certificate" in msg:
                page.error = "SSL_ERROR"
            elif "connection refused" in msg:
                page.error = "CONNECTION_REFUSED"
            else:
                page.error = "CONNECTION_FAILED"

            print(f"[EROARE] {domain} -> {page.error}")
            return page

        page.url = resp.url
        page.status_code = resp.status_code
        page.status = resp.status_code
        page.headers = dict(resp.headers)
        page.cookies = [c.name for c in self.session.cookies]

        if resp.status_code in (403, 429):
            page.error = "BLOCKED_BY_WAF"
        elif resp.status_code >= 400:
            page.error = f"HTTP_{resp.status_code}"

        ctype = resp.headers.get("content-type", "").lower()
        if "text/html" not in ctype and "application/xhtml" not in ctype:
            return page

        if len(resp.content) > 5000000:
            return page

        page.html = resp.text

        try:
            soup = BeautifulSoup(resp.text, "html.parser")

            for s in soup.find_all("script"):
                src = s.get("src")
                if src:
                    page.scripts.append(src)

            for m in soup.find_all("meta"):
                k = m.get("name") or m.get("property")
                v = m.get("content")
                if k and v and k not in page.meta_tag:
                    page.meta_tag[k] = v

            for l in soup.find_all("link"):
                h = l.get("href")
                if h:
                    page.href.append(h)
        except Exception as e:
            print(f"[WARN] Eroare HTML {domain}: {e}")

        return page

    def close(self):
        self.session.close()