import os
import sys
import json
import asyncio
import random
import argparse
import time
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- Fix Windows Unicode ---
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "book_automation_progress.json")
LOCK_DIR = os.path.join(SCRIPT_DIR, ".chapter_locks")
MAX_RETRIES = 5
STALE_LOCK_MINUTES = 30

# --- Book Configurations (all supported books) ---
BOOK_CONFIGS = {
    "1": {
        "name": "GK — 10th Level (Foundation)",
        "base_dir": os.path.join(SCRIPT_DIR, "10th_Level", "GK", "Foundation_10th_GK_WorldClass"),
    },
    "2": {
        "name": "GK — 12th Level (Intermediate)",
        "base_dir": os.path.join(SCRIPT_DIR, "12th_Level", "GK", "Intermediate_12th_GK_WorldClass"),
    },
    "3": {
        "name": "GK — Graduation Level (Advanced)",
        "base_dir": os.path.join(SCRIPT_DIR, "Graduation_Level", "GK", "Advanced_Graduation_GK_WorldClass"),
    },
    "4": {
        "name": "Reasoning — 10th Level (Foundation)",
        "base_dir": os.path.join(SCRIPT_DIR, "10th_Level", "Reasoning"),
    },
    "5": {
        "name": "Reasoning — 12th Level (Intermediate)",
        "base_dir": os.path.join(SCRIPT_DIR, "12th_Level", "Reasoning"),
    },
    "6": {
        "name": "Reasoning — Graduation Level (Advanced)",
        "base_dir": os.path.join(SCRIPT_DIR, "Graduation_Level", "Reasoning"),
    },
}

# Default: GK 10th Level
BASE_DIR = BOOK_CONFIGS["1"]["base_dir"]

def select_book(book_arg=None):
    """Interactive or CLI-based book selection. Returns BASE_DIR path."""
    global BASE_DIR

    if book_arg:
        if book_arg in BOOK_CONFIGS:
            BASE_DIR = BOOK_CONFIGS[book_arg]["base_dir"]
            print(f"  📚 Selected: {BOOK_CONFIGS[book_arg]['name']}")
            return BASE_DIR
        else:
            print(f"  ❌ Invalid book number: {book_arg}")
            return None

    print("\n" + "=" * 60)
    print("  📚 Book Selection — कौन सी किताब बनानी है?")
    print("=" * 60)
    for key, cfg in BOOK_CONFIGS.items():
        path = cfg["base_dir"]
        exists = "✅" if os.path.exists(path) else "❌ (folder missing)"
        chapters = 0
        if os.path.exists(path):
            chapters = len([d for d in os.listdir(path) if d.startswith("Chapter_")])
        print(f"  [{key}] {cfg['name']}  — {chapters} chapters {exists}")
    print("=" * 60)

    while True:
        choice = input("\n👉 Book number chunein (1-6): ").strip()
        if choice in BOOK_CONFIGS:
            BASE_DIR = BOOK_CONFIGS[choice]["base_dir"]
            if not os.path.exists(BASE_DIR):
                print(f"  ❌ {BASE_DIR} folder nahi mila! Pehle GK.py ya Reasoning.py run karein.")
                return None
            print(f"  ✅ Selected: {BOOK_CONFIGS[choice]['name']}")
            return BASE_DIR
        print("  ❌ Invalid choice. 1-6 mein se chunein.")

# --- Lock System ---
def ensure_lock_dir():
    os.makedirs(LOCK_DIR, exist_ok=True)

def get_lock_path(chapter_folder):
    return os.path.join(LOCK_DIR, f"{chapter_folder}.lock")

def is_process_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False

def read_lock(chapter_folder):
    path = get_lock_path(chapter_folder)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        # Stale lock check
        locked_at = datetime.fromisoformat(data.get("locked_at", ""))
        elapsed = (datetime.now() - locked_at).total_seconds() / 60
        if elapsed > STALE_LOCK_MINUTES and not is_process_alive(data.get("pid", 0)):
            os.remove(path)
            return None
        return data
    except:
        return None

