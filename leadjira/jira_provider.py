from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from leadjira.config import JiraSettings
from leadjira.mock_data import Issue, IssueEvent, MOCK_ISSUES


def load_issues(settings: JiraSettings, selected_day: date, target_status: str) -> tuple[Issue, ...]:
    if settings.source_mode.lower() != "jira":
        return MOCK_ISSUES

    if not settings.base_url or not settings.api_token:
        raise RuntimeError("Jira mode requires LEADJIRA_JIRA_URL and LEADJIRA_JIRA_TOKEN.")

    try:
        from jira import JIRA
    except ImportError:
        raise RuntimeError("Package 'jira' is not installed. Run: python3 -m pip install -r requirements.txt")

    options = {
        "server": settings.base_url
    }
    jira_client = JIRA(options=options, token_auth=settings.api_token)
    issues = jira_client.search_issues(
        jql_str=build_effective_jql(settings, selected_day, target_status),
        fields="summary,project,assignee,priority,created",
        expand="changelog",
        maxResults=settings.max_results,
    )
    return tuple(_convert_issue(jira_client, issue, settings) for issue in issues)


def build_effective_jql(settings: JiraSettings, selected_day: date, target_status: str) -> str:
    start_at = datetime.combine(selected_day, time(hour=settings.workday_start_hour))
    end_at = start_at + timedelta(hours=settings.lookback_hours)
    escaped_status = target_status.replace('"', '\\"')
    transition_clause = (
        f'(status CHANGED TO "{escaped_status}" AFTER "{_format_jql_datetime(start_at)}" BEFORE "{_format_jql_datetime(end_at)}" '
        f'OR status CHANGED FROM "{escaped_status}" AFTER "{_format_jql_datetime(start_at)}" BEFORE "{_format_jql_datetime(end_at)}")'
    )

    body, order_by = _split_order_by(settings.jql)
    body = _strip_scope_clauses(body)
    if body:
        return f"{body} AND {transition_clause}{order_by}"
    return f"{transition_clause}{order_by}"


def _split_order_by(jql: str) -> tuple[str, str]:
    match = re.search(r"(?i)\border\s+by\b", jql)
    if not match:
        return jql.strip(), ""
    return jql[: match.start()].strip(), f" {jql[match.start():].strip()}"


def _strip_scope_clauses(jql_body: str) -> str:
    patterns = (
        r"(?i)\s+AND\s+updated\s*(?:>=|>|<=|<)\s*(?:'[^']*'|\"[^\"]*\"|-\d+[mhdw]|\S+)",
        r"(?i)^updated\s*(?:>=|>|<=|<)\s*(?:'[^']*'|\"[^\"]*\"|-\d+[mhdw]|\S+)\s*(?:AND\s+)?",
        r"(?i)\s+AND\s+statusCategory\s*(?:=|!=|IN|NOT IN)\s*(?:\([^)]+\)|'[^']*'|\"[^\"]*\"|\S+)",
        r"(?i)^statusCategory\s*(?:=|!=|IN|NOT IN)\s*(?:\([^)]+\)|'[^']*'|\"[^\"]*\"|\S+)\s*(?:AND\s+)?",
        r"(?i)\s+AND\s+status\s*(?:=|!=|IN|NOT IN)\s*(?:\([^)]+\)|'[^']*'|\"[^\"]*\"|\S+)",
        r"(?i)^status\s*(?:=|!=|IN|NOT IN)\s*(?:\([^)]+\)|'[^']*'|\"[^\"]*\"|\S+)\s*(?:AND\s+)?",
    )
    cleaned = jql_body
    for pattern in patterns:
        cleaned = re.sub(pattern, " ", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _format_jql_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


def _convert_issue(jira_client, raw_issue, settings: JiraSettings) -> Issue:
    fields = raw_issue.fields
    assignee = getattr(getattr(fields, "assignee", None), "displayName", "Unassigned")
    priority = getattr(getattr(fields, "priority", None), "name", "Unknown")
    project_key = getattr(getattr(fields, "project", None), "key", "N/A")
    summary = getattr(fields, "summary", raw_issue.key)
    created_at = _parse_jira_datetime(getattr(fields, "created", None), settings.timezone)
    story_points = _read_story_points(fields, settings.story_points_field)
    events = tuple(_extract_status_events(jira_client, raw_issue, settings.timezone))

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


def _extract_status_events(jira_client, raw_issue, timezone_name: str) -> list[IssueEvent]:
    histories = _load_full_histories(jira_client, raw_issue)
    status_events: list[IssueEvent] = []
    for history in histories:
        created = _parse_jira_datetime(_value(history, "created"), timezone_name)
        author_data = _value(history, "author")
        author = _value(author_data, "displayName", "Unknown") if author_data else "Unknown"
        for item in _value(history, "items", []) or []:
            if _value(item, "field") != "status":
                continue
            status_events.append(
                IssueEvent(
                    at=created,
                    from_status=_value(item, "fromString", "Unknown") or "Unknown",
                    to_status=_value(item, "toString", "Unknown") or "Unknown",
                    author=author,
                )
            )
    return sorted(status_events, key=lambda event: event.at)


def _load_full_histories(jira_client, raw_issue) -> list:
    changelog = getattr(raw_issue, "changelog", None)
    histories = list(getattr(changelog, "histories", []) or [])
    total = getattr(changelog, "total", None)
    if total is None or total <= len(histories):
        return histories

    start_at = len(histories)
    while start_at < total:
        page = jira_client._get_json(
            f"issue/{raw_issue.key}/changelog",
            params={"startAt": start_at, "maxResults": 100},
        )
        values = page.get("values", [])
        if not values:
            break
        histories.extend(values)
        start_at += len(values)
    return histories


def _value(obj, field: str, default=None):
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


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
