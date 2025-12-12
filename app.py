import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def transform_for_frontend(db_object):
    """
    Handles metadata from db format into clean JSON structure for front end
    """
    relations = db_object.get('relations', {})
    if not relations:
        relations = {}
    
    return {
        'id': db_object['smithsonian_id'],
        'title': db_object['title'],
        'cultures': db_object.get('cultures', []), 
        'places': db_object.get('places', []),      
        'date': db_object['date'],
        'form': db_object['form'],
        'description': db_object['description'],
        'image_url': db_object.get('image_url'),
        'museum_name': db_object.get('museum_name'),
        'themes': db_object.get('themes', []),
        'names': db_object.get('names', []),
        'relations': {
            'cultural': relations.get('cultural', []),
            'form': relations.get('form', []),
            'thematic': relations.get('thematic', []),
            'spatial': relations.get('spatial', []),
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/collection')
def get_collection():
    """
    Get all objects from Supabase
    """
    try:
        response = supabase.table('collection').select('*').execute()
        
        if response.data:
            objects = [transform_for_frontend(obj) for obj in response.data]
            return jsonify(objects)
        
        return jsonify([])
    
    except Exception as e:
        print(f"Error fetching collection: {e}")
        return jsonify({'error': 'Failed to fetch collection'}), 500

if __name__ == '__main__':
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Missing Supabase credentials in .env file")
        exit(1)
    
    app.run(debug=False, port=5000)
    