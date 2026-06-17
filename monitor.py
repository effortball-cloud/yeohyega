import json, re, os
import requests
from playwright.sync_api import sync_playwright

USERNAME = "yeo_hye_ga"
NTFY_TOPIC = "yeohyega"
STATE_FILE = "last_seen.json"
PROFILE_URL = f"https://www.threads.com/@{USERNAME}"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

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
    hrefs, html = [], ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, locale="ko-KR",
                                      viewport={"width": 1280, "height": 1800})
        page = context.new_page()
        try:
            resp = page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=60000)
            print("threads status:", resp.status if resp else "?")
            try:
                page.wait_for_selector('a[href*="/post/"]', timeout=20000)
            except Exception as e:
                print("post 링크 대기 실패:", e)
            page.wait_for_timeout(2000)
            html = page.content()
            hrefs = page.eval_on_selector_all(
                'a[href*="/post/"]',
                "els => els.map(e => e.getAttribute('href'))")
        except Exception as e:
            print("navigation error:", e)
        finally:
            browser.close()

    print("rendered html length:", len(html))
    print("post hrefs (first 5):", hrefs[:5])
    codes = []
    for h in hrefs:
        m = re.search(r'/post/([A-Za-z0-9_-]{6,})', h or "")
        if m and not re.fullmatch(r'[a-z]{2}_[A-Z]{2}', m.group(1)):
            codes.append(m.group(1))
    if codes:
        print("codes (first 5):", codes[:5])
        return codes[0]
    print("permalink 못 찾음 (로그인 벽/차단 가능).")
    for token in ["로그인", "Log in"]:
        print(f"   {token!r} in html: {token in html}")
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
        print("게시글을 못 읽음. 위 로그 확인. 에러 없이 종료.")
        return
    post_url = f"{PROFILE_URL}/post/{latest}"
    state = load_state()
    last = state.get("last_code")
    if last is None or last == "ko_KR":
        print("기준점 설정 ->", latest)
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
