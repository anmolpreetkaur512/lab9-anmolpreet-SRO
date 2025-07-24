import requests
import time
import json

class AutomatedResponse:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.incident_api = "http://localhost:5001"
        self.response_actions = {
            'HighErrorRate': self.handle_high_error_rate,
            'HighLatency': self.handle_high_latency,
            'ServiceDown': self.handle_service_down,
            'DatabaseConnectionFailures': self.handle_database_failures
        }

    def handle_high_error_rate(self, incident):
        actions = []
        try:
            r = requests.post(f"{self.backend_url}/admin/failure-mode",
                              json={"mode": "intermittent_failures", "enabled": False})
            if r.status_code == 200:
                actions.append("Disabled intermittent_failures mode")
        except Exception as e:
            actions.append(f"Failed to disable: {e}")
        self.add_timeline(incident['id'], "Automated Response", ", ".join(actions))
        return actions

    def handle_high_latency(self, incident):
        actions = []
        try:
            r = requests.post(f"{self.backend_url}/admin/failure-mode",
                              json={"mode": "high_latency", "enabled": False})
            if r.status_code == 200:
                actions.append("Disabled high_latency mode")
        except Exception as e:
            actions.append(f"Failed to disable: {e}")
        self.add_timeline(incident['id'], "Automated Response", ", ".join(actions))
        return actions

    def handle_service_down(self, incident):
        actions = []
        try:
            r = requests.get(f"{self.backend_url}/health", timeout=3)
            if r.status_code == 200:
                actions.append("Service is actually healthy (false alarm)")
            else:
                actions.append("Health check failed")
        except Exception as e:
            actions.append(f"Health check error: {e}")
        actions.append("Escalation to SRE team needed")
        self.add_timeline(incident['id'], "Automated Response", ", ".join(actions))
        return actions

    def handle_database_failures(self, incident):
        actions = []
        try:
            r = requests.post(f"{self.backend_url}/admin/failure-mode",
                              json={"mode": "database_errors", "enabled": False})
            if r.status_code == 200:
                actions.append("Disabled database_errors mode")
        except Exception as e:
            actions.append(f"Failed to disable: {e}")
        self.add_timeline(incident['id'], "Automated Response", ", ".join(actions))
        return actions

    def add_timeline(self, incident_id, event, details):
        try:
            requests.post(f"{self.incident_api}/incidents/{incident_id}/timeline", json={
                "event": event,
                "details": details,
                "user": "automation"
            })
        except Exception as e:
            print(f"Failed to add timeline: {e}")

    def process(self, incident):
        title = incident.get("title", "").lower()
        for key in self.response_actions:
            if key.lower() in title:
                print(f"Responding to: {key}")
                return self.response_actions[key](incident)
        print(f"No automated response for: {title}")
        return []

def monitor():
    bot = AutomatedResponse()
    seen = set()

    while True:
        try:
            res = requests.get(f"{bot.incident_api}/incidents")
            if res.status_code != 200:
                print("Failed to fetch incidents")
                time.sleep(5)
                continue

            for inc in res.json():
                if inc["id"] in seen or inc["status"] != "open":
                    continue
                print(f"Processing incident {inc['id']} - {inc['title']}")
                bot.process(inc)
                requests.put(f"{bot.incident_api}/incidents/{inc['id']}",
                             json={"status": "investigating"})
                seen.add(inc["id"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    print("🔄 Starting automated incident monitor...")
    monitor()
