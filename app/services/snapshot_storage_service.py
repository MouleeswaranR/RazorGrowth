import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
SNAPSHOT_FILE = os.path.join(DATA_DIR, "latest_simulation.json")


class SnapshotStorageService:
    """Persists and retrieves synthetic simulation datasets in local JSON files."""

    def __init__(self) -> None:
        """Ensures the local data directory exists."""
        os.makedirs(DATA_DIR, exist_ok=True)

    def save_local_snapshot(self, simulation_payload: dict) -> str:
        """Serializes and saves the complete merchant simulation state to latest_simulation.json."""
        simulation_payload["saved_at"] = datetime.utcnow().isoformat()
        with open(SNAPSHOT_FILE, "w", encoding="utf-8") as file:
            json.dump(simulation_payload, file, indent=2, default=str)
        return SNAPSHOT_FILE

    def get_latest_snapshot(self) -> dict | None:
        """Loads and returns the latest locally stored simulation snapshot."""
        if not os.path.exists(SNAPSHOT_FILE):
            return None
        try:
            with open(SNAPSHOT_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return None


snapshot_storage_service = SnapshotStorageService()
