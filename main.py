import json
from concurrent.futures import ThreadPoolExecutor

from fetcher import Fetcher
from detector import Detector

fetcher = Fetcher()
detector = Detector()


def load_domains(path="domenii.txt"):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(line)
    return out


def process_domain(domain):
    page = fetcher.fetch(domain)
    found = detector.detect(page)

    status = page.status_code or page.error
    print(f"[GATA] {domain} (Status: {status}) -> {found}")

    return {
        "domain": domain,
        "status_code": page.status_code,
        "error": page.error,
        "technologies": found,
    }


domains = load_domains()

with ThreadPoolExecutor(max_workers=25) as pool:
    results = list(pool.map(process_domain, domains))

fetcher.close()

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

found_all = []
for r in results:
    found_all.extend(r["technologies"])

total = len(found_all)
unique = len(set(found_all))

line = "=" * 55
print()
print(line)
print(f"Total unelte/tehnologii gasite in toate site-urile: {total}")
print(f"Numar de unelte/tehnologii unice identificate: {unique}")
print(line)
print()