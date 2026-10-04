# TextLab — анализ текста через очередь

Учебный проект для лабораторных 5–8. Nginx обслуживает frontend и проксирует API в Flask/Gunicorn (WSGI).
Backend сохраняет задачи в SQLite на общем томе. Отдельный worker атомарно забирает задачи,
подсчитывает Unicode-слова и сохраняет результат. Backend сам анализ не выполняет.
Опрос очереди каждые 0,5 секунды. Простая очередь на SQLite подходит для учебного стенда;
она не заявляется как решение для распределённого production-кластера.

## Запуск

Из корня этого проекта, при установленном Docker Desktop в режиме Linux containers:

```sh
docker compose up --build
```

Открыть http://localhost:8080. Единственный опубликованный порт основного приложения — Nginx.
Backend и worker общаются через том jobs и внутреннюю сеть Compose.
Проверить полный путь обработки: `python tools/smoke.py`.
Остановить: `docker compose down`. Том с задачами сохраняется.

## Локальная проверка без Docker

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=textlab --cov-report=term-missing
python -m build
bandit -r textlab -ll
pip-audit -r requirements.txt
```

API: POST /api/jobs с JSON `{"text":"…"}` возвращает 202 и id;
GET /api/jobs/{id} возвращает queued/running/done/failed и результат;
GET /metrics публикует textlab_jobs_submitted_total и textlab_jobs{status}.
Счётчик заданий сохраняется между перезапусками и монотонен, пока сохраняется БД.
Текст ограничен 200000 символов и 1 МБ на HTTP-запрос. SQL использует параметры.
Пользовательский текст не пишется в логи и не вставляется в HTML.

## CI и мониторинг

Workflow нужно разместить именно в `.github/workflows/` в корне личного репозитория.
CI собирает пакет, запускает тесты, собирает контейнеры и выполняет HTTP smoke.
Secure CI выполняет тесты, Bandit, Gitleaks и pip-audit; ошибки проверок блокируют job.
Проверки уязвимостей зависят от актуальной базы и могут потребовать обновления зависимостей.

Мониторинг: `docker compose -f compose.yaml -f compose.monitoring.yaml up --build`.
Grafana доступна на http://localhost:3000, готовый dashboard TextLab содержит счётчик,
скорость поступления заданий, статусы очереди и логи API/worker.
Prometheus хранит метрики; Loki хранит логи; Alloy читает контейнерные логи.
Гостевой просмотр Grafana включён только для локального учебного стенда.

## Ограничения проверки

См. ../VALIDATION.md: локальные тесты не заменяют реальный запуск Compose и Actions.
Не прикладывайте вымышленные скриншоты или результаты незапущенного CI.
