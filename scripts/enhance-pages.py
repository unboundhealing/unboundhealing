def inject_related_content(soup, url):
    ...

def inject_tracking_script(soup):
    ...

def inject_future_magic(soup):
    ...

for file in HTML_FILES:

    soup = load_html(file)

    inject_related_content(soup, url)

    inject_tracking_script(soup)

    save_html(file, soup)
