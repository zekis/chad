import json
from datetime import date, timedelta
import config
from bots.langchain_credential_manager import GetCredentials, GetCredential, CreateCredential, UpdateCredential, DeleteCredential
from common.utils import create_email
#from bots.loaders.outlook import get_email_summary


if __name__ == "__main__":

    config.USER_ID = "test"
    config.DATA_DIR = "data"
    
    test_get_all = GetCredentials()
    test_get = GetCredential()
    test_create = CreateCredential()
    test_update = UpdateCredential()
    test_delete = DeleteCredential()


    
    


    print("Create Credential Test")
    response = test_create._run('test_cred', '{"id": "12345", "key": "skdf94367}')
    print(response)

    print("Testing Get")
    response = test_get._run('test_cred')
    print(response)

    
    print("Update Test")
    response = test_update._run('test_cred', '{"id": "abcde", "key": "1234565}')
    print(response)

    print("Testing Get")
    response = test_get._run('test_cred')
    print(response)

    print("Delete Test")
    response = test_delete._run('test_cred')
    print(response)

    print("Get All Test")
    response = test_get_all._run()
    print(response)