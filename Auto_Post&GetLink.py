import pandas as pd
from dotenv import load_dotenv
from playwright_stealth import stealth
from playwright.sync_api import sync_playwright
import os
import time
import random
import requests
from datetime import datetime

# --- INITIALIZATION ---
load_dotenv()

# --- FILE & API CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "Indeed Job Post.xlsx")
TARGET_SHEET = "Url (Ifixx)" 

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
GROUP_ID = os.getenv("GROUP_ID")

if not WEBHOOK_URL:
    WEBHOOK_URL = "https://api.watoolbox.com/webhooks/5DWKPOJ3O"
    GROUP_ID = "120363165584902535@g.us"

def get_all_valid_title():
    if not os.path.exists(EXCEL_FILE):
        return []
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=TARGET_SHEET)
        return df[df['JobTitle'].dropna().astype(str).str.startswith('Internship', na=False)]['JobTitle'].tolist()
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return []

def send_to_watoolbox(message_content):
    payload = {
        "action": "send-message",
        "type": "text",
        "content": message_content,
        "phone": GROUP_ID
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code != 200:
            print(f">>> Webhook Error: {response.text}")
    except Exception as e:
        print(f">>> WhatsApp Connection Error: {e}")

def solve_cloudflare(page):
    """Detects Cloudflare, waits 50s, and clicks specific coordinates"""
    # Check by Title or specific Cloudflare elements
    is_cf = "Just a moment" in page.title() or page.locator("iframe[src*='cloudflare']").count() > 0
    
    if is_cf:
        print("\n" + "!"*60)
        print("CLOUDFLARE DETECTED! Starting 50-second countdown...")
        print("!"*60)
        
        # 50 second wait as requested
        for i in range(50, 0, -1):
            print(f"Waiting for security to process... {i} seconds remaining", end="\r")
            time.sleep(1)
        
        print("\nClicking verification coordinates (X:514, Y:209)...")
        page.mouse.click(514, 209)
        time.sleep(10) # Wait for page to transition after click
        return True
    return False

def update_excel_link(job_title, new_link):
    for attempt in range(3):
        try:
            excel_data = pd.read_excel(EXCEL_FILE, sheet_name=None)
            if TARGET_SHEET in excel_data:
                df = excel_data[TARGET_SHEET]
                mask = df['JobTitle'].astype(str).str.strip() == job_title.strip()
                if mask.any():
                    df.loc[mask, 'Link'] = new_link
                    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
                        for sheet_name, df_sheet in excel_data.items():
                            df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f">>> [EXCEL] Updated link for: {job_title[:30]}")
                    return True
            break 
        except Exception:
            time.sleep(5)
    return False

