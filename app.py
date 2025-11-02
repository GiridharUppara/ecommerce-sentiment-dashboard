import streamlit as st
import json
import pandas as pd
from firebase_admin import credentials, initialize_app
import firebase_admin
from google.cloud import firestore
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="E-commerce Sentiment Dashboard")

# Initialize Firestore from Streamlit secrets
if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
    sa = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
    if not firebase_admin._apps:
        cred = credentials.Certificate(sa)
        initialize_app(cred)
    db = firestore.Client()
else:
    st.error("Service account not found in Streamlit secrets. Add FIREBASE_SERVICE_ACCOUNT in app settings.")
    st.stop()

st.title("E-commerce Review Sentiment Dashboard")

collection_name = st.sidebar.text_input("Collection", value="reviews")
product_filter = st.sidebar.text_input("Filter product_id (leave blank for all)")
min_rating = st.sidebar.slider("Minimum rating", 0.0, 5.0, 0.0, 0.5)
limit = st.sidebar.number_input("Fetch limit", min_value=100, max_value=5000, value=2000, step=100)

@st.cache_data(ttl=300)
def fetch_reviews(limit=2000, product_id=None):
    coll = db.collection(collection_name)
    q = coll
    if product_id:
        q = coll.where("product_id", "==", product_id)
    docs = q.limit(limit).stream()
    rows = []
    for d in docs:
        obj = d.to_dict()
        rows.append(obj)
    if not rows:
        return pd.DataFrame(columns=["review_id","product_id","review_text","rating","date","sentiment"])
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['sentiment_compound'] = df['sentiment'].apply(lambda s: s.get('compound') if isinstance(s, dict) else float(s) if s is not None else 0.0)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    return df

df = fetch_reviews(limit=limit, product_id=product_filter.strip() or None)

if df.empty:
    st.warning("No reviews found. Try increasing limit or remove product filter.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Total reviews", len(df))
col2.metric("Avg rating", round(df['rating'].mean(),2))
col3.metric("Avg sentiment", round(df['sentiment_compound'].mean(),3))

st.subheader("Sentiment over time")
ts = df.dropna(subset=['date']).set_index('date').resample('W')['sentiment_compound'].mean()
st.line_chart(ts)

st.subheader("Top Positive and Negative Reviews")
top_pos = df.sort_values("sentiment_compound", ascending=False).head(5)
top_neg = df.sort_values("sentiment_compound", ascending=True).head(5)

st.markdown("**Top Positive Reviews**")
for _, r in top_pos.iterrows():
    st.write(f"**{r['product_id']}** — {r['sentiment_compound']:.3f} — {r['review_text'][:300]}")

st.markdown("**Top Negative Reviews**")
for _, r in top_neg.iterrows():
    st.write(f"**{r['product_id']}** — {r['sentiment_compound']:.3f} — {r['review_text'][:300]}")

st.subheader("Wordcloud of Reviews")
text = " ".join(df['review_text'].astype(str).tolist())
wc = WordCloud(width=800, height=400, collocations=False).generate(text)
fig, ax = plt.subplots(figsize=(12,5))
ax.imshow(wc, interpolation='bilinear')
ax.axis('off')
st.pyplot(fig)
