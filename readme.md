<H1>Description</H1>

Combines Langchain and MS Teams BOT to allow chatting with openAI in Teams 


<H1>Windows Install Instructions</H1>

Prerequisites, 
NGROK 
You will need to create an account at ngrok.com
installe the windows version using Choco and forwarding port 3978.
```
ngrok http --host-header=rewrite 3978
```


Check out this repo

Right click on folder and open with visual code

Click on requirements.txt

Click create environment

Create API keys for Google Search, Open AI and MS Azure Bot and add to env.example

Rename env.example to .env

To setup the bot in teams see https://github.com/microsoft/botbuilder-python


<h1>Run</h1>

Run with python ./app.py