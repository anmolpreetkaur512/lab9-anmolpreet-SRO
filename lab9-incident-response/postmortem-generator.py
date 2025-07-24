import requests
import json
from datetime import datetime
import argparse

class PostMortemGenerator:
    def __init__(self):
        self.incident_api = "http://localhost:5001"

    def generate_postmortem(self, incident_id):
        res = requests.get(f"{self.incident_api}/incidents/{incident_id}")
        if res.status_code != 200:
            print(f"❌ Incident {incident_id} not found.")
            return None
        incident = res.json()

        created_at = datetime.fromisoformat(incident['created_at'])
        updated_at = datetime.fromisoformat(incident['updated_at'])
        duration = updated_at - created_at

        postmortem = {
            "incident_id": incident_id,
            "title": f"Post-Mortem: {incident['title']}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": {
                "incident_title": incident['title'],
                "severity": incident['severity'],
                "duration": str(duration),
                "services_affected": self.extract_services(incident),
                "user_impact": self.assess_impact(incident['severity'])
            },
            "timeline": self.format_timeline(incident['timeline']),
            "root_cause": {
                "primary_cause": self.determine_cause(incident),
                "contributing_factors": self.contributing_factors(incident)
            },
            "resolution": {
                "immediate_actions": self.get_actions(incident),
                "resolution_method": incident.get("resolution", "TBD")
            },
            "lessons_learned": {
                "what_went_well": [],
                "what_could_be_improved": [],
                "action_items": []
            },
            "follow_up_actions": []
        }

        return postmortem

    def extract_services(self, incident):
        services = set()
        for alert in incident.get("alerts", []):
            svc = alert.get("labels", {}).get("service")
            if svc:
                services.add(svc)
        return list(services)

    def assess_impact(self, severity):
        return {
            "critical": "High - outage or severe degradation",
            "high": "Medium - significant slowdown or loss",
            "medium": "Low - minor performance issue",
            "low": "Minimal - mostly internal"
        }.get(severity, "Unknown")

    def format_timeline(self, timeline):
        return [
            {
                "time": entry["timestamp"],
                "event": entry["event"],
                "details": entry["details"],
                "user": entry.get("user", "system")
            }
            for entry in timeline
        ]

    def determine_cause(self, incident):
        title = incident["title"].lower()
        if "error rate" in title:
            return "Application failure"
        elif "latency" in title:
            return "Performance degradation"
        elif "service down" in title:
            return "Service unavailability"
        elif "database" in title:
            return "Database issue"
        else:
            return "Pending analysis"

    def contributing_factors(self, incident):
        factors = []
        timeline = incident.get("timeline", [])
        if len(timeline) > 5:
            factors.append("Prolonged issue with multiple events")
        if any(t.get("user") == "automation" for t in timeline):
            factors.append("Automation triggered")
        if incident["severity"] == "critical":
            factors.append("High urgency")
        return factors

    def get_actions(self, incident):
        actions = []
        for entry in incident.get("timeline", []):
            if "automated response" in entry["event"].lower():
                actions.append(entry["details"])
        return actions

    def save_json(self, postmortem):
        fname = f"postmortem_{postmortem['incident_id']}.json"
        with open(fname, "w") as f:
            json.dump(postmortem, f, indent=2)
        print(f"✅ Saved JSON: {fname}")
        return fname

    def save_markdown(self, postmortem):
        lines = [
            f"# {postmortem['title']}",
            f"**Date:** {postmortem['date']}",
            f"**Incident ID:** {postmortem['incident_id']}",
            "",
            "## Summary",
            f"- **Severity:** {postmortem['summary']['severity']}",
            f"- **Duration:** {postmortem['summary']['duration']}",
            f"- **Services Affected:** {', '.join(postmortem['summary']['services_affected'])}",
            f"- **User Impact:** {postmortem['summary']['user_impact']}",
            "",
            "## Timeline",
        ]
        for t in postmortem["timeline"]:
            lines.append(f"- **{t['time']}** - {t['event']}: {t['details']}")

        lines += [
            "",
            "## Root Cause",
            f"**Primary Cause:** {postmortem['root_cause']['primary_cause']}",
            "",
            "### Contributing Factors:"
        ] + [f"- {f}" for f in postmortem["root_cause"]["contributing_factors"]] + [
            "",
            "## Resolution",
            "### Immediate Actions:",
        ] + [f"- {a}" for a in postmortem["resolution"]["immediate_actions"]] + [
            "",
            f"**Resolution Method:** {postmortem['resolution']['resolution_method']}",
            "",
            "## Lessons Learned",
            "*(Fill this out during team review)*",
            "- What went well:",
            "- What could be improved:",
            "",
            "## Follow-up Actions",
            "- [ ] Update documentation",
            "- [ ] Conduct RCA review",
        ]

        fname = f"postmortem_{postmortem['incident_id']}.md"
        with open(fname, "w") as f:
            f.write("\n".join(lines))
        print(f"✅ Saved Markdown: {fname}")
        return fname

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("incident_id", help="ID of the incident to generate postmortem for")
    args = parser.parse_args()

    gen = PostMortemGenerator()
    pm = gen.generate_postmortem(args.incident_id)
    if not pm:
        return

    gen.save_json(pm)
    gen.save_markdown(pm)

if __name__ == "__main__":
    main()
