import os
import sys
import ctypes
import urllib.request
import urllib.parse
import time

URLS_FILE = "urls.txt"
DOWNLOAD_TIMEOUT = 60
DOWNLOADS_FOLDER_NAME = "DigitalMember_Assistant_Downloads"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}"', None, 1
        )
    except:
        print("Admin rights not granted. Closing...")
        time.sleep(1)  # Wait so user can read the message
        sys.exit(1)


def make_fullscreen():
    kernel32 = ctypes.WinDLL("kernel32")
    user32 = ctypes.WinDLL("user32")
    hWnd = kernel32.GetConsoleWindow()
    if hWnd:
        user32.ShowWindow(hWnd, 3)  # SW_MAXIMIZE


def get_script_folder():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.abspath(__file__))


def ensure_downloads_folder(base_folder):
    path = os.path.join(base_folder, DOWNLOADS_FOLDER_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def prepare_log_file(downloads_folder):
    log_file = os.path.join(downloads_folder, "log.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("")
    return log_file


def read_urls_file(folder):
    path = os.path.join(folder, URLS_FILE)
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip().startswith(("http://", "https://"))]
    return []


def choose_filename(url, folder):
    name = os.path.basename(urllib.parse.urlparse(url).path) or "file"
    base, ext = os.path.splitext(name)
    counter = 1
    new_name = name
    while os.path.exists(os.path.join(folder, new_name)):
        new_name = f"{base}_{counter}{ext}"
        counter += 1
    return new_name


def log_entry(log_file, text):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def download_url(url, folder, log_file):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Downloader"})
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
            filename = choose_filename(url, folder)
            path = os.path.join(folder, filename)
            with open(path, "wb") as out:
                out.write(resp.read())

        if os.path.exists(path) and os.path.getsize(path) > 0:
            log_entry(log_file, f"SUCCESS {url} -> {filename}")
            return True, path
        else:
            log_entry(log_file, f"FAILED {url}")
            return False, f"File '{filename}' empty or not saved."
    except:
        log_entry(log_file, f"FAILED {url}")
        return False, "Download error"


def main():
    if is_admin():
        make_fullscreen()
        banner = "DigitalMember Assistant Administrator"
    else:
        banner = "DigitalMember Assistant User"

    folder = get_script_folder()
    downloads = ensure_downloads_folder(folder)
    log_file = prepare_log_file(downloads)

    print(f"\n{banner}")
    print(f"Downloads folder: {downloads}")
    print(f"Log file: {log_file}\n")

    print("Checking urls.txt file...")
    path = os.path.join(folder, URLS_FILE)
    if not os.path.isfile(path):
        print("urls.txt file not found.")
        urls = []
    else:
        urls = read_urls_file(folder)
        if urls:
            print(f"Found {len(urls)} URL(s) in urls.txt. Downloading...")
            for u in urls:
                ok, info = download_url(u, downloads, log_file)
                print(f"{'SUCCESS' if ok else 'FAILED'}: {info}")
        else:
            print("No valid URLs found in urls.txt.")

    while True:
        user_input = input("\nType a URL and press Enter, or type Exit and press Enter:\n> ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("\nClosing program.")
            break
        if user_input.startswith(("http://", "https://")):
            ok, info = download_url(user_input, downloads, log_file)
            print(f"{'SUCCESS' if ok else 'FAILED'}: {info}")
        else:
            print("Invalid URL. Try again.")


if __name__ == "__main__":
    if is_admin():
        main()
    else:
        print("\nDigitalMember Assistant User")
        print("This program needs admin rights. Please approve when asked.")
        time.sleep(1)  # Wait 1 second before UAC request
        run_as_admin()
