import json, re, os
import requests

USERNAME = "yeo_hye_ga"
NTFY_TOPIC = "yeohyega"
STATE_FILE = "last_seen.json"
PROFILE_URL = f"https://www.threads.com/@{USERNAME}"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def send_ntfy(title, message, url=None):
    payload = {"topic": NTFY_TOPIC, "title": title, "message": message,
               "priority": 4, "tags": ["bell"]}
    if url:
        payload["click"] = url
    r = requests.post("https://ntfy.sh",
                      data=json.dumps(payload).encode("utf-8"), timeout=20)
    print("ntfy:", r.status_code, r.text)
    r.raise_for_status()

def fetch_latest_code():
    r = requests.get(PROFILE_URL, headers=HEADERS, timeout=30)
    html = r.text
    print("threads status:", r.status_code, "| html length:", len(html))

    # escape 처리된 슬래시/따옴표 정규화 후 매칭
    norm = html.replace('\\/', '/').replace('\\"', '"')
    patterns = [
        r'/@%s/post/([A-Za-z0-9_-]{5,})' % re.escape(USERNAME),
        r'/post/([A-Za-z0-9_-]{5,})',
        r'"code"\s*:\s*"([A-Za-z0-9_-]{5,})"',
    ]
    for i, pat in enumerate(patterns):
        codes = re.findall(pat, norm)
        if codes:
            print(f"matched pattern #{i} -> first 5: {codes[:5]}")
            return codes[0]

    # 아무것도 안 잡히면 진단 정보 출력
    print("no code matched. diagnostics (raw counts):")
    for token in ['/post/', '\\/post\\/', '"code":"', '\\"code\\"',
                  'login', 'Log in', 'ScheduledServerJS', '__bbox',
                  'thread_items', 'profile']:
        print(f"   {token!r}: {html.count(token)}")
    return None

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    latest = fetch_latest_code()
    if not latest:
        print("게시글을 못 읽었습니다. 위 진단 정보를 확인하세요. 에러 없이 종료.")
        return
    post_url = f"{PROFILE_URL}/post/{latest}"
    state = load_state()
    last = state.get("last_code")
    if last is None:
        print("첫 실행: 기준점 설정 ->", latest)
        save_state({"last_code": latest})
        send_ntfy("감시 시작 ✅", f"@{USERNAME} 새 글 감시를 시작합니다.", post_url)
    elif latest != last:
        print("새 글 감지 ->", latest)
        save_state({"last_code": latest})
        send_ntfy("새 글 알림 🔔", f"@{USERNAME}님이 새 글을 올렸어요!", post_url)
    else:
        print("새 글 없음.")

if __name__ == "__main__":
    main()
