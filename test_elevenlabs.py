import json
from elevenlabs import generate, play, set_api_key
import config

if __name__ == "__main__":
    set_api_key(config.ELEVENLABS_API_KEY)
    audio = generate(
    text="Hi! My name is Bella, nice to meet you!",
    voice="Bella",
    model="eleven_monolingual_v1"
    )

    play(audio)