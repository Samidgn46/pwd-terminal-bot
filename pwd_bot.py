#!/usr/bin/env python3
"""
Play with Docker - Tam Otomatik Bot
Docker Hub girisi → PWD oturum → Instance olusturma → Komut calistirma
"""

import time
import json
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
    WebDriverException
)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False


class PWDBot:
    """Play with Docker otomasyonu icin ana sinif."""

    PWD_URL = "https://labs.play-with-docker.com/"
    DOCKER_LOGIN_URL = "https://login.docker.com"

    def __init__(self, headless=True, timeout=40, screenshot_dir="screenshots"):
        self.headless = headless
        self.timeout = timeout
        self.screenshot_dir = screenshot_dir
        self.driver = None
        self.wait = None
        self.short_wait = None
        self.account_label = ""

        os.makedirs(self.screenshot_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  BROWSER KURULUMU
    # ------------------------------------------------------------------ #
    def _setup_driver(self):
        """Chrome WebDriver'i yapilandir ve baslat."""
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

        # Anti-bot algilama onlemleri
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if USE_WDM:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opts)
        else:
            self.driver = webdriver.Chrome(options=opts)

        # navigator.webdriver flag'ini gizle
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            },
        )

        self.wait = WebDriverWait(
            self.driver,
            self.timeout,
            ignored_exceptions=[StaleElementReferenceException],
        )
        self.short_wait = WebDriverWait(self.driver, 10)

        self._log("Chrome baslatildi")

    # ------------------------------------------------------------------ #
    #  YARDIMCI FONKSIYONLAR
    # ------------------------------------------------------------------ #
    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        label = f"[{self.account_label}]" if self.account_label else ""
        print(f"[{ts}]{label} {msg}")

    def _screenshot(self, name):
        try:
            path = os.path.join(
                self.screenshot_dir,
                f"{self.account_label}_{name}_{int(time.time())}.png",
            )
            self.driver.save_screenshot(path)
            self._log(f"  Screenshot: {path}")
        except Exception:
            pass

    def _safe_click(self, element):
        """Tiklanamayan elemanlari JavaScript ile tikla."""
        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    def _find_and_click(self, selectors, description="element"):
        """
        Birden fazla CSS/XPath selektor dene, ilk bulunani tikla.
        selectors: [(By.XXX, "selector"), ...]
        """
        for by, selector in selectors:
            try:
                el = self.short_wait.until(
                    EC.element_to_be_clickable((by, selector))
                )
                self._safe_click(el)
                self._log(f"  {description} tiklandi: {selector}")
                return True
            except (TimeoutException, NoSuchElementException):
                continue
        return False

    def _find_and_type(self, selectors, text, description="input"):
        """
        Birden fazla selektor dene, ilk bulunana yaz.
        """
        for by, selector in selectors:
            try:
                el = self.short_wait.until(
                    EC.presence_of_element_located((by, selector))
                )
                el.clear()
                time.sleep(0.3)
                # Karakter karakter yaz (bot algilamaya karsi)
                for ch in text:
                    el.send_keys(ch)
                    time.sleep(0.05)
                self._log(f"  {description} yazildi: {selector}")
                return True
            except (TimeoutException, NoSuchElementException):
                continue
        return False

    def _wait_for_any(self, selectors, timeout=None):
        """Verilen selektorlerden herhangi birini bekle."""
        t = timeout or self.timeout
        end = time.time() + t
        while time.time() < end:
            for by, selector in selectors:
                try:
                    el = self.driver.find_element(by, selector)
                    if el.is_displayed():
                        return el
                except NoSuchElementException:
                    continue
            time.sleep(0.5)
        return None

    # ------------------------------------------------------------------ #
    #  ADIM 1: PWD ANA SAYFASINA GIT
    # ------------------------------------------------------------------ #
    def _navigate_to_pwd(self):
        self._log("PWD ana sayfasina gidiliyor...")
        self.driver.get(self.PWD_URL)
        time.sleep(4)
        self._screenshot("01_pwd_anasayfa")

    # ------------------------------------------------------------------ #
    #  ADIM 2: LOGIN BUTONUNA TIKLA
    # ------------------------------------------------------------------ #
    def _click_login(self):
        self._log("Login butonu araniyor...")
        login_selectors = [
            (By.XPATH, "//button[contains(translate(text(),'LOGIN','login'),'login')]"),
            (By.XPATH, "//a[contains(translate(text(),'LOGIN','login'),'login')]"),
            (By.XPATH, "//*[contains(@class,'login')]"),
            (By.XPATH, "//button[contains(text(),'Log in')]"),
            (By.XPATH, "//a[contains(text(),'Log in')]"),
            (By.CSS_SELECTOR, "button.btn-primary"),
            (By.CSS_SELECTOR, "#btnGroupDrop"),
            (By.XPATH, "//button[contains(@class,'btn')]"),
        ]

        if not self._find_and_click(login_selectors, "Login butonu"):
            self._screenshot("02_login_bulunamadi")
            raise Exception("Login butonu bulunamadi!")

        time.sleep(3)
        self._screenshot("02_login_sonrasi")

    # ------------------------------------------------------------------ #
    #  ADIM 3: DOCKER PROVIDER BUTONUNA TIKLA
    # ------------------------------------------------------------------ #
    def _click_docker_provider(self):
        self._log("Docker provider butonu araniyor...")
        docker_selectors = [
            (By.XPATH, "//a[contains(translate(text(),'DOCKER','docker'),'docker')]"),
            (By.XPATH, "//button[contains(translate(text(),'DOCKER','docker'),'docker')]"),
            (By.XPATH, "//*[contains(@class,'docker')]"),
            (By.XPATH, "//a[contains(@href,'docker')]"),
            (By.CSS_SELECTOR, ".modal-body a"),
            (By.CSS_SELECTOR, ".providers-list a"),
            (By.XPATH, "//div[contains(@class,'modal')]//a"),
        ]

        if not self._find_and_click(docker_selectors, "Docker butonu"):
            self._screenshot("03_docker_bulunamadi")
            raise Exception("Docker provider butonu bulunamadi!")

        time.sleep(5)
        self._screenshot("03_docker_sonrasi")

    # ------------------------------------------------------------------ #
    #  ADIM 4: DOCKER HUB GIRIS SAYFASI
    # ------------------------------------------------------------------ #
    def _handle_docker_login(self, email, password):
        self._log("Docker Hub giris sayfasi islemleri...")

        # Yeni sekmeye gec (Docker Hub login yeni sekmede acilir)
        original_window = self.driver.current_window_handle
        all_windows = self.driver.window_handles

        if len(all_windows) > 1:
            for w in all_windows:
                if w != original_window:
                    self.driver.switch_to.window(w)
                    break
            self._log("  Yeni sekmeye gecildi")
        else:
            self._log("  Ayni sekmede devam ediliyor")

        time.sleep(4)
        self._screenshot("04_docker_login_sayfasi")
        self._log(f"  Suanki URL: {self.driver.current_url}")

        # ---- EMAIL / USERNAME GIRISI ----
        self._log("  Email/username yaziliyor...")
        email_selectors = [
            (By.ID, "username"),
            (By.NAME, "username"),
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[name='username']"),
            (By.CSS_SELECTOR, "input[autocomplete='username']"),
            (By.XPATH, "//input[@id='username']"),
            (By.XPATH, "//input[@placeholder]"),
        ]

        if not self._find_and_type(email_selectors, email, "Email"):
            self._screenshot("04_email_bulunamadi")
            raise Exception("Email input alani bulunamadi!")

        time.sleep(1)

        # ---- CONTINUE BUTONUNA TIKLA ----
        self._log("  Continue butonuna tiklaniyor...")
        continue_selectors = [
            (By.XPATH, "//button[contains(text(),'Continue')]"),
            (By.XPATH, "//button[contains(text(),'continue')]"),
            (By.XPATH, "//button[contains(text(),'Devam')]"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "button.btn-primary"),
            (By.CSS_SELECTOR, "#continue-button"),
            (By.XPATH, "//button[contains(@class,'continue')]"),
            (By.XPATH, "//button[contains(@data-testid,'continue')]"),
        ]

        if not self._find_and_click(continue_selectors, "Continue butonu"):
            self._screenshot("04_continue_bulunamadi")
            raise Exception("Continue butonu bulunamadi!")

        time.sleep(5)
        self._screenshot("05_password_sayfasi")
        self._log(f"  Suanki URL: {self.driver.current_url}")

        # ---- SIFRE GIRISI ----
        self._log("  Sifre yaziliyor...")
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.XPATH, "//input[@type='password']"),
            (By.XPATH, "//input[@id='password']"),
        ]

        # Sayfanin tamamen yuklenmesini bekle
        for attempt in range(3):
            if self._find_and_type(password_selectors, password, "Password"):
                break
            self._log(f"  Sifre alani bekleniyor... deneme {attempt+1}")
            time.sleep(3)
        else:
            self._screenshot("05_password_bulunamadi")
            raise Exception("Password input alani bulunamadi!")

        time.sleep(1)

        # ---- SIGN IN / LOGIN BUTONUNA TIKLA ----
        self._log("  Sign In butonuna tiklaniyor...")
        signin_selectors = [
            (By.XPATH, "//button[contains(text(),'Sign In')]"),
            (By.XPATH, "//button[contains(text(),'Sign in')]"),
            (By.XPATH, "//button[contains(text(),'Log In')]"),
            (By.XPATH, "//button[contains(text(),'Log in')]"),
            (By.XPATH, "//button[contains(text(),'Login')]"),
            (By.XPATH, "//button[contains(text(),'Giris')]"),
            (By.XPATH, "//button[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "button[data-testid='sign-in-button']"),
            (By.XPATH, "//button[contains(@class,'sign-in')]"),
            (By.CSS_SELECTOR, "#sign-in-button"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "(//button[@type='submit'])[last()]"),
        ]

        if not self._find_and_click(signin_selectors, "Sign In butonu"):
            # Fallback: Enter tusuna bas
            self._log("  Sign In bulunamadi, Enter tusu deneniyor...")
            try:
                pwd_el = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                pwd_el.send_keys(Keys.RETURN)
            except Exception:
                self._screenshot("05_signin_bulunamadi")
                raise Exception("Sign In butonu bulunamadi!")

        time.sleep(8)
        self._screenshot("06_giris_sonrasi")

        # Authorize/Grant sayfasi varsa onayla
        self._handle_authorize_page()

        # PWD sekmesine geri don
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(original_window)
            self._log("  PWD sekmesine geri donuldu")
            time.sleep(3)

        self._screenshot("07_pwd_giris_yapildi")

    # ------------------------------------------------------------------ #
    #  ADIM 4.5: AUTHORIZE SAYFASI (varsa)
    # ------------------------------------------------------------------ #
    def _handle_authorize_page(self):
        """Docker Hub OAuth authorize sayfasi cikarsa onayla."""
        authorize_selectors = [
            (By.XPATH, "//button[contains(text(),'Authorize')]"),
            (By.XPATH, "//button[contains(text(),'Accept')]"),
            (By.XPATH, "//button[contains(text(),'Allow')]"),
            (By.XPATH, "//button[contains(text(),'Grant')]"),
            (By.XPATH, "//input[@value='Authorize']"),
        ]
        if self._find_and_click(authorize_selectors, "Authorize butonu"):
            self._log("  Authorize sayfasi onaylandi")
            time.sleep(5)

    # ------------------------------------------------------------------ #
    #  ADIM 5: START BUTONUNA TIKLA
    # ------------------------------------------------------------------ #
    def _click_start(self):
        self._log("Start butonu araniyor...")
        time.sleep(3)
        self._screenshot("08_start_oncesi")

        start_selectors = [
            (By.XPATH, "//button[contains(text(),'Start')]"),
            (By.XPATH, "//a[contains(text(),'Start')]"),
            (By.XPATH, "//*[contains(text(),'Start')]"),
            (By.CSS_SELECTOR, "button.btn-primary"),
            (By.CSS_SELECTOR, "#btnGroupDrop"),
            (By.XPATH, "//button[contains(@class,'btn-success')]"),
            (By.XPATH, "//button[contains(translate(text(),'START','start'),'start')]"),
        ]

        # Birden fazla deneme
        for attempt in range(5):
            if self._find_and_click(start_selectors, "Start butonu"):
                time.sleep(5)
                self._screenshot("08_start_sonrasi")
                return
            self._log(f"  Start butonu bekleniyor... deneme {attempt+1}")
            time.sleep(3)

            # Belki zaten session sayfasindayiz
            if self._check_if_session_active():
                self._log("  Zaten session aktif!")
                return

        self._screenshot("08_start_bulunamadi")
        raise Exception("Start butonu bulunamadi!")

    def _check_if_session_active(self):
        """Session sayfasinda mi kontrol et."""
        try:
            self.driver.find_element(
                By.XPATH,
                "//*[contains(text(),'ADD NEW INSTANCE') or contains(text(),'Add New Instance')]"
            )
            return True
        except NoSuchElementException:
            return False

    # ------------------------------------------------------------------ #
    #  ADIM 6: ADD NEW INSTANCE
    # ------------------------------------------------------------------ #
    def _add_instance(self):
        self._log("Add New Instance butonu araniyor...")
        time.sleep(3)

        instance_selectors = [
            (By.XPATH, "//button[contains(text(),'ADD NEW INSTANCE')]"),
            (By.XPATH, "//button[contains(text(),'Add New Instance')]"),
            (By.XPATH, "//button[contains(text(),'Add new instance')]"),
            (By.XPATH, "//*[contains(text(),'ADD NEW INSTANCE')]"),
            (By.CSS_SELECTOR, "#newInstanceBtn"),
            (By.CSS_SELECTOR, "button[ng-click*='newInstance']"),
            (By.CSS_SELECTOR, ".new-instance-btn"),
            (By.XPATH, "//button[contains(@class,'instance')]"),
        ]

        for attempt in range(5):
            if self._find_and_click(instance_selectors, "Add Instance butonu"):
                time.sleep(8)
                self._screenshot("09_instance_olusturuldu")
                self._log("  Instance olusturuldu!")
                return
            self._log(f"  Add Instance bekleniyor... deneme {attempt+1}")
            time.sleep(3)

        self._screenshot("09_instance_bulunamadi")
        raise Exception("Add New Instance butonu bulunamadi!")

    # ------------------------------------------------------------------ #
    #  ADIM 7: TERMINALE KOMUT YAZ VE CALISTIR
    # ------------------------------------------------------------------ #
    def _execute_command(self, command):
        self._log("Terminal'e komut yaziliyor...")
        time.sleep(3)

        # xterm.js terminal'ini bul
        terminal_selectors = [
            (By.CSS_SELECTOR, ".xterm-helper-textarea"),
            (By.CSS_SELECTOR, "textarea.xterm-helper-textarea"),
            (By.CSS_SELECTOR, ".terminal textarea"),
            (By.CSS_SELECTOR, ".xterm textarea"),
            (By.CSS_SELECTOR, "#terminal textarea"),
        ]

        terminal = None
        for by, selector in terminal_selectors:
            try:
                terminal = self.wait.until(
                    EC.presence_of_element_located((by, selector))
                )
                self._log(f"  Terminal bulundu: {selector}")
                break
            except TimeoutException:
                continue

        if terminal is None:
            # Fallback: Sayfadaki herhangi bir terminal alanina tikla
            self._log("  Terminal textarea bulunamadi, alternatif yol deneniyor...")
            try:
                term_area = self.driver.find_element(
                    By.CSS_SELECTOR, ".xterm-screen"
                )
                ActionChains(self.driver).click(term_area).perform()
                time.sleep(1)
                terminal = self.driver.find_element(
                    By.CSS_SELECTOR, ".xterm-helper-textarea"
                )
            except Exception:
                self._screenshot("10_terminal_bulunamadi")
                raise Exception("Terminal bulunamadi!")

        # Komutu satir satir gonder
        lines = command.strip
