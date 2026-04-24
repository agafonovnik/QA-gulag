from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from leadjira.config import JiraSettings
from leadjira.mock_data import Issue, IssueEvent, MOCK_ISSUES


def load_issues(settings: JiraSettings) -> tuple[Issue, ...]:
    if settings.source_mode.lower() != "jira":
        return MOCK_ISSUES

    if not settings.base_url or not settings.api_token:
        raise RuntimeError("Jira mode requires LEADJIRA_JIRA_URL and LEADJIRA_JIRA_TOKEN.")

    try:
        from jira import JIRA
    except ImportError:
        raise RuntimeError("Package 'jira' is not installed. Run: python3 -m pip install -r requirements.txt")

    options = {
        "server": settings.base_url,
        "verify": settings.verify_ssl,
    }
    jira_client = JIRA(options=options, token_auth=settings.api_token)
    issues = jira_client.search_issues(
        jql_str=settings.jql,
        fields="summary,project,assignee,priority,created",
        expand="changelog",
        maxResults=settings.max_results,
    )
    return tuple(_convert_issue(issue, settings) for issue in issues)


def _convert_issue(raw_issue, settings: JiraSettings) -> Issue:
    fields = raw_issue.fields
    assignee = getattr(getattr(fields, "assignee", None), "displayName", "Unassigned")
    priority = getattr(getattr(fields, "priority", None), "name", "Unknown")
    project_key = getattr(getattr(fields, "project", None), "key", "N/A")
    summary = getattr(fields, "summary", raw_issue.key)
    created_at = _parse_jira_datetime(getattr(fields, "created", None), settings.timezone)
    story_points = _read_story_points(fields, settings.story_points_field)
    events = tuple(_extract_status_events(raw_issue, settings.timezone))

    return Issue(
        key=raw_issue.key,
        summary=summary,
        project=project_key,
        assignee=assignee,
        priority=priority,
        story_points=story_points,
        created_at=created_at,
        events=events,
    )


def _extract_status_events(raw_issue, timezone_name: str) -> list[IssueEvent]:
    histories = getattr(getattr(raw_issue, "changelog", None), "histories", []) or []
    status_events: list[IssueEvent] = []
    for history in histories:
        created = _parse_jira_datetime(getattr(history, "created", None), timezone_name)
        author = getattr(getattr(history, "author", None), "displayName", "Unknown")
        for item in getattr(history, "items", []) or []:
            if getattr(item, "field", None) != "status":
                continue
            status_events.append(
                IssueEvent(
                    at=created,
                    from_status=getattr(item, "fromString", None) or "Unknown",
                    to_status=getattr(item, "toString", None) or "Unknown",
                    author=author,
                )
            )
    return sorted(status_events, key=lambda event: event.at)


def _parse_jira_datetime(value: str | None, timezone_name: str) -> datetime:
    if not value:
        return datetime.now()

    timezone = ZoneInfo(timezone_name)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt).astimezone(timezone).replace(tzinfo=None)
        except ValueError:
            continue
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone).replace(tzinfo=None)


def _read_story_points(fields, field_name: str) -> int:
    value = getattr(fields, field_name, 0)
    if value in (None, ""):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
