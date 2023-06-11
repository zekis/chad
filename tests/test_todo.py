import json
from datetime import date, timedelta
from bots.loaders.todo import MSGetTaskFolders, MSGetTasks, MSSetTaskComplete, MSCreateTask, MSUpdateTask, MSDeleteTask, MSGetTaskDetail
import config


#from bots.loaders.outlook import get_email_summary


if __name__ == "__main__":
    
    
    print("Test 1")
    test_folder_list = MSGetTaskFolders()
    response = test_folder_list._run("NVM")
    print(response)

    print("Test 2")
    test_get_tasks = MSGetTasks()
    response = test_get_tasks._run(config.Todo_BotsTaskFolder)
    print(response)

    print("Test 3")
    tomorrow = date.today() + timedelta(days=1)
    test_create_task = MSCreateTask()
    task = test_create_task._run(config.Todo_BotsTaskFolder, "Test Task", date.today(), tomorrow,"This is a test task")
    print(task)
    
    print("Test 4")
    test_get_task = MSGetTaskDetail()
    response = test_get_task._run(task)
    print(response)

    print("Test 5")
    next_week = date.today() + timedelta(days=7)
    test_update_task = MSUpdateTask()
    response = test_update_task._run(task, "Test Task 5", next_week, tomorrow, "Updated")
    
    print("Test 6")
    test_get_task = MSGetTaskDetail()
    response = test_get_task._run(task)
    print(response)

    print("Test 7")
    test_delete_task = MSDeleteTask()
    response = test_delete_task._run(task)
    print(response)

    print("Test 8")
    test_get_task = MSGetTaskDetail()
    response = test_get_task._run(task)
    print(response)
