import json
import config
import markdownify


def create_list_card(message,strings_values):
    cards = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "TextBlock",
                "size": "medium",
                "weight": "Bolder",
                "horizontalAlignment": "Left",
                "text": message
            },
            {
                "type": "Input.ChoiceSet",
                "id": "acDecision",
                "value": "1",
                "wrap": True,
                "choices": [],
                "style": "expanded"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Summarise",
                "id": "btnSummary"
            },
            {
                "type": "Action.Submit",
                "title": "Read Aloud",
                "id": "btnReadAloud",
                "data": {
                    "create_tts": f"{message}"
                }
            }
        ]
    }

    for index, (title, value) in enumerate(strings_values):
        cards["body"][1]["choices"].append({
            "title": title,
            "value": value
        })

    return json.dumps(cards)


def create_email_card(message,email, summary):
    cards = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "Bolder",
                        "horizontalAlignment": "Left",
                        "text": message
                    },
                    {
                        "type": "TextBlock",
                        "text": email.sender.address,
                        "weight": "bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": email.received.strftime('%Y-%m-%d %H:%M'),
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": summary,
                        "wrap": True
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Importance",
                                "value": email.importance.value
                            },
                            {
                                "title": "Is Read",
                                "value": email.is_read
                            },
                            {
                                "title": "Has Attachment",
                                "value": email.has_attachments
                            }
                        ]
                    },
                    {
                        "type": "Input.Text",
                        "id": "suggestions",
                        "placeholder": "Help direct the AI by making suggestions",
                        "label": "Suggestions"
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Draft Reply Email",
                "data": {
                    "acDecision": f"Please use the DRAFT_REPLY_TO_EMAIL tool using ConverstationID: {email.conversation_id} to draft a response"
                }
            },
            {
                "type": "Action.Submit",
                "title": "Draft Forward Email",
                "data": {
                    "acDecision": f"Please use the DRAFT_FORWARD_TO_EMAIL tool using ConverstationID: {email.conversation_id} to draft a response"
                }
                
            },
            {
                "type": "Action.Submit",
                "title": "Create Task",
                "data": {
                    "acDecision": f"Please use the TASK_MANAGER tool to create an action for me to do based on the email following summary: {summary}"
                }
                
            },
            {
                "type": "Action.Submit",
                "title": "Read Aloud",
                "id": "btnReadAloud",
                "data": {
                    "create_tts": f"{message}"
                }
            }

            
        ]
    }

    return json.dumps(cards)

def create_draft_email_card(message,email,response):

    # Convert the list of recipients to a string
    recipients = ', '.join([recipient.address for recipient in email.to])
    response_md = h = markdownify.markdownify(response, heading_style="ATX")

    cards = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "Bolder",
                        "horizontalAlignment": "Left",
                        "text": message
                    },
                    {
                        "type": "TextBlock",
                        "text": recipients,
                        "weight": "bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": email.subject,
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": response_md,
                        "wrap": True
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Importance",
                                "value": email.importance.value
                            },
                            {
                                "title": "Has Attachment",
                                "value": email.has_attachments
                            }
                        ]
                    },
                    {
                        "type": "Input.Text",
                        "id": "suggestions",
                        "placeholder": "Please suggest any changes",
                        "label": "Suggestions"
                    }

                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Send",
                "data": {
                    "acDecision": f"Please send an email using the SEND_EMAIL tool to: {recipients}, subject: {email.subject}, body: {response}"
                },
                "associatedInputs": "None"
            },
            {
                "type": "Action.Submit",
                "title": "Modify",
                "data": {
                    "acDecision": f"Please use the DRAFT_EMAIL tool using ConverstationID: {email.conversation_id} to create a new draft based on the current draft: {response}"
                }
            },
            {
                "type": "Action.Submit",
                "title": "Read Aloud",
                "id": "btnReadAloud",
                "data": {
                    "create_tts": f"{message}"
                }
            }
            
        ]
    }

    return json.dumps(cards)


def create_draft_reply_email_card(message,email,response):

    # Convert the list of recipients to a string
    recipients = ', '.join([recipient.address for recipient in email.to])
    response_md = h = markdownify.markdownify(response, heading_style="ATX")

    cards = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "Bolder",
                        "horizontalAlignment": "Left",
                        "text": message
                    },
                    {
                        "type": "TextBlock",
                        "text": recipients,
                        "weight": "bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": email.subject,
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": response_md,
                        "wrap": True
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Importance",
                                "value": email.importance.value
                            },
                            {
                                "title": "Has Attachment",
                                "value": email.has_attachments
                            }
                        ]
                    },
                    {
                        "type": "Input.Text",
                        "id": "suggestions",
                        "placeholder": "Please suggest any changes",
                        "label": "Suggestions"
                    }

                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Send",
                "data": {
                    "acDecision": f"Please send an email using the REPLY_TO_EMAIL tool using ConversationID: {email.conversation_id} with Body: {response}"
                },
                "associatedInputs": "None"
            },
            {
                "type": "Action.Submit",
                "title": "Modify",
                "data": {
                    "acDecision": f"Please use the DRAFT_REPLY_TO_EMAIL tool using ConverstationID: {email.conversation_id} to create a new draft based on the current draft: {response}"
                }
            },
            {
                "type": "Action.Submit",
                "title": "Read Aloud",
                "data": {
                    "create_tts": f"{message}"
                }
                
            }
            
        ]
    }

    return json.dumps(cards)

