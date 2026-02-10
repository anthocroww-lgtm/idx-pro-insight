"""
Konfigurasi koneksi Firebase (Firestore).
Semua credential diambil dari st.secrets - JANGAN hardcode API key di sini.
"""
import streamlit as st


def get_firebase_credentials():
    """Ambil credential Firebase dari st.secrets."""
    try:
        secrets = st.secrets
        if hasattr(secrets, "firebase") and secrets.firebase:
            return secrets.firebase
        return None
    except Exception:
        return None


def get_firestore_client():
    """
    Inisialisasi dan return client Firestore.
    Memerlukan st.secrets dengan struktur firebase (service_account atau credentials).
    """
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        return None

    creds_dict = get_firebase_credentials()
    if not creds_dict:
        return None

    # Jangan inisialisasi jika masih placeholder (belum isi Service Account)
    pk = creds_dict.get("private_key") or ""
    if not isinstance(pk, str) or "BEGIN PRIVATE KEY" not in pk or "ISI_DARI" in pk:
        return None

    try:
        # Jika sudah ada app default, return existing client
        if not firebase_admin._apps:
            d = dict(creds_dict) if not isinstance(creds_dict, dict) else creds_dict.copy()
            # Pastikan private_key punya newline asli (bukan literal \n)
            pk = d.get("private_key")
            if isinstance(pk, str) and "\\n" in pk:
                d["private_key"] = pk.replace("\\n", "\n")
            cred = credentials.Certificate(d)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception:
        return None


def verify_firebase_id_token(id_token: str):
    """
    Verifikasi Firebase ID token (dari login). Return dict {uid, email, display_name} atau None.
    Tidak mengubah data; hanya untuk restore session setelah refresh.
    """
    if not id_token or not isinstance(id_token, str) or not id_token.strip():
        return None
    try:
        import firebase_admin
        from firebase_admin import auth
        if not firebase_admin._apps:
            get_firestore_client()
        if not firebase_admin._apps:
            return None
        decoded = auth.verify_id_token(id_token.strip())
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "display_name": decoded.get("name") or (decoded.get("email") or "").split("@")[0],
        }
    except Exception:
        return None


def save_to_firestore(user_id: str, collection: str, data: dict, doc_id: str = None):
    """
    Simpan data ke sub-collection user di Firestore.
    users -> [user_id] -> watchlist | trading_journal
    """
    db = get_firestore_client()
    if not db:
        return False, "Firebase tidak dikonfigurasi. Cek .streamlit/secrets.toml"
    try:
        ref = db.collection("users").document(user_id).collection(collection)
        if doc_id:
            ref.document(doc_id).set(data, merge=True)
        else:
            ref.add(data)
        return True, "Berhasil disimpan"
    except Exception as e:
        return False, str(e)


def get_from_firestore(user_id: str, collection: str):
    """Ambil semua dokumen dari sub-collection user."""
    db = get_firestore_client()
    if not db:
        return []
    try:
        ref = db.collection("users").document(user_id).collection(collection)
        docs = ref.stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception:
        return []


def delete_from_firestore(user_id: str, collection: str, doc_id: str):
    """Hapus dokumen dari sub-collection."""
    db = get_firestore_client()
    if not db:
        return False
    try:
        db.collection("users").document(user_id).collection(collection).document(doc_id).delete()
        return True
    except Exception:
        return False
