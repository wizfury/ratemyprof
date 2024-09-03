from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()
import json
import os
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

app = Flask(__name__)
model = SentenceTransformer('all-MiniLM-L6-v2')

def scrape_rmp_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    first_name = soup.select_one('.NameTitle__Name-dowf0z-0.cfjPUG > span').get_text(strip=True)
    last_name = soup.select_one('.NameTitle__LastNameWrapper-dowf0z-2.glXOHH').get_text(strip=True).split()[0]
    fullname = first_name + ' ' + last_name

    subject = soup.select_one('.TeacherDepartment__StyledDepartmentLink-fl79e8-0.iMmVHb b').get_text(strip=True).replace('department', '').strip()
    numerator = soup.select_one('.RatingValue__Numerator-qw8sqy-2.liyUjw').get_text(strip=True)
    denominator = soup.select_one('.RatingValue__Denominator-qw8sqy-4.UqFtE').get_text(strip=True).strip('/ ')
    rating = f"{numerator}/{denominator} stars"

    # reviews = soup.select('.Comments__StyledComments-dzzyvm-0.gRjWel')[:5]
    # all_reviews = [review.get_text(strip=True) for review in reviews]
    review = soup.select('.Comments__StyledComments-dzzyvm-0.gRjWel')[0].get_text(strip=True)
    
    # print(review)

    # tags = [span.get_text(strip=True) for span in soup.select('.RatingTags__StyledTags-sc-1boeqx2-0.eLpnFv .Tag-bs9vf4-0.hHOVKF')]

    professorData = {
        'professor': fullname,
        'subject': subject,
        'rating': rating,
        'review': review
    }
    
    embedding = model.encode(professorData["review"])
    
    processed_data = [{
        "values": embedding.tolist(),
        "id": professorData["professor"],
        "metadata": {
            "review": professorData["review"],
            "subject": professorData["subject"],
            "stars": professorData["rating"]
        }
    }]
    
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index('rag')
    index.upsert(
        vectors=processed_data,
        namespace='ns1'
    )
    return processed_data[0]["values"]


@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        url = data['url']
        
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        result = scrape_rmp_page(url)
    
        return jsonify({'embeddings': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
