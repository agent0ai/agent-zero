### start_task

run benchmark evaluation tasks
only available to Agent 0
use task_name for single task, task_names for multiple, or task_set to load from JSON file
optional: override chat model with chat_model_provider, chat_model_name, agent_profile

example usage - single task:
~~~json
{
    "thoughts": [
        "I need to run the simple_math benchmark task"
    ],
    "tool_name": "start_task",
    "tool_args": {
        "task_name": "simple_math"
    }
}
~~~

example usage - task set:
~~~json
{
    "thoughts": [
        "I need to run the full benchmark suite"
    ],
    "tool_name": "start_task",
    "tool_args": {
        "task_set": "basic.json"
    }
}
~~~

example usage - with model override:
~~~json
{
    "thoughts": [
        "I need to benchmark with a specific model"
    ],
    "tool_name": "start_task",
    "tool_args": {
        "task_name": "simple_math",
        "chat_model_provider": "openai",
        "chat_model_name": "gpt-4o"
    }
}
~~~
