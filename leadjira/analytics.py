from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from statistics import mean

from leadjira.mock_data import Issue


def _fallback_segment_end(start_at: datetime, selected_day: date, current_time: datetime) -> datetime:
    day_end = datetime.combine(selected_day, time.max)
    if selected_day == current_time.date():
        return max(start_at, min(current_time, day_end))
    return max(start_at, day_end)


def _actual_end_of_segment(issue: Issue, start_index: int, selected_day: date, current_time: datetime) -> datetime:
    next_index = start_index + 1
    if next_index < len(issue.events):
        return issue.events[next_index].at
    return _fallback_segment_end(issue.events[start_index].at, selected_day, current_time)


def _next_status(issue: Issue, start_index: int, current_status: str) -> str:
    next_index = start_index + 1
    if next_index < len(issue.events):
        return issue.events[next_index].to_status
    return f"Still in {current_status}"


def _group_name(issue: Issue, event_author: str, group_mode: str) -> str:
    if group_mode == "assignee":
        return issue.assignee
    return event_author


def _normalize_status(status: str) -> str:
    return " ".join((status or "").strip().lower().split())


def _format_segment_label(value: datetime, selected_day: date, include_date: bool) -> str:
    if include_date or value.date() != selected_day:
        return value.strftime("%d.%m %H:%M")
    return value.strftime("%H:%M")


def _clamp_timeline_end(value: datetime, selected_day: date) -> datetime:
    day_last_hour = datetime.combine(selected_day, time(23, 0))
    rounded = (value + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return min(rounded, day_last_hour)


def build_dashboard_data(
    issues: tuple[Issue, ...],
    selected_day: date,
    projects: set[str],
    people: set[str],
    target_status: str,
    group_mode: str,
    current_time: datetime | None = None,
) -> dict:
    now = current_time or datetime.now()
    normalized_target_status = _normalize_status(target_status)
    segments_by_person: dict[str, list[dict]] = defaultdict(list)
    matching_projects: set[str] = set()
    assignees: set[str] = set()
    transition_authors: set[str] = set()
    projects_all: set[str] = set()

    for issue in issues:
        projects_all.add(issue.project)
        assignees.add(issue.assignee)
        for event in issue.events:
            transition_authors.add(event.author)

    day_start = datetime.combine(selected_day, time.min)
    day_end = datetime.combine(selected_day, time.max)

    for issue in issues:
        if projects and issue.project not in projects:
            continue
        matching_projects.add(issue.project)

        for index, event in enumerate(issue.events):
            if _normalize_status(event.to_status) != normalized_target_status:
                continue
            if not (day_start <= event.at <= day_end):
                continue

            owner = _group_name(issue, event.author, group_mode)
            if people and owner not in people:
                continue

            actual_end_at = _actual_end_of_segment(issue, index, selected_day, now)
            display_end_at = min(actual_end_at, day_end)
            duration_minutes = max(int((display_end_at - event.at).total_seconds() // 60), 1)
            segments_by_person[owner].append(
                {
                    "issue_key": issue.key,
                    "summary": issue.summary,
                    "project": issue.project,
                    "assignee": issue.assignee,
                    "actor": event.author,
                    "priority": issue.priority,
                    "story_points": issue.story_points,
                    "start": event.at,
                    "actual_end": actual_end_at,
                    "display_end": display_end_at,
                    "next_status": _next_status(issue, index, target_status),
                    "duration_minutes": duration_minutes,
                }
            )

    rows: list[dict] = []
    all_segments: list[dict] = []
    durations: list[int] = []
    gaps: list[int] = []

    for person, segments in sorted(segments_by_person.items()):
        ordered = sorted(segments, key=lambda item: item["start"])
        row_segments: list[dict] = []
        previous_end: datetime | None = None

        for segment in ordered:
            gap_minutes = 0
            if previous_end is not None:
                gap_minutes = max(int((segment["start"] - previous_end).total_seconds() // 60), 0)
                gaps.append(gap_minutes)
            previous_end = segment["display_end"]
            durations.append(segment["duration_minutes"])
            spills_over_day = segment["actual_end"].date() != selected_day or segment["actual_end"] > day_end
            start_display_label = _format_segment_label(segment["start"], selected_day, spills_over_day)
            end_display_label = _format_segment_label(segment["actual_end"], selected_day, spills_over_day)

            row_segment = {
                "start_iso": segment["start"].isoformat(),
                "end_iso": segment["display_end"].isoformat(),
                "actual_end_iso": segment["actual_end"].isoformat(),
                "start_label": segment["start"].strftime("%H:%M"),
                "end_label": segment["display_end"].strftime("%H:%M"),
                "range_label": f"{start_display_label}-{end_display_label}",
                "issue_key": segment["issue_key"],
                "summary": segment["summary"],
                "project": segment["project"],
                "assignee": segment["assignee"],
                "actor": segment["actor"],
                "priority": segment["priority"],
                "story_points": segment["story_points"],
                "next_status": segment["next_status"],
                "duration_minutes": segment["duration_minutes"],
                "gap_minutes": gap_minutes,
                "spills_over_day": spills_over_day,
            }
            row_segments.append(row_segment)
            all_segments.append(
                {
                    "start": segment["start"],
                    "end": segment["display_end"],
                    **row_segment,
                }
            )

        total_minutes = sum(item["duration_minutes"] for item in ordered)
        rows.append(
            {
                "person": person,
                "segment_count": len(ordered),
                "total_minutes": total_minutes,
                "total_label": format_minutes(total_minutes),
                "segments": row_segments,
            }
        )

    timeline_start = min((segment["start"] for segment in all_segments), default=day_start.replace(hour=9))
    timeline_end = max((segment["end"] for segment in all_segments), default=day_start.replace(hour=18))
    timeline_start = timeline_start.replace(minute=0, second=0, microsecond=0)
    timeline_end = _clamp_timeline_end(timeline_end, selected_day)

    hours: list[str] = []
    cursor = timeline_start
    while cursor <= timeline_end:
        hours.append(cursor.strftime("%H:%M"))
        cursor += timedelta(hours=1)

    return {
        "filters": {
            "available_projects": sorted(projects_all),
            "available_assignees": sorted(assignees),
            "available_transition_authors": sorted(transition_authors),
            "group_mode": group_mode,
            "target_status": target_status,
            "date": selected_day.isoformat(),
        },
        "summary": {
            "segments": len(all_segments),
            "people": len(rows),
            "avg_testing_minutes": round(mean(durations), 1) if durations else 0,
            "avg_gap_minutes": round(mean(gaps), 1) if gaps else 0,
            "projects_covered": len(matching_projects),
        },
        "timeline": {
            "start_iso": timeline_start.isoformat(),
            "end_iso": timeline_end.isoformat(),
            "hour_marks": hours,
            "rows": rows,
        },
    }


def format_minutes(value: int) -> str:
    hours, minutes = divmod(value, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"
