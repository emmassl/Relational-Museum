-- Relational Museum Database Schema
-- To be ran in Supabase SQL Editor

-- Get rid of old table if exists
DROP TABLE IF EXISTS collection CASCADE;

-- Main table storing objects
CREATE TABLE collection (
    -- Database ID (increments: 1, 2, 3, etc.)
    id SERIAL PRIMARY KEY,
    -- Smithsonian's unique ID (ex: "edanmdm-nmaahc_2017.30.9")
    smithsonian_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    
    -- Fields
    -- Arrays allow multiple values, ex: cultures = ['Akan', 'Asante']
    cultures TEXT[],
    places TEXT[],
    -- Single values
    date TEXT,
    form TEXT,
    description TEXT,
    image_url TEXT,
    
    -- Smithsonian museum (ex: "NMAI", "National Museum of the American Indian")
    unit_code TEXT,
    museum_name TEXT,
    
    -- Thematic connections
    themes TEXT[],
    names TEXT[],
    
    -- JSONB stores the relationship links as flexible JSON:
    -- { "cultural": ["id1", "id2"], "form": ["id3"], "thematic": [...], "spatial": [...] }
    relations JSONB,              -- cultural, form, thematic, spatial
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- INDEXES: Speed up searches on frequently queried columns
-- w/o every query scans all rows

-- Standard indexes for exact matches
CREATE INDEX idx_smithsonian_id ON collection(smithsonian_id);
CREATE INDEX idx_unit_code ON collection(unit_code);
CREATE INDEX idx_museum_name ON collection(museum_name);

-- GIN (Generalized Inverted Index) is designed for array and JSONB fields. Allows for efficiently queries,
-- fast "contains" queries on array fields, especially useful for when you scale for larger DB queries. 
-- And when you want to implement search on server-side rather than client (front end)
CREATE INDEX idx_cultures ON collection USING GIN(cultures);
CREATE INDEX idx_places ON collection USING GIN(places);
CREATE INDEX idx_themes ON collection USING GIN(themes);