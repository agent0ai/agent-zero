import uuid
from python.helpers.tool import Tool, Response

class TodoTool(Tool):

    def __init__(self, agent, name, method, args, message, **kwargs):
        super().__init__(agent, name, method, args, message, **kwargs)
        if not self.agent.get_data("todo_list"):
            self.agent.set_data("todo_list", [])

    async def execute(self, **kwargs) -> Response:
        if self.method == "add":
            return self._add(**kwargs)
        elif self.method == "update":
            return self._update(**kwargs)
        elif self.method == "list":
            return self._list()
        elif self.method == "next":
            return self._next()
        else:
            return Response(message=f"Unknown method '{self.method}' for tool 'todo'", break_loop=False)

    def _add(self, task: str) -> Response:
        todo_list = self.agent.get_data("todo_list")
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "description": task,
            "status": "todo"
        }
        todo_list.append(new_task)
        self.agent.set_data("todo_list", todo_list)
        return Response(message=f"Task added with ID: {new_task['id']}", break_loop=False)

    def _update(self, task_id: str, status: str) -> Response:
        if status not in ["todo", "in_progress", "done"]:
            return Response(message="Invalid status. Must be one of: todo, in_progress, done", break_loop=False)

        todo_list = self.agent.get_data("todo_list")
        for task in todo_list:
            if task["id"] == task_id:
                task["status"] = status
                self.agent.set_data("todo_list", todo_list)
                return Response(message=f"Task {task_id} updated to '{status}'", break_loop=False)

        return Response(message=f"Task with ID {task_id} not found", break_loop=False)

    def _list(self) -> Response:
        todo_list = self.agent.get_data("todo_list")
        if not todo_list:
            return Response(message="The to-do list is empty.", break_loop=False)

        response_message = "To-Do List:\n"
        for task in todo_list:
            response_message += f"- [ID: {task['id']}] {task['description']} ({task['status']})\n"

        return Response(message=response_message, break_loop=False)

    def _next(self) -> Response:
        todo_list = self.agent.get_data("todo_list")
        for task in todo_list:
            if task["status"] == "todo":
                return Response(message=f"Next task: [ID: {task['id']}] {task['description']}", break_loop=False)

        return Response(message="No pending tasks in the to-do list.", break_loop=False)
