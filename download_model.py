
import os
from sentence_transformers import SentenceTransformer

# Define the model name and the local path
model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
local_model_path = os.path.join('local_models', os.path.basename(model_name))

# Create the directory if it doesn't exist
os.makedirs(local_model_path, exist_ok=True)

print(f"Downloading model to {local_model_path}...")

# Download and save the model
model = SentenceTransformer(model_name)
model.save(local_model_path)

print("Model downloaded and saved successfully.")