def acquire_lock(chapter_folder, instance_id):
    ensure_lock_dir()
    lock = read_lock(chapter_folder)
    if lock and lock.get("locked_by") != instance_id:
        return False
    data = {
        "locked_by": instance_id,
        "locked_at": datetime.now().isoformat(),
        "pid": os.getpid(),
        "chapter": chapter_folder
    }
    with open(get_lock_path(chapter_folder), 'w') as f:
        json.dump(data, f, indent=2)
    return True

def release_lock(chapter_folder, instance_id):
    path = get_lock_path(chapter_folder)
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if data.get("locked_by") == instance_id:
            os.remove(path)
    except:
        pass

def release_all_my_locks(instance_id):
    if not os.path.exists(LOCK_DIR):
        return
    for f in os.listdir(LOCK_DIR):
        if f.endswith(".lock"):
            try:
                path = os.path.join(LOCK_DIR, f)
                with open(path, 'r') as fh:
                    data = json.load(fh)
                if data.get("locked_by") == instance_id:
                    os.remove(path)
            except:
                pass

# --- Progress System ---
def load_progress():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {"completed_paths": []}

def is_path_completed(file_path, log):
    """Case-insensitive path comparison for Windows"""
    norm = os.path.normcase(file_path)
    return any(os.path.normcase(p) == norm for p in log["completed_paths"])

def save_progress(path):
    # Re-read every time for multi-instance safety
    log = load_progress()
    if not is_path_completed(path, log):
        log["completed_paths"].append(path)
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=4)

# --- Chapter Menu ---
def get_chapter_status(folder, log):
    folder_path = os.path.join(BASE_DIR, folder)
    prompts_dir = os.path.join(folder_path, "Prompts")
    target_dir = prompts_dir if os.path.exists(prompts_dir) else folder_path
    
    files = [f for f in os.listdir(target_dir) if f.endswith(".txt")]
    if not files:
        return "empty", 0, 0
    done = sum(1 for f in files if is_path_completed(os.path.join(target_dir, f), log))
    if done >= len(files):
        return "complete", done, len(files)
    return "pending", done, len(files)

def display_chapter_menu(chapter_dirs, log, instance_id):
    print("\n" + "=" * 65)
    print("  📚 DeepSeek Book Builder — Chapter Selector")
    print("=" * 65)
    print(f"  {'No.':<6}{'Chapter':<35}{'Status':<20}")
    print("  " + "-" * 60)

    for i, folder in enumerate(chapter_dirs, 1):
        name = folder.replace("Chapter_", "").replace("_", " ")
        # Remove leading number
        parts = name.split(" ", 1)
        if len(parts) > 1 and parts[0].isdigit():
            name = parts[1]

        status, done, total = get_chapter_status(folder, log)
        lock = read_lock(folder)

        if status == "complete":
            icon = f"✅ Done ({done}/{total})"
        elif lock and lock.get("locked_by") != instance_id:
            icon = f"🔒 Locked ({lock['locked_by']})"
        elif done > 0:
            icon = f"🔄 {done}/{total} files"
        else:
            icon = f"⏳ Pending (0/{total})"

        print(f"  {i:<6}{name:<35}{icon}")

    print("  " + "-" * 60)
    print("  0  = Auto (first available pending chapter)")
    print("  q  = Quit")
    print("=" * 65)

