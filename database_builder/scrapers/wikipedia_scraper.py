import requests
from bs4 import BeautifulSoup
import json
import time
import os

# Set up paths relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

USER_AGENT = "IT_History_Bot/1.0 (test@example.com)"

def get_wikipedia_timeline(page_title):
    print(f"Fetching {page_title}...")
    url = f"https://en.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text"
    }
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {page_title}: HTTP {response.status_code}")
            return None
            
        data = response.json()
        if "parse" not in data:
            print(f"Error parsing {page_title}: {data}")
            return None
            
        raw_html = data["parse"]["text"]["*"]
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # We don't want to over-clean because the LLM is smart.
        # But we do want to strip navigation menus, styling, and javascript.
        # Let's extracttext from paragraphs and lists, which contain the timeline facts.
        content_blocks = []
        for element in soup.find_all(['p', 'li', 'h2', 'h3']):
            text = element.get_text().strip()
            # Filter out very short strings to reduce token usage
            if text and len(text) > 15: 
                content_blocks.append(text)
                
        raw_text = "\n".join(content_blocks)
        print(f"-> Successfully extracted {len(raw_text)} characters.")
        return raw_text
        
    except Exception as e:
        print(f"Exception while fetching {page_title}: {e}")
        return None

if __name__ == "__main__":
    pages_to_scrape = [
        "Timeline_of_computing",
        "Timeline_of_computing_1950–1979",
        "Timeline_of_computing_1980–1989",
        "Timeline_of_computing_1990–1999",
        "Timeline_of_computing_2000–2009",
        "Timeline_of_computing_2010–2019",
        "Timeline_of_computing_2020–present",
        "Timeline_of_programming_languages",
        "List_of_software_bugs",
        "Timeline_of_artificial_intelligence"
    ]

    all_raw_data = {}

    for page in pages_to_scrape:
        raw_text = get_wikipedia_timeline(page)
        if raw_text:
            all_raw_data[page] = raw_text
        # Respect Wikipedia's API rate limits
        time.sleep(2) 

    output_file = os.path.join(RAW_DATA_DIR, "wikipedia_timelines_raw.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_raw_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Successfully scraped {len(all_raw_data)} pages.")
    print(f"💾 Saved raw dataset to {output_file}")
    
    total_chars = sum(len(text) for text in all_raw_data.values())
    print(f"📊 Total characters collected for LLM processing: {total_chars}")
