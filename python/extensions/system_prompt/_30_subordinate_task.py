from typing import Any
from python.helpers.extension import Extension
from agent import Agent, LoopData


class SubordinateTask(Extension):

    async def execute(self, system_prompt: list[str] = [], loop_data: LoopData = LoopData(), **kwargs: Any):
        task_details = self.agent.get_data("task_details")
        if task_details:
            prompt = self.format_task_details(task_details)
            system_prompt.append(prompt)

    def format_task_details(self, task_details: dict) -> str:
        prompt = "You have been assigned the following task by your superior:\n\n"

        if task_details.get("parent_task"):
            prompt += f"The main task is: {task_details['parent_task']}\n"

        prompt += f"Your task is: {task_details['task']}\n\n"

        if task_details.get("objectives"):
            prompt += "Objectives:\n"
            for objective in task_details["objectives"]:
                prompt += f"- {objective}\n"
            prompt += "\n"

        if task_details.get("context"):
            prompt += f"Context: {task_details['context']}\n\n"

        if task_details.get("scopes"):
            prompt += "In scope:\n"
            for scope in task_details["scopes"]:
                prompt += f"- {scope}\n"
            prompt += "\n"

        if task_details.get("non_goals"):
            prompt += "Out of scope:\n"
            for non_goal in task_details["non_goals"]:
                prompt += f"- {non_goal}\n"
            prompt += "\n"

        if task_details.get("success_criteria"):
            prompt += "Success criteria:\n"
            for criteria in task_details["success_criteria"]:
                prompt += f"- {criteria}\n"
            prompt += "\n"

        if task_details.get("errors_to_avoid"):
            prompt += "Errors to avoid:\n"
            for error in task_details["errors_to_avoid"]:
                prompt += f"- {error}\n"
            prompt += "\n"

        return prompt
