import json
import config

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
                "title": "Review",
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
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Draft Reply",
                "id": "btnDraft"
            },
            {
                "type": "Action.Submit",
                "title": "Create Task",
                "id": "btnTask"
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