import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta, timezone

# 1. 설정 정보
SLACK_URL = os.environ.get("SLACK_URL")
TARGET_URLS = {
    "Upbit": "https://upbit.com/service_center/notice",
    "Korbit": "https://exchange.korbit.co.kr/notice/"
}
KEYWORDS = ["Bitcoin", "Ethereum", "Polygon", "Avalanche", "XRP", "USDC", "Solana", "BITCOIN", "ETHEREUM", "POLYGON", "AVALANCHE", "SOLANA", "XRP", "비트코인", "이더리움", "아발란체", "폴리곤", "솔라나"]
DB_FILE = "notified_list.txt"

# 🌟 한국 시간(KST) 설정 (GitHub Actions 서버 시간 오차 해결)
KST = timezone(timedelta(hours=9))

def load_notified_list():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_notified_id(msg_id):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(msg_id + "\n")

def check_notices():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    notified_list = load_notified_list()
    now = datetime.now(KST) # 한국 시간 적용
    
    today_formats = [now.strftime("%Y.%m.%d"), now.strftime("%Y-%m-%d"), now.strftime("%m.%d")]
    any_keyword_found_today = False 
    
    for name, url in TARGET_URLS.items():
        print(f"🔍 {name} 체크 중...")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ {name} 접속 실패: {response.status_code}")
                continue

            page_text = response.text
            is_today = any(fmt in page_text for fmt in today_formats)
            
            if is_today:
                for word in KEYWORDS:
                    if word.lower() in page_text.lower():
                        msg_id = f"{now.strftime('%Y%m%d')}_{name}_{word}"
                        if msg_id not in notified_list:
                            send_slack(f"🚨 [{name}] 오늘 공지 키워드 '{word}' 발견!")
                            save_notified_id(msg_id)
                            notified_list.add(msg_id)
                        any_keyword_found_today = True

        except Exception as e:
            print(f"🔺 {name} 에러 발생: {e}")

    # 🌟 주석 해제 완료: 키워드가 하나도 없을 경우 알림 발송
    no_alert_id = f"{now.strftime('%Y%m%d')}_NO_ALERTS"
    if not any_keyword_found_today and no_alert_id not in notified_list:
        send_slack(f"✅ [{now.strftime('%Y-%m-%d')}] 현재까지 신규 알람이 없습니다.")
        save_notified_id(no_alert_id)

def send_slack(msg):
    try:
        # SLACK_URL이 설정되어 있지 않을 경우를 대비한 방어 로직
        if not SLACK_URL:
            print("❌ 슬랙 URL이 환경 변수에 설정되어 있지 않습니다.")
            return
        requests.post(SLACK_URL, json={"text": msg})
    except Exception as e: 
        print(f"❌ 슬랙 발송 에러: {e}")

if __name__ == "__main__":
    print(f"🚀 시스템 체크 시작: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 딱 한 번만 실행되도록 수정 (while True 삭제)
    check_notices()
    
    print("✅ 체크 완료 후 깔끔하게 종료!")
