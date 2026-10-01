import sqlite3
import uuid
from pathlib import Path

DB = Path("wardrobe.db")
IMG_DIR = Path("wardrobe_images")
IMG_DIR.mkdir(exist_ok=True)

NEUTRALS = {"Black", "White", "Grey", "Brown / Neutral"}

# Colours that look good with each non-neutral colour
GOOD = {
    "Red / Pink": {"Black", "White", "Grey", "Blue / Purple"},
    "Yellow / Green": {"Blue / Purple", "White", "Black", "Brown / Neutral"},
    "Blue / Purple": {"White", "Grey", "Black", "Brown / Neutral", "Yellow / Green"},
    "Green": {"White", "Black", "Brown / Neutral", "Grey"},
}

# What colours to shop for, given the colour you already have
PARTNER_TEXT = {
    "Black": "white, grey or any bright colour",
    "White": "black, navy, grey or any colour you like",
    "Grey": "black, white, navy or a bold colour",
    "Red / Pink": "black, white, grey or navy",
    "Yellow / Green": "navy, white, black or brown",
    "Blue / Purple": "white, grey, black or beige",
    "Green": "white, black, beige or grey",
    "Brown / Neutral": "white, navy, black or olive",
}

OCCASION_FIT = {
    "Formal": {"formal shirt", "shirt", "trousers", "skirt", "dress", "jacket"},
    "Casual": {"t-shirt", "hoodie", "jeans", "shorts", "top", "shirt", "trousers", "skirt"},
    "College": {"t-shirt", "shirt", "hoodie", "jeans", "trousers", "top", "jacket", "shorts"},
    "Party": {"dress", "top", "jeans", "skirt", "jacket", "shirt", "trousers"},
}

TOPS = {"t-shirt", "shirt", "formal shirt", "hoodie", "jacket", "top"}
BOTTOMS = {"trousers", "jeans", "shorts", "skirt"}


def category(item_type):
    if item_type in TOPS:
        return "Top"
    if item_type in BOTTOMS:
        return "Bottom"
    if item_type == "dress":
        return "One-piece"
    return "Other"


# ---------- storage ----------
def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT, item_type TEXT, category TEXT,
                color TEXT, confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
        )


def add_item(image, item_type, color, confidence):
    path = IMG_DIR / f"{uuid.uuid4().hex}.jpg"
    image.convert("RGB").save(path, quality=90)
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO items (image_path, item_type, category, color, confidence) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(path), item_type, category(item_type), color, confidence),
        )
        return cur.lastrowid


def list_items(cat=None):
    with _conn() as c:
        if cat:
            return c.execute(
                "SELECT * FROM items WHERE category=? ORDER BY id DESC", (cat,)
            ).fetchall()
        return c.execute("SELECT * FROM items ORDER BY id DESC").fetchall()


def delete_item(item_id):
    with _conn() as c:
        row = c.execute("SELECT image_path FROM items WHERE id=?", (item_id,)).fetchone()
        if row:
            Path(row["image_path"]).unlink(missing_ok=True)
        c.execute("DELETE FROM items WHERE id=?", (item_id,))


# ---------- matching ----------
def color_score(a, b):
    if a == b:
        return 0.6 if a in NEUTRALS else 0.3  # same bright colour head-to-toe clashes
    if a in NEUTRALS or b in NEUTRALS:
        return 0.9
    return 1.0 if b in GOOD.get(a, set()) else 0.4


def pair_score(type_a, color_a, type_b, color_b, occasion, preferred="Any"):
    fit = (type_a in OCCASION_FIT[occasion]) + (type_b in OCCASION_FIT[occasion])
    score = 0.6 * color_score(color_a, color_b) + 0.4 * (fit / 2)
    if preferred != "Any" and preferred in (color_a, color_b):
        score += 0.1
    return min(score, 1.0)


def recommend(item_type, color, occasion, preferred="Any", limit=4):
    """Rank wardrobe items that pair with the given item."""
    cat = category(item_type)
    target = {"Top": "Bottom", "Bottom": "Top"}.get(cat)
    if not target:
        return []
    ranked = [
        (r, pair_score(item_type, color, r["item_type"], r["color"], occasion, preferred))
        for r in list_items(target)
    ]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[:limit]


def build_outfits(occasion, preferred="Any", limit=6):
    tops, bottoms = list_items("Top"), list_items("Bottom")
    combos = [
        (t, b, pair_score(t["item_type"], t["color"], b["item_type"], b["color"], occasion, preferred))
        for t in tops for b in bottoms
    ]
    combos.sort(key=lambda x: x[2], reverse=True)
    return combos[:limit]


def shopping_idea(item_type, color, occasion):
    cat = category(item_type)
    if cat == "Top":
        noun = "formal trousers" if occasion == "Formal" else "jeans or trousers"
    elif cat == "Bottom":
        noun = "formal shirts" if occasion == "Formal" else "tops or t-shirts"
    else:
        return "Keep accessories simple and pick footwear to suit the occasion."
    return f"Look for {noun} in {PARTNER_TEXT.get(color, 'neutral shades')}."
