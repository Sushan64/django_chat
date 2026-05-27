#from django.test import TestCase

# Create your tests here.
def test():
  import os
  from google import genai
  from dotenv import load_dotenv
  
  load_dotenv()
  
  API_KEY= os.environ.get('GOOGLE_API_KEY')
  client = genai.Client(api_key=API_KEY)
  
  chat = client.chats.create(model="gemini-3.5-flash")
  
  while True:
    response = chat.send_message(input("Q: "))
    print("--------------")
    print("A:" + response.text)
    print('--------------')
    
  '''
  response = client.models.generate_content_stream(
    model="gemini-3.5-flash",
    contents="Hi! What is your name?"
    )
  for chunk in response:
    print(chunk.text, end="", flush=True)
  '''
  
test()