def main():
    all_title = get_all_valid_title()
    if not all_title: return
    success_count = 0
    dash_url = "https://employers.indeed.com/jobs?status=open%2Cpaused&claimed=false&createdOnIndeed=true&tab=0&sortDirection=DESC&sortField=datePostedOnIndeed"

    with sync_playwright() as p:
        user_data_dir = os.path.join(BASE_DIR, "user_data")
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False, viewport=None,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        page = context.pages[0] 
        
        try: stealth(page)
        except: pass

        print("\n" + "="*60 + "\n############# INDEED AUTO POST (SECURITY MONITORING) #############\n" + "="*60)

        for index, full_title in enumerate(all_title, 1):
            print(f"\n>>> [JOB {index}/{len(all_title)}] PROCESSING: {full_title}")
            try:
                # --- NAVIGATION 1 ---
                page.goto("https://employers.indeed.com/job-posting/choose-flow", wait_until="domcontentloaded")
                time.sleep(5)
                solve_cloudflare(page) # Constant Check 1

                # Search and Select
                selector_search = 'input[placeholder="Search by job title"]'
                page.wait_for_selector(selector_search, timeout=10000)
                page.click(selector_search); page.keyboard.press("Control+A"); page.keyboard.press("Backspace")
                page.type(selector_search, full_title, delay=100); page.keyboard.press("Enter")
                time.sleep(6)
                solve_cloudflare(page) # Constant Check 2 (After search trigger)

                page.get_by_text(full_title[:30]).first.dispatch_event("click"); time.sleep(3)
                if page.locator('text=Make a selection').is_visible(): page.get_by_role("radio").first.click(force=True)

                # Navigation
                page.mouse.click(314, 355); page.keyboard.press("End"); time.sleep(2)
                page.locator('button[data-testid="footer-continue-btn"]').filter(visible=True).first.click(force=True)
                time.sleep(6)

                # Set Hires
                selector_hires = 'input[data-testid="job-hires-needed-input"]'
                if page.locator(selector_hires).is_visible():
                    page.click(selector_hires); page.keyboard.press("Control+A"); page.keyboard.press("Backspace")
                    page.type(selector_hires, "5", delay=100)
                
                page.mouse.wheel(0, 1000); time.sleep(2); page.mouse.click(995, 420); time.sleep(10)

                # Finalizing
                selector_confirm = 'button[data-testid="location-change-confirm-button"]'
                agree_btn = page.locator('button[data-testid="footer-continue-btn"]').filter(visible=True).first
                no_thanks = page.locator('button[data-dd-action-name="FTP-button"]').filter(visible=True).first
                sponsored = page.locator('button[data-dd-action-name="sponsored-button"]').filter(visible=True).first

                if page.locator(selector_confirm).is_visible():
                    page.click(selector_confirm, force=True); time.sleep(4)
                    if agree_btn.is_visible(): agree_btn.click(force=True)
                else:
                    if agree_btn.is_visible(): agree_btn.click(force=True)

                time.sleep(12) 
                solve_cloudflare(page) # Constant Check 3 (Transition to Sponsorship)

                if no_thanks.is_visible(): no_thanks.click(force=True); time.sleep(8)
                elif sponsored.is_visible(): sponsored.click(force=True); time.sleep(8)

                # --- DASHBOARD NAVIGATION ---
                page.goto(dash_url, wait_until="domcontentloaded")
                solve_cloudflare(page) # Constant Check 4 (At Dashboard)
                page.wait_for_selector('tr[data-testid="job-row"]', timeout=30000)
                time.sleep(5)
                
                rows = page.locator('tr[data-testid="job-row"]').all()
                for row in rows:
                    if full_title[:30] in row.inner_text():
                        # --- RECOVERY LOGIC ---
                        finish_btn = row.locator('button:has-text("Finish posting")')
                        if finish_btn.is_visible():
                            print(f">>> [RECOVERY] Job {index} is INCOMPLETE. Clicking Finish Posting...")
                            finish_btn.click()
                            time.sleep(10)
                            solve_cloudflare(page) # Constant Check 5 (Inside Recovery)
                            page.keyboard.press("End"); time.sleep(2)
                            final_confirm = page.locator('button[data-testid="footer-continue-btn"]').filter(visible=True).first
                            if final_confirm.is_visible():
                                final_confirm.click(force=True)
                                time.sleep(10)
                                page.goto(dash_url, wait_until="domcontentloaded")
                                solve_cloudflare(page) # Constant Check 6 (Return to Dashboard)
                                page.wait_for_selector('tr[data-testid="job-row"]', timeout=30000)
                                row = page.locator('tr[data-testid="job-row"]').filter(has_text=full_title[:30]).first

                        # --- GET LINK ---
                        link_loc = row.locator('a[data-testid="UnifiedJobTldLink"]')
                        if link_loc.count() > 0:
                            new_href = link_loc.get_attribute("href")
                            if new_href:
                                full_url = f"https://employers.indeed.com{new_href}"
                                update_excel_link(full_title, full_url)
                                report = (f"Account Name: Ifixx\nTime: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                                          f"Automation Name: Indeed Get Link (Ifixx)\nRemarks: Link captured successfully.\n"
                                          f"Job List:\n{full_title}: {full_url}")
                                print(report); send_to_watoolbox(report)
                                success_count += 1; break
            except Exception as e:
                print(f"Error on Job {index}: {e}"); continue

        final_summary = f"Account Name: Ifixx\nTime: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nTask: Indeed Repost\nAutomation Name: Indeed Auto Post (Ifixx)\nRemarks: Processed {success_count} jobs."
        print("\n" + "="*40 + "\n" + final_summary + "\n" + "="*40); send_to_watoolbox(final_summary)
        context.close()

if __name__ == "__main__":
    main()