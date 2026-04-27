# Lead Jira Helper

Вебприложение на Python для кастомной аналитики поверх Jira-потока задач:

- гибкая фильтрация по проектам, людям и статусу;
- дневной timeline в стиле gantt;
- отображение порядка взятия задач в работу тестирования;
- расчет длительности задач и пауз между ними;
- поддержка мок-данных и реальной Jira через библиотеку `jira`.

## Запуск

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

Открой `http://127.0.0.1:8765`.

## Глобальная конфигурация

Под будущую интеграцию с реальной Jira уже оставлены переменные окружения:

- `LEADJIRA_SOURCE` (`mock` или `jira`)
- `LEADJIRA_JIRA_URL`
- `LEADJIRA_JIRA_TOKEN`
- `LEADJIRA_DEFAULT_JQL`
- `LEADJIRA_TARGET_STATUS`
- `LEADJIRA_TIMEZONE`
- `LEADJIRA_MAX_RESULTS`
- `LEADJIRA_STORY_POINTS_FIELD`
- `LEADJIRA_LOOKBACK_HOURS`
- `LEADJIRA_WORKDAY_START_HOUR`
- `LEADJIRA_HOST`
- `LEADJIRA_PORT`

По умолчанию приложение использует мок-ответы из [leadjira/mock_data.py](/Users/nikita/LeadJiraHelper/leadjira/mock_data.py).

## Подключение реальной Jira

Пример:

```bash
export LEADJIRA_SOURCE=jira
export LEADJIRA_JIRA_URL="https://your-jira.example.com"
export LEADJIRA_JIRA_TOKEN="your-token"
export LEADJIRA_DEFAULT_JQL='project = CORE ORDER BY updated DESC'
export LEADJIRA_LOOKBACK_HOURS=12
export LEADJIRA_WORKDAY_START_HOUR=9
python3 main.py
```

В режиме `jira` приложение использует библиотеку `jira`, создает клиент через `JIRA(options=..., token_auth=...)`, добавляет к JQL динамическое 12-часовое окно по выбранной дате и строит таймлайн по истории переходов статусов.
