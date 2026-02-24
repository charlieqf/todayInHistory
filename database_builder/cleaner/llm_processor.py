import os
import sys
import json
import time
from datetime import datetime, timedelta
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

def process_dates_with_gemini(start_month=3, start_day=6, days_to_fetch=30):
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Set it in .env")
        return
        
    client = genai.Client(api_key=api_key)
    storage.init_db()

    total_inserted = 0

    print(f"🤖 Starting Date-Based Gemini Pipeline (Target: {days_to_fetch} days)...")
    
    current_date = datetime(2024, start_month, start_day) # Year doesn't matter for the loop logic
    
    for i in range(days_to_fetch):
        month = current_date.month
        day = current_date.day
        date_str = f"{month}月{day}日"
        print(f"\n📅 Processing Date: {date_str} ({i+1}/{days_to_fetch})...")
        
        prompt = f"""
        You are an elite IT History archivist. Provide exactly 3 to 5 of the most important IT, Computer, Hacker, or Web historical events that happened precisely on this calendar date: {month}-{day} (Month {month}, Day {day}).
        
        Rules:
        1. The month and day MUST match {month}-{day}.
        2. Focus on world-changing tech releases, legendary company foundings, major hacks, or classic video game console launches.
        3. Provide the specific year.
        4. Provide a highly catchy Chinese title (for short videos).
        5. Provide a strictly factual Chinese summary.
        6. Provide an appropriate category (e.g., Hardware, Software, Hacker, Internet, Game).
        """
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-3-flash-preview',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EventList,
                        temperature=0.3,
                    ),
                )
                
                extracted_data = json.loads(response.text)
                extracted_events = extracted_data.get('events', [])
                
                if not extracted_events:
                    print("     ⚠️ No valid events found for this date.")
                    break
                    
                inserted, duplicates = storage.insert_events(extracted_events, source=f"gemini_date/{month}_{day}")
                print(f"     ✅ Found {len(extracted_events)} events for {date_str} -> {inserted} inserted, {duplicates} duplicate skipped.")
                total_inserted += inserted
                break

            except Exception as e:
                error_msg = str(e)
                print(f"     ❌ Gemini API Error for {date_str} (Attempt {attempt+1}/{max_retries}): {error_msg}")
                if attempt < max_retries - 1:
                    sleep_time = 15 * (2 ** attempt)
                    print(f"     ⏳ Sleeping for {sleep_time}s before retrying...")
                    time.sleep(sleep_time)
                else:
                    print(f"     ☠️ Max retries reached for {date_str}. Skipping to next date.")
                    
        # Move to the next day
        current_date += timedelta(days=1)
        # Gentle pacing between days to respect API rates
        time.sleep(5)
                
    print(f"\n🎉 Fully Complete! Total DB Grown By: +{total_inserted} events.")

if __name__ == "__main__":
    process_dates_with_gemini(start_month=3, start_day=6, days_to_fetch=30)
