import ssl
import socket
import os
import logging
import random
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import xml.etree.ElementTree as ET

log_folder = 'logs'
os.makedirs(log_folder, exist_ok=True)
current_date = datetime.now().strftime('%d-%m-%Y')
log_file = os.path.join(log_folder, f'epp_client_{current_date}.log')

logger = logging.getLogger('EPPClient')
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1)
handler.suffix = "%d-%m-%Y"
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class EPPClient:
    def __init__(self, host, port):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.sock = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=host)
        self.sock.connect((host, port))
        self._read_initial_greeting()
        
    def _read_initial_greeting(self):
        try:
            response = self._read_response()
            logger.info(f"Initial greeting: {response}")
        except Exception as e:
            logger.error(f"Failed to read initial greeting: {e}")

    def _read_response(self):
        self.sock.settimeout(1)
        response = b""
        while True:
            try:
                part = self.sock.recv(4096)
                response += part
                if not part:
                    break
            except socket.timeout:
                break
        return response.decode('utf-8', errors='ignore')
            
    def send_epp_command(self, command_name, replacements=None):
        replacements = replacements or {}

        if 'cltrid' not in replacements:
            replacements['cltrid'] = str(random.randint(100000, 999999))

        command_file = f"{command_name}.xml"
        command_path = os.path.join('commands', command_file)

        try:
            with open(command_path, 'r') as file:
                xml = file.read()

            if 'ns' in replacements:
                ns_list = replacements['ns']

                ns_xml = "".join([f"<domain:hostObj>{ns}</domain:hostObj>" for ns in ns_list])
                xml = xml.replace("{ns}", ns_xml)

            for key, value in replacements.items():
                if key != 'ns':
                    xml = xml.replace(f'{{{key}}}', value)

            logger.debug(f"Sending EPP command from {command_file}: {xml}")
            self.sock.sendall(xml.encode('utf-8'))
            response = self._read_response()
            logger.debug(f"Received response: {response}")
            
            # Parse the response with regex
            result_code = re.search(r'<result code=\"(\d+)\"', response)
            message = re.search(r'<msg>(.*?)</msg>', response)
            cltrid = re.search(r'<clTRID>(.*?)</clTRID>', response)
            svtrid = re.search(r'<svTRID>(.*?)</svTRID>', response)

            # Create a JSON object with the extracted data
            response_json = {
                "result_code": result_code.group(1) if result_code else "",
                "message": message.group(1) if message else "",
                "cltrid": cltrid.group(1) if cltrid else "",
                "svtrid": svtrid.group(1) if svtrid else ""
            }

            return json.dumps(response_json)  # Return the JSON object as a string

        except Exception as e:
            logger.error(f"Failed to send EPP command from {command_file}: {e}")
            return None

    def command(self, command_name, **kwargs):
        return self.send_epp_command(command_name, kwargs)