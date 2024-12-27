import os
from flask import Flask, json, render_template, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
import requests
import asyncio
import aiohttp

app = Flask(__name__)
CORS(app)

async def fetch_public_ip():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.ipify.org') as response:
            return await response.text()

async def fetch_all_records():
    api_url = "https://twitertrend.onrender.com/api/trends"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status != 200:
                return {"error": f"Failed to fetch data: {response.status}"}
            return await response.json()

async def twitter_login_and_get_attributes():
    proxy_pac_url = "file://./configs/proxy.pac"  # Path to your PAC file

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(f"--proxy-pac-url={proxy_pac_url}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Fetch current time
        current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

        driver.get("https://twitter.com/login")

        username = "saravan19212894"
        email = "saravananannewday@gmail.com"
        password = "clashofclans"

        # Enter username
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@name="text"]'))
        )
        username_field.send_keys(username)

        # Click next button
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/button[2]'))
        )
        next_button.click()

        # Check if email field is required
        try:
            email_field = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[2]/label/div/div[2]/div/input'))
            )
            email_field.send_keys(email)

            next_button_again = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/button'))
            )
            next_button_again.click()
        except:
            pass

        # Enter password
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@name="password"]'))
        )
        password_field.send_keys(password)

        # Click login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/button'))
        )
        login_button.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Timeline: Trending now"]'))
        )

        # Click on the specified element
        target_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div/div[7]/div/a/div'))
        )
        target_element.click()

        # Collect text content for trends
        span_xpath = '//span[@dir="ltr" and contains(@class, "css-1jxf684")]'
        trend_elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, span_xpath))
        )
        top_5_trends = [trend.text for trend in trend_elements[:5]]

        # Fetch public IP address asynchronously
        public_ip = await fetch_public_ip()

        data = {
            "currentTime": current_time,
            "publicIp": public_ip,
            "trends": top_5_trends
        }

        driver.quit()
        return data

    except Exception as e:
        driver.quit()
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['GET'])
async def run_script():
    selenium_data = await twitter_login_and_get_attributes()  # Run your Selenium script and get one data set
    if "error" in selenium_data:
        return jsonify({"error": selenium_data["error"]}), 500
    
    records = await fetch_all_records()  # Fetch all records from your API endpoint
    if "error" in records:
        return jsonify({"error": records["error"]}), 500
    
    # Combine selenium_data and records into one response
    combined_data = {
        "selenium_data": selenium_data,
        "db_data": records
    }
    
    return app.response_class(
        response=json.dumps(combined_data, ensure_ascii=False),  # Disable ASCII encoding
        status=200,
        mimetype="application/json"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
