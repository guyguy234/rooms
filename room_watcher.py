import json
import urllib.request
import urllib.error
import os

# הוובהוק החדש שלך
WEBHOOK_URL = "https://discord.com/api/webhooks/1423983135183470624/NFKgKL82HUjpOpi5ot-nr-PKo_XbBJSd23TCmxYGHd3tEARGZzDH_Bxkn8YDb6zkjEde"

# URL של ה-JSON
JSON_URL = "https://play.tropy.co.il/data/rooms.json"

# קובץ לשמירה והשוואה
DATA_FILE = "previous.json"

def send_to_discord(message):
    """שולח הודעה לוובהוק"""
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL לא מוגדר")
        return
    try:
        data = json.dumps({"content": message}).encode("utf-8")
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
        print("✅ הודעה נשלחה!")
    except Exception as e:
        print(f"❌ שגיאה בשליחת הודעה: {e}")

def safe_load_json(path):
    """טוען JSON בצורה בטוחה. אם הקובץ חסר או פגום, מחזיר רשימה ריקה"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("⚠️ הקובץ previous.json פגום או לא קריא, איפוס:", e)
        send_to_discord("⚠️ הקובץ previous.json היה פגום או לא קריא ולכן אופס.")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[]")
        return []

def save_data(data):
    """שומר את הנתונים החדשים"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_new_data():
    """מוריד את הנתונים מה-JSON"""
    try:
        with urllib.request.urlopen(JSON_URL) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print("❌ שגיאה בהורדת JSON:", e)
        send_to_discord("❌ שגיאה בהורדת JSON: " + str(e))
        return []

def compare_data(old, new):
    """משווה בין נתונים ישנים לחדשים לפי מזהה '0'"""
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
        print("❌ לא התקבל מידע חדש.")
        send_to_discord("❌ לא התקבל מידע חדש.")
        return

    added, removed, updated = compare_data(old_data, new_data)

    if not added and not removed and not updated:
        send_to_discord("ℹ️ אין שינויים בחדרים.")
    else:
        msg = []
        if added:
            msg.append(f"🟢 נוספו {len(added)} חדרים חדשים:\n" + "\n".join([r['1'] for r in added]))
        if removed:
            msg.append(f"🔴 הוסרו {len(removed)} חדרים:\n" + "\n".join([r['1'] for r in removed]))
        if updated:
            msg.append(f"🟡 עודכנו {len(updated)} חדרים:\n" + "\n".join([r['1'] for r in updated]))
        send_to_discord("\n\n".join(msg))

    save_data(new_data)

if __name__ == "__main__":
    main()
