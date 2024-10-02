from flask import Flask, request, jsonify
from Lib.EPPClient import EPPClient
import json
import re

app = Flask(__name__)

# Load config safely
with open('config.json', 'r') as f:
    config = json.load(f)

clients = {}
def initialize_epp_clients():
    connections = config.get('connections', {})
    for username, conn_info in connections.items():
        host = conn_info.get('host')
        port = conn_info.get('port', 700)
        password = conn_info.get('password')

        if not (host and username and password):
            app.logger.error(f"Missing required fields for {username} in config")
            continue

        client = EPPClient(host, port)
        app.logger.info(f"Connecting to EPP server for {username} at {host}:{port}")
        login_response = client.command('login', username=username, password=password)
        
        if login_response["response_info"] == "success":
            clients[username] = client
            app.logger.info(f"Successfully logged in for {username}")
        else:
            app.logger.error(f"Failed to login for {username}")

@app.route('/renewDomain', methods=['POST'])
def renew_domain():
    auth_error = authenticate_request()
    if auth_error:
        return jsonify(auth_error), 403

    data = request.json
    username = validate_username(data)
    if isinstance(username, dict):
        return jsonify(username), 400

    domain_name = data.get('domain_name')
    renewal_period = data.get('renewal_period', 1)

    if not domain_name:
        return jsonify({"error": "Domain name is required"}), 400

    client = clients[username]
    
    response = client.command('info', domain_name=domain_name)
    if not response:
        return jsonify({"error": "Failed to retrieve domain info"}), 500

    try:
        expiry_date = extract_expiry_date(response)
        if not expiry_date:
            return jsonify({"error": "Failed to retrieve expiry date"}), 500

        renewal_response = client.command(
            'renew',
            domain_name=domain_name,
            expiry_date=expiry_date,
            renewal_period=renewal_period
        )

        if renewal_response:
            return jsonify({"response": renewal_response}), 200
        else:
            return jsonify({"error": "Failed to renew domain"}), 500

    except Exception as e:
        app.logger.error(f"Error during domain renewal: {e}")
        return jsonify({"error": "Failed to renew domain"}), 500

@app.route('/setNS', methods=['POST'])
def set_ns():
    auth_error = authenticate_request()
    if auth_error:
        return jsonify(auth_error), 403

    data = request.json
    username = validate_username(data)
    if isinstance(username, dict):
        return jsonify(username), 400

    domain_name = data.get('domain_name')
    ns_list = data.get('nameservers', [])
    keep_ns = data.get('keepNS', False)

    if not domain_name:
        return jsonify({"error": "Domain name is required"}), 400

    if not ns_list or not isinstance(ns_list, list):
        return jsonify({"error": "At least one nameserver is required"}), 400

    client = clients[username]

    if not keep_ns:
        response = client.command('info', domain_name=domain_name)
        if not response:
            return jsonify({"error": "Failed to retrieve current nameservers"}), 500
        
        current_ns_list = extract_nameservers(response)
        if current_ns_list:
            remove_response = client.command('nameservers-remove', domain_name=domain_name, ns=current_ns_list)
            app.logger.info(f"Nameservers removed: {remove_response}")
            if not remove_response:
                return jsonify({"error": "Failed to remove existing nameservers"}), 500

    add_response = client.command('nameservers-add', domain_name=domain_name, ns=ns_list)
    if not add_response:
        return jsonify({"error": "Failed to add new nameservers"}), 500
    return jsonify({"response": add_response}), 200

@app.route('/command/<command_name>', methods=['POST'])
def command(command_name):
    auth_error = authenticate_request()
    if auth_error:
        return jsonify(auth_error), 403

    data = request.json
    username = validate_username(data)
    if isinstance(username, dict):
        return jsonify(username), 400

    client = clients[username]
    response = client.command(command_name, **data)

    if response:
        return jsonify({"response": response}), 200
    else:
        return jsonify({"error": "Failed to send command"}), 500

def extract_nameservers(xml_response):
    pattern = r"<domain:hostObj>(.*?)<\/domain:hostObj>"
    return re.findall(pattern, xml_response)

def authenticate_request():
    api_key = request.headers.get('API-Key')
    if api_key != config.get('api_key'):
        return {"error": "Invalid API key"}, 403
    return None

def validate_username(data):
    username = data.pop('username', None)
    if not username or username not in clients:
        return {"error": "Invalid or missing username"}, 400
    return username

def extract_expiry_date(xml_response):
    """Extracts the expiration date (exDate) from XML response."""
    pattern = r"<domain:exDate>(.*?)<\/domain:exDate>"
    match = re.search(pattern, xml_response)
    if match:
        expiry_date = match.group(1)
        return expiry_date.split('T')[0]
    return None

if __name__ == "__main__":
    initialize_epp_clients()
    app.run(host=config.get('api_url', '0.0.0.0'), port=config.get('api_port', 5000))