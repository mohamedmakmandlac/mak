import os
import json
from datetime import datetime

TASK_FILE = "tasks.json"

class Task:
    def __init__(self, title, completed=False, created_at=None):
        self.title = title
        self.completed = completed
        self.created_at = created_at if created_at else datetime.now().isoformat()


    @staticmethod
    def from_dict(data):
        return Task(data['title'], data['completed'], data['created_at'])

class ToDoList:
    def __init__(self):
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(TASK_FILE):
            with open(TASK_FILE, 'r') as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(d) for d in data]

    def save_tasks(self):
        with open(TASK_FILE, 'w') as f:
            json.dump([t.to_dict() for t in self.tasks], f, indent=4)

    def add_task(self, title):
        task = Task(title)
        self.tasks.append(task)
        self.save_tasks()

    def list_tasks(self):
        if not self.tasks:
            print("\nNo tasks found.")
            return
        for idx, task in enumerate(self.tasks):
            status = "✅" if task.completed else "❌"
            print(f"{idx + 1}. [{status}] {task.title} (Created: {task.created_at})")

    def complete_task(self, task_num):
        if 1 <= task_num <= len(self.tasks):
            self.tasks[task_num - 1].mark_complete()
            self.save_tasks()
            print("Task marked as complete.")
        else:
            print("Invalid task number.")

    def delete_task(self, task_num):
        if 1 <= task_num <= len(self.tasks):
            del self.tasks[task_num - 1]
            self.save_tasks()
            print("Task deleted.")
        else:
            print("Invalid task number.")

def main_menu():
    todo = ToDoList()
    while True:
        print("\n========= To-Do List Menu =========")
        print("1. Add Task")
        print("2. View Tasks")
        print("3. Complete Task")
        print("4. Delete Task")
        print("5. Exit")
        print("===================================")
        choice = input("Enter your choice (1-5): ")

        if choice == "1":
            title = input("Enter task title: ")
            todo.add_task(title)
        elif choice == "2":
            todo.list_tasks()
        elif choice == "3":
            todo.list_tasks()
            try:
                num = int(input("Enter task number to mark complete: "))
                todo.complete_task(num)
            except ValueError:
                print("Invalid input.")
        elif choice == "4":
            todo.list_tasks()
            try:
                num = int(input("Enter task number to delete: "))
                todo.delete_task(num)
            except ValueError:
                print("Invalid input.")
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
