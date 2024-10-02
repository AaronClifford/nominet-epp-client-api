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
            parsed_response = self._parse_xml_to_dict(response)
            print(parsed_response)
            return parsed_response
        except Exception as e:
            logger.error(f"Failed to send EPP command from {command_file}: {e}")
            return None

    def _parse_xml_to_dict(self, xml_response):
        try:
            root = ET.fromstring(xml_response)
            response_dict = {root.tag: {}}

            for child in root:
                response_dict[root.tag][child.tag] = child.text

                if list(child):
                    response_dict[root.tag][child.tag] = self._parse_element(child)

            return response_dict
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return None

    def _parse_element(self, element):
        elem_dict = {}
        for child in element:
            if list(child):
                elem_dict[child.tag] = self._parse_element(child)
            else:
                elem_dict[child.tag] = child.text
        return elem_dict

    def command(self, command_name, **kwargs):
        return self.send_epp_command(command_name, kwargs)