from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JiraSettings:
    source_mode: str = os.getenv("LEADJIRA_SOURCE", "mock")
    base_url: str = os.getenv("LEADJIRA_JIRA_URL", "https://your-jira.example.com")
    api_token: str = os.getenv("LEADJIRA_JIRA_TOKEN", "set-me")
    jql: str = os.getenv(
        "LEADJIRA_DEFAULT_JQL",
        "project in (CORE, API, UI) AND statusCategory != Done ORDER BY updated DESC",
    )
    target_status: str = os.getenv("LEADJIRA_TARGET_STATUS", "Testing")
    timezone: str = os.getenv("LEADJIRA_TIMEZONE", "Europe/Moscow")
    verify_ssl: bool = os.getenv("LEADJIRA_VERIFY_SSL", "true").lower() == "true"
    max_results: int = int(os.getenv("LEADJIRA_MAX_RESULTS", "100"))
    story_points_field: str = os.getenv("LEADJIRA_STORY_POINTS_FIELD", "customfield_10016")
    app_host: str = os.getenv("LEADJIRA_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("LEADJIRA_PORT", "8765"))


SETTINGS = JiraSettings()
