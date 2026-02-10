#!/usr/bin/env python3
"""
PWD Automator - Ana Calistirici
GitHub Actions + Yerel kullanim destegi
"""

import json
import os
import sys
import time
import re
import argparse
from datetime import datetime

from pwd_bot import PWDBot


def load_accounts_from_env():
    """
    Hesap bilgilerini environment variable'lardan yukle.
    Birden fazla format destekler:
      1) ACCOUNTS_JSON = tek satirlik JSON
      2) ACCOUNT_1_EMAIL + ACCOUNT_1_PASSWORD (tek tek)
    """
    config = {"accounts": [], "command_file": "command.txt"}

    # --- YONTEM 1: ACCOUNTS_JSON ---
    accounts_json = os.environ.get("ACCOUNTS_JSON", "").strip()

    if accounts_json:
        # Debug: ilk 50 karakteri goster (sifreleri gizle)
        print(f"[DEBUG] ACCOUNTS_JSON ilk 50 karakter: {accounts_json[:50]}...")
        print(f"[DEBUG] ACCOUNTS_JSON uzunluk: {len(accounts_json)}")

        # Olasi sorunlari temizle
        # Bazi shell'ler bas/son tirnak ekler
        if accounts_json.startswith("'") and accounts_json.endswith("'"):
            accounts_json = accounts_json[1:-1]
        if accounts_json.startswith('"') and accounts_json.endswith('"'):
            accounts_json = accounts_json[1:-1]

        # Cift tirnak yerine tek tirnak kullanilmissa duzelt
        # (GitHub Secrets bazen bozar)
        if "'" in accounts_json and '"' not in accounts_json:
            accounts_json = accounts_json.replace("'", '"')

        try:
            parsed = json.loads(accounts_json)
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list):
                return {"accounts": parsed, "command_file": "command.txt"}
        except json.JSONDecodeError as e:
            print(f"[UYARI] JSON parse hatasi: {e}")
            print(f"[UYARI] Ham veri: {repr(accounts_json[:200])}")
            print("[UYARI] Tek tek ACCOUNT degiskenleri deneniyor...")

    # --- YONTEM 2: TEK TEK DEGISKENLER ---
    command = os.environ.get("COMMAND", "")
    if command:
        config["command_override"] = command

    for i in range(1, 11):
        email = os.environ.get(f"ACCOUNT_{i}_EMAIL", "").strip()
        password = os.environ.get(f"ACCOUNT_{i}_PASSWORD", "").strip()

        if email and password:
            config["accounts"].append({
                "email": email,
                "password": password,
                "enabled": True
            })

    if not config["accounts"]:
        print("=" * 60)
        print("HATA: Hesap bilgisi bulunamadi!")
        print()
        print("COZUM: GitHub Secrets'a su sekilde ekleyin:")
        print()
        print("  Secret adi: ACCOUNT_1_EMAIL")
        print("  Secret degeri: ornek@mail.com")
        print()
        print("  Secret adi: ACCOUNT_1_PASSWORD")
        print("  Secret degeri: sifreniz123")
        print()
        print("  (5 hesap icin ACCOUNT_1 den ACCOUNT_5 e kadar)")
        print("=" * 60)
        sys.exit(1)

    return config


def load_accounts_from_file(config_path="accounts.json"):
    """JSON dosyasindan yukle."""
    if not os.path.exists(config_path):
        print(f"HATA: {config_path} bulunamadi!")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_command(config):
    """Komutu yukle."""
    if "command_override" in config:
        return config["command_override"]

    cmd_file = config.get("command_file", "command.txt")
    if os.path.exists(cmd_file):
        with open(cmd_file, "r", encoding="utf-8") as f:
            cmd = f.read().strip()
            if cmd:
                return cmd

    cmd = os.environ.get("COMMAND", "").strip()
    if cmd:
        return cmd

    return 'echo "PWD Bot calisti!" && date'


def run_all_accounts(config, headless=True):
    """Tum hesaplar icin otomasyonu calistir."""
    accounts = config.get("accounts", [])
    command = load_command(config)

    print("=" * 60)
    print(f"  PWD AUTOMATOR")
    print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Hesap sayisi: {len(accounts)}")
    print(f"  Komut: {command[:80]}...")
    print("=" * 60)

    results = []

    for idx, account in enumerate(accounts, 1):
        if not account.get("enabled", True):
            print(f"\n[{idx}] {account['email']} → ATLANDI")
            results.append({"email": account["email"], "status": "skipped"})
            continue

        print(f"\n{'─' * 50}")
        print(f"  Hesap {idx}/{len(accounts)}: {account['email']}")
        print(f"{'─' * 50}")

        bot = PWDBot(headless=headless)
        success = bot.run(
            email=account["email"],
            password=account["password"],
            command=command
        )

        results.append({
            "email": account["email"],
            "status": "success" if success else "failed"
        })

        if idx < len(accounts):
            print(f"\n  Sonraki hesap icin 15sn bekleniyor...")
            time.sleep(15)

    # RAPOR
    print("\n" + "=" * 60)
    print("  SONUC RAPORU")
    print("=" * 60)
    for r in results:
        icon = {"success": "OK", "failed": "FAIL", "skipped": "SKIP"}[r["status"]]
        print(f"  [{icon}] {r['email']}")

    ok = sum(1 for r in results if r["status"] == "success")
    total = sum(1 for r in results if r["status"] != "skipped")
    print(f"\n  Basarili: {ok}/{total}")
    print("=" * 60)

    return all(r["status"] != "failed" for r in results)


def main():
    parser = argparse.ArgumentParser(description="PWD Automator")
    parser.add_argument("--config", "-c", default="accounts.json")
    parser.add_argument("--env", "-e", action="store_true")
    parser.add_argument("--visible", "-v", action="store_true")
    parser.add_argument("--command", "-cmd", default=None)

    args = parser.parse_args()

    if args.env:
        config = load_accounts_from_env()
    else:
        config = load_accounts_from_file(args.config)

    if args.command:
        config["command_override"] = args.command

    success = run_all_accounts(config, headless=not args.visible)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
