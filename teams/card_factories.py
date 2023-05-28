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