import traceback
import config
import pika

from common.card_factories import (
    create_draft_email_card, 
    create_draft_forward_email_card, 
    create_draft_reply_email_card, 
    create_email_card, 
    create_event_card, 
    create_list_card, 
    create_media_card
)

from common.utils import encode_message, decode_message, encode_response, decode_response

from botbuilder.schema import (
    ActionTypes,
    CardImage,
    CardAction
)

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
    print(message)
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
    print(message)
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
    
    message = encode_message("cards", message, cards)
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