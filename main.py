from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from analytics import get_trending, init_analytics_db, log_query
from cache import init_db
from models import SearchResponse
from scraper import (
    iter_related_items,
    iter_scrape_items,
    iter_search_items,
    scrape_pin,
)
from streaming import get_next_batch, reset_stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_analytics_db()
    yield


app = FastAPI(title="Pinwall API", lifespan=lifespan)

# Allow requests from Flutter Web / any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pinterest/pinterest-dl has no "browse by category" feature
GENRES = {
    "nature": "nature wallpaper",
    "abstract": "abstract wallpaper",
    "minimalist": "minimalist wallpaper",
    "dark": "dark aesthetic wallpaper",
    "anime": "anime wallpaper",
    "space": "space wallpaper",
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/genres")
def list_genres():
    return {"genres": list(GENRES.keys())}


@app.get("/search", response_model=SearchResponse)
def search(
    query: str = Query(..., min_length=1),
    count: int = Query(30, ge=1, le=100),
):
    log_query(query)  # feeds the /trending endpoint
    key = f"search:{query}"
    items = get_next_batch(key, count, lambda: iter_search_items(query))
    return SearchResponse(query=query, count=len(items), cached=False, items=items)


@app.get("/genre/{slug}", response_model=SearchResponse)
def genre(slug: str, count: int = Query(30, ge=1, le=100)):
    if slug not in GENRES:
        raise HTTPException(status_code=404, detail=f"Unknown genre '{slug}'")
    query = GENRES[slug]
    key = f"genre:{slug}"
    items = get_next_batch(key, count, lambda: iter_search_items(query))
    return SearchResponse(query=slug, count=len(items), cached=False, items=items)


@app.get("/trending")
def trending(limit: int = Query(10, ge=1, le=50)):
    return {"trending": get_trending(limit=limit)}


@app.get("/pin/{pin_id}")
def pin(pin_id: str):
    item = scrape_pin(pin_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pin not found")
    return item


@app.get("/related", response_model=SearchResponse)
def related(pin_id: str = Query(...), count: int = Query(30, ge=1, le=100)):
    key = f"related:{pin_id}"
    items = get_next_batch(key, count, lambda: iter_related_items(pin_id))
    return SearchResponse(query=pin_id, count=len(items), cached=False, items=items)


@app.get("/board/{board_id:path}", response_model=SearchResponse)
def board(board_id: str, count: int = Query(30, ge=1, le=100)):
    # board_id is the full Pinterest board URL (or username/board-name path)
    key = f"board:{board_id}"
    items = get_next_batch(key, count, lambda: iter_scrape_items(board_id))
    return SearchResponse(query=board_id, count=len(items), cached=False, items=items)


@app.post("/reset")
def reset(key: str = Query(..., description="e.g. 'search:cats' or 'board:<url>'")):
    """Forget a stream's position -- next request for it starts over."""
    reset_stream(key)
    return {"reset": key}
