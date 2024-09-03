from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

# Load the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

@app.route('/embed', methods=['POST'])
def embed_text():
    # Get the text from the request
    data = request.json
    text = data['text']

    # Generate the embeddings
    embeddings = model.encode(text).tolist()
    
    
    
    # Return the embeddings as JSON
    return jsonify({'embeddings': embeddings})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
