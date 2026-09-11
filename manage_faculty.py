"""
Faculty Input Manager CLI
=========================
Command-line utility to view, add, remove, and manage faculty names
in 'faculty_input.xlsx' without needing Microsoft Excel installed.

Usage:
    python manage_faculty.py                # Interactive menu mode
    python manage_faculty.py --list         # List all faculty names
    python manage_faculty.py --add "Name"   # Add a faculty name
    python manage_faculty.py --delete "Name"# Delete a faculty name
    python manage_faculty.py --clear        # Clear all faculty names
"""

import os
import sys
import argparse
import pandas as pd

EXCEL_FILE = "faculty_input.xlsx"
COLUMN_NAME = "Faculty Name"


def load_faculty(file_path: str = EXCEL_FILE) -> list[str]:
    """Loads faculty list from Excel, creating the file if it doesn't exist."""
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=[COLUMN_NAME])
        df.to_excel(file_path, index=False)
        return []
    try:
        df = pd.read_excel(file_path)
        col = None
        for c in df.columns:
            if "faculty" in str(c).lower() or "name" in str(c).lower():
                col = c
                break
        if not col and len(df.columns) > 0:
            col = df.columns[0]
        if col:
            return [str(x).strip() for x in df[col].dropna() if str(x).strip()]
        return []
    except Exception as e:
        print(f"[Error reading {file_path}]: {e}")
        return []


def save_faculty(faculty_list: list[str], file_path: str = EXCEL_FILE):
    """Saves faculty list back to Excel."""
    # Deduplicate while preserving order
    seen = set()
    cleaned = []
    for name in faculty_list:
        n = str(name).strip()
        if n and n not in seen:
            seen.add(n)
            cleaned.append(n)
    df = pd.DataFrame({COLUMN_NAME: cleaned})
    df.to_excel(file_path, index=False)
    return cleaned


def add_faculty(name: str, file_path: str = EXCEL_FILE) -> bool:
    name = name.strip()
    if not name:
        return False
    faculty = load_faculty(file_path)
    if name in faculty:
        print(f"[Info] '{name}' is already in the list.")
        return False
    faculty.append(name)
    save_faculty(faculty, file_path)
    print(f"[Success] Added '{name}' (Total: {len(faculty)})")
    return True


def delete_faculty(name: str, file_path: str = EXCEL_FILE) -> bool:
    name = name.strip()
    faculty = load_faculty(file_path)
    # Match case-insensitively
    matched = [f for f in faculty if f.lower() == name.lower()]
    if not matched:
        print(f"[Warning] '{name}' not found in the list.")
        return False
    target = matched[0]
    faculty.remove(target)
    save_faculty(faculty, file_path)
    print(f"[Success] Removed '{target}' (Total remaining: {len(faculty)})")
    return True


def list_faculty(file_path: str = EXCEL_FILE):
    faculty = load_faculty(file_path)
    print(f"\n--- Current Faculty List in '{file_path}' ({len(faculty)} total) ---")
    if not faculty:
        print("  (No faculty names added yet)")
    else:
        for idx, f in enumerate(faculty, start=1):
            print(f"  {idx:2d}. {f}")
    print("-----------------------------------------------------------\n")


def interactive_menu(file_path: str = EXCEL_FILE):
    """Simple terminal menu."""
    while True:
        faculty = load_faculty(file_path)
        print("\n" + "=" * 45)
        print(f"   Faculty List Manager ({len(faculty)} faculty registered)")
        print("=" * 45)
        print("1. View current faculty list")
        print("2. Add new faculty name")
        print("3. Bulk add faculty names (comma or newline separated)")
        print("4. Remove a faculty name")
        print("5. Clear all faculty names")
        print("6. Run Vidwan Publication Extractor")
        print("0. Exit")
        print("=" * 45)

        choice = input("Enter choice [0-6]: ").strip()
        if choice == "1":
            list_faculty(file_path)
        elif choice == "2":
            name = input("Enter Faculty Name: ").strip()
            if name:
                add_faculty(name, file_path)
        elif choice == "3":
            print("Enter names (separate with commas or paste multiple lines, then press Enter twice):")
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            raw_text = "\n".join(lines)
            tokens = [t.strip() for t in raw_text.replace(",", "\n").splitlines() if t.strip()]
            added_cnt = 0
            for t in tokens:
                if t not in faculty:
                    faculty.append(t)
                    added_cnt += 1
            save_faculty(faculty, file_path)
            print(f"[Success] Added {added_cnt} new faculty member(s). Total: {len(faculty)}")
        elif choice == "4":
            list_faculty(file_path)
            inp = input("Enter exact name or number to remove: ").strip()
            if inp.isdigit():
                idx = int(inp) - 1
                if 0 <= idx < len(faculty):
                    removed = faculty.pop(idx)
                    save_faculty(faculty, file_path)
                    print(f"[Success] Removed '{removed}'.")
                else:
                    print("[Error] Invalid number.")
            else:
                delete_faculty(inp, file_path)
        elif choice == "5":
            confirm = input("Are you sure you want to clear all names? (y/N): ").strip().lower()
            if confirm == "y":
                save_faculty([], file_path)
                print("[Success] Cleared all names.")
        elif choice == "6":
            print("\nStarting extraction pipeline...")
            os.system(f"python fetch_faculty_publications.py --input {file_path} --output faculty_publications_output.xlsx")
        elif choice == "0":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please try again.")


def main():
    parser = argparse.ArgumentParser(description="Manage faculty names in 'faculty_input.xlsx' without Excel.")
    parser.add_argument("-f", "--file", default=EXCEL_FILE, help="Excel file path (default: faculty_input.xlsx)")
    parser.add_argument("-l", "--list", action="store_true", help="List all faculty names")
    parser.add_argument("-a", "--add", type=str, help="Add a single faculty name")
    parser.add_argument("-d", "--delete", type=str, help="Delete a faculty name")
    parser.add_argument("--clear", action="store_true", help="Clear all faculty names")
    args = parser.parse_args()

    if args.list:
        list_faculty(args.file)
    elif args.add:
        add_faculty(args.add, args.file)
    elif args.delete:
        delete_faculty(args.delete, args.file)
    elif args.clear:
        save_faculty([], args.file)
        print(f"Cleared all entries in '{args.file}'.")
    else:
        interactive_menu(args.file)


if __name__ == "__main__":
    main()
