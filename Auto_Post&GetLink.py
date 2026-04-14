import pandas as pd
from playwright_stealth import stealth
from playwright.sync_api import sync_playwright
import os
import time
import random
import requests
from datetime import datetime

# --- FILE & API CONFIGURATION ---
EXCEL_FILE = "Indeed Job Post.xlsx"


#  —------------ !!!!!! READ THIS !!!!!! —------------
#  Sheet2 you can create it by your self
#  this Sheet2 is for testing only
#  after you confirm the program is run successfully,
#  you can change to Url (Ifixx)
TARGET_SHEET = "Sheet2"

WEBHOOK_URL = "https://api.watoolbox.com/webhooks/5DWKPOJ3O"
GROUP_ID = "120363165584902535@g.us"

def get_all_valid_title():
    """Reads JobTitles from Sheet2 that start with 'Internship'"""
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: File {EXCEL_FILE} not found.")
        return []
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=TARGET_SHEET)
        valid_titles = df[df['JobTitle'].dropna().astype(str).str.startswith('Internship', na=False)]
        return valid_titles['JobTitle'].tolist()
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return []

def send_to_watoolbox(message_content):
    """Sends message using the mandatory WAToolbox JSON schema"""
    payload = {
        "action": "send-message",
        "type": "text",
        "content": message_content,
        "phone": GROUP_ID
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f">>> Webhook Error: {response.text}")
    except Exception as e:
        print(f">>> WhatsApp Connection Error: {e}")

def send_whatsapp_and_terminal_report(full_title, full_url):
    """Formats and mirrors the individual link report to terminal and WhatsApp"""
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    report = (
        f"Account Name: Ifixx\n"
        f"Time: {now}\n"
        f"Automation Name: Indeed Get Link (Ifixx)\n"
        f"Remarks: The newest link is updated.\n"
        f"Job List:\n"
        f"{full_title}: {full_url}"
    )
    print("\n" + "-"*40 + "\n" + report + "\n" + "-"*40)
    send_to_watoolbox(report)

def update_excel_link(job_title, new_link):
    """Updates Excel Link column with retry logic"""
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
                    print(f">>> [SUCCESS] Excel database updated.")
                    return True
            break 
        except Exception:
            print(f">>> [RETRY] Excel locked. Retrying in 5s...")
            time.sleep(5)                                                       
    return False            

