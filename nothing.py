import os
import shutil

def organize_folder(target_path):
    # Define mapping of extensions to folder names
    file_types = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg"],
        "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx"],
        "Audio": [".mp3", ".wav", ".aac"],
        "Videos": [".mp4", ".mov", ".mkv"],
        "Archives": [".zip", ".rar", ".7z"]
    }

    # Change to the target directory
    os.chdir(target_path)

    for file in os.listdir():
        # Skip directories, we only want files
        if os.path.isfile(file):
            filename, extension = os.path.splitext(file)
            extension = extension.lower()

            # Find the right folder for this extension
            moved = False
            for folder, extensions in file_types.items():
                if extension in extensions:
                    # Create the folder if it doesn't exist
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                    
                    # Move the file
                    shutil.move(file, f"{folder}/{file}")
                    print(f"📦 Moved {file} to {folder}/")
                    moved = True
                    break
            
            if not moved:
                print(f"❓ Skipped {file} (Unknown type)")

if __name__ == "__main__":
    # WARNING: Replace this with a path to a test folder first!
    path = input("Enter the full path of the folder to organize: ")
    if os.path.exists(path):
        organize_folder(path)
        print("\n✨ Cleanup complete!")
    else:
        print("Invalid path.")