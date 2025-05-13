"""
This file generates the config.json file for the MCP client.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import json


load_dotenv()


def resolve_env_vars(config: dict) -> dict:
    for server_name, server_config in config.items():
        for property in server_config.keys():
            if property == "env":
                for key, value in server_config[property].items():
                    if isinstance(value, str) and value.startswith("${"):
                        env_var_name = value[2:-1]
                        env_var_value = os.environ.get(env_var_name, None)
                        if env_var_value is None:
                            raise ValueError(f"Environment variable {env_var_name} is not set")
                        config[server_name][property][key] = env_var_value
    return config


config_file = Path(__file__).parent / "mcp_config.json"
if not config_file.exists():
    raise FileNotFoundError(f"mcp_config.json file {config_file} does not exist")

with open(config_file, "r") as f:
    config = json.load(f)
    
mcp_config = resolve_env_vars(config)
