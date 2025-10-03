#!/usr/bin/env python3
# Termux UI standardizer for HTML files
# Uses home.html visual conventions

from bs4 import BeautifulSoup, NavigableString
import os
import re
from pathlib import Path
from copy import deepcopy

PROJECT = Path(".")
TOP_LEVEL = {
    "home.html": "home",
    "search_results.html": "search",
    "saved.html": "saved",
    "message_threads.html": "messages",
    "profile.html": "profile",
    "map.html": "map",
}

STD_HEAD_LINKS = [
    # Plus Jakarta Sans
    ('link', dict(rel="preconnect", href="https://fonts.googleapis.com")),
    ('link', dict(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=True)),
    ('link', dict(rel="preload", as_="style",
                  href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap",
                  onload="this.rel='stylesheet'")),
    # Material Symbols Outlined (baseline opsz=24)
    ('link', dict(href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0",
                  rel="stylesheet")),
    # Tailwind
    ('script', dict(src="https://cdn.tailwindcss.com?plugins=forms,container-queries")),
    ('script', dict(id="tailwind-config")),
]

STD_TAILWIND_CONFIG = """\
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#13a4ec",
        "background-light": "#f6f7f8",
        "background-dark": "#101c22",
      },
      fontFamily: {
        display: ["Plus Jakarta Sans", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "1rem",
        xl: "1.5rem",
        full: "9999px",
      },
    },
  },
};
"""

STD_ICON_STYLE = """\
/* Material Symbols baseline */
.material-symbols-outlined{
  font-family:"Material Symbols Outlined";
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  line-height:1;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}
"""

STD_BACK_HEADER_HTML = """\
<header class="sticky top-0 z-50 bg-white/90 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
  <div class="h-14 flex items-center gap-3 px-4">
    <a href="javascript:history.back()" class="inline-flex h-10 w-10 items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200" aria-label="Back">
      <span class="material-symbols-outlined text-[24px]" aria-hidden="true">arrow_back</span>
    </a>
    <h1 class="text-base font-bold tracking-wide truncate">Page title</h1>
  </div>
</header>
"""

STD_BOTTOM_NAV_HTML = """\
<nav class="fixed bottom-0 inset-x-0 z-50 border-t border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/90 backdrop-blur">
  <ul class="grid grid-cols-5 text-xs">
    <li>
      <a href="home.html" data-tab="home" class="flex flex-col items-center justify-center py-2 text-slate-600 dark:text-slate-300 hover:text-primary">
        <span class="material-symbols-outlined text-[22px]">home</span>
        <span class="text-[10px] leading-none mt-1">Home</span>
      </a>
    </li>
    <li>
      <a href="search_results.html" data-tab="search" class="flex flex-col items-center justify-center py-2 text-slate-600 dark:text-slate-300 hover:text-primary">
        <span class="material-symbols-outlined text-[22px]">search</span>
        <span class="text-[10px] leading-none mt-1">Search</span>
      </a>
    </li>
    <li>
      <a href="saved.html" data-tab="saved" class="flex flex-col items-center justify-center py-2 text-slate-600 dark:text-slate-300 hover:text-primary">
        <span class="material-symbols-outlined text-[22px]">bookmark</span>
        <span class="text-[10px] leading-none mt-1">Saved</span>
      </a>
    </li>
    <li>
      <a href="message_threads.html" data-tab="messages" class="flex flex-col items-center justify-center py-2 text-slate-600 dark:text-slate-300 hover:text-primary">
        <span class="material-symbols-outlined text-[22px]">chat</span>
        <span class="text-[10px] leading-none mt-1">Messages</span>
      </a>
    </li>
    <li>
      <a href="profile.html" data-tab="profile" class="flex flex-col items-center justify-center py-2 text-slate-600 dark:text-slate-300 hover:text-primary">
        <span class="material-symbols-outlined text-[22px]">person</span>
        <span class="text-[10px] leading-none mt-1">Profile</span>
      </a>
    </li>
  </ul>
</nav>
"""

BACK_ICON_NAMES = {
    "arrow_back", "arrow_back_ios", "arrow_back_ios_new", "arrowback", "arrowbackiosnew",
    "chevron_left", "chevronleft", "keyboard_backspace"
}

