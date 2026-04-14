import pandas as pd
from dotenv import load_dotenv
from playwright_stealth import stealth
from playwright.sync_api import sync_playwright
import os
import time
import random
import requests
from datetime import datetime

# --- FILE & API CONFIGURATION ---
EXCEL_FILE = "Indeed Job Post.xlsx"
SHEET_NAME = "Url (Ifixx)" 
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
GROUP_ID = os.getenv("GROUP_ID")

def get_all_valid_links():
    """Function to retrieve ALL valid links from the Excel file"""
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: File {EXCEL_FILE} not found.")
        return []
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        # Filter: Retrieve all rows where the 'Link' column starts with 'http'
        valid_links_series = df[df['Link'].astype(str).str.startswith('http', na=False)]
        return valid_links_series['Link'].tolist()
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def send_to_watoolbox(message_text):
    """Sends message using the official WaToolbox JSON schema from documentation"""
    payload = {
        "action": "send-message",
        "type": "text",
        "content": message_text,
        "phone": GROUP_ID
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f"Webhook Error: {response.text}")
    except Exception as e:
        print(f"WhatsApp Connection Error: {e}")

def send_whatsapp_and_terminal_report_close(current_url):
    """Formats and mirrors the individual close report to terminal and WhatsApp"""
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    report = (
        f"Account Name: Ifixx\n"
        f"Time: {now}\n"
        f"Task: Indeed Repost\n"
        f"Automation Name: Indeed Auto Close (Ifixx)\n"
        f"Remarks: Job closed successfully.\n"
        f"Job URL: {current_url}"
    )
    
    # 1. Mirror output to terminal
    print("\n" + "-"*40)
    print(report)
    print("-"*40 + "\n")
    
    # 2. Send to WhatsApp Group
    send_to_watoolbox(report)

def main():
    all_links = get_all_valid_links()
    if not all_links:
        print("Warning: No valid links found. Exiting...")
        return

    closed_jobs_count = 0

    with sync_playwright() as p:
        # Setup Browser with Persistent Context
        user_data_dir = os.path.join(os.getcwd(), "user_data")
        context = p.chromium.launch_persistent_context(
            user_data_dir, 
            headless=False, 
            viewport=None,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        
        page = context.pages[0]
        try:
            stealth(page)
        except:
            pass

        print("\n" + "="*60)
        print("############# INDEED AUTO CLOSE (Ifixx) #############")
        print("="*60)

        # --- STEP 1: WARM UP ---
        print("Step 1: Warm-up on Google...")
        page.goto("https://www.google.com")
        time.sleep(2)
        
        # --- STEP 2: CLOUDFLARE CHECK ---
        print("Step 2: Checking Cloudflare Verification on first link...")
        page.goto(all_links[0], wait_until="domcontentloaded")
        time.sleep(7) 

        # Cloudflare detection
        if "Just a moment" in page.title() or page.locator("iframe[src*='cloudflare']").count() > 0:
            print("\nCLOUDFLARE DETECTED!")
            # Automated verification wait based on your logic
            time.sleep(50)
            page.mouse.click(509, 218)  
            print("Verification challenge clicked.")
            time.sleep(10)

        print(f"\n--- Starting the Process: {len(all_links)} Links Found ---")

        # --- START LOOPING THROUGH EACH LINK ---
        for index, current_link in enumerate(all_links, 1):
            print(f"\n[{index}/{len(all_links)}] Checking: {current_link}")
            
            try:
                if index > 1:
                    page.goto(current_link, wait_until="domcontentloaded")
                    time.sleep(5)

                # Identify the status element
                status_box = page.locator('div[data-testid="top-level-job-status"]').filter(visible=True).first
                status_box.wait_for(state="visible", timeout=15000)
                
                current_status = status_box.inner_text().strip()
                print(f"Current Status: {current_status}")

                if "Closed" in current_status:
                    print(f">>> SKIPPED: Job-{index} is already 'Closed'.")
                    closed_jobs_count += 1
                    continue 

                else:
                    print(f">>> PROCESSING: Closing Job-{index}...")

                    # 1. Open Menu
                    status_box.click()
                    time.sleep(3)

                    # 2. Select Closed
                    try:
                        page.get_by_role("menuitem", name="Closed").click()
                    except:
                        page.get_by_text("Closed").first.click()
                    time.sleep(3)

                    # --- COORDINATE CLICKS FOR CLOSING (UNTOUCHED) ---
                    page.mouse.click(384, 418)  # Reason
                    time.sleep(2)
                    page.mouse.click(871, 523)  # Continue
                    time.sleep(2)
                    page.mouse.click(377, 526)  # Hiring on hold
                    time.sleep(2)
                    page.mouse.click(840, 598)  # Final Confirm
                    
                    closed_jobs_count += 1
                    
                    # --- INDIVIDUAL MIRRORED REPORT ---
                    send_whatsapp_and_terminal_report_close(current_link)

            except Exception as e:
                print(f"Error on row {index}: {e}")
            
            time.sleep(random.uniform(2, 5))

        # --- FINAL SUMMARY REPORT ---
        final_summary = (
            f"Account Name: Ifixx\n"
            f"Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"Task: Indeed Repost\n"
            f"Automation Name: Indeed Auto Close (Ifixx)\n"
            f"Remarks: All {closed_jobs_count} previous jobs is successfully closed."
        )

        print("\n" + "="*40)
        print("FINAL SESSION SUMMARY:")
        print(final_summary)
        print("="*40 + "\n")
        
        # Send Final Summary using the corrected JSON schema
        send_to_watoolbox(final_summary)

        print("\nALL CLOSE TASKS COMPLETED. PRESS ENTER TO EXIT.")
        # input("")
        context.close()

if __name__ == "__main__":
    main()