def select_chapters(chapter_dirs, log, instance_id):
    display_chapter_menu(chapter_dirs, log, instance_id)
    while True:
        choice = input("\n👉 Chapter number enter karein (e.g. 5 ya 5,7,9): ").strip()
        if choice.lower() == 'q':
            return []
        if choice == '0':
            # Auto: select ALL unlocked pending chapters
            selected = []
            for i, folder in enumerate(chapter_dirs):
                st, _, _ = get_chapter_status(folder, log)
                if st != "complete" and not read_lock(folder):
                    selected.append(folder)
            
            if selected:
                print(f"  🎯 Auto-selected ALL {len(selected)} pending chapters!")
                return selected
            else:
                print("  ❌ Koi available pending chapter nahi mila!")
                return []
        try:
            nums = [int(x.strip()) for x in choice.split(",")]
            selected = []
            
            if len(nums) == 1:
                # Start from this chapter and select all pending to the end
                start_idx = nums[0] - 1
                if 0 <= start_idx < len(chapter_dirs):
                    for i in range(start_idx, len(chapter_dirs)):
                        folder = chapter_dirs[i]
                        st, _, _ = get_chapter_status(folder, log)
                        lock = read_lock(folder)
                        if st != "complete" and not (lock and lock.get("locked_by") != instance_id):
                            selected.append(folder)
                    if selected:
                        print(f"  🎯 Auto-selected {len(selected)} chapters continuously starting from {nums[0]}!")
                        return selected
                else:
                    print(f"  ⚠️ Invalid number: {nums[0]}")
            else:
                for n in nums:
                    if 1 <= n <= len(chapter_dirs):
                        folder = chapter_dirs[n - 1]
                        lock = read_lock(folder)
                        if lock and lock.get("locked_by") != instance_id:
                            print(f"  ⚠️ Chapter {n} locked by {lock['locked_by']}. Skip.")
                        else:
                            selected.append(folder)
                    else:
                        print(f"  ⚠️ Invalid number: {n}")
                if selected:
                    return selected
        except ValueError:
            print("  ❌ Invalid input. Number ya comma-separated numbers dein.")

# --- Network & DeepSeek Helpers ---
async def wait_for_internet(page, max_wait=300):
    print("  🌐 Internet check kar raha hoon...")
    for i in range(max_wait // 5):
        try:
            await page.evaluate("() => navigator.onLine")
            response = await page.goto("https://chat.deepseek.com/", timeout=15000)
            if response and response.ok:
                print("  ✅ Internet wapas aa gaya!")
                await asyncio.sleep(3)
                return True
        except:
            pass
        print(f"  ⏳ Internet nahi hai... retry {i+1} (har 5 sec mein check)")
        await asyncio.sleep(5)
    return False

async def switch_to_expert_mode(page):
    """DeepSeek UI mein Expert tab click kare — Instant se Expert switch"""
    # Strategy 1: Direct "Expert" text tab click
    for selector, label in [
        ("div:has-text('Expert')", "Expert Tab"),
        ("span:has-text('Expert')", "Expert Span"),
        ("button:has-text('Expert')", "Expert Button"),
        ("[role='tab']:has-text('Expert')", "Expert Role-Tab"),
    ]:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=3000):
                await btn.click()
                print(f"  🧠 {label} Mode ON!")
                await asyncio.sleep(2)
                return True
        except:
            pass

    # Strategy 2: Click by exact text
    try:
        await page.get_by_text("Expert", exact=True).first.click()
        print("  🧠 Expert Mode ON! (text match)")
        await asyncio.sleep(2)
        return True
    except:
        pass

    # Strategy 3: Old DeepThink selectors (fallback)
    for selector, label in [
        ("div:has-text('DeepThink')", "DeepThink"),
        ("button:has-text('Think')", "Think"),
    ]:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                print(f"  🧠 {label} Mode ON!")
                await asyncio.sleep(1)
                return True
        except:
            pass

    print("  ⚠️ Expert mode button nahi mila. Manual switch karein ya ENTER dabayein...")
    return False

