import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

prompt = "Create a playlist with 10 songs that fit the following description: An Effective Alturism party: "

response = openai.Completion.create(model="text-davinci-003",prompt=prompt,temperature=1,max_tokens=256)
print(response)

completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are playlist creation bot. Create playlists with a diverse set of songs that fit the given description. Use real songs from Spotify. Create the playlist as a numbered list. Provide no other text."},
    {"role": "user", "content": "Create a playlist with 10 songs that fit the following description: An Effective Alturism party:"},
  ],
  temperature=0.7
)
print(completion)
