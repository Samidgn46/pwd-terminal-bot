#!/usr/bin/env python3
"""
PWD Automator - Ana Calistirici
5 hesap icin sirayla Play with Docker otomasyonu yapar.

Kullanim:
  python main.py                         # accounts.json dosyasindan
  python main.py --config my_config.json # ozel config
  python main.py --env                   # environment variable'lardan
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime

from pwd_bot import PWDBot


def load_accounts_from_file(config_path="accounts.json"):
    """Hesap bilgilerini JSON dosyasindan yukle."""
    if not os.path.exists(config_path):
        print(f"HATA: {config_path} dosyasi bulunamadi!")
        print("accounts.json.example dosyasini kopyalayip duzenleyin.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config


def load_accounts_from_env():
    """
    Hesap bilgilerini environment variable'lardan yukle.
    GitHub Actions Secrets icin ideal.

    Beklenen format:
      ACCOUNTS_JSON = '{"accounts": [...], "command_file": "command.txt"}'
    veya tek tek:
      ACCOUNT_1_EMAIL, ACCOUNT_1_PASSWORD, ...
      COMMAND
    """
    accounts_json = os.environ.get("ACCOUNTS_JSON")

    if accounts_json:
        return json.loads(accounts_json)

    # Tek tek environment variable'lar
    config = {"accounts": [], "command_file": "command.txt"}
    command = os.environ.get("COMMAND", "")

    if command:
        config["command_override"] = command

    for i in range(1, 11):
        email = os.environ.get(f"ACCOUNT_{i}_EMAIL")
        password = os.environ.get(f"ACCOUNT_{i}_PASSWORD")

        if email and password:
            config["accounts"].append({
                "email": email,
                "password": password,
                "enabled": True
            })

    if not config["accounts"]:
        print("HATA: Hicbir hesap bilgisi bulunamadi!")
        print("ACCOUNTS_JSON veya ACCOUNT_1_EMAIL/PASSWORD env var'lari set edin.")
        sys.exit(1)

    return config


def load_command(config):
    """Calistirilacak komutu yukle."""
    # Oncelik: config icindeki override → command_file → default
    if "command_override" in config:
        return config["command_override"]

    cmd_file = config.get("command_file", "command.txt")

    if os.path.exists(cmd_file):
        with open(cmd_file, "r", encoding="utf-8") as f:
            return f.read().strip()

    # Environment variable'dan
    cmd = os.environ.get("COMMAND", "")
    if cmd:
        return cmd

    return 'echo "PWD Bot basariyla calisti!" && date'


def run_all_accounts(config, headless=True):
    """Tum hesaplar icin otomasyonu calistir."""
    accounts = config.get("accounts", [])
    command = load_command(config)

    print("=" * 70)
    print(f"  PWD AUTOMATOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Toplam hesap: {len(accounts)}")
    print(f"  Komut: {command[:100]}...")
    print("=" * 70)
    print()

    results = []

    for idx, account in enumerate(accounts, 1):
        if not account.get("enabled", True):
            print(f"[{idx}/{len(accounts)}] {account['email']} → ATLANILDI (devre disi)")
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

        # Hesaplar arasi bekleme (rate limiting)
        if idx < len(accounts):
            wait_time = 15
            print(f"\n  Sonraki hesap icin {wait_time}sn bekleniyor...")
            time.sleep(wait_time)

    # SONUC RAPORU
    print("\n" + "=" * 70)
    print("  SONUC RAPORU")
    print("=" * 70)

    for r in results:
        icon = "✓" if r["status"] == "success" else \
               "✗" if r["status"] == "failed" else "○"
        print(f"  {icon} {r['email']}: {r['status']}")

    success_count = sum(1 for r in results if r["status"] == "success")
    total_active = sum(1 for r in results if r["status"] != "skipped")
    print(f"\n  Basarili: {success_count}/{total_active}")
    print("=" * 70)

    return all(r["status"] != "failed" for r in results)


def main():
    parser = argparse.ArgumentParser(description="PWD Automator")
    parser.add_argument(
        "--config", "-c",
        default="accounts.json",
        help="Config dosyasi yolu (default: accounts.json)"
    )
    parser.add_argument(
        "--env", "-e",
        action="store_true",
        help="Hesap bilgilerini environment variable'lardan al"
    )
    parser.add_argument(
        "--visible", "-v",
        action="store_true",
        help="Tarayiciyi gorunur calistir (debug icin)"
    )
    parser.add_argument(
        "--command", "-cmd",
        default=None,
        help="Calistirilacak komut (dosya yerine)"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Surekli dongu modunda calistir"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.5,
        help="Dongu arasi bekleme suresi (saat, default: 3.5)"
    )

    args = parser.parse_args()

    # Config yukle
    if args.env:
        config = load_accounts_from_env()
    else:
        config = load_accounts_from_file(args.config)

    # Komut override
    if args.command:
        config["command_override"] = args.command

    headless = not args.visible

    if args.loop:
        # Surekli dongu modu
        interval_seconds = args.interval * 3600
        print(f"Dongu modu aktif - Her {args.interval} saatte bir calisacak")

        while True:
            run_all_accounts(config, headless=headless)
            print(f"\nSonraki calistirma: {args.interval} saat sonra")
            print(f"Bekleniyor ({int(interval_seconds)} saniye)...")
            time.sleep(interval_seconds)
    else:
        # Tek seferlik calistirma
        success = run_all_accounts(config, headless=headless)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
