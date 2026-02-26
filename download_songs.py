import urllib.request
import urllib.parse
import json
import os

songs = [
    ("齐秦", "不让我的眼泪陪我过夜"),
    ("齐秦", "大约在冬季"),
    ("周华健", "难念的经")
]

SAVE_DIR = "c:/work/code/todayInHistory"

def search_and_download():
    for artist, title in songs:
        print(f"\n🔍 Searching for: {artist} - {title}")
        query = urllib.parse.quote(f"{artist} {title}")
        # Using a public NetEase Cloud Music API mirror for search
        search_url = f"https://api.imjad.cn/cloudmusic/?type=search&search_type=1&s={query}"
        
        try:
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                search_data = json.loads(response.read().decode())
                
            songs_list = search_data.get('result', {}).get('songs', [])
            if not songs_list:
                print(f"❌ Could not find {title}")
                continue
                
            # Get the ID of the first result
            song_id = songs_list[0]['id']
            print(f"🎵 Found Song ID: {song_id}")
            
            # Fetch the actual MP3 URL
            song_url = f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"
            
            save_path = os.path.join(SAVE_DIR, f"{title}.mp3")
            print(f"⬇️ Downloading to {save_path}...")
            
            # Download file
            urllib.request.urlretrieve(song_url, save_path)
            print(f"✅ Success! Saved {title}.mp3")
            
        except Exception as e:
            print(f"❌ Error downloading {title}: {e}")

if __name__ == "__main__":
    search_and_download()
