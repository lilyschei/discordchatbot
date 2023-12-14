import os
import json
import requests
import discord
import random


# this is my Hugging Face profile link
API_URL = 'https://api-inference.huggingface.co/models/peachteaboba/'
# Choose a name for the bot
bot_name = "AstarionBot"
# Initialize chat_history_ids
chat_history_ids = None

# Storage for conversation history
full_chat_history = []
greetings = [
    "Hello darling",
    "Gods you're beautiful",
    "Yes, darling?",
    "Hello, my sweet, It's always a pleasure to see you sauntering over.",
    "I did miss that face, you know.",
    "Is there something you want to talk about, my dear?",
    "Come to get your afternoon cuddle?"
]

intelligent_responses = [
    "What's your favourite part of our adventure?",
    "So...how do you feel about Gale?",
    "Is there something else you wanted to talk about darling?",
    "Who's your favourite companion?",
    "Tell me I'm beautiful",
    "Why does Wyll always wave his chalice around like that?",
    "That Owlbear is awfully cute, isn't it?",
    "There goes Lae'zel and Shadowheart again, always fighting",
    "I saw Halsin leave for a nature walk, joint in hand",
    "I do like Karlach you know, she's the sweetest",
    "Baby Owlbear or Scratch?",
    "Let's gossip about Gale"
]
trigger_phrases = ["fair enough", "okay", "sounds good", "i see", "got it", "lmao", "lol", "haha", "ok", "sure", "sure thing", "thanks", "thank you", "ty"]


# Shuffle the greetings to randomize the order
random.shuffle(greetings)


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
        self.chat_history = {}  # Dictionary to store chat history for each channel
  
    def update_chat_history(self, user_id, user_message, bot_response=None):
        """
        Update the chat history for a specific user
        """
        if user_id not in self.chat_history:
            self.chat_history[user_id] = []

        self.chat_history[user_id].append((user_message, bot_response))

        # Limit history size
        self.chat_history[user_id] = self.chat_history[user_id][-10:]  # Keep last 10 interactions
    

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
        self.structured_prompts = self.load_structured_prompts('Prompts.txt')

    def load_structured_prompts(self, filepath):
        structured_prompts = {}
        current_prompt = None
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith("User:"):
                    current_prompt = line[len("User:"):].strip().lower()
                elif line.startswith("Bot:") and current_prompt:
                    responses = [resp.strip() for resp in line[len("Bot:"):].split('|')]
                    structured_prompts[current_prompt] = responses
        return structured_prompts
    
    

    async def on_message(self, message):
      # Ignore the message if it comes from the bot itself
      if message.author.id == self.user.id:
          return

      user_id = message.author.id  # Get the user's ID

      # Update chat history with the user's message
      self.update_chat_history(user_id, message.content)

  
      # Check if the message is a greeting and respond with a random greeting
      if any(greeting.lower() in message.content.lower() for greeting in greetings):
          await message.channel.send(random.choice(greetings))
          return
  
      # Check for exact match with trigger phrases
      if message.content.strip().lower() in trigger_phrases:
          await message.channel.send(random.choice(intelligent_responses))
          return
      
      user_msg_lower = message.content.lower()
      if user_msg_lower in self.structured_prompts:
          responses = self.structured_prompts[user_msg_lower]
          await message.channel.send(random.choice(responses))
          return
  
      # Use only the user's recent messages, excluding the bot's responses
      recent_user_messages = [msg for msg, resp in self.chat_history[user_id][-5:] if resp is None]
      chat_context = " ".join(recent_user_messages)
      payload = {'inputs': {'text': chat_context + '\n' + message.content}}

  
      # while the bot is waiting on a response from the model
      # set the its status as typing for user-friendliness
      async with message.channel.typing():
          response = self.query(payload)
      bot_response = response.get('generated_text', None)
  
      # Handle ill-formed responses
      if not bot_response:
          if 'error' in response:
              bot_response = '`Error: {}`'.format(response['error'])
          else:
              bot_response = 'Hmm... something is not right.'
      # Update chat history with the bot's response
      self.update_chat_history(message.channel.id, message.content, bot_response)

      # Handle the response from the model
      if bot_response:
          # Remove 'Astarion' from the response
          bot_response = bot_response.replace('Astarion', '')


  
      # send the model's response to the Discord channel
      await message.channel.send(bot_response)

def main():
    # DialoGPT-medium-joshua is my model name
    client = MyClient('newastarionbot')
    client.run(os.environ['DISCORD_TOKEN'])

if __name__ == '__main__':
  main()