# Rethinking Digital Museum Collections: A Relational Interface Design for Museum Discovery

The first semester instillaiton of a yearlong development at a modern web application that visualizes museum collections through informed relationships: the basis of a relational interface that presents museum objects not as isolated items in a collections list, but as nodes in a larger network of cultural, form, and contextual connections. Rather than requiring users to know what they're looking for, this system reveals relationships between objects, inviting discovery through navigation.
This project draws on Khoo et al.'s (2024) concept of "knowledge graph visualization." It supports associative browsing and broader understanding in comparison to simple retrieval. 

## Design Philosophy

Digital museum collections and databases largely mirror rigid, Western taxonomies that can flatten cultural meaning and relationships.
- Most interfaces prioritize tools like precise search, chronology, and predetermined geographic regions— structures that don’t always align with how many cultures understand or relate to their own objects.
- Because of this, online collections become object-focused rather than relational, potentially loosing the cultural networks, protocols, and context that surround each item.
- The aspect of discovery and learning through navigating the interface itself is also usually overlooked, with search efficiency prioritized over curiosity, depth, and the spontaneous learning
that physical museum exhibitions can offer.
When was the last time searching a museum database taught you about what you found beyond just the object you clicked on?

## Features

> 1,000 total objects fetched from 8 diverse Smithsonian museums with diverse collections (the API has access to over 11 million objects from 19 museums)
> 4 preliminary relation filtering types: Cultural, Form, Thematic, Spatial, and a force-directed layout for connected object clustering
> Interactive graph where users can filter connections, click to view an object in detail, or activate a spontaneous “Collections Walk” tour

Additional Features and Technical Components:
- Up to 8 connections per object, using pagination and display limits (50 objects per page) to enable discovery without overwhelming user with connection links
- Only objects with digital images are displayed, aiding immersion
- Async API fetching (18 concurrent requests across 9 museums)
- Relational metadata extraction: cultures, places, form, themes
- Force-directed graph visualization with zoom/pan navigation
- Real-time filtering by relation type
- "Collections Walk" mode for guided serendipitous exploration

## Project Structure

```
relational-museum/
├── templates/
│   └── index.html              # Frontend interface
├── app.py                      # Flask backend API
├── fetch_smithsonian.py        # Data fetching & processing script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .env                        # Your API keys (to create, sensitive, not in git repo)
├── README.md                  
└── .gitignore                  # Git ignore file
```

### Prereqs

- Python 3.8 or higher
- A Smithsonian API key
- A Supabase account

### 1. Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd museum

# Install dependencies
pip install -r requirements.txt
```

### 2. Get API Credentials

**Smithsonian API Key:**
1. Visit https://api.data.gov/signup/
2. Fill out the form with your email
3. Receive your API key via email

**Supabase Setup:**
1. Create account at https://supabase.com
2. Create a new project
3. Go to Settings –> API
4. Copy your Project URL and anon public key

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
SMITHSONIAN_API_KEY=your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
```

### 4. Set Up Database

In your Supabase dashboard, go to SQL Editor and run:

```sql
DROP TABLE IF EXISTS collection CASCADE;

CREATE TABLE collection (
    id SERIAL PRIMARY KEY,
    smithsonian_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    
    cultures TEXT[],
    places TEXT[],

    date TEXT,
    form TEXT,
    description TEXT,
    image_url TEXT,
    
    unit_code TEXT,
    museum_name TEXT,
    
    themes TEXT[],
    names TEXT[],
    
    relations JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_smithsonian_id ON collection(smithsonian_id);
CREATE INDEX idx_unit_code ON collection(unit_code);
CREATE INDEX idx_museum_name ON collection(museum_name);
CREATE INDEX idx_cultures ON collection USING GIN(cultures);
CREATE INDEX idx_places ON collection USING GIN(places);
CREATE INDEX idx_themes ON collection USING GIN(themes);
```

### 5. Fetch Data

```bash
# Run the fetcher script (takes 2-5 minutes)
python fetch_smithsonian.py
```

This will:
- Fetch ~1000 viable artifacts from 8 Smithsonian museums
- Extract metadata and images
- Determine cultural, thematic, form, and spatial relationships
- Store everything in your Supabase database

### 6. Run the Application

```bash
# Start the Flask server
python app.py

# Open your browser to
# http://localhost:5000
```

## Tools & Resources

PostgreSQL:
https://www.postgresql.org/docs/current/indexes.html
https://www.postgresql.org/docs/current/gin.html 

Smithsonian API:
https://www.si.edu/openaccess/devtools
https://www.youtube.com/watch?v=TP7X-EFRVNM

D3.js:
https://www.youtube.com/watch?v=y2-sgZh49dQ

Asyncio:
https://youtu.be/ngXbyui-weA?si=hkhvFOC2BZ--5VF7