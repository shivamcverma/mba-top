# mbacollege.py
from fastapi import FastAPI, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import asyncio
import re

app = FastAPI(title="MBA Colleges API")

# Cached data
cached_mba_data = []

# MBA sections URLs
mba_sections = {
    "Top MBA Colleges in India": "https://www.shiksha.com/mba/ranking/top-mba-colleges-in-india/2-2-0-0-0",
    "Private MBA Colleges in India": "https://www.shiksha.com/mba/ranking/top-private-mba-colleges-in-india/125-2-0-0-0",
    "Top MBA Colleges in Bangalore": "https://www.shiksha.com/mba/ranking/top-mba-colleges-in-bangalore/2-2-0-278-0",
    "Top MBA Colleges in Chennai": "https://www.shiksha.com/mba/ranking/top-mba-colleges-in-mumbai/2-2-0-151-0"
}

# ------------------------------- DRIVER CREATOR ------------------------------
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0")

    # Render environment paths
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    return webdriver.Chrome(service=service, options=options)

# ------------------------------- SCRAPER ------------------------------------
def scrape_mba_colleges():
    driver = create_driver()
    all_sections_data = []

    try:
        for category_name, category_url in mba_sections.items():
            colleges_in_section = []

            for page in range(1, 5):
                page_url = category_url if page == 1 else f"{category_url}?pageNo={page}"
                driver.get(page_url)

                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.clear_float.desk-col.source-selected")
                    )
                )

                soup = BeautifulSoup(driver.page_source, "html.parser")

                for college_card in soup.select("div.clear_float.desk-col.source-selected"):

                    name_tag = college_card.select_one("h4.f14_bold.link")
                    college_name = name_tag.get_text(strip=True) if name_tag else ""

                    nirf_tag = college_card.select_one("div.flt_left.rank_section span.circleText")
                    nirf_rank = nirf_tag.get_text(strip=True) if nirf_tag else ""

                    fees, salary = "", ""
                    for blk in college_card.select("div.flex_v.text--secondary"):
                        txt = blk.get_text(" ", strip=True)
                        if "Fees" in txt:
                            fees = txt.replace("Fees", "").strip()
                        elif "Salary" in txt:
                            salary = txt.replace("Salary", "").strip()

                    business_today, outlook_rank = "", ""
                    for row in college_card.select("div.hrzntl_flex"):
                        cols = row.find_all("div")
                        if len(cols) >= 2:
                            label = cols[1].get_text(strip=True).lower()
                            match = re.search(r'\d+', cols[1].get_text())
                            number = match.group() if match else ""
                            if "business" in label:
                                business_today = number
                            elif "outlook" in label:
                                outlook_rank = number

                    colleges_in_section.append({
                        "name": college_name,
                        "nirf": nirf_rank,
                        "details": {
                            "fees": fees,
                            "salary": salary,
                            "rankings": {
                                "business_today": business_today,
                                "outlook": outlook_rank
                            }
                        }
                    })

            all_sections_data.append({
                "category": category_name,
                "colleges": colleges_in_section
            })

    finally:
        driver.quit()

    return all_sections_data

# -------------------------- PERIODIC SCRAPER -----------------------------
async def periodic_scrape(interval=3600):
    global cached_mba_data
    while True:
        try:
            cached_mba_data = await asyncio.to_thread(scrape_mba_colleges)
        except Exception as e:
            print(f"Error during scraping: {e}")
        await asyncio.sleep(interval)

# --------------------------- STARTUP EVENT ------------------------------

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_scrape(interval=3600))


# --------------------------- UTIL ------------------------------
def get_all_colleges_with_id():
    colleges_list = []
    idx = 1
    for section in cached_mba_data:
        for college in section["colleges"]:
            temp = college.copy()
            temp["id"] = idx
            colleges_list.append(temp)
            idx += 1
    return colleges_list

# ----------------------------- ROUTES ------------------------------
@app.get("/")
async def root():
    return {"message": "API is running! Go to /mba_colleges to see all colleges."}

@app.get("/mba_colleges")
async def get_all_colleges():
    return {"mba_colleges": get_all_colleges_with_id()}

@app.get("/mba_colleges/{college_id}")
async def get_college_by_id(college_id: int):
    for college in get_all_colleges_with_id():
        if college["id"] == college_id:
            return college
    raise HTTPException(status_code=404, detail="College not found")
