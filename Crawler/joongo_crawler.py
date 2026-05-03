from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import urllib.parse
import re
import numpy as np

# 1. 검색어 변수
keyword = "갤럭시S26"
num_how_many_results = 50

# 2. URL용 검색어
encoded_keyword = urllib.parse.quote(keyword)

# 3. 드라이버 실행
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

results = []
page = 1

# 🔥 페이지 반복
while len(results) < num_how_many_results:
    url = f"https://web.joongna.com/search/{encoded_keyword}?page={page}"
    print(f"\n=== {page} 페이지 ===")

    driver.get(url)
    time.sleep(3)

    # 🔥 스크롤 (lazy loading 대응)
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    # 🔥 상품만 가져오기
    items = driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
    print("현재 페이지 아이템 개수:", len(items))

    for item in items:
        try:
            link = item.get_attribute("href")
            raw_text = item.text

            if link and re.search(r"/product/\d+$", link) and raw_text.strip():

                lines = raw_text.split("\n")
                title = lines[0].strip()

                # =========================
                # 🔥 가격 파싱 (완성형)
                # =========================
                price = None

                for i in range(len(lines)):
                    line = lines[i].strip()

                    # 1️⃣ "105만원"
                    match_man = re.search(r"(\d+)\s*만원", line)
                    if match_man:
                        price = int(match_man.group(1)) * 10000
                        break

                    # 2️⃣ "1,050,000원"
                    match_won = re.search(r"([\d,]+)\s*원", line)
                    if match_won:
                        price = int(match_won.group(1).replace(",", ""))
                        break

                    # 3️⃣ "1,050,000" + 다음줄 "원"
                    if i < len(lines) - 1 and "원" in lines[i + 1]:
                        num = re.sub(r"[^\d]", "", line)
                        if num:
                            price = int(num)
                            break

                # 🔥 노이즈 제거 (악세서리 제거)
                if price and price < 50000:
                    continue

                # 🔥 디버그 출력
                print("\n--- RAW ITEM ---")
                print("LINK:", link)
                print("RAW_TEXT:\n", raw_text)
                print("PARSED_TITLE:", title)
                print("PARSED_PRICE:", price)
                print("LINES:", lines)
                print("----------------")

                if price is None:
                    print("⚠️ 가격 못찾음:", lines)

                results.append({
                    "title": title,
                    "price": price,
                    "link": link
                })

        except:
            continue

    print(f"현재까지 수집된 개수: {len(results)}")

    # 종료 조건
    if len(results) >= num_how_many_results:
        break

    page += 1

    if page > 50:
        print("페이지 제한 도달 → 종료")
        break

# 👉 드라이버 종료
driver.quit()

# =========================
# 🔥 후처리
# =========================

# 중복 제거
unique_results = []
seen = set()

for r in results:
    if r["link"] not in seen:
        unique_results.append(r)
        seen.add(r["link"])

# 가격 있는 것만
filtered = [r for r in unique_results if r["price"] is not None]

# 가격 정렬
sorted_results = sorted(filtered, key=lambda x: x["price"])

print("\n=== 가격 낮은순 정렬 ===\n")

for i, r in enumerate(sorted_results[:num_how_many_results], 1):
    print(f"{i}. {r['title']}")
    print(f"   가격: {r['price']:,}원")
    print(f"   링크: {r['link']}")
    print()

# =========================
# 🔥 중앙값 기반 90% 필터
# =========================

if len(filtered) > 0:
    prices_np = np.array([r["price"] for r in filtered])

    median = np.median(prices_np)
    distances = np.abs(prices_np - median)

    cutoff_index = int(len(distances) * 0.9)
    threshold = np.sort(distances)[cutoff_index]

    filtered_90 = [
        r for r in filtered
        if abs(r["price"] - median) <= threshold
    ]

    sorted_90 = sorted(filtered_90, key=lambda x: x["price"])

    print("\n=== 중앙값 기준 90% 데이터 ===\n")

    for i, r in enumerate(sorted_90[:num_how_many_results], 1):
        print(f"{i}. {r['title']}")
        print(f"   가격: {r['price']:,}원")
        print(f"   링크: {r['link']}")
        print()

    # 🔥 리스트 따로 저장
    titles_90 = [r["title"] for r in sorted_90]
    prices_90 = [r["price"] for r in sorted_90]
    links_90 = [r["link"] for r in sorted_90]

    print("\n=== 90% 데이터 개수 ===")
    print(len(filtered_90), "/", len(filtered))

    # 🔥 리스트 출력
    for i in range(len(titles_90)):
        print(f"{i+1}. {titles_90[i]}")
        print(f"   가격: {prices_90[i]:,}원")
        print(f"   링크: {links_90[i]}")
        print()

else:
    print("⚠️ 가격 데이터 없음 → 분석 불가")