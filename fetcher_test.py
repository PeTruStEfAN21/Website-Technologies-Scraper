from fetcher import PageData, Fetcher
from detector import Detector

fetcher = Fetcher()
detector = Detector()

domenii_test = [
    "wordpress.org",
    "5starremoval.weebly.com",
    "avocatalinamanciu.ro",
    "github.com",
    "disneystore.com",
    "google.com",
    "wikipedia.org"
]

for site in domenii_test:
    page = fetcher.fetch(site)
    tehnologii = detector.detect(page)
    print(f"{site} (Status: {page.status_code}) -> Tehnologii: {tehnologii}")

fetcher.close()