async def safe_action(page, action_func, description, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            return await action_func()
        except Exception as e:
            error_msg = str(e).lower()
            if any(k in error_msg for k in ["target closed", "net::err", "timeout", "disconnected", "connection"]):
                print(f"  ⚠️ {description} mein error: {e}")
                print(f"  🔄 Retry {attempt+1}/{retries}... 10 sec baad...")
                await asyncio.sleep(10)
                try:
                    await wait_for_internet(page)
                    await page.wait_for_selector("textarea", timeout=30000)
                except:
                    pass
            else:
                raise e
    print(f"  ❌ {description} failed after {retries} retries!")
    return None

# --- Dashboard ---
def show_dashboard(instance_id, port, current_chapter, file_done, file_total):
    print("\n" + "=" * 50)
    print(f"  📊 Instance: {instance_id} (Port {port})")
    print(f"  📂 Working: {current_chapter}")
    print(f"  📄 Files: {file_done}/{file_total}")
    # Show other active instances
    if os.path.exists(LOCK_DIR):
        others = []
        for f in os.listdir(LOCK_DIR):
            if f.endswith(".lock"):
                try:
                    with open(os.path.join(LOCK_DIR, f), 'r') as fh:
                        data = json.load(fh)
                    if data.get("locked_by") != instance_id:
                        others.append(f"    └─ {data['locked_by']} → {data['chapter']}")
                except:
                    pass
        if others:
            print(f"  👥 Other instances: {len(others)}")
            for o in others:
                print(o)
    print("=" * 50 + "\n")

# --- Main ---
async def automate_deepseek(port, selected_chapters, instance_id, browser_type="chrome", skip_login=False):
    import subprocess

    if browser_type.lower() == "edge":
        browser_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        browser_name = "Edge"
    else:
        browser_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(browser_path):
            browser_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        browser_name = "Chrome"

    # Port 9222 = original profile (login saved), others = new profiles
    if port == 9222:
        user_data_dir = os.path.join(SCRIPT_DIR, f"{browser_name.lower()}_profile")
    else:
        user_data_dir = os.path.join(SCRIPT_DIR, f"{browser_name.lower()}_profile_{port}")

    do_bypass_login = False
    if not skip_login:
        print("\n🔑 DeepSeek Login Option:")
        print("  [1] Google Login Bypass Mode (Browser normal mode me open hoga, aap login karke ENTER dabayein)")
        print("  [2] Direct Automation Mode (Aap pehle se logged in hain/profile ready hai)")
        choice = input("👉 Option chunein [Default: 2]: ").strip()
        if choice == "1":
            do_bypass_login = True

    if do_bypass_login:
        print(f"\n🔒 Google Login Bypass Mode active.")
        print(f"🚀 Launching {browser_name} in normal mode for login...")
        login_process = subprocess.Popen([
            browser_path,
            f"--user-data-dir={user_data_dir}",
            "--disable-blink-features=AutomationControlled",
            "https://chat.deepseek.com/sign_in"
        ])
        print(f"\n👉 Browser open ho gaya hai. Kripya Google ya email se login karein.")
        input("Login complete hone ke baad aur DeepSeek home page aane par yahan ENTER dabayein: ")
        
        print("  🧹 Closing login browser...")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(login_process.pid)], capture_output=True)
            else:
                login_process.terminate()
        except Exception as e:
            print(f"  ⚠️ Browser close karne me error: {e}")
        await asyncio.sleep(3) # Wait for file locks to release

    print(f"\n🚀 Launching {browser_name} on port {port}...")
    chrome_process = subprocess.Popen([
        browser_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--disable-blink-features=AutomationControlled",
        "https://chat.deepseek.com/"
    ])

    print(f"  ⏳ {browser_name} start hone ka wait... 8 sec...")
    await asyncio.sleep(8)

    try:
        async with async_playwright() as p:
            # Retry CDP connection up to 5 times
            browser = None
            for attempt in range(5):
                try:
                    print(f"  🔌 Connecting to Chrome CDP (attempt {attempt+1}/5)...")
                    browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=15000)
                    print("  ✅ Chrome se connected!")
                    break
                except Exception as e:
                    print(f"  ⚠️ Connect failed: {e}")
                    if attempt < 4:
                        print("  🔄 Retrying in 5 sec...")
                        await asyncio.sleep(5)
                    else:
                        print("  ❌ Chrome se connect nahi ho paya! Check karein ki Chrome chal raha hai.")
                        raise e
            context = browser.contexts[0]
            print(f"  📋 Context found. Pages: {len(context.pages)}")

            page = None
            for p_page in context.pages:
                try:
                    url = p_page.url
                    print(f"    Tab: {url[:60]}...")
                    if "deepseek.com" in url:
                        page = p_page
                        break
                except:
                    pass

            if not page:
                print("  🌐 DeepSeek tab nahi mila, naya open kar rahe hain...")
                page = await context.new_page()
                await page.goto("https://chat.deepseek.com/", timeout=30000)

            print("  🧹 Extra tabs band kar rahe hain...")
            for p_page in context.pages:
                if p_page != page:
                    try:
                        tab_url = p_page.url
                        # Skip Chrome internal pages — closing them causes hang
                        if tab_url.startswith("chrome://") or tab_url.startswith("chrome-extension://"):
                            print(f"    ⏭️ Skipping internal: {tab_url[:50]}")
                            continue
                        await p_page.close()
                        print(f"    ❌ Closed: {tab_url[:50]}")
                    except:
                        pass

            print("  🔝 Page bring to front...")
            await page.bring_to_front()
            
            print("  🕵️ Stealth apply kar rahe hain...")
            await stealth_async(page)
            
            print("  ✅ Setup complete!")

            if not skip_login and not do_bypass_login:
                print(f"\n[STEP 1] DeepSeek par Login karein ({instance_id}).")
                input("Login ke baad yahan ENTER dabayein: ")
            elif do_bypass_login:
                print(f"\n[STEP 1] Google Login Bypass completed. Session loaded!")
            else:
                print(f"\n[STEP 1] Skipping login prompt due to --skip-login flag.")

            for folder in selected_chapters:
                folder_path = os.path.join(BASE_DIR, folder)

                # Acquire lock
                if not acquire_lock(folder, instance_id):
                    lock = read_lock(folder)
                    print(f"  🔒 {folder} locked by {lock['locked_by']}. Skipping...")
                    continue

                prompts_dir = os.path.join(folder_path, "Prompts")
                target_dir = prompts_dir if os.path.exists(prompts_dir) else folder_path
                
                log = load_progress()
                files_to_process = sorted([f for f in os.listdir(target_dir) if f.endswith(".txt")])
                done_count = sum(1 for f in files_to_process if is_path_completed(os.path.join(target_dir, f), log))

                if done_count >= len(files_to_process):
                    print(f"  ⏭️ Already done: {folder}")
                    release_lock(folder, instance_id)
                    continue

                show_dashboard(instance_id, port, folder, done_count, len(files_to_process))
                print(f"\n📂 Processing: {folder}")

                # New Chat or New Tab
                if folder != selected_chapters[0]:
                    print("  🆕 Naya tab open kar rahe hain new chapter ke liye...")
                    new_page = await context.new_page()
                    await new_page.goto("https://chat.deepseek.com/", timeout=30000)
                    try:
                        await page.close()
                    except:
                        pass
                    page = new_page
                    await stealth_async(page)
                    await asyncio.sleep(3)
                else:
                    try:
                        await page.get_by_text("New Chat").first.click()
                        await asyncio.sleep(2)
                    except:
                        pass

                await switch_to_expert_mode(page)

                # Intro prompt first
                if "Chapter_Intro_Prompt.txt" in files_to_process:
                    files_to_process.remove("Chapter_Intro_Prompt.txt")
                    files_to_process.insert(0, "Chapter_Intro_Prompt.txt")

                for file_name in files_to_process:
                    file_full_path = os.path.join(target_dir, file_name)

                    log = load_progress()
                    if is_path_completed(file_full_path, log):
                        continue

                    print(f"  ✍️ Writing: {file_name}...")

                    with open(file_full_path, 'r', encoding='utf-8') as f:
                        prompt = f.read()

                    # Capture the last response text BEFORE sending the prompt
                    try:
                        all_texts_before = await page.locator(".ds-markdown").all_inner_texts()
                        last_text_before_prompt = all_texts_before[-1] if all_texts_before else None
                    except:
                        last_text_before_prompt = None

                    async def send_prompt():
                        await page.wait_for_selector("textarea", timeout=60000)
                        await page.locator("textarea").fill(prompt)
                        await page.keyboard.press("Enter")

                    result = await safe_action(page, send_prompt, f"Sending prompt for {file_name}")

                    # Wait for AI response
                    await asyncio.sleep(5)
                    last_text = ""
                    unchanged_count = 0
                    error_count = 0

                    while True:
                        try:
                            current_responses = await page.locator(".ds-markdown").all_inner_texts()
                            if not current_responses:
                                await asyncio.sleep(3)
                                error_count = 0
                                continue

                            current_text = current_responses[-1]
                            
                            # WAIT FOR NEW GENERATION TO START
                            if current_text == last_text_before_prompt:
                                print(f"  ⏳ Waiting for DeepSeek to start generating...")
                                if not await page.evaluate("() => navigator.onLine"):
                                    print("  🌐 Internet down! Waiting for connection...")
                                    await wait_for_internet(page)
                                    # Try to click regenerate if it failed
                                    try:
                                        regen_btn = page.locator("div.ds-icon-button", has_text="Regenerate").first
                                        if await regen_btn.is_visible(timeout=2000):
                                            print("  🔄 Clicked Regenerate button after network error.")
                                            await regen_btn.click()
                                    except:
                                        pass
                                await asyncio.sleep(3)
                                continue

                            if current_text == last_text and len(current_text) > 0:
                                is_online = await page.evaluate("() => navigator.onLine")
                                if not is_online:
                                    print("  🌐 Internet disconnected during generation! Waiting...")
                                    await wait_for_internet(page)
                                    unchanged_count = 0
                                else:
                                    unchanged_count += 1
                            else:
                                unchanged_count = 0
                                last_text = current_text

                            if unchanged_count >= 5: # increased from 4 to 5 for safety
                                break

                            page_content = (await page.content()).lower()
                            if "quota exceeded" in page_content or "too many requests" in page_content:
                                print("🛑 Quota Limit! Nayi ID login karein aur ENTER dabayein.")
                                input("ID badalne ke baad ENTER dabayein...")
                                await page.locator("textarea").fill(prompt)
                                await page.keyboard.press("Enter")
                                unchanged_count = 0
                                last_text = ""

                            error_count = 0
                            await asyncio.sleep(3)

                        except Exception as e:
                            error_count += 1
                            print(f"  ⚠️ Response wait error ({error_count}/{MAX_RETRIES}): {e}")
                            if error_count >= MAX_RETRIES:
                                print(f"  ❌ Too many errors, skipping {file_name}")
                                break
                            print("  🔄 Recovering... 10 sec wait...")
                            await asyncio.sleep(10)
                            try:
                                recovered = await wait_for_internet(page)
                                if recovered:
                                        # Update last_text_before_prompt before resending
                                        try:
                                            all_texts_before = await page.locator(".ds-markdown").all_inner_texts()
                                            last_text_before_prompt = all_texts_before[-1] if all_texts_before else None
                                        except:
                                            pass

                                        await page.wait_for_selector("textarea", timeout=30000)
                                        await page.locator("textarea").fill(prompt)
                                        await page.keyboard.press("Enter")
                                        unchanged_count = 0
                                        last_text = ""
                                        error_count = 0
                                        await asyncio.sleep(5)
                            except:
                                pass

                    # Save response
                    try:
                        import re
                        all_elements = await page.locator(".ds-markdown").all()
                        if all_elements:
                            last_el = all_elements[-1]
                            final_text = await last_el.evaluate("el => el.innerText")
                            final_text = re.sub(r'\n{3,}', '\n\n', final_text)
                            final_text = re.sub(r'[ \t]+\n', '\n', final_text)
                            final_text = re.sub(r'\n[ \t]+\n', '\n\n', final_text)
                            final_text = final_text.strip()

                            with open(file_full_path, 'w', encoding='utf-8') as f:
                                f.write(final_text)

                            save_progress(file_full_path)
                            print(f"  ✔️ Done: {file_name}")
                        else:
                            print(f"  ⚠️ No response for: {file_name}")
                    except Exception as e:
                        print(f"  ⚠️ Save error: {e}")

                    print("  ⏳ Waiting ~30 sec buffer...")
                    await asyncio.sleep(random.uniform(25, 35))

                # Chapter done
                release_lock(folder, instance_id)
                print(f"\n✅ Chapter Complete: {folder}")

            print(f"\n🎉 {instance_id}: Saare selected chapters complete!")
            await browser.close()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        release_all_my_locks(instance_id)
    finally:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(chrome_process.pid)], capture_output=True)
            else:
                chrome_process.terminate()
        except:
            pass

