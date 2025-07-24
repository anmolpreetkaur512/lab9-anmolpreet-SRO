# incident-handler.py
from flask import Flask, request, jsonify
import json
import datetime
import uuid

app = Flask(__name__)

incidents = {}  # Stores incident details
incident_log = []  # For tracking changes/events

class IncidentManager:
    def __init__(self):
        self.severity_levels = ['low', 'medium', 'high', 'critical']
        self.status_levels = ['open', 'investigating', 'identified', 'monitoring', 'resolved']

    def create_incident(self, alert_data):
        incident_id = str(uuid.uuid4())[:8]
        incident = {
            'id': incident_id,
            'title': alert_data.get('commonAnnotations', {}).get('summary', 'Unknown incident'),
            'description': alert_data.get('commonAnnotations', {}).get('description', ''),
            'severity': self.determine_severity(alert_data),
            'status': 'open',
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat(),
            'alerts': alert_data.get('alerts', []),
            'timeline': [{
                'timestamp': datetime.datetime.now().isoformat(),
                'event': 'Incident created',
                'details': f"Alert received: {alert_data.get('commonAnnotations', {}).get('summary', '')}"
            }],
            'assigned_to': None,
            'resolution': None
        }
        incidents[incident_id] = incident
        incident_log.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'action': 'incident_created',
            'incident_id': incident_id,
            'severity': incident['severity']
        })
        return incident

    def determine_severity(self, alert_data):
        severity_mapping = {
            'critical': 'critical',
            'warning': 'medium',
            'info': 'low'
        }
        highest = 'low'
        for alert in alert_data.get('alerts', []):
            label = alert.get('labels', {}).get('severity', 'medium')
            mapped = severity_mapping.get(label, 'medium')
            if self.severity_levels.index(mapped) > self.severity_levels.index(highest):
                highest = mapped
        return highest

    def update_incident(self, incident_id, updates):
        if incident_id not in incidents:
            return None
        incident = incidents[incident_id]
        for key, value in updates.items():
            if key in incident:
                old_value = incident[key]
                incident[key] = value
                incident['timeline'].append({
                    'timestamp': datetime.datetime.now().isoformat(),
                    'event': f'{key} updated',
                    'details': f'Changed from "{old_value}" to "{value}"'
                })
        incident['updated_at'] = datetime.datetime.now().isoformat()
        return incident

incident_manager = IncidentManager()

@app.route('/ping')
def ping():
    return "pong"


@app.route('/webhook', methods=['POST'])
def webhook():
    alert_data = request.json
    if alert_data.get('status') == 'resolved':
        return jsonify({'message': 'Alert resolved'}), 200
    incident = incident_manager.create_incident(alert_data)
    print(f"\n🛑 NEW INCIDENT: {incident['id']}")
    print(f" Title: {incident['title']}")
    print(f" Severity: {incident['severity']}")
    return jsonify({'message': 'Incident created', 'incident_id': incident['id']}), 200

@app.route('/incidents')
def list_incidents():
    return jsonify(list(incidents.values()))

@app.route('/incidents/<incident_id>')
def get_incident(incident_id):
    if incident_id not in incidents:
        return jsonify({'error': 'Incident not found'}), 404
    return jsonify(incidents[incident_id])

@app.route('/incidents/<incident_id>', methods=['PUT'])
def update_incident(incident_id):
    updates = request.json
    incident = incident_manager.update_incident(incident_id, updates)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    return jsonify(incident)

@app.route('/incidents/<incident_id>/timeline', methods=['POST'])
def add_timeline_entry(incident_id):
    if incident_id not in incidents:
        return jsonify({'error': 'Incident not found'}), 404
    data = request.json
    entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'event': data.get('event', 'Manual update'),
        'details': data.get('details', ''),
        'user': data.get('user', 'system')
    }
    incidents[incident_id]['timeline'].append(entry)
    incidents[incident_id]['updated_at'] = datetime.datetime.now().isoformat()
    return jsonify(entry)

@app.route('/dashboard')
def dashboard():
    stats = {
        'total_incidents': len(incidents),
        'open_incidents': len([i for i in incidents.values() if i['status'] != 'resolved']),
        'critical_incidents': len([i for i in incidents.values() if i['severity'] == 'critical']),
        'recent_incidents': sorted(incidents.values(), key=lambda x: x['created_at'], reverse=True)[:5]
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
