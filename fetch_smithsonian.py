import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SMITHSONIAN_API_KEY = os.getenv('SMITHSONIAN_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_URL = 'https://api.si.edu/openaccess/api/v1.0/search'

# Museum unit codes
MUSEUM_UNITS = {
    'NMAI': {'name': 'National Museum of the American Indian'},
    'NMAAHC': {'name': 'African American History & Culture'},
    'FSG': {'name': 'Freer/Sackler Asian Art'},
    'NMAfA': {'name': 'National Museum of African Art'},
    'SAAM': {'name': 'American Art Museum'},
    'NPG': {'name': 'National Portrait Gallery'},
    'CHNDM': {'name': 'Cooper Hewitt Design Museum'},
    'ACM': {'name': 'Anacostia Community Museum'},
    'HMSG': {'name': 'Hirshhorn Museum'},
}

# ============================================================
# Start of Async API Fetching (speeds up dramatically!)
# ============================================================

async def fetch_one_page(session, query, start, description):
    """Fetch one page from Smith. API"""
    params = {
        'api_key': SMITHSONIAN_API_KEY,
        'q': query,
        'rows': 100,
        'start': start,
        'online_media_type': 'Images',
    }
    
    try:
        async with session.get(BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
            data = await response.json()
            if 'response' in data and 'rows' in data['response']:
                rows = data['response']['rows']
                print(f"  √ {description} (page {start//100 + 1}): {len(rows)} objects")
                return rows
            return []
    except Exception as e:
        print(f"  X Error fetching {description}: {e}")
        return []

async def fetch_all_async():
    """Fetch ALL pages at once using async"""
    search_configs = [
        ('unit_code:NMAI', 'American Indian'),
        ('unit_code:NMAfA', 'African art'),
        ('unit_code:FSG', 'Asian art'),
        ('unit_code:NMAAHC', 'African American history'),
        ('unit_code:SAAM', 'American Art'),
        ('unit_code:NPG', 'Portraits'),
        ('unit_code:CHNDM', 'Design objects'),
        ('unit_code:ACM', 'Anacostia Community Museum'),
        ('unit_code:HMSG', 'Hirshhorn Museum'),
    ]

    # Create all tasks (this fetches everything at once!)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for query, description in search_configs:
            for start in [0, 100]:  # 2 pages per museum
                task = fetch_one_page(session, query, start, description)
                tasks.append(task)
        
        # Run all 18 API calls simultaneously
        print("\nFetching from API (async):")
        all_results = await asyncio.gather(*tasks)
    
    # Flatten results into one list
    all_raw_objects = []
    for result in all_results:
        all_raw_objects.extend(result)
    
    return all_raw_objects

# ============================================================
# Helper functions
# ============================================================

def extract_image_url(raw_object):
    """Extract image URL from API response"""
    try:
        content = raw_object.get('content', {})
        descriptive = content.get('descriptiveNonRepeating', {})
        online_media = descriptive.get('online_media', {})
        
        if not online_media:
            return None
        
        media_list = online_media.get('media', [])
        for media in media_list:
            if media.get('type') == 'Images':
                content_url = media.get('content')
                if content_url:
                    return content_url
                
                ids_id = media.get('idsId')
                if ids_id:
                    return f"https://ids.si.edu/ids/deliveryService?id={ids_id}"
        
        return None
    except:
        return None

def extract_themes(indexed, freetext):
    """Extract themes. Potential here for more culturally informed categories"""
    themes = set()
    
    # Topics as themes
    topics = indexed.get('topic', [])
    for topic in topics[:5]:
        if topic and len(topic) > 2:
            themes.add(topic.lower())
    
    # Object type as form theme
    obj_types = indexed.get('object_type', [])
    for ot in obj_types[:3]:
        if ot and len(ot) > 2:
            themes.add(ot.lower())
    
    return list(themes)

def extract_object_data(raw_object):
    """Extract object data"""
    try:
        content = raw_object.get('content', {})
        descriptive = content.get('descriptiveNonRepeating', {})
        indexed = content.get('indexedStructured', {})
        freetext = content.get('freetext', {})
        
        obj_id = raw_object.get('id', '')
        
        # Title
        title_obj = descriptive.get('title', {})
        if isinstance(title_obj, dict):
            title = title_obj.get('content', 'Untitled')
        else:
            title = str(title_obj) if title_obj else 'Untitled'
        
        # Cultures
        culture_list = indexed.get('culture', [])
        
        # Places
        place_list = indexed.get('place', [])
        
        # Date
        date_list = indexed.get('date', [])
        date_str = date_list[0] if date_list else 'Unknown'
        
        # Forms
        object_types = indexed.get('object_type', [])
        form = ', '.join(object_types[:3]) if object_types else 'Unknown'
        
        # Description
        description = 'No description available'
        notes = freetext.get('notes', [])
        if notes and isinstance(notes, list):
            for note in notes:
                if isinstance(note, dict):
                    content_text = note.get('content', '')
                    if content_text and len(content_text) > 20:
                        description = content_text
                        break
        
        # Themes
        themes = extract_themes(indexed, freetext)
        
        # Extract image URL
        image_url = extract_image_url(raw_object)
        if not image_url:
            return None
        
        # Museum
        unit_code = descriptive.get('unit_code', 'Unknown')
        museum_info = MUSEUM_UNITS.get(unit_code, {'name': unit_code})
        
        # Names
        names = indexed.get('name', [])
        # names = normalize_names(raw_names)?
        
        return {
            'smithsonian_id': obj_id,
            'title': title[:1000],
            'cultures': culture_list[:5],
            'places': place_list[:5],
            'date': date_str[:200],
            'form': form[:500],
            'description': description[:2000],
            'image_url': image_url,
            'unit_code': unit_code,
            'museum_name': museum_info['name'],
            'themes': themes[:30],
            'names': names[:20],
        }
    
    except Exception as e:
        return None

def determine_relations(objects):
    """Determine connections between objects"""
    print("\nBuilding connections...")
    
    for i, obj in enumerate(objects):
        if i % 100 == 0 and i > 0:
            print(f"  Progress: {i}/{len(objects)}")
        
        relations = {
            'cultural': [],
            'form': [],
            'thematic': [],
            'spatial': [],
        }
        
        # Extract comparison data
        obj_cultures = set(c.lower() for c in obj.get('cultures', []) if c)
        obj_places = set(p.lower() for p in obj.get('places', []) if p)
        obj_forms = set(m.lower().strip() for m in obj.get('form', '').split(',') if m.strip())
        obj_themes = set(t.lower() for t in obj.get('themes', []) if t)
        
        for j, other_obj in enumerate(objects):
            if i == j:
                continue
            
            other_cultures = set(c.lower() for c in other_obj.get('cultures', []) if c)
            other_places = set(p.lower() for p in other_obj.get('places', []) if p)
            other_forms = set(m.lower().strip() for m in other_obj.get('form', '').split(',') if m.strip())
            other_themes = set(t.lower() for t in other_obj.get('themes', []) if t)
            
            # Cultural connections
            if obj_cultures & other_cultures:
                relations['cultural'].append(other_obj['smithsonian_id'])
            
            # Form connections
            if obj_forms & other_forms and 'unknown' not in obj_forms:
                relations['form'].append(other_obj['smithsonian_id'])
            
            # Thematic connections
            if obj_themes & other_themes:
                relations['thematic'].append(other_obj['smithsonian_id'])
            
            # Spatial connections
            if obj_places & other_places:
                relations['spatial'].append(other_obj['smithsonian_id'])
        
        # Limit to top 8 per type
        obj['relations'] = {
            'cultural': relations['cultural'][:8],
            'form': relations['form'][:8],
            'thematic': relations['thematic'][:8],
            'spatial': relations['spatial'][:8],
        }
    
    return objects

def store_in_supabase(objects):
    """Store objects in Supabase using batching"""
    try:
        print("\nStoring in database...")
        
        batch_size = 100
        total = len(objects)
        
        for i in range(0, total, batch_size):
            batch = objects[i:i + batch_size]
            supabase.table('collection').upsert(
                batch,
                on_conflict='smithsonian_id'
            ).execute()
            print(f"  √ Stored batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
        
        print(f"√ Stored: {len(objects)} objects")
        return True
        
    except Exception as e:
        print(f"X Storage error: {e}")
        return False
    
# ============================================================
# Main Function
# ============================================================

def main():
    """Main execution"""
    print("Smithsonian Multicultural Ecosystem Collection")
    
    
    # Step 1: Fetch from API (async)
    print("\nStep 1: Fetching from Smithsonian API")
    all_raw_objects = asyncio.run(fetch_all_async())
    
    print(f"\n√ Fetched {len(all_raw_objects)} raw objects")
    
    # Step 2: Extract objects with images
    print("\nStep 2: Extracting objects with images")
    all_objects = []
    for raw_obj in all_raw_objects:
        extracted = extract_object_data(raw_obj)
        if extracted:
            all_objects.append(extracted)
    
    # Remove duplicates
    unique_objects = {obj['smithsonian_id']: obj for obj in all_objects}
    unique_objects = list(unique_objects.values())[:1000] #object cap
    
    print(f"✓ Extracted {len(unique_objects)} unique objects with images")
    
    # Show museum distribution
    museums = {}
    for obj in unique_objects:
        unit = obj.get('museum_name', 'Unknown')
        museums[unit] = museums.get(unit, 0) + 1
    
    print(f"\nMuseum distribution:")
    for museum, count in sorted(museums.items(), key=lambda x: -x[1])[:8]:
        print(f"  {museum}: {count}")
    
    # Step 3: Determine relations
    print("\nStep 3: Building connections")
    objects_with_relations = determine_relations(unique_objects)
    
    # Step 4: Store
    print("\nStep 4: Storing in database")
    store_in_supabase(objects_with_relations)
    
    print(f"\n√ Complete!")
    print(f"   {len(unique_objects)} objects")
    print(f"   {len(museums)} museums")

if __name__ == '__main__':
    if not SMITHSONIAN_API_KEY:
        print("X Missing SMITHSONIAN_API_KEY")
        exit(1)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("X Missing Supabase credentials")
        exit(1)
    
    main()