# the os module helps us access environment variables
# i.e., our API keys
import os

# these modules are for querying the Hugging Face model
import json
import requests

# the Discord Python API
import discord

# this is my Hugging Face profile link
API_URL = 'https://api-inference.huggingface.co/models/peachteaboba/'

class MyClient(discord.Client):
    def __init__(self, model_name):
        # adding intents module to prevent intents error in __init__ method in newer versions of Discord.py
        intents = discord.Intents.default() # Select all the intents in your bot settings as it's easier
        intents.message_content = True
        super().__init__(intents=intents)
        self.api_endpoint = API_URL + model_name
        # retrieve the secret API token from the system environment
        huggingface_token = os.environ['HUGGINGFACE_TOKEN']
        # format the header in our request to Hugging Face
        self.request_headers = {
            'Authorization': 'Bearer {}'.format(huggingface_token)
        }
      # Load structured prompts from the text file
        self.structured_prompts = self.load_structured_prompts('Prompts.txt')

    def load_structured_prompts(self, filepath):
        structured_prompts = {}
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith("User:"):
                    current_prompt = line[len("User:"):].strip().lower()
                elif line.startswith("Bot:") and current_prompt:
                    responses = [resp.strip() for resp in line[len("Bot:"):].split('|')]
                    structured_prompts[current_prompt] = responses
        return structured_prompts
      

    def query(self, payload):
        """
        make request to the Hugging Face model API
        """
        data = json.dumps(payload)
        response = requests.request('POST',
                                    self.api_endpoint,
                                    headers=self.request_headers,
                                    data=data)
        ret = json.loads(response.content.decode('utf-8'))
        return ret

    async def on_ready(self):
        # print out information when the bot wakes up
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        # send a request to the model without caring about the response
        # just so that the model wakes up and starts loading
        self.query({'inputs': {'text': 'Hello!'}})

    async def on_message(self, message):
        """
        this function is called whenever the bot sees a message in a channel
        """
        # ignore the message if it comes from the bot itself
        if message.author.id == self.user.id:
            return
        # Check for a structured prompt match
        user_msg_lower = message.content.lower()
        if user_msg_lower in self.structured_prompts:
            responses = self.structured_prompts[user_msg_lower]
            await message.channel.send(random.choice(responses))
            return

        # form query payload with the content of the message
        payload = {'inputs': {'text': message.content}}

        # while the bot is waiting on a response from the model
        # set the its status as typing for user-friendliness
        async with message.channel.typing():
          response = self.query(payload)
          bot_response = response.get('generated_text', None)
          if not bot_response:
            if 'error' in response:
                # Custom message for loading
                bot_response = "Hold on darling, I'm loading. Can you repeat that for me in a few seconds?"
            
        # send the model's response to the Discord channel
        await message.channel.send(bot_response)

def main():
    # DialoGPT-medium-joshua is my model name
    client = MyClient('newastarionbot')
    client.run(os.environ['DISCORD_TOKEN'])

if __name__ == '__main__':
  main()
