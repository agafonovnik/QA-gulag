from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from leadjira.config import JiraSettings
from leadjira.mock_data import Issue, IssueEvent, MOCK_ISSUES


def load_issues(settings: JiraSettings, selected_day: date) -> tuple[Issue, ...]:
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
        jql_str=build_effective_jql(settings, selected_day),
        fields="summary,project,assignee,priority,created",
        expand="changelog",
        maxResults=settings.max_results,
    )
    return tuple(_convert_issue(issue, settings) for issue in issues)


def build_effective_jql(settings: JiraSettings, selected_day: date) -> str:
    start_at = datetime.combine(selected_day, time(hour=settings.workday_start_hour))
    end_at = start_at + timedelta(hours=settings.lookback_hours)
    updated_clause = f'updated >= "{_format_jql_datetime(start_at)}" AND updated <= "{_format_jql_datetime(end_at)}"'

    body, order_by = _split_order_by(settings.jql)
    body = _strip_updated_clauses(body)
    if body:
        return f"{body} AND {updated_clause}{order_by}"
    return f"{updated_clause}{order_by}"


def _split_order_by(jql: str) -> tuple[str, str]:
    match = re.search(r"(?i)\border\s+by\b", jql)
    if not match:
        return jql.strip(), ""
    return jql[: match.start()].strip(), f" {jql[match.start():].strip()}"


def _strip_updated_clauses(jql_body: str) -> str:
    patterns = (
        r"(?i)\s+AND\s+updated\s*(?:>=|>|<=|<)\s*(?:'[^']*'|\"[^\"]*\"|-\d+[mhdw]|\S+)",
        r"(?i)^updated\s*(?:>=|>|<=|<)\s*(?:'[^']*'|\"[^\"]*\"|-\d+[mhdw]|\S+)\s*(?:AND\s+)?",
    )
    cleaned = jql_body
    for pattern in patterns:
        cleaned = re.sub(pattern, " ", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _format_jql_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


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
