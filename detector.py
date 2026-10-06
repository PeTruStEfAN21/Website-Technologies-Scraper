import json


class Detector:
    def __init__(self, signatures_file="signatures.json"):
        with open(signatures_file, "r", encoding="utf-8") as f:
            self.signatures = json.load(f)

    def detect(self, page):
        detected = []
        if page.status_code == 0:
            return detected

        headers_lower = {k.lower(): v.lower() for k, v in page.headers.items()}
        meta_lower = {k.lower(): v.lower() for k, v in page.meta_tag.items()}
        cookies_lower = [c.lower() for c in page.cookies]
        scripts_lower = [s.lower() for s in page.scripts]
        href_lower = [h.lower() for h in page.href]
        html_lower = page.html.lower()

        for tech_name, rules in self.signatures.items():
            for rule_type, patterns in rules.items():
                if rule_type == "category":
                    continue

                if tech_name in detected:
                    break

                if rule_type == "headers":
                    for h_name, pattern in patterns.items():
                        if h_name in headers_lower and (pattern == "" or pattern in headers_lower[h_name]):
                            detected.append(tech_name)
                            break

                elif rule_type == "meta_tag":
                    for m_name, pattern in patterns.items():
                        if m_name in meta_lower and pattern in meta_lower[m_name]:
                            detected.append(tech_name)
                            break

                elif rule_type == "cookies":
                    for pattern in patterns:
                        if any(pattern in c for c in cookies_lower):
                            detected.append(tech_name)
                            break

                elif rule_type == "scripts":
                    for pattern in patterns:
                        if any(pattern in s for s in scripts_lower):
                            detected.append(tech_name)
                            break

                elif rule_type == "href":
                    for pattern in patterns:
                        if any(pattern in h for h in href_lower):
                            detected.append(tech_name)
                            break

                elif rule_type == "html":
                    for pattern in patterns:
                        if pattern in html_lower:
                            detected.append(tech_name)
                            break

        return detected