def create_draft_forward_email_card(message,email,response):

    # Convert the list of recipients to a string
    recipients = ', '.join([recipient.address for recipient in email.to])
    response_md = h = markdownify.markdownify(response, heading_style="ATX")

    cards = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "Bolder",
                        "horizontalAlignment": "Left",
                        "text": message
                    },
                    {
                        "type": "TextBlock",
                        "text": recipients,
                        "weight": "bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": email.subject,
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": response_md,
                        "wrap": True
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Importance",
                                "value": email.importance.value
                            },
                            {
                                "title": "Has Attachment",
                                "value": email.has_attachments
                            }
                        ]
                    },
                    {
                        "type": "Input.Text",
                        "id": "suggestions",
                        "placeholder": "Please suggest any changes",
                        "label": "Suggestions"
                    }

                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Send",
                "data": {
                    "acDecision": f"Please send an email using the FORWARD_TO_EMAIL tool using ConversationID: {email.conversation_id} to: {recipients}, with Body: {response}"
                },
                "associatedInputs": "None"
            },
            {
                "type": "Action.Submit",
                "title": "Modify",
                "data": {
                    "acDecision": f"Please use the DRAFT_FORWARD_TO_EMAIL tool using ConverstationID: {email.conversation_id} to create a new draft based on the current draft: {response}"
                }
            },
            {
                "type": "Action.Submit",
                "title": "Read Aloud",
                "id": "btnReadAloud",
                "data": {
                    "create_tts": f"{message}"
                }
            }
            
        ]
    }

    return json.dumps(cards)

def create_event_card(message,event):
    cards = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "Bolder",
                        "horizontalAlignment": "Left",
                        "text": message
                    },
                    {
                        "type": "TextBlock",
                        "text": event.subject,
                        "weight": "bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": event.start.strftime('%Y-%m-%d %H:%M'),
                        "isSubtle": True,
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": event.location.get('displayName'),
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            }
            
        ]
    }

    return json.dumps(cards)

def create_media_card(message, url):
    cards = {
        "type": "AdaptiveCard",
        "version": "1.6",
        "fallbackText": "This card requires CaptionSource to be viewed. Ask your platform to update to Adaptive Cards v1.6 for this and more!",
        "body": [
            {
                "type": "TextBlock",
                "text": "Text To Speech"
            },
            {
                "type": "",
                "url": url
            }
        ]
    }
    return cards


        #     created = {task.created}
    #     modified = {task.modified}
    #     importance = {task.importance}
    #     is_starred = {task.is_starred}
    #     due = {task.due}
    #     completed = {task.completed}
    #     description = {task.body}
    # """

def create_todo_card(message,event):
    cards = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "size": "medium",
                        "weight": "Bolder",
                        "horizontalAlignment": "Left",
                        "text": message
                    },
                    {
                        "type": "TextBlock",
                        "text": event.subject,
                        "weight": "bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": f"Due {event.due_date.strftime('%Y-%m-%d %H:%M')}",
                        "isSubtle": True,
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": f"Importance: {event.importance}",
                        "isSubtle": True,
                        "wrap": True
                    }
                    ,
                    {
                        "type": "TextBlock",
                        "spacing": "none",
                        "text": f"Completed {event.importance}",
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            }
            
        ]
    }

    return json.dumps(cards)

def create_input_card(intro, parameters):
    # Begin creating card body with initial text block
    card_body = [
        {
            "type": "TextBlock",
            "text": intro
        }
    ]

    # Loop through parameters and create input fields for each
    for param in parameters:
        card_body.append(
            {
                "type": "TextBlock",
                "text": param['label']
            }
        )
        
        input_field = {
            "type": "Input.Text",
            "id": param['id'],
            "placeholder": param.get('placeholder', "Enter value"),
            "maxLength": param.get('maxLength', 500)
        }
        
        # Add multiline if specified
        if param.get('isMultiline', False):
            input_field["isMultiline"] = True
        
        # Add pre-filled value if specified
        if 'value' in param:
            input_field["value"] = param['value']

        # Append the input field to the card body
        card_body.append(input_field)

    # Create card with body and submit action
    card = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": card_body,
        "actions": [
            {
                "type": "Action.Submit",
                "title": "OK"
            }
        ]
    }

    return json.dumps(card)
