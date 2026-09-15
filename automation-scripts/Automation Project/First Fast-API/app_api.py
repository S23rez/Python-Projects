from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Cloud Security Automation API",
    description="Automated endpoint for receiving security alerts.",
    version="1.0.0"
)


# 1. Define the exact structure of data our API expects to receive
class IncidentAlert(BaseModel):
    ip_address: str
    vulnerability_type: str
    severity_score: int  # Scale of 1 to 10


# 2. A simple GET endpoint (similar to loading a homepage)
@app.get("/")
def read_root():
    return {"status": "API is online", "system": "SecOps-Gatekeeper"}


# 3. A POST endpoint (used by cloud tools or scrapers to send data to our script)
@app.post("/submit-alert/")
def process_alert(alert: IncidentAlert):
    # THE GATEKEEPER: Run logic checks on the data received
    if alert.severity_score >= 8:
        action_required = True
        status_message = "CRITICAL: Automated firewall blocking initiated."
    elif alert.severity_score >= 4:
        action_required = False
        status_message = "WARNING: Incident logged to cloud database."
    else:
        action_required = False
        status_message = "INFO: Trivial alert ignored."

    # Send a JSON confirmation back to the tool that sent the alert
    return {
        "received": True,
        "payload_status": "Processed Successfully",
        "evaluation": {
            "remediation_triggered": action_required,
            "next_steps": status_message
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)