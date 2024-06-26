import requests
import pymongo
from datetime import datetime 
import openai
import ollama
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access API key
api_key = os.getenv('HF_TOKEN')

hf_token = api_key
mongo_link = os.getenv('MONGO_LINK')
embedding_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"


client = pymongo.MongoClient(mongo_link)
db = client.convo
collection = db.thoughts

def generate_embedding(text: str) -> list[float]:

	response = requests.post(
		embedding_url,
		headers={"Authorization": f"Bearer {hf_token}"},
		json={"inputs": text})

	if response.status_code != 200:
		raise ValueError(f"Request failed with status code {response.status_code}: {response.text}")

	return response.json()

def insert_thoughts(new_thoughts):
    try:
        new_time = datetime.now()
        thought_embedding = generate_embedding(new_thoughts)
        new_idea = {
            'thought': new_thoughts,
            'thought_embedding': thought_embedding,
			'time': new_time
        }

        # Insert the document and wait for acknowledgment
        result = collection.insert_one(new_idea)
        print(f"Inserted thought with _id: {result.inserted_id}")
    except Exception as e:
        print(f"Error inserting thought: {e}")

def enter_thoughts():
	thought = input("enter your thoughts: ")
	while(thought != "end"):
		insert_thoughts(thought)
		thought = input("enter your thoughts: ")

def retrieve_thoughts():
	question = input("search within your thoughts: ")
	while (question != "end"):
		results = collection.aggregate([
		{"$vectorSearch": {
			"queryVector": generate_embedding(question),
			"path": "thought_embedding",
			"numCandidates": 100,
			"limit": 4,
			"index": "thought_embed",
			}}
		]);	
		print("here are the relevant thoughts: \n")
		info = ""
		for document in results:
			order = 1
			print(f'Thought {order} : {document["thought"]}')
			info += document["thought"] + "time of insert:" + document["time"].strftime("%m/%d/%Y, %H:%M:%S")
			order += 1
		output = ollama.generate(
  		model="llama2",
  		prompt=f"Using this data that I have entered : {info}. Respond to this prompt: {question} like an assistant, answer consisely in 1 to 4 sentence"
		)
		info += f"Previous Question: {question}, Previous Response: {output['response']}"
		print(output["response"], '\n')
		
		question = input("search within your thoughts: ")
# enter_thoughts()

choose = input ("read or write")
if choose == "read":
	retrieve_thoughts()
else:
	enter_thoughts()
# query = "outer space"

# results = collection.aggregate([
#   {"$vectorSearch": {
#     "queryVector": generate_embedding(query),
#     "path": "plot_embedding_hf",
#     "numCandidates": 100,
#     "limit": 4,
#     "index": "PlotSemanticSearch",
#       }}
# ]);

# for document in results:
#     print(f'Movie Name: {document["title"]},\nMovie Plot: {document["plot"]}\n')