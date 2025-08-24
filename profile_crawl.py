from playwright.sync_api import sync_playwright
import json

def scrape_x_profile_json(profile_url: str) -> dict:
    """Scrape X profile data"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        profile_data = None

        def capture_response(response):
            nonlocal profile_data
            if "UserByScreenName" in response.url and response.status == 200:
                try:
                    body = response.body()
                    profile_data = json.loads(body)
                except:
                    pass

        page.on("response", capture_response)

        page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)

        # Wait up to 10 seconds for network calls
        for _ in range(20):
            if profile_data:
                break
            page.wait_for_timeout(500)  # wait 0.5 sec

        browser.close()
        return profile_data["data"]["user"]["result"]

# test
profile_url = "https://x.com/cobie"
profile_data = scrape_x_profile_json(profile_url)
print(profile_data)

