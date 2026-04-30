# firestore_writer.py
import firebase_admin
from firebase_admin import credentials, firestore
import config

def init_firestore():
    cred = credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)
    return firestore.client()

def save_signal(db, signal_dict):
    doc_ref = db.collection('signals').document()
    doc_ref.set(signal_dict)
    return doc_ref.id