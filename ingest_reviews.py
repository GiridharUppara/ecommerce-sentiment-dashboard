import os
import json
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import firebase_admin
from firebase_admin import credentials, firestore

# -----------------------------------------------------------------
# Load Firebase credentials from GitHub Secrets (passed as env var)
# -----------------------------------------------------------------
sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

if not sa_json:
    raise ValueError("❌ Firebase service account not found. Make sure GitHub Secret is set correctly.")

service_account_info = json.loads(sa_json)
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)

# -----------------------------------------------------------------
# Connect to Firestore
# -----------------------------------------------------------------
db = firestore.client()
print("✅ Connected to Firestore successfully")

# -----------------------------------------------------------------
# Load your dataset
# -----------------------------------------------------------------
CSV_PATH = "reviews.csv"  # make sure this file is in your repo root
COLLECTION_NAME = "reviews"  # Firestore collection name

print(f"📂 Loading dataset from {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)

# Ensure required columns exist
required_cols = ['review_id', 'product_id', 'review_text', 'rating', 'date']
for c in required_cols:
    if c not in df.columns:
        raise ValueError(f"Missing required column: {c}")

print(f"✅ Loaded {len(df)} reviews")

# -----------------------------------------------------------------
# Sentiment analysis setup
# -----------------------------------------------------------------
analyzer = SentimentIntensityAnalyzer()

def compute_sentiment(text):
    if not isinstance(text, str) or text.strip() == "":
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    return analyzer.polarity_scores(text)

# -----------------------------------------------------------------
# Upload to Firestore in batches
# -----------------------------------------------------------------
batch_size = 500
batch = db.batch()
count = 0

for i, row in df.iterrows():
    sentiment = compute_sentiment(row['review_text'])
    doc_data = {
        "review_id": str(row['review_id']),
        "product_id": str(row['product_id']),
        "review_text": str(row['review_text']),
        "rating": float(row['rating']),
        "date": str(row['date']),
        "sentiment": sentiment
    }

    doc_ref = db.collection(COLLECTION_NAME).document(str(row['review_id']))
    batch.set(doc_ref, doc_data)
    count += 1

    # Commit every 500 documents
    if count % batch_size == 0 or i == len(df) - 1:
        batch.commit()
        print(f"🔥 Uploaded batch ending at row {i + 1}")
        batch = db.batch()

print(f"✅ Upload complete! Total reviews uploaded: {len(df)}")
