import streamlit as st
from PIL import Image
from transformers import pipeline
import numpy as np
from collections import Counter

import wardrobe as wd

st.set_page_config(page_title="StyleSense AI", page_icon="👗", layout="wide")
wd.init_db()

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg, #FFF8F3 0%, #FBE9E7 100%);}
    section[data-testid="stSidebar"] {background: #F6E7DF;}
    h1, h2, h3 {font-family: Georgia, serif; letter-spacing: 0.5px;}
    h1 {color: #8E2C48;}
    .stButton > button {border-radius: 999px; padding: 0.4rem 1.4rem;}
    img {border-radius: 14px;}
    </style>
    """,
    unsafe_allow_html=True,
)

ITEM_TYPES = [
    "t-shirt", "shirt", "formal shirt", "hoodie", "jacket",
    "dress", "top", "trousers", "jeans", "shorts", "skirt",
]
COLORS = [
    "Black", "White", "Grey", "Red / Pink", "Yellow / Green",
    "Blue / Purple", "Green", "Brown / Neutral",
]


@st.cache_resource
def load_classifier():
    return pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")


def dominant_color(image):
    img = image.convert("RGB").resize((80, 80))
    pixels = np.array(img).reshape(-1, 3)
    pixels = pixels[(pixels.sum(axis=1) > 45) & (pixels.sum(axis=1) < 720)]
    if len(pixels) == 0:
        pixels = np.array(img).reshape(-1, 3)
    quantized = (pixels // 32) * 32
    r, g, b = Counter(map(tuple, quantized)).most_common(1)[0][0]
    r, g, b = int(r), int(g), int(b)

    if max(r, g, b) - min(r, g, b) < 25:
        if (r + g + b) / 3 < 80:
            return "Black"
        if (r + g + b) / 3 > 200:
            return "White"
        return "Grey"
    if r > g * 1.25 and r > b * 1.25:
        return "Red / Pink"
    if r > b * 1.15 and g > b * 1.10:
        return "Yellow / Green"
    if b > r * 1.15 and b > g * 1.05:
        return "Blue / Purple"
    if g > r * 1.15 and g > b * 1.05:
        return "Green"
    return "Brown / Neutral"


def classify_clothing(image, classifier):
    result = classifier(image, candidate_labels=ITEM_TYPES)
    return result[0]["label"], result[0]["score"]


# ---------- sidebar ----------
with st.sidebar:
    st.header("Preferences")
    preferred_color = st.selectbox("Preferred colour", ["Any"] + COLORS)
    occasion = st.selectbox("Occasion", ["Casual", "College", "Formal", "Party"])
    st.metric("Items in wardrobe", len(wd.list_items()))

st.title("StyleSense AI 👗")
st.caption("Build your digital wardrobe and get outfit matches from clothes you own")

tab_add, tab_wardrobe, tab_outfits = st.tabs(["➕ Add item", "👚 My wardrobe", "✨ Outfit ideas"])

# ---------- Add item ----------
with tab_add:
    uploaded = st.file_uploader("Upload a clear photo of a top, bottom, dress, or jacket",
                                type=["jpg", "jpeg", "png"])
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        left, right = st.columns([1, 2])
        left.image(image, width=280)

        with right:
            if st.button("Analyze with StyleSense AI", type="primary"):
                with st.spinner("Analyzing..."):
                    item, conf = classify_clothing(image, load_classifier())
                    st.session_state.analysis = {
                        "file": uploaded.name, "item": item,
                        "conf": conf, "color": dominant_color(image),
                    }

            a = st.session_state.get("analysis")
            if a and a["file"] == uploaded.name:
                st.caption(f"AI confidence: {a['conf']:.0%}. Correct anything that looks wrong.")
                item = st.selectbox("Item type", ITEM_TYPES, index=ITEM_TYPES.index(a["item"]))
                color = st.selectbox("Colour", COLORS, index=COLORS.index(a["color"]))

                if st.button("💾 Save to wardrobe"):
                    wd.add_item(image, item, color, a["conf"])
                    st.success("Saved! It's now part of your wardrobe.")

                st.subheader("Matches from your wardrobe")
                matches = wd.recommend(item, color, occasion, preferred_color)
                if matches:
                    cols = st.columns(len(matches))
                    for col, (row, score) in zip(cols, matches):
                        col.image(row["image_path"], use_container_width=True)
                        col.caption(f"{row['item_type'].title()} · {row['color']}\n\nMatch: {score:.0%}")
                elif wd.category(item) in ("Top", "Bottom"):
                    st.info("Nothing to match yet. Add some "
                            f"{'bottoms' if wd.category(item) == 'Top' else 'tops'} to your wardrobe.")
                st.success("💡 " + wd.shopping_idea(item, color, occasion))

# ---------- Wardrobe ----------
with tab_wardrobe:
    items = wd.list_items()
    if not items:
        st.info("Your wardrobe is empty. Add your first item in the first tab.")
    for i in range(0, len(items), 4):
        cols = st.columns(4)
        for col, row in zip(cols, items[i:i + 4]):
            col.image(row["image_path"], use_container_width=True)
            col.caption(f"{row['item_type'].title()} · {row['category']} · {row['color']}")
            if col.button("🗑 Remove", key=f"del{row['id']}"):
                wd.delete_item(row["id"])
                st.rerun()

# ---------- Outfits ----------
with tab_outfits:
    outfits = wd.build_outfits(occasion, preferred_color)
    if not outfits:
        st.info("Add at least one top and one bottom to see outfit ideas.")
    else:
        st.write(f"Best combinations for **{occasion}**:")
        for top, bottom, score in outfits:
            c1, c2, c3 = st.columns([1, 1, 2])
            c1.image(top["image_path"], width=160)
            c2.image(bottom["image_path"], width=160)
            c3.metric("Match", f"{score:.0%}")
            c3.caption(f"{top['color']} {top['item_type']} + {bottom['color']} {bottom['item_type']}")
            st.divider()
