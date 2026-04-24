from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IssueEvent:
    at: datetime
    from_status: str
    to_status: str
    author: str


@dataclass(frozen=True)
class Issue:
    key: str
    summary: str
    project: str
    assignee: str
    priority: str
    story_points: int
    created_at: datetime
    events: tuple[IssueEvent, ...]


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


MOCK_ISSUES: tuple[Issue, ...] = (
    Issue(
        key="CORE-1842",
        summary="Stabilize webhook retries for payment sync",
        project="CORE",
        assignee="Artem Belov",
        priority="High",
        story_points=5,
        created_at=dt("2026-04-24T08:10:00"),
        events=(
            IssueEvent(dt("2026-04-24T08:35:00"), "To Do", "In Progress", "Artem Belov"),
            IssueEvent(dt("2026-04-24T10:05:00"), "In Progress", "Code Review", "Artem Belov"),
            IssueEvent(dt("2026-04-24T10:20:00"), "Code Review", "Testing", "Mila Sidorova"),
            IssueEvent(dt("2026-04-24T11:10:00"), "Testing", "Ready for Release", "Mila Sidorova"),
        ),
    ),
    Issue(
        key="CORE-1848",
        summary="Fix duplicate comments in CRM sync job",
        project="CORE",
        assignee="Artem Belov",
        priority="Medium",
        story_points=3,
        created_at=dt("2026-04-24T10:45:00"),
        events=(
            IssueEvent(dt("2026-04-24T11:25:00"), "To Do", "In Progress", "Artem Belov"),
            IssueEvent(dt("2026-04-24T12:05:00"), "In Progress", "Code Review", "Artem Belov"),
            IssueEvent(dt("2026-04-24T12:18:00"), "Code Review", "Testing", "Mila Sidorova"),
            IssueEvent(dt("2026-04-24T13:02:00"), "Testing", "Blocked", "Mila Sidorova"),
            IssueEvent(dt("2026-04-24T14:12:00"), "Blocked", "Testing", "Mila Sidorova"),
            IssueEvent(dt("2026-04-24T14:46:00"), "Testing", "Done", "Mila Sidorova"),
        ),
    ),
    Issue(
        key="API-901",
        summary="Expose rate-limit diagnostics in admin API",
        project="API",
        assignee="Polina Vetrova",
        priority="High",
        story_points=8,
        created_at=dt("2026-04-24T08:55:00"),
        events=(
            IssueEvent(dt("2026-04-24T09:10:00"), "To Do", "In Progress", "Polina Vetrova"),
            IssueEvent(dt("2026-04-24T11:40:00"), "In Progress", "Code Review", "Polina Vetrova"),
            IssueEvent(dt("2026-04-24T11:55:00"), "Code Review", "Testing", "Ilya Romanov"),
            IssueEvent(dt("2026-04-24T13:34:00"), "Testing", "Done", "Ilya Romanov"),
        ),
    ),
    Issue(
        key="API-915",
        summary="Tune partner API caching headers",
        project="API",
        assignee="Polina Vetrova",
        priority="Low",
        story_points=2,
        created_at=dt("2026-04-24T13:00:00"),
        events=(
            IssueEvent(dt("2026-04-24T13:18:00"), "To Do", "In Progress", "Polina Vetrova"),
            IssueEvent(dt("2026-04-24T15:08:00"), "In Progress", "Testing", "Ilya Romanov"),
            IssueEvent(dt("2026-04-24T15:40:00"), "Testing", "Done", "Ilya Romanov"),
        ),
    ),
    Issue(
        key="UI-1207",
        summary="Refresh dashboard widgets for morning digest",
        project="UI",
        assignee="Sofia Mironova",
        priority="Medium",
        story_points=5,
        created_at=dt("2026-04-24T09:05:00"),
        events=(
            IssueEvent(dt("2026-04-24T09:22:00"), "To Do", "In Progress", "Sofia Mironova"),
            IssueEvent(dt("2026-04-24T10:54:00"), "In Progress", "Code Review", "Sofia Mironova"),
            IssueEvent(dt("2026-04-24T11:08:00"), "Code Review", "Testing", "Nikita Vibecoder"),
            IssueEvent(dt("2026-04-24T12:14:00"), "Testing", "To Do", "Nikita Vibecoder"),
        ),
    ),
    Issue(
        key="UI-1210",
        summary="Reduce flicker on kanban swimlane drag",
        project="UI",
        assignee="Sofia Mironova",
        priority="High",
        story_points=3,
        created_at=dt("2026-04-24T11:30:00"),
        events=(
            IssueEvent(dt("2026-04-24T12:02:00"), "To Do", "In Progress", "Sofia Mironova"),
            IssueEvent(dt("2026-04-24T13:26:00"), "In Progress", "Testing", "Nikita Vibecoder"),
            IssueEvent(dt("2026-04-24T14:22:00"), "Testing", "Done", "Nikita Vibecoder"),
        ),
    ),
    Issue(
        key="CORE-1855",
        summary="Backfill audit log details for legacy retries",
        project="CORE",
        assignee="Oleg Smirnov",
        priority="Medium",
        story_points=8,
        created_at=dt("2026-04-24T14:05:00"),
        events=(
            IssueEvent(dt("2026-04-24T14:20:00"), "To Do", "In Progress", "Oleg Smirnov"),
            IssueEvent(dt("2026-04-24T16:25:00"), "In Progress", "Testing", "Mila Sidorova"),
            IssueEvent(dt("2026-04-24T17:35:00"), "Testing", "Ready for Release", "Mila Sidorova"),
        ),
    ),
)

