import os


class Settings:
    api_key: str = os.environ.get("ARTIFACT_API_KEY", "")
    base_url: str = os.environ.get("ARTIFACT_BASE_URL", "http://localhost:8090")


settings = Settings()
