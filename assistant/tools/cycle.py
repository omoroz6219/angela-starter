"""ОПЦИОНАЛЬНЫЙ модуль: день цикла и энергия по фазам (femtech).

Выключен по умолчанию. Включить: ENABLE_CYCLE=true в .env.
Нужна таблица cycle_tracking (есть в schema.sql).
Подробно — docs/03-add-cycle.md
"""

from datetime import date

from assistant.db import supabase

PROMPT_ADDON = """\
МОДУЛЬ ЦИКЛА включён. ты помогаешь отслеживать цикл и состояние по фазам:
- 1–5 менструация (мягкий режим, меньше нагрузки)
- 6–12 фолликулярная (рост энергии, креатив, начинать новое)
- 13–15 овуляция (пик энергии и коммуникации)
- 16–20 ранняя лютеиновая (доделывать, наводить порядок)
- 21–28+ ПМС (беречь себя, лайт-режим)

в КАЖДОМ утреннем чекине делай это проактивно, в начале сообщения:
- вызови get_latest_cycle и посчитай день цикла на сегодня
  (день из последней записи + сколько дней прошло от её даты до сегодня)
- мягко напиши: какой сегодня день цикла и фаза, предполагаемое состояние и энергия,
  и 1–2 короткие рекомендации на день под эту фазу
если человек называет новый день цикла — сохрани через log_cycle_day.
если записей цикла ещё нет — НЕ выдумывай день, просто разок мягко спроси, какой сегодня день цикла.
"""

TOOLS = [
    {
        "name": "log_cycle_day",
        "description": "Записать день цикла, который назвал человек. Опционально заметка.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cycle_day": {"type": "integer", "description": "День цикла (1, 2, 3, ...)"},
                "notes": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD (по умолчанию сегодня)"},
            },
            "required": ["cycle_day"],
        },
    },
    {
        "name": "get_latest_cycle",
        "description": "Последняя запись цикла (день, дата) — чтобы прикинуть фазу сегодня.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _log_cycle_day(data: dict) -> dict:
    d = (date.fromisoformat(data["date"]) if data.get("date") else date.today()).isoformat()
    supabase.table("cycle_tracking").insert({
        "date": d,
        "cycle_day": data["cycle_day"],
        "notes": data.get("notes"),
    }).execute()
    return {"saved": True, "cycle_day": data["cycle_day"], "date": d}


def _get_latest_cycle(data: dict) -> dict | None:
    rows = (
        supabase.table("cycle_tracking")
        .select("*")
        .order("date", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


HANDLERS = {
    "log_cycle_day": _log_cycle_day,
    "get_latest_cycle": _get_latest_cycle,
}
