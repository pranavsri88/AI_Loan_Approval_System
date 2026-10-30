"""Configuration settings - simple approach without pydantic_settings."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from environment variables."""

    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        self.app_env = os.getenv("APP_ENV", "development")
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", 8000))
        self.streamlit_port = int(os.getenv("STREAMLIT_PORT", 8501))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.db_path = os.getenv("DB_PATH", "./data/loans.db")
        self.db_backup_path = os.getenv("DB_BACKUP_PATH", "./data/backups/")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")
        self.log_file = os.getenv("LOG_FILE", "./logs/app.log")
        self.request_timeout_seconds = 30
        self.agent_timeout_seconds = 2
        self.mcp_timeout_seconds = 1
        self.llm_timeout_seconds = 10
        self.dti_favorable_max = 0.36
        self.dti_acceptable_max = 0.43
        self.dti_borderline_max = 0.50
        self.dti_high_risk_min = 0.50
        self.credit_excellent_min = 750
        self.credit_good_min = 700
        self.credit_fair_min = 650
        self.credit_poor_min = 550
        self.lti_favorable_max = 2.5
        self.lti_acceptable_max = 4.0
        self.lti_high_risk_min = 4.0
        self.confidence_threshold = 0.75
        self.anomaly_score_threshold = 0.6
        self.max_agent_retries = 2
        self.enable_anomaly_detection = True
        self.enable_detailed_explanations = True
        self.enable_notifications = True
        self.use_mock_data = True
        self.mock_mcp_responses = True
        self.seed_mock_db = True

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


settings = Settings()

__all__ = ["Settings", "settings"]
