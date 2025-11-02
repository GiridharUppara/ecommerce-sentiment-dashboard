# ---------- robust Firestore init  ----------
import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
import traceback

def init_firestore_from_secrets():
    # 1) ensure secret exists
    if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
        st.error("FIREBASE_SERVICE_ACCOUNT not found in Streamlit Secrets. Go to App → Settings → Secrets and add it.")
        st.stop()

    # 2) parse JSON safely
    try:
        sa_text = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
        service_account = json.loads(sa_text)
    except Exception as e:
        st.error("Failed to parse FIREBASE_SERVICE_ACCOUNT JSON. Re-copy the exact JSON file into Secrets.")
        st.write("Parsing error:", str(e))
        st.stop()

    # 3) initialize firebase-admin (only once) and create firestore client with explicit project
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred, {'projectId': service_account.get("project_id")})
        db = firestore.Client(project=service_account.get("project_id"))
        return db
    except Exception as e:
        st.error("Failed to initialize Firestore client. Check service account and permissions.")
        st.text("Initialization traceback (for debugging):")
        st.text(traceback.format_exc())
        st.stop()

# call this once and use `db` below
db = init_firestore_from_secrets()
# --------------------------------------------------------------------------

