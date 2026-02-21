import os
import sys
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Automatically append the db path so we can import storage.py
sys.path.append(os.path.join(SCRIPT_DIR, "..", "db"))
import storage

# The script is in database_builder/cleaner/
# The data is in database_builder/data/raw/
RAW_DATA_FILE = os.path.join(SCRIPT_DIR, "..", "data", "raw", "wikipedia_timelines_raw.json")

# ----------------- PYDANTIC SCHEMA DEFINITIONS -----------------
class HistoricalEvent(BaseModel):
    month: int = Field(description="Month from 1 to 12. Must extract exact month.")
    day: int = Field(description="Day from 1 to 31. Must extract exact day.")
    year: int = Field(description="Year of the event, e.g., 1995")
    title: str = Field(description="A highly catchy title for short videos, max 30 words")
    summary: str = Field(description="Detailed factual summary of the tech event")
    category: str = Field(description="E.g., Hardware, Software, Company, Hacker, OpenSource, Internet")
    importance_score: int = Field(description="1-10 video burst potential. 10=changes world tech history (e.g. iPhone). Routine hardware updates=3-5.")

class EventList(BaseModel):
    events: list[HistoricalEvent] = Field(description="List of extracted tech/IT events.")

# -------------------------------------------------------------

def chunk_text(text, max_chars=100000):
    """Chunks the huge Wikipedia HTML/text into pieces for Gemini (which handles large contexts)."""
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_len = 0
    for line in lines:
        if current_len + len(line) > max_chars and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(line)
        current_len += len(line)
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks

def process_wikipedia_with_gemini(target_events=200):
    # Using the exact API key the user provided
    api_key = "AIzaSyCUHdikBUmurUge__gob5Ch1ViUiCrjS6A"
    client = genai.Client(api_key=api_key)
    storage.init_db()

    with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    total_inserted = 0

    print("🤖 Starting Gemini Pipeline to process raw HTML -> SQLite Events...")
    
    for page_title, full_text in raw_data.items():
        print(f"\n📖 Processing Wiki Page: {page_title}...")
        chunks = chunk_text(full_text, max_chars=100000) 
        
        for i, chunk in enumerate(chunks):
            if total_inserted >= target_events: 
                print(f"\n[!] Reached target of {target_events} events. Stopping extraction.")
                print(f"🎉 Process Complete! Total DB Grown By: +{total_inserted} events.")
                return

            print(f"  -> Extrating events from chunk {i+1}/{len(chunks)}...")
            prompt = f"""
            You are an IT History archivist. Extract factual computer/IT history events from the following Wikipedia text.
            Ignore noise, non-IT news, and items missing an EXACT month and day. Provide a catchy Chinese title and Chinese summary for each event to be used in videos.
            
            Text:
            {chunk}
            """
            
            try:
                # Using google-genai structured outputs
                response = client.models.generate_content(
                    model='gemini-3-flash-preview',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EventList,
                        temperature=0.1,
                    ),
                )
                
                # Gemini returns the Pydantic model directly via parsed JSON response
                extracted_data = json.loads(response.text)
                extracted_events = extracted_data.get('events', [])
                
                if not extracted_events:
                    print("     ⚠️ No valid events found in this chunk.")
                    continue
                    
                inserted, duplicates = storage.insert_events(extracted_events, source=f"wikipedia/{page_title}")
                print(f"     ✅ Found {len(extracted_events)} events -> {inserted} inserted, {duplicates} duplicate skipped.")
                total_inserted += inserted
                
            except Exception as e:
                print(f"     ❌ Gemini API Error on chunk {i+1}: {e}")
                
    print(f"\n🎉 Fully Complete! Total DB Grown By: +{total_inserted} events.")

if __name__ == "__main__":
    # The user wants to build up the database to 200 events.
    process_wikipedia_with_gemini(target_events=200)
