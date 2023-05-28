import json
from datetime import date, timedelta
from bots.loaders.outlook import MSCreateEmail, MSGetEmailDetail, MSAutoReplyToEmail, MSSearchEmailsId, MSForwardEmail
from bots.utils import create_email
#from bots.loaders.outlook import get_email_summary


if __name__ == "__main__":
    
    test_create = MSCreateEmail()
    test_get_detail = MSGetEmailDetail()
    test_search_id = MSSearchEmailsId()
    test_auto_reply = MSAutoReplyToEmail()
    test_forward = MSForwardEmail()

#     print("Create Test")
#     body = '''<p>Hi Tester,</p>

# <p>This is a test</p>

# <p>Regards, Bot</p>'''

#     response = test_create._run('test.test@gmail.com', 'Test email', body)
#     print(response)

    
    print("Search Test")
    yesterday = date.today() - timedelta(days=1)
    #today = date.today()
    query = f"received:{yesterday.strftime('%d/%m/%Y')}..{date.today().strftime('%d/%m/%Y')}"
    search_response = test_search_id._run(query)
    print(search_response)

    print("Search Test 2")
    query = f"from:Dan AND received:2023-05-19..2023-05-20"
    search_response = test_search_id._run(query, 1)
    print(search_response)
    # print("Get Email Detail Test - Conversation")
    # response = test_get_detail._run(ConversationID='AAQkAGExNDVmN2RjLTg2ZDQtNDU2NC1iNzgyLWNjMzliOTQzMzBkOQAQAO_WUehjE06khrzgbWswqsA=')
    # print(response)
    
    # print("Get Email Detail Test - Object")
    # response = test_get_detail._run(ObjectID='AAMkAGExNDVmN2RjLTg2ZDQtNDU2NC1iNzgyLWNjMzliOTQzMzBkOQBGAAAAAAD-Q3lIfgU4T7wkoEnWWeYlBwAsihHNxVFCTLRbnkIV5qoRAAAAAAEMAAAsihHNxVFCTLRbnkIV5qoRAAUjfSBMAAA=')
    # print(response)

    #for email in search_response:
    #response = test_get_detail._run(ObjectID=search_response['emails']['object_id'])
    #print(response)
    print("Reply Test 1")
    response = test_auto_reply._run(ConversationID = search_response['emails']['conversationid'])
    print(response)


    print("Search Test 3")
    query = f"from:Ian AND received:2023-05-15..2023-05-19"
    search_response = test_search_id._run(query, 1)
    print(search_response)

    print("Reply Test 2")
    response = test_forward._run(ConversationID = search_response['emails']['conversationid'], recipient='test.test@gmail.com', body='test')
    print(response)