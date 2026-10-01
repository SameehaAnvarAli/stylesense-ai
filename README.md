# StyleSense AI 👗

StyleSense AI is a virtual wardrobe and outfit recommendation prototype.

## Features

- Upload a clothing image
- AI-based clothing-item classification using CLIP
- Basic clothing category detection
- Dominant colour detection using image processing
- Occasion and colour preferences
- Simple outfit recommendations
- User-friendly Streamlit interface

## Tech Stack

- Python
- Streamlit
- Hugging Face Transformers
- OpenAI CLIP
- PyTorch
- Pillow
- NumPy

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The first analysis may take longer because the CLIP model needs to be downloaded.

## Project workflow

```text
Clothing Image
      ↓
Image Upload
      ↓
CLIP-based Clothing Classification
      ↓
Dominant Colour Extraction
      ↓
Category + User Preferences
      ↓
Outfit Recommendation
```

## Important note

This is a prototype. Classification confidence can vary depending on lighting, background, camera quality, and how clearly the clothing item is visible.