def main():
    all_title = get_all_valid_title()
    if not all_title: return

    pending_paid_jobs = [] 
    success_count = 0

    with sync_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "user_data")
        context = p.chromium.launch_persistent_context(
            user_data_dir, headless=False, viewport=None,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        page = context.pages[0]
        try: stealth(page)
        except: pass

        print("\n" + "="*60)
        print("############# INDEED AUTO POST & LINK RETRIEVAL #############")
        print("="*60)

        for index, full_title in enumerate(all_title, 1):
            print(f"\n>>> [JOB {index}/{len(all_title)}] POSTING: {full_title}")
            try:
                page.goto("https://employers.indeed.com/job-posting/choose-flow", wait_until="domcontentloaded")
                time.sleep(5)

                # 1. Search and Select
                selector_search = 'input[placeholder="Search by job title"]'
                page.wait_for_selector(selector_search, timeout=10000)
                page.click(selector_search)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.type(selector_search, full_title, delay=100)
                page.keyboard.press("Enter")
                time.sleep(6)

                page.get_by_text(full_title[:30]).first.dispatch_event("click")
                time.sleep(3)
                if page.locator('text=Make a selection').is_visible():
                    page.get_by_role("radio").first.click(force=True)

                # 2. Scroll and Continue
                page.mouse.click(314, 355) 
                page.keyboard.press("End")
                time.sleep(2)
                page.locator('button[data-testid="footer-continue-btn"]').filter(visible=True).first.click(force=True)
                time.sleep(6)

                # 3. Set Hires Number
                selector_hires = 'input[data-testid="job-hires-needed-input"]'
                if page.locator(selector_hires).is_visible():
                    page.click(selector_hires)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.type(selector_hires, "5", delay=100)
                
                page.mouse.wheel(0, 1000)
                time.sleep(2)
                page.mouse.click(995, 420) 
                time.sleep(10)

                # --- 4. FINALIZING LOGIC ---
                selector_confirm = 'button[data-testid="location-change-confirm-button"]'
                agree_btn = page.locator('button[data-testid="footer-continue-btn"]').filter(visible=True).first
                save_btn = page.locator('button[data-dd-action-name="continue-button"]').filter(visible=True).first
                
                no_thanks = page.locator('button[data-dd-action-name="FTP-button"]').filter(visible=True).first
                sponsored = page.locator('button[data-dd-action-name="sponsored-button"]').filter(visible=True).first

                if page.locator(selector_confirm).is_visible():
                    page.click(selector_confirm, force=True)
                    time.sleep(4)
                    if agree_btn.is_visible(): agree_btn.click(force=True)
                else:
                    if agree_btn.is_visible(): agree_btn.click(force=True)
                    elif save_btn.is_visible(): save_btn.click(force=True)

                time.sleep(10) # Wait for redirect to sponsorship

                # --- 5. SPONSORSHIP BRANCHING ---
                if no_thanks.is_visible():
                    print(">>> Logic: Clicking 'No thanks' (Free).")
                    no_thanks.click(force=True)
                    time.sleep(6)
                    
                    # Capture link now
                    page.goto("https://employers.indeed.com/jobs?status=open%2Cpaused&claimed=false&createdOnIndeed=true&tab=0&sortDirection=DESC&sortField=datePostedOnIndeed", wait_until="domcontentloaded")
                    page.wait_for_selector('tr[data-testid="job-row"]', timeout=25000)
                    time.sleep(5)
                    first_row = page.locator('tr[data-testid="job-row"]').first
                    link_loc = first_row.locator('a[data-testid="UnifiedJobTldLink"]')
                    link_loc.wait_for(state="attached")
                    new_href = link_loc.get_attribute("href")
                    if new_href:
                        f_url = f"https://employers.indeed.com{new_href}"
                        update_excel_link(full_title, f_url)
                        send_whatsapp_and_terminal_report(full_title, f_url)
                        success_count += 1
                
                elif sponsored.is_visible():
                    print(f">>> Logic: 'No thanks' missing. Clicking 'Save and continue' (Sponsored).")
                    sponsored.click(force=True)
                    print(f"!!! [PENDING] Job {index} added to Monitoring Queue (Awaiting Payment).")
                    pending_paid_jobs.append(full_title)

            except Exception as e:
                print(f"Error on Job {index}: {e}")
                continue

        # --- PHASE 2: AUTO-MONITORING FOR PAYMENTS ---
        if pending_paid_jobs:
            print(f"\nMonitoring {len(pending_paid_jobs)} pending payments...")
            dash_url = "https://employers.indeed.com/jobs?status=open%2Cpaused&claimed=false&createdOnIndeed=true&tab=0&sortDirection=DESC&sortField=datePostedOnIndeed"
            while pending_paid_jobs:
                page.goto(dash_url, wait_until="domcontentloaded")
                time.sleep(10)
                rows = page.locator('tr[data-testid="job-row"]').all()
                for title in pending_paid_jobs[:]:
                    for row in rows:
                        if title[:30] in row.inner_text():
                            link_loc = row.locator('a[data-testid="UnifiedJobTldLink"]')
                            new_href = link_loc.get_attribute("href")
                            if new_href:
                                f_url = f"https://employers.indeed.com{new_href}"
                                print(f"✅ PAYMENT DETECTED: {title} is now ACTIVE.")
                                update_excel_link(title, f_url)
                                send_whatsapp_and_terminal_report(title, f_url)
                                success_count += 1
                                pending_paid_jobs.remove(title)
                                break
                if pending_paid_jobs:
                    print(f"Still waiting for {len(pending_paid_jobs)} payments. Refreshing in 60s...")
                    time.sleep(60) 

        # --- FINAL SUMMARY ---
        final_summary = (
            f"Account Name: Ifixx\n"
            f"Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"Task: Indeed Repost\n"
            f"Automation Name: Indeed Auto Post (Ifixx)\n"
            f"Remarks: All {success_count} new jobs is successfully posted."
        )
        print("\n" + "="*40 + "\nFINAL SUMMARY\n" + final_summary + "\n" + "="*40)
        send_to_watoolbox(final_summary)
        # input("")
        context.close()

if __name__ == "__main__":
    main()