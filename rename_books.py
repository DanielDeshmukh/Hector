# rename_books.py

import os
import re


def rename_legal_books(directory):
    if not os.path.exists(directory):
        print(f"Error: The path {directory} was not found.")
        return

    print(f"Starting renaming process in: {directory}\n")

    for filename in os.listdir(directory):
        old_path = os.path.join(directory, filename)
        if not os.path.isfile(old_path):
            continue

        name_part, extension = os.path.splitext(filename)

        clean_name = re.sub(r"\(.*?\)", "", name_part)
        clean_name = re.sub(r"[^a-zA-Z0-9\s]", " ", clean_name)

        words = clean_name.split()
        short_name = "_".join(words[:4])

        if not short_name:
            short_name = "legal_doc"

        new_filename = f"{short_name}{extension}"
        new_path = os.path.join(directory, new_filename)

        counter = 1
        base_short_name = short_name
        while os.path.exists(new_path):
            if old_path == new_path:
                break
            new_filename = f"{base_short_name}_{counter}{extension}"
            new_path = os.path.join(directory, new_filename)
            counter += 1

        try:
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f"Fixed: {filename}  -->  {new_filename}")
            else:
                print(f"Skipped (Already Correct): {filename}")
        except Exception as e:
            print(f"Failed to rename {filename}: {e}")


if __name__ == "__main__":
    target_dir = r" "  # <-- Set this to the path of your legal books directory
    rename_legal_books(target_dir)
