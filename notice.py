import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta, timezone

# 1. 설정 정보
# 깃허브 Secrets에 저장한 주소를 check.yml을 통해 불러옵니다.
SLACK_URL = os.environ.get("SLACK_URL")

TARGET_URLS = {
    "Upbit": "https://upbit.com/service_center/notice",
    "Korbit": "https://exchange.korbit.co.kr/notice/",
    "https://feed.bithumb.com/notice?category=7&page=1"
    }

KEYWORDS = ["Bitcoin", "Ethereum", "Polygon", "Avalanche", "XRP", "USDC", "Solana", "비트코인", "이더리움", "아발란체", "폴리곤", "솔라나"]
DB_FILE = "notified_list.txt"

# 한국 표준시(KST) 설정
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
    now = datetime.now(KST) # 한국 시간 기준 현재 시각
    
    # 거래소마다 다른 날짜 형식 대응
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
            # 오늘 날짜의 공지가 있는지 확인
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

    # [중요] 오늘 새로운 키워드가 발견되지 않았을 경우 '알람 없음' 메시지 발송
    no_alert_id = f"{now.strftime('%Y%m%d')}_NO_ALERTS"
    if not any_keyword_found_today and no_alert_id not in notified_list:
        send_slack(f"✅ [{now.strftime('%Y-%m-%d')}] 현재까지 신규 알람이 없습니다.")
        save_notified_id(no_alert_id)

def send_slack(msg):
    try:
        if not SLACK_URL:
            print("❌ SLACK_URL 환경변수가 설정되지 않았습니다.")
            return
        requests.post(SLACK_URL, json={"text": msg})
    except Exception as e:
        print(f"❌ 슬랙 전송 에러: {e}")

if __name__ == "__main__":
    print(f"🚀 시스템 체크 시작 (한국시간): {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")
    check_notices()
    print("✅ 체크 완료 후 정상 종료")
    # 깃허브 액션에서는 무한루프(while True)를 절대로 사용하지 않습니다.
