def parse_date(date_str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")

def calculate_file_hash(file_path):
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

from bs4 import BeautifulSoup

def process_html_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    for t in soup.find_all(["script", "style", "noscript", "iframe"]):
        t.decompose()

    body = soup.body or soup

    selectors = [
        "div.content",
        "main",
        "#main",
        "article",
        "div[itemprop='articleBody']",
        "div.container.mb-4",
    ]

    main_el = None
    for sel in selectors:
        cand = body.select_one(sel)
        if cand and cand.get_text(strip=True):
            main_el = cand
            break

    if main_el and main_el.name == "div" and "content" in (main_el.get("class") or []):
        parent = main_el.parent
        if parent and parent.find("h1", class_="page-title"):
            main_el = parent

    if not main_el:
        candidates = body.find_all(["div", "section", "article", "main"])
        main_el = max(
            candidates,
            key=lambda t: len(t.get_text(" ", strip=True)),
            default=body
        )

    out = BeautifulSoup("<body></body>", "html.parser")
    out.body.append(main_el)

    chrome_selectors = [
        "header", "footer", "nav", "aside",
        "#globalCookieBar", ".cookie",
        "#binderFixed", ".social-banner",
        ".return-to-search",
        "button", "svg",
        "form", "input", "select", "textarea",
    ]
    for sel in chrome_selectors:
        for t in out.select(sel):
            t.decompose()

    for t in out.find_all(["div", "section"], recursive=True):
        if not t.get_text(strip=True) and not t.find(["img", "table"]):
            t.decompose()

    return str(out.body)



def parse_link(self, response):
        record = response.meta["record"]
        os.makedirs("downloads", exist_ok=True)

        content_type = response.headers.get('Content-Type', b'').decode('utf-8')

        if "pdf" in content_type:
            ext = ".pdf"
        elif "msword" in content_type or "word" in content_type:
            ext = ".doc"
        else:
            ext = ".html"

        filename = f"{record['identifier']}{ext}"
        file_path = os.path.join("downloads", filename)

        with open(file_path, "wb") as f:
            f.write(response.body)

        file_hash = hashlib.sha256(response.body).hexdigest()

        record["file_path"] = file_path
        record["file_hash"] = file_hash

        yield record