def get_available_port(start_port=9222):
    import socket
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return start_port

def main():
    global BASE_DIR
    parser = argparse.ArgumentParser(description="DeepSeek Book Builder — Multi-Instance")
    parser.add_argument("--port", type=int, default=0, help="Chrome debug port (default: 0 for auto-assign)")
    parser.add_argument("--browser", type=str, default="chrome", choices=["chrome", "edge"], help="Select browser to use")
    parser.add_argument("--auto-chapters", type=str, default="", help="Comma separated list of chapters to process automatically (e.g. 1,2,3,4)")
    parser.add_argument("--skip-login", action="store_true", help="Skip the login prompt")
    parser.add_argument("--book", type=str, default="", help="Book number (1-6): 1=GK 10th, 2=GK 12th, 3=GK Grad, 4=Reasoning 10th, 5=Reasoning 12th, 6=Reasoning Grad")
    args = parser.parse_args()

    port = args.port if args.port != 0 else get_available_port(9222)
    instance_id = f"Instance_{port}"

    print(f"\n🚀 DeepSeek Builder — {instance_id}")

    # --- Book Selection ---
    selected_dir = select_book(args.book if args.book else None)
    if not selected_dir:
        print("❌ No valid book selected!")
        return
    BASE_DIR = selected_dir

    if not os.path.exists(BASE_DIR):
        print(f"❌ {BASE_DIR} folder nahi mila! Pehle GK.py ya Reasoning.py run karein.")
        return

    ensure_lock_dir()
    log = load_progress()
    chapter_dirs = sorted([d for d in os.listdir(BASE_DIR) if d.startswith("Chapter_")])

    if args.auto_chapters:
        nums = [int(x.strip()) for x in args.auto_chapters.split(",")]
        selected = []
        for n in nums:
            if 1 <= n <= len(chapter_dirs):
                folder = chapter_dirs[n - 1]
                lock = read_lock(folder)
                if lock and lock.get("locked_by") != instance_id:
                    print(f"  ⚠️ Chapter {n} locked by {lock['locked_by']}. Skip.")
                else:
                    selected.append(folder)
    else:
        selected = select_chapters(chapter_dirs, log, instance_id)
    if not selected:
        print("👋 Bye!")
        return

    print(f"\n📋 Selected chapters: {', '.join(selected)}")

    try:
        asyncio.run(automate_deepseek(port, selected, instance_id, browser_type=args.browser, skip_login=args.skip_login))
    except KeyboardInterrupt:
        print("\n⛔ Interrupted! Releasing locks...")
    finally:
        release_all_my_locks(instance_id)
        print("🔓 All locks released.")

if __name__ == "__main__":
    main()
