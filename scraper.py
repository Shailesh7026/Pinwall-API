# pyrefly: ignore [missing-import]
from pinterest_dl import PinterestDL


def iter_search_items(query: str):
    """
    Search on pinterest. -- basic generator function for search
    """
    scraper = PinterestDL.with_api(timeout=5, verbose=False)
    for media in scraper.iter_search(query):
        yield _to_item(media)

def iter_scrape_items(url: str):
    """Same idea as iter_search_items, for a board or pin URL."""
    scraper = PinterestDL.with_api(timeout=5, verbose=False)
    for media in scraper.iter_scrape(url):
        yield _to_item(media)

def iter_related_items(pin_id: str):
    """
    pinterest-dl's iter_scrape on a pin URL yields the pin itself first,
    then related pins. We discard that first item so this generator only
    ever yields "related" content.
    """
    url = f"https://www.pinterest.com/pin/{pin_id}/"
    scraper = PinterestDL.with_api(timeout=5, verbose=False)
    it = scraper.iter_scrape(url)
    next(it, None)  # discard the pin itself
    for media in it:
        yield _to_item(media)


def scrape_pin(pin_id: str):
    """Fetches a single pin by id. Returns None if not found."""
    url = f"https://www.pinterest.com/pin/{pin_id}/"
    medias = PinterestDL.with_api(timeout=5, verbose=False).scrape(url=url, num=1)
    if not medias:
        return None
    return _to_item(medias[0])

def _to_item(media) -> dict:
    """
    Normalizes a pinterest-dl media object into expected structure.
    """
    d = media.to_dict()
    res = d.get("resolution") or {}
    width = res.get("x") or d.get("width")
    height = res.get("y") or d.get("height")
    item_id = d.get("id")
    if item_id is not None:
        item_id = str(item_id)

    return {
        "id": item_id,
        "url": d.get("src") or d.get("url"),
        "src": d.get("src"),
        "width": width,
        "height": height,
        "alt": d.get("alt"),
        "origin": d.get("origin"),
        "resolution": {
            "x": width,
            "y": height,
        },
        "is_video": d.get("is_video") or False,
    }
