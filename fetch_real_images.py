import requests
import os

def get_wiki_image(title, filename):
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=pageimages&format=json&pithumbsize=1080"
    headers = {"User-Agent": "Bot/1.0 (test@example.com)"}
    try:
        r = requests.get(url, headers=headers).json()
        pages = r['query']['pages']
        for page_id in pages:
            if 'thumbnail' in pages[page_id]:
                img_url = pages[page_id]['thumbnail']['source']
                print(f"Downloading {title} from {img_url} to {filename}")
                img_data = requests.get(img_url, headers=headers).content
                with open(filename, 'wb') as handler:
                    handler.write(img_data)
                return True
        print(f"No thumbnail found for {title}")
    except Exception as e:
        print(f"Error fetching {title}: {e}")
    return False

os.makedirs("assets", exist_ok=True)
get_wiki_image("Xerox_Alto", "assets/real_xerox_alto.jpg")
get_wiki_image("Steve_Jobs", "assets/real_steve_jobs.jpg")
get_wiki_image("PARC_(company)", "assets/real_xerox_parc.jpg")
