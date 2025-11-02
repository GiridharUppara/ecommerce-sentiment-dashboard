

# ---------- robust Firestore init (handles multiple secret formats) ----------
import streamlit as st
import json
import os
import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
import traceback

def init_firestore_from_secrets():
    # 1) Ensure secret exists
    if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
        st.error("FIREBASE_SERVICE_ACCOUNT not found in Streamlit Secrets. Go to App → Settings → Secrets and add it.")
        st.stop()

    sa_value = st.secrets["FIREBASE_SERVICE_ACCOUNT"]

    # 2) Allow either a JSON string or a parsed dict (Streamlit can provide either)
    service_account = None
    if isinstance(sa_value, dict):
        service_account = sa_value
    else:
        # Try to parse string
        try:
            service_account = json.loads(sa_value)
        except Exception as e:
            st.error("Failed to parse FIREBASE_SERVICE_ACCOUNT JSON. Please paste the exact JSON into Secrets.")
            st.write("Parsing error:", str(e))
            st.stop()

    # 3) Ensure project_id exists (try env fallback too)
    project_id = service_account.get("project_id") if isinstance(service_account, dict) else None
    if not project_id:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    if not project_id:
        st.error("Project ID not found in service account JSON and no GOOGLE_CLOUD_PROJECT env var set.")
        st.write("service_account keys:", list(service_account.keys()) if isinstance(service_account, dict) else "not a dict")
        st.stop()

    # 4) Initialize admin SDK and client
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        db = firestore.Client(project=project_id)
        st.session_state["__firestore_initialized__"] = True
        return db
    except Exception as e:
        st.error("Failed to initialize Firestore client. Check service account and permissions.")
        st.text("Initialization traceback (compact):")
        st.text(traceback.format_exc())
        st.stop()

# call this once and use db below
db = init_firestore_from_secrets()
# --------------------------------------------------------------------------
