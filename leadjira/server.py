from __future__ import annotations

import json
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from leadjira.analytics import build_dashboard_data
from leadjira.config import SETTINGS
from leadjira.jira_provider import load_issues


HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lead Jira Helper by PAMF</title>
  <style>
    :root {
      --bg: #07111f;
      --bg-soft: rgba(13, 26, 46, 0.72);
      --panel: rgba(9, 19, 35, 0.84);
      --panel-strong: rgba(8, 16, 30, 0.92);
      --line: rgba(148, 163, 184, 0.18);
      --text: #ecf5ff;
      --muted: #9db0c7;
      --cyan: #52d1ff;
      --teal: #61f4c7;
      --gold: #f7c66c;
      --rose: #ff8b9d;
      --shadow: 0 22px 70px rgba(0, 0, 0, 0.35);
      --radius: 24px;
      --font: Manrope, "Segoe UI Variable", "Trebuchet MS", sans-serif;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--font);
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(82, 209, 255, 0.18), transparent 28%),
        radial-gradient(circle at 85% 10%, rgba(97, 244, 199, 0.16), transparent 25%),
        linear-gradient(160deg, #040913 0%, #091323 52%, #07111f 100%);
      min-height: 100vh;
    }

    body.menu-open {
      overflow: hidden;
    }

    .shell {
      width: min(1440px, calc(100vw - 40px));
      margin: 28px auto 40px;
      position: relative;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      backdrop-filter: blur(24px);
      border-radius: var(--radius);
    }

    .topbar {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 18px;
    }

    .menu-toggle,
    .sidebar-close {
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(9, 19, 35, 0.86);
      color: var(--text);
      border-radius: 18px;
      cursor: pointer;
      backdrop-filter: blur(24px);
    }

    .menu-toggle {
      width: 58px;
      height: 58px;
      display: grid;
      place-items: center;
      box-shadow: var(--shadow);
      flex: 0 0 auto;
    }

    .burger {
      width: 22px;
      height: 14px;
      position: relative;
      display: block;
    }

    .burger::before,
    .burger::after,
    .burger span {
      content: "";
      position: absolute;
      left: 0;
      width: 100%;
      height: 2px;
      border-radius: 999px;
      background: var(--text);
    }

    .burger::before { top: 0; }
    .burger span { top: 6px; }
    .burger::after { bottom: 0; }

    .topbar-copy {
      min-width: 0;
    }

    .topbar-copy strong {
      display: block;
      font-size: 18px;
      line-height: 1.1;
    }

    .topbar-copy span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 13px;
    }

    .sidebar-overlay {
      position: fixed;
      inset: 0;
      background: rgba(2, 7, 15, 0.62);
      opacity: 0;
      pointer-events: none;
      transition: opacity 180ms ease;
      z-index: 20;
    }

    body.menu-open .sidebar-overlay {
      opacity: 1;
      pointer-events: auto;
    }

    .sidebar {
      position: fixed;
      top: 20px;
      left: 20px;
      bottom: 20px;
      width: min(360px, calc(100vw - 32px));
      padding: 20px;
      overflow-y: auto;
      z-index: 30;
      transform: translateX(calc(-100% - 28px));
      transition: transform 220ms ease;
    }

    body.menu-open .sidebar {
      transform: translateX(0);
    }

    .sidebar-header {
      display: flex;
      justify-content: space-between;
      align-items: start;
      gap: 14px;
    }

    .sidebar-close {
      width: 44px;
      height: 44px;
      font-size: 24px;
      line-height: 1;
      flex: 0 0 auto;
    }

    .brand {
      margin-bottom: 24px;
      min-width: 0;
    }

    .eyebrow {
      display: inline-flex;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(82, 209, 255, 0.12);
      color: var(--cyan);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    h1 {
      margin: 14px 0 8px;
      font-size: 34px;
      line-height: 1;
    }

    .subtitle {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }

    .config-box {
      margin-top: 18px;
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .config-box code {
      color: var(--teal);
      font-size: 13px;
      display: block;
      margin-top: 6px;
      word-break: break-all;
    }

    .filter-group {
      margin-top: 20px;
    }

    .filter-group label,
    .legend-title {
      display: block;
      margin-bottom: 10px;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: #bfd1e4;
    }

    .control,
    .chips {
      width: 100%;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
    }

    .control {
      padding: 13px 14px;
      font-size: 14px;
    }

    .chips {
      padding: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      min-height: 56px;
    }

    .chip {
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
      padding: 7px 12px;
      cursor: pointer;
      transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
    }

    .chip:hover { transform: translateY(-1px); }
    .chip.active {
      background: rgba(82, 209, 255, 0.17);
      border-color: rgba(82, 209, 255, 0.42);
      color: #dff8ff;
    }

    .btn {
      width: 100%;
      margin-top: 18px;
      padding: 14px;
      border: 0;
      border-radius: 16px;
      font: inherit;
      font-weight: 800;
      color: #04111b;
      background: linear-gradient(135deg, var(--teal), var(--cyan));
      cursor: pointer;
      box-shadow: 0 18px 30px rgba(82, 209, 255, 0.18);
    }

    .btn.secondary {
      margin-top: 10px;
      color: var(--text);
      background: rgba(255, 255, 255, 0.08);
      box-shadow: none;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .main {
      display: grid;
      gap: 24px;
    }

    .hero {
      padding: 20px 22px;
      overflow: hidden;
      position: relative;
    }

    .hero::after {
      content: "";
      position: absolute;
      inset: auto -10% -45% auto;
      width: 360px;
      height: 360px;
      background: radial-gradient(circle, rgba(247, 198, 108, 0.24), transparent 70%);
      pointer-events: none;
    }

    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 560px) minmax(360px, 420px);
      justify-content: space-between;
      gap: 22px;
      position: relative;
      z-index: 1;
      align-items: start;
    }

    .hero-copy {
      max-width: 560px;
    }

    .hero-copy h2 {
      margin: 0;
      font-size: 29px;
      line-height: 1.04;
      max-width: 12ch;
    }

    .hero-copy p {
      margin: 12px 0 0;
      color: var(--muted);
      max-width: 62ch;
      line-height: 1.45;
      font-size: 14px;
    }

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(150px, 1fr));
      gap: 10px;
      width: min(100%, 420px);
      justify-self: end;
    }

    .metric {
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.06);
      min-height: 88px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .metric strong {
      display: block;
      margin-top: 8px;
      font-size: 26px;
      line-height: 1;
    }

    .board {
      padding: 24px;
    }

    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 18px;
      margin-bottom: 18px;
    }

    .section-title h3 {
      margin: 0;
      font-size: 26px;
    }

    .section-title p {
      margin: 6px 0 0;
      color: var(--muted);
    }

    .timeline-header,
    .timeline-row {
      display: grid;
      grid-template-columns: 230px 1fr;
      gap: 18px;
      align-items: stretch;
    }

    .timeline-header {
      margin-bottom: 12px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .timeline-axis {
      position: relative;
      min-height: 28px;
      padding-left: 12px;
    }

    .axis-mark {
      position: absolute;
      top: 0;
      transform: translateX(-50%);
      white-space: nowrap;
    }

    .axis-mark::before {
      content: "";
      position: absolute;
      left: 50%;
      top: -2px;
      width: 1px;
      height: 24px;
      transform: translateX(-50%);
      background: rgba(255, 255, 255, 0.09);
    }

    .axis-mark.start {
      transform: none;
    }

    .axis-mark.start::before {
      left: 0;
      transform: none;
    }

    .axis-mark.end {
      transform: translateX(-100%);
      text-align: right;
    }

    .axis-mark.end::before {
      left: 100%;
      transform: translateX(-100%);
    }

    .timeline-row + .timeline-row {
      margin-top: 16px;
    }

    .person-card {
      padding: 18px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.045);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .person-card strong {
      display: block;
      font-size: 17px;
      margin-bottom: 8px;
    }

    .person-card small {
      color: var(--muted);
      line-height: 1.5;
      display: block;
    }

    .lane {
      position: relative;
      min-height: 168px;
      border-radius: 22px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.02)),
        repeating-linear-gradient(
          to right,
          rgba(255, 255, 255, 0.06) 0,
          rgba(255, 255, 255, 0.06) 1px,
          transparent 1px,
          transparent calc(100% / var(--intervals))
        );
      border: 1px solid rgba(255, 255, 255, 0.06);
      overflow: visible;
    }

    .lane-inner {
      position: absolute;
      inset: 12px;
    }

    .task-group {
      position: absolute;
      height: 82px;
    }

    .task {
      position: relative;
      width: 100%;
      min-width: 0;
      min-height: 50px;
      border-radius: 14px;
      padding: 10px 12px 9px;
      display: grid;
      grid-template-rows: auto auto;
      align-content: center;
      gap: 4px;
      color: #04111b;
      font-weight: 800;
      overflow: hidden;
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
    }

    .task .task-key {
      font-size: 17px;
      line-height: 1;
      letter-spacing: 0;
      white-space: nowrap;
    }

    .task .task-meta {
      font-size: 12px;
      font-weight: 700;
      opacity: 0.74;
      line-height: 1.1;
      white-space: nowrap;
    }

    .task-status {
      position: absolute;
      right: -10px;
      bottom: 2px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: max-content;
      max-width: 220px;
      padding: 6px 11px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 900;
      line-height: 1;
      letter-spacing: 0.04em;
      text-align: center;
      white-space: nowrap;
      box-shadow: 0 16px 28px rgba(0, 0, 0, 0.34);
      border: 1px solid transparent;
      backdrop-filter: blur(0);
      z-index: 3;
    }

    .task.compact {
      padding-inline: 10px;
    }

    .task.compact .task-key {
      font-size: 15px;
    }

    .task.compact .task-meta {
      font-size: 10px;
    }

    .task.tight {
      padding-inline: 8px;
      gap: 1px;
    }

    .task.tight .task-key {
      font-size: 13px;
    }

    .task.tight .task-meta {
      font-size: 9px;
    }

    .task.tight + .task-status,
    .task.compact + .task-status {
      font-size: 9px;
      padding: 5px 9px;
    }

    .gap {
      position: absolute;
      height: 26px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffcfdb;
      font-size: 11px;
      font-weight: 800;
      background: rgba(255, 139, 157, 0.14);
      border: 1px dashed rgba(255, 139, 157, 0.35);
    }

    .issues {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }

    .issue-card {
      padding: 18px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .issue-card .topline {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
    }

    .pill {
      display: inline-flex;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .pill.project { background: rgba(82, 209, 255, 0.14); color: var(--cyan); }
    .pill.priority { background: rgba(247, 198, 108, 0.16); color: var(--gold); }
    .pill.outcome,
    .task-status {
      border-style: solid;
    }

    .tone-done {
      background: #0f4d42;
      color: #d9fff4;
      border-color: #2d8f7b;
    }

    .tone-release {
      background: #5a4315;
      color: #ffefc3;
      border-color: #b68628;
    }

    .tone-blocked {
      background: #060c16;
      color: #d9e2f2;
      border-color: #516279;
    }

    .tone-reopened {
      background: #114760;
      color: #ddf6ff;
      border-color: #4ba6c9;
    }

    .tone-progress {
      background: #2b356f;
      color: #e2e7ff;
      border-color: #6d7fd6;
    }

    .tone-neutral {
      background: #253140;
      color: #ecf5ff;
      border-color: #526172;
    }

    .issue-card h4 {
      margin: 0 0 12px;
      font-size: 18px;
      line-height: 1.35;
    }

    .issue-card p {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }

    .empty {
      padding: 28px;
      border-radius: 22px;
      color: var(--muted);
      text-align: center;
      border: 1px dashed rgba(255, 255, 255, 0.12);
      background: rgba(255, 255, 255, 0.03);
    }

    @media (max-width: 1280px) {
      .hero-grid {
        grid-template-columns: 1fr;
        justify-content: stretch;
      }

      .meta-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        width: 100%;
        justify-self: stretch;
      }
    }

    @media (max-width: 1100px) {
      .timeline-header,
      .timeline-row {
        grid-template-columns: 1fr;
      }

      .timeline-axis {
        overflow-x: auto;
      }
    }

    @media (max-width: 720px) {
      .shell {
        width: min(100vw - 20px, 1440px);
        margin: 10px auto 24px;
      }

      .topbar {
        margin-bottom: 14px;
      }

      .menu-toggle {
        width: 52px;
        height: 52px;
      }

      .hero {
        padding: 18px;
      }

      .hero-copy h2 {
        font-size: 26px;
      }

      .meta-grid {
        grid-template-columns: 1fr 1fr;
      }
    }
  </style>
</head>
<body>
  <div id="sidebarOverlay" class="sidebar-overlay"></div>
  <div class="shell">
    <div class="topbar">
      <button id="menuToggle" class="menu-toggle" type="button" aria-label="Открыть фильтры">
        <span class="burger"><span></span></span>
      </button>
      <div class="topbar-copy">
        <strong>Lead Jira Helper by PAMF</strong>
        <span>Фильтры и настройки</span>
      </div>
    </div>

    <aside class="panel sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <span class="eyebrow">Mock Jira Console</span>
          <h1>Lead Jira Helper</h1>
          <p class="subtitle">Настройки</p>
        </div>
        <button id="sidebarClose" class="sidebar-close" type="button" aria-label="Закрыть фильтры">×</button>
      </div>

      <div class="config-box">
        Jira config:
        <code>LEADJIRA_JIRA_URL=__BASE_URL__</code>
        <code>LEADJIRA_JIRA_TOKEN=***</code>
      </div>

      <div class="filter-group">
        <label for="dayInput">Дата</label>
        <input id="dayInput" class="control" type="date">
      </div>

      <div class="filter-group">
        <label for="statusInput">Целевой статус</label>
        <input id="statusInput" class="control" type="text" value="Testing">
      </div>

      <div class="filter-group">
        <label for="groupMode">Группировка людей</label>
        <select id="groupMode" class="control">
          <option value="transition_author">Кто перевел в Testing</option>
          <option value="assignee">Исполнитель задачи</option>
        </select>
      </div>

      <div class="filter-group">
        <span class="legend-title">Проекты</span>
        <div id="projectChips" class="chips"></div>
      </div>

      <div class="filter-group">
        <span class="legend-title">Люди</span>
        <div id="peopleChips" class="chips"></div>
      </div>

      <button id="applyBtn" class="btn">Обновить дашборд</button>
      <button id="resetBtn" class="btn secondary">Сбросить фильтры</button>
    </aside>

    <main class="main">
      <section class="panel hero">
        <div class="hero-grid">
          <div class="hero-copy">
            <span class="eyebrow">Timeline Intelligence</span>
            <h2>Последовательность задач, паузы и нагрузка тестирования</h2>
            <p id="heroText">Смотрим, кто и когда взял задачу в тест, сколько она была в статусе, и какой простой получился между переключениями в течение дня.</p>
          </div>
          <div id="summaryGrid" class="meta-grid"></div>
        </div>
      </section>

      <section class="panel board">
        <div class="section-title">
          <div>
            <h3>Дневной timeline</h3>
            <p id="timelineSubtitle">Отображает задачи в порядке взятия по выбранным людям.</p>
          </div>
        </div>

        <div class="timeline-header">
          <div>Люди</div>
          <div id="axis" class="timeline-axis"></div>
        </div>

        <div id="timelineRows"></div>
      </section>

      <section class="panel board">
        <div class="section-title">
          <div>
            <h3>Сегменты тестирования</h3>
            <p>Карточки ниже помогают быстро перейти от общего графика к конкретным задачам и длительностям.</p>
          </div>
        </div>
        <div id="issuesGrid" class="issues"></div>
      </section>
    </main>
  </div>

  <script>
    const state = {
      selectedProjects: new Set(),
      selectedPeople: new Set(),
      options: null,
      lastData: null,
    };

    const palette = ["#61f4c7", "#52d1ff", "#f7c66c", "#ff8b9d", "#8ea7ff", "#8ff0ff"];

    function el(id) {
      return document.getElementById(id);
    }

    function formatMinutes(value) {
      const hours = Math.floor(value / 60);
      const minutes = value % 60;
      if (hours && minutes) return `${hours}h ${minutes}m`;
      if (hours) return `${hours}h`;
      return `${minutes}m`;
    }

    function buildTaskMeta(segment, density) {
      const range = `${segment.start_label}-${segment.end_label}`;
      const duration = formatMinutes(segment.duration_minutes);
      if (density === "tight") return duration;
      if (density === "compact") return range;
      return `${range} · ${duration}`;
    }

    function getOutcomeTone(status) {
      const normalized = status.toLowerCase();
      if (normalized.includes("done")) return "tone-done";
      if (normalized.includes("release")) return "tone-release";
      if (normalized.includes("blocked")) return "tone-blocked";
      if (normalized.includes("to do")) return "tone-reopened";
      if (normalized.includes("testing") || normalized.includes("review") || normalized.includes("progress")) return "tone-progress";
      return "tone-neutral";
    }

    function buildOutcomeLabel(status) {
      if (status === "To Do") return "Reopen";
      if (status === "Ready for Release") return "Ready for Release";
      if (status === "Still in Testing") return "Still in Testing";
      return status;
    }

    function metricCard(label, value) {
      return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
    }

    function buildChip(container, value, activeSet) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chip";
      button.textContent = value;
      if (activeSet.has(value)) button.classList.add("active");
      button.addEventListener("click", () => {
        if (activeSet.has(value)) {
          activeSet.delete(value);
          button.classList.remove("active");
        } else {
          activeSet.add(value);
          button.classList.add("active");
        }
      });
      container.appendChild(button);
    }

    function renderFilterOptions(filters) {
      const availablePeople = filters.group_mode === "assignee"
        ? filters.available_assignees
        : filters.available_transition_authors;

      el("dayInput").value = filters.date;
      el("statusInput").value = filters.target_status;
      el("groupMode").value = filters.group_mode;

      const projectChips = el("projectChips");
      projectChips.innerHTML = "";
      filters.available_projects.forEach((project) => buildChip(projectChips, project, state.selectedProjects));

      const peopleChips = el("peopleChips");
      peopleChips.innerHTML = "";
      availablePeople.forEach((person) => buildChip(peopleChips, person, state.selectedPeople));
    }

    function renderSummary(summary, filters) {
      el("summaryGrid").innerHTML = [
        metricCard("Людей в таймлайне", summary.people),
        metricCard("Задач", summary.segments),
        metricCard("Среднее время теста", `${summary.avg_testing_minutes}m`),
        metricCard("Средний простой", `${summary.avg_gap_minutes}m`),
      ].join("");

      el("heroText").textContent =
        `Дата ${filters.date}, статус "${filters.target_status}", режим "${filters.group_mode === "assignee" ? "исполнитель" : "автор перехода"}".`;
    }

    function renderAxis(hourMarks) {
      const axis = el("axis");
      const intervals = Math.max(hourMarks.length - 1, 1);
      document.documentElement.style.setProperty("--intervals", intervals);
      axis.innerHTML = hourMarks.map((mark, index) => {
        const left = intervals === 0 ? 0 : (index / intervals) * 100;
        const edgeClass = index === 0 ? "start" : index === hourMarks.length - 1 ? "end" : "";
        return `<div class="axis-mark ${edgeClass}" style="left:${left}%">${mark}</div>`;
      }).join("");
    }

    function renderTimeline(timeline) {
      const rows = el("timelineRows");
      const issuesGrid = el("issuesGrid");
      rows.innerHTML = "";
      issuesGrid.innerHTML = "";

      const start = new Date(timeline.start_iso).getTime();
      const end = new Date(timeline.end_iso).getTime();
      const total = Math.max(end - start, 1);

      if (!timeline.rows.length) {
        rows.innerHTML = '<div class="empty">По текущим фильтрам нет переходов в выбранный статус.</div>';
        issuesGrid.innerHTML = '<div class="empty">Измени дату, проекты или режим группировки, чтобы увидеть задачи.</div>';
        return;
      }

      timeline.rows.forEach((row, rowIndex) => {
        const wrapper = document.createElement("div");
        wrapper.className = "timeline-row";
        const totalLabel = row.total_label;
        wrapper.innerHTML = `
          <div class="person-card">
            <strong>${row.person}</strong>
            <small>${row.segment_count} сегм. за день</small>
            <small>Суммарно в статусе: ${totalLabel}</small>
          </div>
          <div class="lane">
            <div class="lane-inner"></div>
          </div>
        `;
        rows.appendChild(wrapper);

        const laneInner = wrapper.querySelector(".lane-inner");
        const laneWidth = laneInner.getBoundingClientRect().width || 1;
        const levelWidth = [];
        const levelHeight = 82;
        const lanePlacements = row.segments.map((segment, segmentIndex) => {
          const startMs = new Date(segment.start_iso).getTime();
          const endMs = new Date(segment.end_iso).getTime();
          const actualLeftPx = ((startMs - start) / total) * laneWidth;
          const actualWidthPx = Math.max(((endMs - startMs) / total) * laneWidth, 4);
          const density = actualWidthPx < 82 ? "tight" : actualWidthPx < 148 ? "compact" : "full";
          const visualWidthPx =
            density === "tight" ? Math.max(actualWidthPx, 104) :
            density === "compact" ? Math.max(actualWidthPx, 136) :
            actualWidthPx;
          const outcomeLabel = buildOutcomeLabel(segment.next_status);
          const statusWidthPx = Math.min(
            176,
            Math.max(density === "tight" ? 72 : 88, outcomeLabel.length * (density === "tight" ? 5.4 : 6.3) + 24)
          );
          const clampedLeftPx = Math.min(
            Math.max(actualLeftPx, 0),
            Math.max(laneWidth - visualWidthPx - 2, 0)
          );
          const footprintStart = Math.min(clampedLeftPx, clampedLeftPx + visualWidthPx - statusWidthPx - 10);
          const footprintEnd = clampedLeftPx + visualWidthPx + 10;
          let level = 0;
          while (levelWidth[level] !== undefined && footprintStart < levelWidth[level] + 8) {
            level += 1;
          }
          levelWidth[level] = footprintEnd;
          return {
            segment,
            segmentIndex,
            density,
            outcomeLabel,
            leftPx: clampedLeftPx,
            widthPx: visualWidthPx,
            topPx: level * levelHeight,
            level,
          };
        });

        const levelCount = Math.max(...lanePlacements.map((item) => item.level), 0) + 1;
        const gapTopPx = 14 + levelCount * levelHeight;
        wrapper.querySelector(".lane").style.minHeight = `${Math.max(168, gapTopPx + 52)}px`;

        lanePlacements.forEach((placement) => {
          const { segment, segmentIndex, density, outcomeLabel, leftPx, widthPx, topPx } = placement;
          const color = palette[(rowIndex + segmentIndex) % palette.length];
          const group = document.createElement("div");
          group.className = "task-group";
          group.style.left = `${leftPx}px`;
          group.style.top = `${topPx}px`;
          group.style.width = `${widthPx}px`;
          group.title = `${segment.issue_key}: ${segment.summary}`;

          const task = document.createElement("div");
          task.className = "task";
          task.style.width = "100%";
          task.style.background = `linear-gradient(135deg, ${color}, #ffffff)`;
          if (density !== "full") task.classList.add(density);
          task.innerHTML = `
            <span class="task-key">${segment.issue_key}</span>
            <span class="task-meta">${buildTaskMeta(segment, density)}</span>
          `;
          const status = document.createElement("div");
          status.className = `task-status ${getOutcomeTone(segment.next_status)}`;
          status.textContent = outcomeLabel;
          status.title = `После Testing: ${segment.next_status}`;
          group.appendChild(task);
          group.appendChild(status);
          laneInner.appendChild(group);
        });

        row.segments.forEach((segment) => {
          if (segment.gap_minutes > 0) {
            const gapStartPx = ((new Date(segment.start_iso).getTime() - start) / total) * laneWidth;
            const gap = document.createElement("div");
            gap.className = "gap";
            gap.style.top = `${gapTopPx}px`;
            gap.style.left = `${Math.max(gapStartPx - 28, 0)}px`;
            gap.style.width = "74px";
            gap.textContent = `${segment.gap_minutes}m gap`;
            laneInner.appendChild(gap);
          }

          const issueCard = document.createElement("article");
          issueCard.className = "issue-card";
          issueCard.innerHTML = `
            <div class="topline">
              <span class="pill project">${segment.project}</span>
              <span class="pill outcome ${getOutcomeTone(segment.next_status)}">${buildOutcomeLabel(segment.next_status)}</span>
            </div>
            <h4>${segment.issue_key} · ${segment.summary}</h4>
            <p>${row.person} · ${segment.start_label}-${segment.end_label} · ${formatMinutes(segment.duration_minutes)}</p>
            <p>Исполнитель: ${segment.assignee}. Перевел в статус: ${segment.actor}. Следующий статус: ${segment.next_status}. ${segment.story_points} SP.</p>
          `;
          issuesGrid.appendChild(issueCard);
        });
      });
    }

    async function fetchDashboard() {
      const params = new URLSearchParams();
      params.set("date", el("dayInput").value);
      params.set("target_status", el("statusInput").value.trim() || "Testing");
      params.set("group_mode", el("groupMode").value);
      state.selectedProjects.forEach((value) => params.append("projects", value));
      state.selectedPeople.forEach((value) => params.append("people", value));

      const response = await fetch(`/api/dashboard-data?${params.toString()}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
      const data = await response.json();
      state.lastData = data;
      renderFilterOptions(data.filters);
      renderSummary(data.summary, data.filters);
      renderAxis(data.timeline.hour_marks);
      renderTimeline(data.timeline);
      el("timelineSubtitle").textContent =
        `Окно ${data.timeline.hour_marks[0]}-${data.timeline.hour_marks[data.timeline.hour_marks.length - 1]} по локальному времени.`;
      setMenuOpen(false);
    }

    function resetFilters() {
      state.selectedProjects.clear();
      state.selectedPeople.clear();
      if (state.lastData) {
        el("dayInput").value = state.lastData.filters.date;
        el("statusInput").value = state.lastData.filters.target_status;
        el("groupMode").value = "transition_author";
      }
      fetchDashboard();
    }

    el("applyBtn").addEventListener("click", fetchDashboard);
    el("resetBtn").addEventListener("click", resetFilters);
    el("groupMode").addEventListener("change", () => {
      state.selectedPeople.clear();
      fetchDashboard();
    });

    function setMenuOpen(value) {
      document.body.classList.toggle("menu-open", value);
    }

    el("menuToggle").addEventListener("click", () => setMenuOpen(true));
    el("sidebarClose").addEventListener("click", () => setMenuOpen(false));
    el("sidebarOverlay").addEventListener("click", () => setMenuOpen(false));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    });

    fetchDashboard().catch((error) => {
      el("timelineRows").innerHTML = `<div class="empty">Ошибка загрузки: ${error.message}</div>`;
    });
  </script>
</body>
</html>
"""


class LeadJiraHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html()
            return
        if parsed.path == "/api/dashboard-data":
            self._send_dashboard_data(parsed.query)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(self) -> None:
        body = (
            HTML.replace("__BASE_URL__", SETTINGS.base_url)
            .encode("utf-8")
        )
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_dashboard_data(self, query: str) -> None:
        params = parse_qs(query)
        raw_date = params.get("date", [date(2026, 4, 24).isoformat()])[0]
        selected_day = date.fromisoformat(raw_date)
        projects = set(params.get("projects", []))
        people = set(params.get("people", []))
        target_status = params.get("target_status", [SETTINGS.target_status])[0] or SETTINGS.target_status
        group_mode = params.get("group_mode", ["transition_author"])[0]

        try:
            payload = build_dashboard_data(
                issues=load_issues(SETTINGS, selected_day),
                selected_day=selected_day,
                projects=projects,
                people=people,
                target_status=target_status,
                group_mode=group_mode,
            )
            status = HTTPStatus.OK
        except Exception as exc:
            payload = {"error": str(exc)}
            status = HTTPStatus.INTERNAL_SERVER_ERROR

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    server = ThreadingHTTPServer((SETTINGS.app_host, SETTINGS.app_port), LeadJiraHandler)
    print(f"Lead Jira Helper mock dashboard: http://{SETTINGS.app_host}:{SETTINGS.app_port}")
    server.serve_forever()
