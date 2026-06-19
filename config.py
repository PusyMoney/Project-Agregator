import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)
