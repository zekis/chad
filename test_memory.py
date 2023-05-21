import json
from bots.langchain_browser import WebBot
from bots.langchain_memory import MemoryBotRetrieveAll, MemoryBotSearch, MemoryBotStore, MemoryBotDelete, MemoryBotUpdate

if __name__ == "__main__":
    
    test_store = MemoryBotStore()
    test_retrieve = MemoryBotRetrieveAll()
    test_search = MemoryBotSearch()
    test_delete = MemoryBotDelete()
    test_update = MemoryBotUpdate()

    print("Retrieve Test")
    response = test_retrieve('test')
    print(response)

    
    print("Store Test")
    response = test_store._run(value_name="name", value_type="string", value="Zeke Tierney")
    print(response)

    print("Store Test 2")
    response = test_store._run(value_name="temperature", value_type="int", value="24.0")
    print(response)

    print("Retrieve Test")
    response = test_retrieve._run()
    print(response)

    print("Search Test")
    response = test_search._run(value_name="name")
    print(response)

    print("Delete Test")
    response = test_delete._run(value_name="name")
    print(response)

    print("Search Test")
    response = test_search._run(value_name="name")
    print(response)

    print("Update Test")
    response = test_update._run(value_name="temperature", value_type="int", value="22.0")
    print(response)

    print("Retrieve Test")
    response = test_retrieve._run()
    print(response)

    print("Delete Test")
    response = test_delete._run(value_name="temperature")
    print(response)