import os
import json
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")


class TraceLoggerService:
    """Records complete multi-agent growth loop execution traces per session to the local output/ folder."""

    def __init__(self) -> None:
        """Ensures the output directory exists."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def log_trace_step(self, run_id: str, step_name: str, step_data: dict, session_id: str | None = None) -> str:
        """Appends step data to a session trace file and updates latest_run_trace.json."""
        sid = session_id or run_id
        trace_file = os.path.join(OUTPUT_DIR, f"session_{sid}.json")
        latest_file = os.path.join(OUTPUT_DIR, "latest_run_trace.json")

        trace_content = {}
        if os.path.exists(trace_file):
            try:
                with open(trace_file, "r", encoding="utf-8") as f:
                    trace_content = json.load(f)
            except Exception:
                trace_content = {}

        trace_content["session_id"] = sid
        trace_content["merchant_id"] = run_id
        trace_content["last_updated"] = datetime.utcnow().isoformat()
        trace_content.setdefault("steps", {})[step_name] = {
            "recorded_at": datetime.utcnow().isoformat(),
            "data": step_data,
        }

        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(trace_content, f, indent=2, default=str)

        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(trace_content, f, indent=2, default=str)

        return trace_file

    def get_session_trace(self, session_id: str) -> dict | None:
        """Reads and returns the trace for a specific session."""
        session_file = os.path.join(OUTPUT_DIR, f"session_{session_id}.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def get_latest_trace(self) -> dict | None:
        """Reads and returns the most recent full flow trace."""
        latest_file = os.path.join(OUTPUT_DIR, "latest_run_trace.json")
        if not os.path.exists(latest_file):
            return None
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def list_all_sessions(self) -> list[dict]:
        """Scans output directory and returns summary metadata for all saved session traces."""
        sessions = []
        if not os.path.exists(OUTPUT_DIR):
            return sessions

        for filename in os.listdir(OUTPUT_DIR):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_id = filename[len("session_"):-len(".json")]
                file_path = os.path.join(OUTPUT_DIR, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    steps = data.get("steps", {})
                    step2 = steps.get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})
                    step3 = steps.get("3_campaign_launch_and_dispatch", {}).get("data", {})
                    step4 = steps.get("4_experiment_ab_lift_measurement", {}).get("data", {})

                    sessions.append({
                        "session_id": session_id,
                        "merchant_id": data.get("merchant_id", "merch_demo"),
                        "last_updated": data.get("last_updated", ""),
                        "top_opportunity": step2.get("action_plan", {}).get("opportunity_title", "Growth Scan"),
                        "campaign_id": step3.get("campaign_id"),
                        "total_audience": step3.get("total_audience", 0),
                        "has_experiment": bool(step4),
                        "lift_display": step4.get("metrics", {}).get("relative_lift_display", "Pending"),
                        "incremental_gmv": step4.get("metrics", {}).get("incremental_revenue_inr", 0.0),
                    })
                except Exception:
                    continue

        sessions.sort(key=lambda s: s.get("last_updated", ""), reverse=True)
        return sessions


trace_logger_service = TraceLoggerService()

