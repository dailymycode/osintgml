#!/usr/bin/env python3
"""
Account recovery + Email variations — Common entry menu.
Run: python main.py
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    return r"""
   ___   ____ ___ _   _ _____ ____ _____ _____ __  __ _
  / _ \ / ___|_ _| \ | |_   _/ ___|_   _|_   _|  \/  | |
 | | | | |  _ | ||  \| | | | \___ \ | |   | | | |\/| | |
 | |_| | |_| || || |\  | | |  ___) || |   | | | |  | | |___
  \___/ \____|___|_| \_| |_| |____/ |_|   |_| |_|  |_|_____|

              O S I N T G M L

  [1]  Account recovery (forgot password)
       -> Username/email -> masked contact info

  [2]  Email variations
       -> Masked email + first name, last name, numbers, username

  [0]  Exit
"""


def run_recovery():
    clear()
    print("\n  Account recovery — Enter username or email.\n")
    user = input("  Username / email: ").strip()
    if not user:
        print("  Empty, returning to menu.")
        input("\n  Press Enter to continue...")
        return
    path = os.path.join(SCRIPT_DIR, "account_recovery.py")
    subprocess.run([sys.executable, path, user], cwd=SCRIPT_DIR)
    input("\n  Press Enter to return to menu...")


def run_variations():
    clear()
    print("\n  Email variations\n")
    print("  Enter masked email first, then known info (optional).\n")

    masked = input("  Masked email (e.g. d*******4@gmail.com): ").strip()
    if not masked:
        print("  Empty, returning to menu.")
        input("\n  Press Enter to continue...")
        return

    first_name = input("  First name (if known): ").strip()
    last_name = input("  Last name (if known): ").strip()
    numbers = input("  Numbers used (if known, comma-separated): ").strip()
    username = input("  Username (if known): ").strip()

    env = os.environ.copy()
    if first_name:
        env["EXTRA_AD"] = first_name
    if last_name:
        env["EXTRA_SOYAD"] = last_name
    if numbers:
        env["EXTRA_NUMARALAR"] = numbers
    if username:
        env["EXTRA_KULLANICI_ADI"] = username

    path = os.path.join(SCRIPT_DIR, "email_variations.py")
    subprocess.run([sys.executable, path, masked], cwd=SCRIPT_DIR, env=env)
    input("\n  Press Enter to return to menu...")


def main():
    while True:
        clear()
        print(banner())
        try:
            choice = input("  Choice [0-2]: ").strip() or " "
        except (KeyboardInterrupt, EOFError):
            print("\n  Exiting.")
            break
        if choice == "0":
            print("  Bye.")
            break
        if choice == "1":
            run_recovery()
        elif choice == "2":
            run_variations()
        else:
            print("  Invalid. Enter 0, 1, or 2.")
            input("  Press Enter to continue...")


if __name__ == "__main__":
    main()
