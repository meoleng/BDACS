import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

# 1. 설정 정보
SLACK_URL = "https://hooks.slack.com/services/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"
TARGET_URLS = {
    "Upbit": "https://upbit.com/service_center/notice",
    "Korbit": "https://exchange.korbit.co.kr/notice/"
}
KEYWORDS = ["Bitcoin", "Ethereum", "Polygon", "Avalanche", "XRP", "USDC", "Solana", "BITCOIN", "ETHEREUM", "POLYGON", "AVALANCHE", "SOLANA", "XRP"]
DB_FILE = "notified_list.txt"

def load_notified_list():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_notified_id(msg_id):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(msg_id + "\n")

def check_notices():
    # 최대한 일반 사용자의 브라우저인 것처럼 보이도록 구성
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Origin': 'https://coinone.co.kr',
        'Referer': 'https://coinone.co.kr/'
    }
    notified_list = load_notified_list()
    now = datetime.now()
    # 다양한 날짜 형식 대응
    today_formats = [now.strftime("%Y.%m.%d"), now.strftime("%Y-%m-%d"), now.strftime("%m.%d")]
    
    any_keyword_found_today = False 
    
    for name, url in TARGET_URLS.items():
        print(f"🔍 {name} 체크 중...")
        try:
            # 코인원의 경우 POST 요청이 필요할 수도 있으나 우선 GET으로 시도
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ {name} 접속 실패: {response.status_code} (URL 확인 필요)")
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

    no_alert_id = f"{now.strftime('%Y%m%d')}_NO_ALERTS"
    if not any_keyword_found_today and no_alert_id not in notified_list:
        send_slack(f"✅ [{now.strftime('%Y-%m-%d')}] 현재까지 신규 알람이 없습니다.")
        save_notified_id(no_alert_id)

def send_slack(msg):
    try:
        requests.post(SLACK_URL, json={"text": msg})
    except: pass

if __name__ == "__main__":
    print(f"🚀 시스템 시작: {datetime.now().strftime('%H:%M:%S')}")
    # 시작하자마자 파일 삭제해서 깨끗하게 테스트하려면 아래 주석 해제 (선택사항)
    # if os.path.exists(DB_FILE): os.remove(DB_FILE)
    
    check_notices()
    while True:
        time.sleep(300)
        check_notices()