from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re, json, time

mba_sections = {
    "Top MBA Colleges in India": "https://www.shiksha.com/mba/ranking/top-mba-colleges-in-india/2-2-0-0-0",
    "Private MBA Colleges in India": "https://www.shiksha.com/mba/ranking/top-private-mba-colleges-in-india/125-2-0-0-0",
    "Top MBA Colleges in Bangalore": "https://www.shiksha.com/mba/ranking/top-mba-colleges-in-bangalore/2-2-0-278-0",
    "Top MBA Colleges in Chennai": "https://www.shiksha.com/mba/ranking/top-mba-colleges-in-mumbai/2-2-0-151-0"
}

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import platform

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0")

    if platform.system() == "Windows":
        # Windows pe webdriver-manager use karo
        service = Service(ChromeDriverManager().install())
    else:
        # Linux / Render / VPS
        options.binary_location = "/usr/bin/chromium"
        service = Service("/usr/bin/chromedriver")

    return webdriver.Chrome(service=service, options=options)

def scrape():
    driver = create_driver()
    all_sections_data = []

    try:
        for category_name, category_url in mba_sections.items():
            colleges_in_section = []

            for page in range(1, 5):
                url = category_url if page == 1 else f"{category_url}?pageNo={page}"
                driver.get(url)

                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.clear_float.desk-col.source-selected")
                    )
                )

                soup = BeautifulSoup(driver.page_source, "html.parser")

                for card in soup.select("div.clear_float.desk-col.source-selected"):
                    name = card.select_one("h4.f14_bold.link")
                    college_name = name.get_text(strip=True) if name else ""

                    nirf = card.select_one("div.flt_left.rank_section span.circleText")
                    nirf_rank = nirf.get_text(strip=True) if nirf else ""

                    fees, salary = "", ""
                    for blk in card.select("div.flex_v.text--secondary"):
                        text = blk.get_text(" ", strip=True)
                        if "Fees" in text:
                            fees = text.replace("Fees", "").strip()
                        elif "Salary" in text:
                            salary = text.replace("Salary", "").strip()

                    business_today, outlook = "", ""
                    for row in card.select("div.hrzntl_flex"):
                        cols = row.find_all("div")
                        if len(cols) >= 2:
                            label = cols[1].get_text(strip=True).lower()
                            match = re.search(r"\d+", cols[1].get_text())
                            number = match.group() if match else ""
                            if "business" in label:
                                business_today = number
                            elif "outlook" in label:
                                outlook = number

                    colleges_in_section.append({
                        "name": college_name,
                        "nirf": nirf_rank,
                        "details": {
                            "fees": fees,
                            "salary": salary,
                            "rankings": {
                                "business_today": business_today,
                                "outlook": outlook
                            }
                        }
                    })

                time.sleep(2)

            all_sections_data.append({
                "category": category_name,
                "colleges": colleges_in_section
            })

    finally:
        driver.quit()

    with open("mba_data.json", "w", encoding="utf-8") as f:
        json.dump(all_sections_data, f, indent=2, ensure_ascii=False)

    print("✅ Data scraped & saved successfully")

if __name__ == "__main__":
    scrape()
