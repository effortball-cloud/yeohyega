import os, json, requests

NTFY_TOPIC = os.environ["yeohyega"]

def send_ntfy(title, message):
    resp = requests.post(
        "https://ntfy.sh",
        data=json.dumps({
            "topic": NTFY_TOPIC,
            "title": title,
            "message": message,
            "priority": 4,
            "tags": ["bell"],
        }).encode("utf-8"),
        timeout=20,
    )
    print("ntfy:", resp.status_code, resp.text)

if __name__ == "__main__":
    send_ntfy("테스트 알림", "GitHub Actions → ntfy 연결 성공 ✅")
