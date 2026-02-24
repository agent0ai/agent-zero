## Health log tools (deterministic – use these, never fabricate):
Workdir defaults to settings.workdir_path (e.g. /a0/usr/workdir). Pass workdir to override.

### health_log_archive
Copy Today.md → health_log_archives/Health Log YYYYMMDD.md. Optionally backup Today.md first.
~~~json
{
    "tool_name": "health_log_archive",
    "tool_args": {
        "workdir": "",
        "date_yyyymmdd": "20260224",
        "backup": true
    }
}
~~~

### health_log_supplement_list
Read Supplements.md, format as section 08 (Day Pack / Night Pack / Other). Returns ready-to-insert markdown.
~~~json
{
    "tool_name": "health_log_supplement_list",
    "tool_args": {
        "workdir": ""
    }
}
~~~

### health_log_macro_lookup
Look up item in MacrosAndRecipes.md. Returns kcal | P C F or "Did you mean?" list. Never invent macros.
~~~json
{
    "tool_name": "health_log_macro_lookup",
    "tool_args": {
        "workdir": "",
        "item_name": "Post Workout Shake",
        "serving_size": ""
    }
}
~~~

### health_log_energy_delta
Parse archives + Today.md, compute Today's Delta, 7-Day Avg/Delta, 14-Day Avg/Delta. Returns formatted section 05.
~~~json
{
    "tool_name": "health_log_energy_delta",
    "tool_args": {
        "workdir": ""
    }
}
~~~

### health_log_new_day
Initialize Today.md with template for new day. Sets header, Cycle Day, location, next measure.
~~~json
{
    "tool_name": "health_log_new_day",
    "tool_args": {
        "workdir": "",
        "date_yyyymmdd": "20260224",
        "cycle_day": "61",
        "location": "On the boat, Ashdod",
        "next_measure": "2026-02-25"
    }
}
~~~

### health_log_section_write
Replace section 0–11 in Today.md. Section numbers: 0=Header, 1=Sleep, 2=Morning Notes, 3=Nutrition, 4=Macros Total, 5=Energy Delta, 6=Exercise, 7=Activity Summary, 8=Supplements, 9=Notes, 10=Monitoring, 11=Day Closure.
~~~json
{
    "tool_name": "health_log_section_write",
    "tool_args": {
        "workdir": "",
        "section_number": 6,
        "content": "## Exercise\n**Terunofuji-style Supersets:**\n- 5x12 Smith Bench @80kg\n- 10m Sauna @100°C"
    }
}
~~~

### health_log_routine_build
Build Today's Routine.md from a named routine (e.g. Taihō, Hakuhō, Terunofuji) or freestyle (routine_name empty). Populates fillable table with exercises and latest weights from Exercise Progression.
~~~json
{
    "tool_name": "health_log_routine_build",
    "tool_args": {
        "workdir": "",
        "routine_name": "Terunofuji",
        "date_yyyymmdd": "20260224",
        "session_notes": ""
    }
}
~~~

### health_log_workout_submit
Parse filled workout table, append completed rows to Exercise Progression, write section 06 in Today.md. Use filled_table_content (markdown table) or use_todays_routine_file=true to read from Today's Routine.md.
~~~json
{
    "tool_name": "health_log_workout_submit",
    "tool_args": {
        "workdir": "",
        "filled_table_content": "| Incline DB press | 5 | ~12 | 32 kg each | 12/11/12 | Done |",
        "date_yyyymmdd": "20260224",
        "routine_label": "Terunofuji-style",
        "use_todays_routine_file": false
    }
}
~~~

### health_log_exercise_append
Append a single exercise row to Exercise Progression table. Use when recording one-off exercises not from a routine.
~~~json
{
    "tool_name": "health_log_exercise_append",
    "tool_args": {
        "workdir": "",
        "exercise_name": "Incline DB press",
        "date_yyyymmdd": "20260224",
        "sets": "5",
        "reps": "~12",
        "weight": "32 kg each",
        "notes": "Superset with rows"
    }
}
~~~
