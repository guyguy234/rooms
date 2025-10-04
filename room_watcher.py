import json
import urllib.request
import os
import subprocess

# קבע את ה‑Webhook ב‑Secrets או בסביבה
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
DATA_FILE = "previous.json"
JSON_URL = "https://play.tropy.co.il/data/rooms.json"

def send_embed(title, description, color):
    """שולח Embed לוובהוק"""
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL לא מוגדר")
        return
    embed = {"embeds":[{"title": title, "description": description, "color": color}]}
    try:
        data = json.dumps(embed).encode("utf-8")
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
        print("✅ Embed נשלח!")
    except Exception as e:
        print(f"❌ שגיאה בשליחת הודעה: {e}")

def load_json_safe(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        send_embed("⚠️ previous.json פגום", str(e), 0xFFFF00)
        return []

def fetch_new_data():
    try:
        with urllib.request.urlopen(JSON_URL) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        send_embed("❌ שגיאה בהורדת JSON", str(e), 0xFF0000)
        return []

def compare_data(old, new):
    old_ids = {str(x["0"]): x for x in old}
    new_ids = {str(x["0"]): x for x in new}
    added = [new_ids[i] for i in new_ids if i not in old_ids]
    removed = [old_ids[i] for i in old_ids if i not in new_ids]
    updated = [new_ids[i] for i in new_ids if i in old_ids and new_ids[i] != old_ids[i]]
    return added, removed, updated

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def git_commit_push():
    GH_TOKEN = os.getenv("GH_TOKEN")
    REPO = os.getenv("GITHUB_REPOSITORY")  # מסופק אוטומטית ב‑GitHub Actions
    if not GH_TOKEN:
        print("⚠️ GH_TOKEN לא מוגדר, push ל‑GitHub לא יתבצע")
        return
    try:
        subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", DATA_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update previous.json"], check=True)
        subprocess.run(["git", "push", f"https://{GH_TOKEN}@github.com/{REPO}.git", "HEAD:main"], check=True)
        print("✅ previous.json עדכן ב-GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ שגיאה ב-git: {e}")

def main():
    old_data = load_json_safe(DATA_FILE)
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

    save_json(DATA_FILE, new_data)
    git_commit_push()  # רק אם GH_TOKEN מוגדר

if __name__ == "__main__":
    main()
