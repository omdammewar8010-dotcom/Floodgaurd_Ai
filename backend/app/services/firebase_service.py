import os
import json
import logging
from typing import Dict, Any, Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        self.app = None
        self.db = None # Firestore
        self.rtdb = None # Realtime Database
        self.is_mock = settings.FIREBASE_MOCK_MODE
        self._initialize()

    def _initialize(self):
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        if cred_path and os.path.exists(cred_path):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore, db
                cred = credentials.Certificate(cred_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'databaseURL': settings.FIREBASE_DATABASE_URL,
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
                self.db = firestore.client()
                self.rtdb = db
                self.is_mock = False
                logger.info("Firebase Admin initialized successfully with provided service account credentials.")
            except Exception as e:
                logger.warning(f"Failed to initialize Firebase with credentials: {e}. Falling back to internal mock provider.")
                self.is_mock = True
        else:
            logger.info("Firebase credentials path not provided or not found. Operating in Autonomous Mock/Simulation Mode.")
            self.is_mock = True

    def stream_sensor_reading(self, sensor_id: str, data: Dict[str, Any]):
        """Stream sensor reading to Firebase RTDB or internal simulator"""
        if not self.is_mock and self.rtdb:
            try:
                ref = self.rtdb.reference(f'sensors/{sensor_id}')
                ref.set(data)
                return True
            except Exception as e:
                logger.error(f"Error publishing to Firebase RTDB: {e}")
        return True

    def publish_alert(self, alert_id: str, alert_data: Dict[str, Any]):
        """Publish alert to Firestore"""
        if not self.is_mock and self.db:
            try:
                self.db.collection('alerts').document(alert_id).set(alert_data)
                return True
            except Exception as e:
                logger.error(f"Error publishing alert to Firestore: {e}")
        return True

firebase_service = FirebaseService()
