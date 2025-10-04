import json
import urllib.request
import urllib.error
import os

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
JSON_URL = "https://play.tropy.co.il/data/rooms.json"
DATA_FILE = "previous.json"

def send_embed(title, description, color):
    """שולח Embed לוובהוק"""
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL לא מוגדר")
        return
    embed = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color
        }]
    }
    try:
        data = json.dumps(embed).encode("utf-8")
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
        print("✅ Embed נשלח!")
    except Exception as e:
        print(f"❌ שגיאה בשליחת Embed: {e}")

def safe_load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        send_embed("⚠️ previous.json פגום", str(e), 0xFFFF00)
        with open(path, "w", encoding="utf-8") as f:
            f.write("[]")
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_new_data():
    try:
        with urllib.request.urlopen(JSON_URL) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        send_embed("❌ שגיאה בהורדת JSON", str(e), 0xFF0000)
        return []

def compare_data(old, new):
    old_ids = {str(item["0"]): item for item in old}
    new_ids = {str(item["0"]): item for item in new}

    added = [new_ids[i] for i in new_ids if i not in old_ids]
    removed = [old_ids[i] for i in old_ids if i not in new_ids]
    updated = [new_ids[i] for i in new_ids if i in old_ids and new_ids[i] != old_ids[i]]

    return added, removed, updated

def main():
    old_data = safe_load_json(DATA_FILE)
    new_data = fetch_new_data()
    if not new_data:
        return

    added, removed, updated = compare_data(old_data, new_data)

    if not added and not removed and not updated:
        send_embed("ℹ️ אין שינויים", "כל החדרים כפי שהם.", 0x808080)
    else:
        if added:
            send_embed("🟢 חדרים חדשים", "\n".join([r['1'] for r in added]), 0x00FF00)
        if removed:
            send_embed("🔴 חדרים הוסרו", "\n".join([r['1'] for r in removed]), 0xFF0000)
        if updated:
            send_embed("🟡 חדרים עודכנו", "\n".join([r['1'] for r in updated]), 0xFFFF00)

    save_data(new_data)

if __name__ == "__main__":
    main()
