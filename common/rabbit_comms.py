import traceback
import config
import pika
import json
import time 

from common.card_factories import (
    create_draft_email_card, 
    create_draft_forward_email_card, 
    create_draft_reply_email_card, 
    create_email_card, 
    create_event_card, 
    create_list_card,
    create_folder_list_card, 
    create_media_card,
    create_todo_card,
    create_input_card
)

#from common.utils import encode_message, decode_message, encode_response, decode_response

from botbuilder.schema import (
    ActionTypes,
    CardImage,
    CardAction
)

def encode_response(prompt):
    #actions = [action.__dict__ for action in actions] if actions else []
    response = {
        "prompt": prompt
    }
    #print(f"ENCODING: {response}")
    return json.dumps(response)

def decode_response(response):
    try:
        response = response.decode("utf-8")
        #print(f"DECODING: {response}")
        response_dict = json.loads(response)
        prompt = response_dict.get('prompt')
        
        #actions = [CardAction(**action) for action in actions_data] if actions_data else []
        return prompt
    except Exception as e:
        traceback.print_exc()
        return "prompt", f"error: {e}", None

def encode_message(user_id, type, prompt, actions=None):
    #actions = [action.__dict__ for action in actions] if actions else []
    message = {
        "user_id": user_id,
        "type": type,
        "prompt": prompt,
        "actions": actions
    }
    #print(f"ENCODING: {message}")
    return json.dumps(message)

def decode_message(message):
    try:
        message = message.decode("utf-8")
        #print(f"DECODING: {message}")
        message_dict = json.loads(message)

        user_id = message_dict.get('user_id')
        type = message_dict.get('type')
        prompt = message_dict.get('prompt')
        actions = message_dict.get('actions')
        #actions = [CardAction(**action) for action in actions_data] if actions_data else []
        return user_id, type, prompt, actions
    except Exception as e:
        traceback.print_exc()
        return "prompt", f"error: {e}", None
    

def publish(message, override_id=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    if not override_id:
        message = encode_message(config.USER_ID, 'prompt', message)
    else:
        message = encode_message(override_id, 'prompt', message)
    notify_channel = connection.channel()
    notify_channel.basic_publish(exchange='',
                      routing_key='notify',
                      body=message)
    #print(message)
    notify_channel.close()



def publish_action(message, button1, button2, override_id=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    actions = [CardAction(
        type=ActionTypes.im_back,
        title=button1,
        value=button1,
    ),
    CardAction(
        type=ActionTypes.im_back,
        title=button2,
        value=button2,
    )]
    actions = [action.__dict__ for action in actions] if actions else []
    if not override_id:
        message = encode_message(config.USER_ID, 'action', message, actions)
    else:
        message = encode_message(override_id, 'action', message, actions)
    
    notify_channel = connection.channel()
    notify_channel.basic_publish(exchange='',
                      routing_key='notify',
                      body=message)
    #print(message)
    notify_channel.close()

def publish_actions(message, buttons, override_id=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

    actions = [CardAction(
        type=ActionTypes.im_back,
        title=button[0],
        value=button[1],
        mode="secondary"
    ) for button in buttons]

    actions = [action.__dict__ for action in actions] if actions else []

    if not override_id:
        message = encode_message(config.USER_ID, 'action', message, actions)
    else:
        message = encode_message(override_id, 'action', message, actions)

    notify_channel = connection.channel()
    notify_channel.basic_publish(exchange='',
                      routing_key='notify',
                      body=message)
    #print(message)
    notify_channel.close()


def publish_list(message,strings_values):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_list_card(message,strings_values)
        #cards = create_list_card("Choose an option:", [("Option 1", "1"), ("Option 2", "2"), ("Option 3", "3")])
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_folder_list(message,strings_values):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_folder_list_card(message,strings_values)
        #cards = create_list_card("Choose an option:", [("Option 1", "1"), ("Option 2", "2"), ("Option 3", "3")])
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_event_card(message,event):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_event_card(message,event)
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_todo_card(message,task):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_todo_card(message,task)
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)
    
def publish_email_card(message,email,summary):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_email_card(message,email,summary)
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_draft_card(message,email,response, reply=False):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        if reply:
            cards = create_draft_reply_email_card(message,email,response)
        else:
            cards = create_draft_email_card(message,email,response)
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_draft_forward_card(message,email,response):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_draft_forward_email_card(message,email,response)
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_input_card(intro,parameters):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    try:
        card = create_input_card(intro, parameters)
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message(config.USER_ID, "cards", intro, card)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

#Consume bot messages
def consume(override_id=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    message_channel = connection.channel()
    if not override_id:
        message_channel.queue_declare(queue=config.USER_ID)
        method, properties, body = message_channel.basic_get(queue=config.USER_ID, auto_ack=True)
    else:
        message_channel.queue_declare(queue=override_id)
        method, properties, body = message_channel.basic_get(queue=override_id, auto_ack=True)
    message_channel.close()
    if body:
        response = decode_response(body)
        return response
    else:
        return None

#clear bots messages (do this on start)
def clear_queue(id):
    print("Clearing message queue")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    message_channel = connection.channel()
    message_channel.queue_delete(id)
    message_channel.queue_declare(id)

#Send to the bot
def send_to_bot(user_id, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    message_channel = connection.channel()
    message_channel.queue_declare(queue=user_id)
    message = encode_response(message)
    message_channel.basic_publish(exchange='',routing_key=user_id,body=message)


def receive_from_bot():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    method, properties, body = notify_channel.basic_get(queue='notify',auto_ack=True)
    if body:
        user_id, type, body, data = decode_message(body)
        return user_id, type, body, data
    else:
        return None, None,None, None

#callbacks
def get_input(timeout_minutes=1):
    timeout = time.time() + 60*timeout_minutes   # 5 minutes from now
    #print("Insert your text. Press Ctrl-D (or Ctrl-Z on Windows) to end.")
    #contents = []
    while True:
        msg = consume()
        if msg and msg != "":
            question = msg
            break
        if timeout_minutes != 0:
            if time.time() > timeout:
                question = "break"
                break
        time.sleep(0.5)
        #await asyncio.sleep(0.5)
    return question

def send_prompt(query):
        publish(query + "?")
