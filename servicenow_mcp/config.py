
import os
from dataclasses import dataclass

ENV_KEYS = {
    "dev": ("SERVICENOW_DEV_INSTANCE_URL", "SERVICENOW_DEV_USERNAME", "SERVICENOW_DEV_PASSWORD"),
    "test": ("SERVICENOW_TEST_INSTANCE_URL", "SERVICENOW_TEST_USERNAME", "SERVICENOW_TEST_PASSWORD"),
    "prod": ("SERVICENOW_PROD_INSTANCE_URL", "SERVICENOW_PROD_USERNAME", "SERVICENOW_PROD_PASSWORD"),
}

@dataclass
class Config:
    instance_url: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> "Config":
        url = os.getenv("SERVICENOW_INSTANCE_URL", "").rstrip("/")
        user = os.getenv("SERVICENOW_USERNAME", "")
        pwd = os.getenv("SERVICENOW_PASSWORD", "")
        if not url or not user or not pwd:
            raise RuntimeError("Missing env vars. Set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, SERVICENOW_PASSWORD.")
        return cls(url, user, pwd)

    @classmethod
    def for_env(cls, env: str) -> "Config":
        env = (env or 'dev').lower()
        if env in ENV_KEYS:
            url_key, user_key, pass_key = ENV_KEYS[env]
            url = (os.getenv(url_key) or "").rstrip("/")
            user = os.getenv(user_key) or ""
            pwd = os.getenv(pass_key) or ""
            if url and user and pwd:
                return cls(url, user, pwd)
        return cls.from_env()
