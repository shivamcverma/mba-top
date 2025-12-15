from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re, json, time
from webdriver_manager.chrome import ChromeDriverManager
import platform

mba_sections = {
    "Top MBA Colleges in India": "https://www.shiksha.com/mba/ranking/top-mba-colleges-in-india/2-2-0-0-0",
}

def create_driver():
    options = Options()
    # options.add_argument("--headless")  # comment out for visible browser
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if platform.system() == "Windows":
        service = Service(ChromeDriverManager().install())
    else:
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
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)

                # Wait for cards to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.clear_float.desk-col.source-selected")
                    )
                )

                cards = driver.find_elements(By.CSS_SELECTOR, "div.clear_float.desk-col.source-selected")

                for card_element in cards:
                    try:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});", card_element
                        )
                        time.sleep(0.4)
                    
                        img_element = card_element.find_element(By.CSS_SELECTOR, "div.tuple-inst-img img")
                    
                        college_img = (
                            img_element.get_attribute("src")
                            or img_element.get_attribute("data-src")
                            or img_element.get_attribute("data-original")
                            or ""
                        )
                    except:
                        college_img = ""

 

                    try:
                        college_name = card_element.find_element(By.CSS_SELECTOR, "h4.f14_bold.link").text
                    except:
                        college_name = ""

                    try:
                        nirf_rank = card_element.find_element(By.CSS_SELECTOR, "div.flt_left.rank_section span.circleText").text
                    except:
                        nirf_rank = ""

                    fees, salary = "", ""
                    try:
                        for blk in card_element.find_elements(By.CSS_SELECTOR, "div.flex_v.text--secondary"):
                            text = blk.text
                            if "Fees" in text:
                                fees = text.replace("Fees", "").strip()
                            elif "Salary" in text:
                                salary = text.replace("Salary", "").strip()
                    except:
                        pass

                    business_today, outlook = "", ""
                    try:
                        for row in card_element.find_elements(By.CSS_SELECTOR, "div.hrzntl_flex"):
                            cols = row.find_elements(By.TAG_NAME, "div")
                            if len(cols) >= 2:
                                label = cols[1].text.lower()
                                match = re.search(r"\d+", cols[1].text)
                                number = match.group() if match else ""
                                if "business" in label:
                                    business_today = number
                                elif "outlook" in label:
                                    outlook = number
                    except:
                        pass

                    colleges_in_section.append({
                        "college_img": college_img,
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
