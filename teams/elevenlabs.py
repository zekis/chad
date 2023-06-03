"""ElevenLabs speech module"""
import os
import requests
import config



def speech(filename: str, text: str, voice_index: int = "Rachel") -> bool:
   
    voice_options = {
        "Rachel": "21m00Tcm4TlvDq8ikWAM",
        "Domi": "AZnzlk1XvdvUeBnXmlld",
        "Bella": "EXAVITQu4vr4xnSDxMaL",
        "Antoni": "ErXwobaYiN019PkySvjV",
        "Elli": "MF3mGyEYCl7XYWbV9V6O",
        "Josh": "TxGEqnHWrfWFTfGW9XjX",
        "Arnold": "VR6AewLTigWG4xSOukaG",
        "Adam": "pNInz6obpgDQGcFmaJgB",
        "Sam": "yoZ06aMxZJJ28mfd3POQ",
    }
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": config.ELEVENLABS_API_KEY,
    }

    tts_url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_options[voice_index]}"
    )
    response = requests.post(tts_url, headers=headers, json={"text": text})

    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        #playsound("speech.mpeg", True)
        #os.remove("speech.mpeg")
        return True
    else:
        print("Request failed with status code:", response.status_code)
        print("Response content:", response.content)
        return False


