import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from datetime import datetime

# 🚀 1. 設定即時匯率 API
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"  # 取得最新匯率
response = requests.get(EXCHANGE_API_URL)
exchange_rates = response.json().get("rates", {})

# 🚀 2. 設定一些常見貨幣轉換成 TWD
currency_map = {
    "US$": "USD",
    "HK$": "HKD",
    "MYR": "MYR",
    "¥": "JPY",
    "￦": "KRW",
    "SGD": "SGD",
    "AU$": "AUD",  # 🇦🇺 澳幣
    "IDR": "IDR",  # 🇮🇩 印尼盾
    "CA$": "CAD",  # 🇨🇦 加拿大元
    "ARS": "ARS",  # 🇦🇷 阿根廷披索 ✅ 新增
    "£": "GBP",    # 🇬🇧 英鎊 ✅ 新增
    "$": "TWD"     # 如果是台幣，則不轉換
}

# 🚀 3. 啟動 Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 無頭模式
options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 🚀 4. 前往 YouTube 影片
video_url = "https://www.youtube.com/watch?v=kOZWQgtqps4&t=3s"
driver.get(video_url)
time.sleep(5)

# 🚀 5. 滾動到頁面底部，確保所有留言載入
scroll_attempts = 0
last_height = driver.execute_script("return document.documentElement.scrollHeight")

while True:  # 無限滾動，直到留言不再增加
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)  # 滾動到底部
    time.sleep(5)  # 等待新留言載入 (增加等待時間)

    new_height = driver.execute_script("return document.documentElement.scrollHeight")
    
    # 如果高度沒變，檢查是否有「顯示更多留言」按鈕
    if new_height == last_height:
        try:
            load_more_button = driver.find_element(By.CSS_SELECTOR, "yt-next-continuation #more-button")
            load_more_button.click()  # 點擊「顯示更多留言」
            time.sleep(5)  # 等待留言載入
        except:
            break  # 沒有按鈕，代表留言已完全載入

    last_height = new_height
    scroll_attempts += 1

# 🚀 6. 抓取捐款金額
total_twd = 0
donation_count = 0
donation_elements = driver.find_elements(By.CSS_SELECTOR, "span#comment-chip-price")

for el in donation_elements:
    text = el.text.strip()
    
    # 嘗試解析貨幣與金額
    match = re.match(r"([^\d\s]+)?\s*([\d,]+(?:\.\d+)?)", text)
    if not match:
        continue  # 如果找不到符合的數據，就跳過
    
    currency_symbol, amount_text = match.groups()
    amount = float(amount_text.replace(",", ""))  # 去掉千分位，轉換成浮點數

    # 取得貨幣代碼
    currency_code = currency_map.get(currency_symbol, "UNKNOWN")
    if currency_code == "UNKNOWN":
        print(f"⚠️ 未知貨幣：{text}")
        continue  # 如果找不到貨幣代碼，就跳過

    # 轉換為 TWD
    if currency_code == "TWD":
        converted_amount = amount
    else:
        exchange_rate = exchange_rates.get(currency_code, None)
        if exchange_rate:
            converted_amount = amount * exchange_rates["TWD"] / exchange_rate  # 轉換成 TWD
        else:
            print(f"⚠️ 無法取得 {currency_code} 匯率，跳過：{text}")
            continue

    total_twd += converted_amount
    donation_count += 1
    print(f"✅ {text} -> TWD {converted_amount:.2f}")

# 🚀 7. 計算總留言數
all_comments = driver.find_elements(By.CSS_SELECTOR, "ytd-comment-view-model#comment")
total_comments = len(all_comments)

# 避免除以 0 的錯誤
donation_ratio = (donation_count / total_comments * 100) if total_comments > 0 else 0

# 🚀 8. 取得影片標題
video_title = driver.find_element(By.CSS_SELECTOR, "title").get_attribute("textContent").replace("- YouTube", "").strip()

# 🚀 9. 取得現在的日期與時間
current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

# 🚀 10. 輸出結果
print(f"\n------------作者：張展豪-----------------")

print(f"\n✅ 已載入所有留言 (滾動 {scroll_attempts} 次)")

print(f"\n🎬 影片標題: {video_title}")
print(f"⏰ 爬取時間: {current_time}")

print(f"\n📊 總留言數: {total_comments}")
print(f"💎 捐款留言數: {donation_count}")
print(f"📈 捐款留言佔比: {donation_ratio:.2f}%")
print(f"💰 總捐款金額 (TWD): ${total_twd:,.2f}")

# 🚀 8. 關閉瀏覽器
driver.quit()
