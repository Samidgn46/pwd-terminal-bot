#!/usr/bin/env python3
import time
import os
import traceback
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False


class PWDBot:

    PWD_URL = "https://labs.play-with-docker.com/"

    def __init__(self, headless=True, timeout=40):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.wait = None
        self.short_wait = None
        self.label = ""
        os.makedirs("screenshots", exist_ok=True)

    # ── yardimci ──────────────────────────────────────────

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}][{self.label}] {msg}")

    def snap(self, name):
        try:
            p = f"screenshots/{self.label}_{name}_{int(time.time())}.png"
            self.driver.save_screenshot(p)
        except Exception:
            pass

    def safe_click(self, el):
        try:
            el.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", el)

    def find_click(self, sels, desc="element"):
        for by, sel in sels:
            try:
                el = self.short_wait.until(
                    EC.element_to_be_clickable((by, sel))
                )
                self.safe_click(el)
                self.log(f"  {desc} tiklandi")
                return True
            except (TimeoutException, NoSuchElementException):
                continue
        return False

    def find_type(self, sels, text, desc="input"):
        for by, sel in sels:
            try:
                el = self.short_wait.until(
                    EC.presence_of_element_located((by, sel))
                )
                el.clear()
                time.sleep(0.3)
                for ch in text:
                    el.send_keys(ch)
                    time.sleep(0.04)
                self.log(f"  {desc} yazildi")
                return True
            except (TimeoutException, NoSuchElementException):
                continue
        return False

    # ── tarayici ──────────────────────────────────────────

    def setup_driver(self):
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--lang=en-US")
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if HAS_WDM:
            svc = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=svc, options=opts)
        else:
            self.driver = webdriver.Chrome(options=opts)

        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"},
        )
        self.wait = WebDriverWait(
            self.driver, self.timeout,
            ignored_exceptions=[StaleElementReferenceException],
        )
        self.short_wait = WebDriverWait(self.driver, 12)
        self.log("Chrome baslatildi")

    # ── adim 1 : pwd ana sayfa ────────────────────────────

    def step1_goto_pwd(self):
        self.log("PWD sayfasina gidiliyor...")
        self.driver.get(self.PWD_URL)
        time.sleep(5)
        self.snap("01_anasayfa")

    # ── adim 2 : login tikla ─────────────────────────────

    def step2_click_login(self):
        self.log("Login butonu araniyor...")
        sels = [
            (By.XPATH, "//button[contains(translate(text(),'LOGIN','login'),'login')]"),
            (By.XPATH, "//a[contains(translate(text(),'LOGIN','login'),'login')]"),
            (By.XPATH, "//*[contains(@class,'login')]"),
            (By.XPATH, "//button[contains(text(),'Log in')]"),
            (By.XPATH, "//a[contains(text(),'Log in')]"),
            (By.CSS_SELECTOR, "button.btn-primary"),
            (By.XPATH, "//button[contains(@class,'btn')]"),
        ]
        if not self.find_click(sels, "Login"):
            self.snap("02_login_yok")
            raise Exception("Login butonu bulunamadi!")
        time.sleep(3)
        self.snap("02_login_ok")

    # ── adim 3 : docker provider tikla ───────────────────

    def step3_click_docker(self):
        self.log("Docker butonu araniyor...")
        sels = [
            (By.XPATH, "//a[contains(translate(text(),'DOCKER','docker'),'docker')]"),
            (By.XPATH, "//button[contains(translate(text(),'DOCKER','docker'),'docker')]"),
            (By.XPATH, "//*[contains(@class,'docker')]"),
            (By.XPATH, "//a[contains(@href,'docker')]"),
            (By.CSS_SELECTOR, ".modal-body a"),
            (By.CSS_SELECTOR, ".providers-list a"),
            (By.XPATH, "//div[contains(@class,'modal')]//a"),
        ]
        if not self.find_click(sels, "Docker"):
            self.snap("03_docker_yok")
            raise Exception("Docker butonu bulunamadi!")
        time.sleep(6)
        self.snap("03_docker_ok")

    # ── adim 4 : docker hub giris ────────────────────────

    def step4_docker_login(self, email, password):
        self.log("Docker Hub girisi...")

        original = self.driver.current_window_handle
        all_wins = self.driver.window_handles
        if len(all_wins) > 1:
            for w in all_wins:
                if w != original:
                    self.driver.switch_to.window(w)
                    break
            self.log("  Yeni sekmeye gecildi")

        time.sleep(5)
        self.snap("04_login_sayfa")
        self.log(f"  URL: {self.driver.current_url}")

        # --- email ---
        self.log("  Email yaziliyor...")
        email_sels = [
            (By.ID, "username"),
            (By.NAME, "username"),
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[name='username']"),
            (By.CSS_SELECTOR, "input[autocomplete='username']"),
        ]
        if not self.find_type(email_sels, email, "Email"):
            self.snap("04_email_yok")
            raise Exception("Email alani bulunamadi!")
        time.sleep(1)

        # --- continue ---
        self.log("  Continue tiklaniyor...")
        cont_sels = [
            (By.XPATH, "//button[contains(text(),'Continue')]"),
            (By.XPATH, "//button[contains(text(),'continue')]"),
            (By.XPATH, "//button[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "button[data-testid='continue-button']"),
        ]
        if not self.find_click(cont_sels, "Continue"):
            self.snap("04_continue_yok")
            raise Exception("Continue butonu bulunamadi!")
        time.sleep(6)
        self.snap("05_sifre_sayfa")

        # --- password ---
        self.log("  Sifre yaziliyor...")
        pw_sels = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@type='password']"),
        ]
        for attempt in range(4):
            if self.find_type(pw_sels, password, "Password"):
                break
            self.log(f"  Sifre alani bekleniyor... {attempt+1}")
            time.sleep(3)
        else:
            self.snap("05_sifre_yok")
            raise Exception("Sifre alani bulunamadi!")
        time.sleep(1)

        # --- sign in ---
        self.log("  Sign In tiklaniyor...")
        sign_sels = [
            (By.XPATH, "//button[contains(text(),'Sign In')]"),
            (By.XPATH, "//button[contains(text(),'Sign in')]"),
            (By.XPATH, "//button[contains(text(),'Log In')]"),
            (By.XPATH, "//button[contains(text(),'Log in')]"),
            (By.XPATH, "//button[contains(text(),'Login')]"),
            (By.XPATH, "//button[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "(//button[@type='submit'])[last()]"),
        ]
        if not self.find_click(sign_sels, "Sign In"):
            self.log("  Enter tusu deneniyor...")
            try:
                p = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                p.send_keys(Keys.RETURN)
            except Exception:
                raise Exception("Sign In bulunamadi!")

        time.sleep(10)
        self.snap("06_giris_ok")

        # --- authorize (varsa) ---
        auth_sels = [
            (By.XPATH, "//button[contains(text(),'Authorize')]"),
            (By.XPATH, "//button[contains(text(),'Accept')]"),
            (By.XPATH, "//button[contains(text(),'Allow')]"),
        ]
        if self.find_click(auth_sels, "Authorize"):
            time.sleep(5)

        # --- pwd sekmesine don ---
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(original)
            self.log("  PWD sekmesine donuldu")
            time.sleep(4)

        self.snap("07_pwd_ok")

    # ── adim 5 : start tikla ─────────────────────────────

    def step5_click_start(self):
        self.log("Start butonu araniyor...")
        time.sleep(3)

        start_sels = [
            (By.XPATH, "//button[contains(translate(text(),'START','start'),'start')]"),
            (By.XPATH, "//a[contains(translate(text(),'START','start'),'start')]"),
            (By.XPATH, "//*[contains(text(),'Start')]"),
            (By.CSS_SELECTOR, "button.btn-primary"),
            (By.CSS_SELECTOR, "button.btn-success"),
        ]

        for attempt in range(6):
            if self.find_click(start_sels, "Start"):
                time.sleep(6)
                self.snap("08_start_ok")
                return
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//*[contains(text(),'ADD NEW INSTANCE') or "
                    "contains(text(),'Add New Instance') or "
                    "contains(text(),'Add new instance')]",
                )
                self.log("  Session zaten aktif!")
                return
            except NoSuchElementException:
                pass
            self.log(f"  Start bekleniyor... {attempt+1}")
            time.sleep(3)

        self.snap("08_start_yok")
        raise Exception("Start butonu bulunamadi!")

    # ── adim 6 : add new instance ────────────────────────

    def step6_add_instance(self):
        self.log("Add New Instance araniyor...")
        time.sleep(3)

        inst_sels = [
            (By.XPATH, "//button[contains(text(),'ADD NEW INSTANCE')]"),
            (By.XPATH, "//button[contains(text(),'Add New Instance')]"),
            (By.XPATH, "//button[contains(text(),'Add new instance')]"),
            (By.XPATH, "//*[contains(text(),'ADD NEW INSTANCE')]"),
            (By.CSS_SELECTOR, "#newInstanceBtn"),
            (By.CSS_SELECTOR, "button[ng-click*='newInstance']"),
        ]

        for attempt in range(6):
            if self.find_click(inst_sels, "Add Instance"):
                time.sleep(10)
                self.snap("09_instance_ok")
                self.log("  Instance olusturuldu!")
                return
            self.log(f"  Instance bekleniyor... {attempt+1}")
            time.sleep(3)

        self.snap("09_instance_yok")
        raise Exception("Add Instance bulunamadi!")

    # ── adim 7 : komut calistir ──────────────────────────

    def step7_run_command(self, command):
        self.log("Terminale komut yaziliyor...")
        time.sleep(4)

        terminal = None
        term_sels = [
            (By.CSS_SELECTOR, ".xterm-helper-textarea"),
            (By.CSS_SELECTOR, "textarea.xterm-helper-textarea"),
            (By.CSS_SELECTOR, ".terminal textarea"),
        ]
        for by, sel in term_sels:
            try:
                terminal = self.wait.until(
                    EC.presence_of_element_located((by, sel))
                )
                self.log("  Terminal bulundu")
                break
            except TimeoutException:
                continue

        if terminal is None:
            self.log("  xterm-screen deneniyor...")
            try:
                scr = self.driver.find_element(By.CSS_SELECTOR, ".xterm-screen")
                ActionChains(self.driver).click(scr).perform()
                time.sleep(1)
                terminal = self.driver.find_element(
                    By.CSS_SELECTOR, ".xterm-helper-textarea"
                )
            except Exception:
                self.snap("10_terminal_yok")
                raise Exception("Terminal bulunamadi!")

        lines = command.strip().split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            self.log(f"  Komut [{i+1}/{len(lines)}]: {line[:70]}")
            terminal.send_keys(line)
            time.sleep(0.5)
            terminal.send_keys(Keys.RETURN)
            time.sleep(3)

        self.snap("10_komut_ok")
        self.log("  Komutlar gonderildi!")
        time.sleep(15)
        self.snap("11_sonuc")

    # ── ANA RUN METODU ───────────────────────────────────

    def run(self, email, password, command):
        """Tek hesap icin tum adimlari calistir."""
        self.label = email.split("@")[0] if "@" in email else email[:10]
        success = False

        try:
            self.log("=" * 50)
            self.log(f"BASLATILIYOR: {email}")
            self.log("=" * 50)

            self.setup_driver()
            self.step1_goto_pwd()
            self.step2_click_login()
            self.step3_click_docker()
            self.step4_docker_login(email, password)
            self.step5_click_start()
            self.step6_add_instance()
            self.step7_run_command(command)

            success = True
            self.log(f"BASARILI: {email}")

        except Exception as e:
            self.log(f"HATA: {e}")
            self.snap("HATA")
            traceback.print_exc()

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None

        return success