def clean_head_keep_title(soup: BeautifulSoup):
    head = soup.head
    if not head:
        head = soup.new_tag("head")
        soup.html.insert(0, head)
    # Preserve title text
    title_text = None
    if head.title and head.title.string:
        title_text = head.title.string.strip()

    # Wipe head children
    for el in list(head.contents):
        el.extract()

    # Write title back
    title = soup.new_tag("title")
    title.string = title_text or "App"
    head.append(title)

    # Insert standard links/scripts
    for tag_name, attrs in STD_HEAD_LINKS:
        if tag_name == "script" and attrs.get("id") == "tailwind-config":
            script = soup.new_tag("script", id="tailwind-config")
            script.string = STD_TAILWIND_CONFIG
            head.append(script)
        else:
            head.append(soup.new_tag(tag_name, **attrs))

    # Add icon baseline style
    style = soup.new_tag("style")
    style.string = STD_ICON_STYLE
    head.append(style)

def remove_existing_bottom_nav(soup: BeautifulSoup):
    for nav in soup.find_all("nav"):
        classes = " ".join(nav.get("class", []))
        if "bottom" in classes or "fixed" in classes or "sticky" in classes:
            # Heuristic: bottom navs often sit near end
            nav.extract()

def insert_bottom_nav(soup: BeautifulSoup, active: str):
    body = soup.body or soup
    container = BeautifulSoup(STD_BOTTOM_NAV_HTML, "lxml").body
    new_nav = container.find("nav")
    # Mark active
    for a in new_nav.select("[data-tab]"):
        if a.get("data-tab") == active:
            a["aria-current"] = "page"
            a["class"] = (a.get("class") or []) + ["text-primary"]
    body.append(new_nav)

def remove_back_headers(soup: BeautifulSoup):
    # Remove headers with a back icon
    for header in soup.find_all("header"):
        text = header.get_text(separator=" ").lower()
        if any(k.replace("_", "") in text for k in BACK_ICON_NAMES):
            header.extract()

def insert_back_header(soup: BeautifulSoup, title: str):
    body = soup.body or soup
    frag = BeautifulSoup(STD_BACK_HEADER_HTML, "lxml").body
    header = frag.find("header")
    header.h1.string = title or "Back"
    # Insert at top of body
    if body.contents:
        body.insert(0, header)
    else:
        body.append(header)

def normalize_icons(soup: BeautifulSoup):
    # material-icons -> material-symbols-outlined
    for el in soup.select(".material-icons"):
        classes = el.get("class", [])
        classes = [c for c in classes if c != "material-icons"]
        classes.append("material-symbols-outlined")
        el["class"] = classes

    # Normalize back arrow glyphs
    for el in soup.find_all("span", class_=lambda x: x and "material-symbols" in " ".join(x)):
        glyph = (el.string or "").strip().lower().replace(" ", "")
        if glyph in BACK_ICON_NAMES:
            el.string = "arrow_back"

    # Normalize messages icon where needed
    for el in soup.find_all("span", class_=lambda x: x and "material-symbols" in " ".join(x)):
        glyph = (el.string or "").strip().lower()
        if glyph in {"chatbubble", "mail"}:
            el.string = "chat"

def find_page_title(soup: BeautifulSoup, file_name: str) -> str:
    # Prefer h1 in first visible header/main
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    # Fallback to prettified file name
    return Path(file_name).stem.replace("_", " ").title()

def process_file(path: Path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    # Ensure html/body exist
    if not soup.html:
        root = soup.new_tag("html")
        if soup.body:
            root.append(soup.body)
        else:
            body = soup.new_tag("body")
            root.append(body)
        soup.append(root)

    # 1) Standard head
    clean_head_keep_title(soup)

    # 2) Icons normalization
    normalize_icons(soup)

    # 3) Header/back vs top-level
    is_top = path.name in TOP_LEVEL
    title = find_page_title(soup, path.name)
    if is_top:
        remove_back_headers(soup)
    else:
        remove_back_headers(soup)
        insert_back_header(soup, title)

    # 4) Bottom nav
    remove_existing_bottom_nav(soup)
    if is_top:
        active = TOP_LEVEL[path.name]
        insert_bottom_nav(soup, active)

    # Save backup and write
    backup = path.with_suffix(path.suffix + ".bak")
    path.replace(backup)
    path.write_text(str(soup), encoding="utf-8")

def main():
    htmls = [p for p in PROJECT.iterdir() if p.suffix.lower() == ".html"]
    for p in htmls:
        try:
            process_file(p)
            print(f"Updated: {p}")
        except Exception as e:
            print(f"[ERROR] {p}: {e}")

if __name__ == "__main__":
    main()
