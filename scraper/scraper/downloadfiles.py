import os
import zipfile
import tempfile
from docx import Document
from oletools.olevba3 import VBA_Parser
import fitz  # PyMuPDF
import subprocess
import shutil

# ---------- Config ----------
TO_PROCESS_FURTHER_PATH = r"scraper\scraper\toProcessFurther"
SUPPORTED_EXTENSIONS = {".docx", ".doc", ".pdf", ".zip"}


# ---------- Extractors ----------
def extract_links_from_docx(filepath):
    links = []
    try:
        doc = Document(filepath)
        for para in doc.paragraphs:
            for run in para.runs:
                if "http" in run.text or "www." in run.text:
                    links.append(run.text.strip())
        for rel in doc.part.rels.values():
            if "http" in str(rel.target_ref):
                links.append(str(rel.target_ref))
    except Exception as e:
        print(f"⚠️ Error reading .docx file {filepath}: {e}")
    return links


def extract_links_from_doc(filepath):
    links = []
    vba = None
    try:
        vba = VBA_Parser(filepath)
        if vba.detect_vba_macros():
            for _, _, vba_code in vba.extract_macros():
                for line in vba_code.splitlines():
                    if "http" in line or "www." in line:
                        links.append(line.strip())
    except Exception as e:
        print(f"⚠️ Error reading .doc file {filepath}: {e}")
    finally:
        if vba:
            vba.close()
    return links


def extract_links_from_pdf(filepath):
    links = []
    try:
        doc = fitz.open(filepath)
        for page in doc:
            text = page.get_text()
            for word in text.split():
                if "http" in word or "www." in word:
                    links.append(word.strip())
            for link in page.get_links():
                uri = link.get("uri", "")
                if uri:
                    links.append(uri.strip())
        doc.close()
    except Exception as e:
        print(f"⚠️ Error reading PDF file {filepath}: {e}")
    return links


# ---------- ZIP Handler ----------
def extract_zip_recursive(zip_path, parent_display_path, all_links):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(temp_dir)

            for root, dirs, files in os.walk(temp_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    ext = os.path.splitext(fpath)[1].lower()

                    display_path = os.path.relpath(fpath, temp_dir)
                    display_path = f"{parent_display_path}/{display_path}"

                    if ext in SUPPORTED_EXTENSIONS:
                        if ext == ".zip":
                            extract_zip_recursive(fpath, display_path, all_links)
                        else:
                            file_links = scan_single_file(fpath)
                            all_links[display_path] = file_links
    except Exception as e:
        print(f"⚠️ Failed to handle ZIP {zip_path}: {e}")


# ---------- File Scanner ----------
def scan_single_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".docx":
        return extract_links_from_docx(filepath)
    elif ext == ".doc":
        return extract_links_from_doc(filepath)
    elif ext == ".pdf":
        return extract_links_from_pdf(filepath)
    return []


# ---------- Folder Scanner ----------
def scan_folder_for_links(folder_path):
    all_links = {}

    def recursive_scan(path):
        if os.path.isdir(path):
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                recursive_scan(full_path)
        elif os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                display_name = os.path.relpath(path, folder_path)
                if ext == ".zip":
                    extract_zip_recursive(path, display_name, all_links)
                else:
                    links = scan_single_file(path)
                    all_links[display_name] = links

    recursive_scan(folder_path)
    return all_links


# ---------- Unzip Initial Files ----------
def unzipFolders():
    for filename in os.listdir(TO_PROCESS_FURTHER_PATH):
        if filename.endswith(".zip"):
            zip_path = os.path.join(TO_PROCESS_FURTHER_PATH, filename)
            extract_folder = os.path.join(TO_PROCESS_FURTHER_PATH, filename[:-4])
            os.makedirs(extract_folder, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_folder)
            print(f"Unzipped: {filename} -> {extract_folder}")


# ---------- ClamAV Scanner ----------
def scanWithClamAV():
    print("\n[!] Running ClamAV scan...")
    scan_command = [
        r"C:\Program Files (x86)\ClamAV\clamscan.exe",
        "-r",
        "--infected",
        "--no-summary",
        TO_PROCESS_FURTHER_PATH,
    ]
    try:
        result = subprocess.run(
            scan_command, capture_output=True, text=True, check=False
        )
        print("[!] Scan complete.\n")
        print(result.stdout if result.stdout else "[+] No infected files found.")
    except FileNotFoundError:
        print(
            "[ERROR] ClamAV (clamscan) not found. Make sure it is installed and added to PATH."
        )


# ---------- Cleanup ----------
def clear_directory():
    if not os.path.exists(TO_PROCESS_FURTHER_PATH):
        print(f"[!] Path does not exist: {TO_PROCESS_FURTHER_PATH}")
        return
    for item in os.listdir(TO_PROCESS_FURTHER_PATH):
        item_path = os.path.join(TO_PROCESS_FURTHER_PATH, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                print(f"[+] File deleted: {item_path}")
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"[+] Folder deleted: {item_path}")
        except Exception as e:
            print(f"[ERROR] Could not delete {item_path}. Reason: {e}")


from urllib.parse import urlparse


def is_scrapable_moodle_link(url: str) -> bool:
    parsed = urlparse(url)

    if not url or url.startswith("mailto:") or url.strip() == "https://":
        return False

    domain = parsed.netloc.lower()

    # Allow Moodle course/resource pages
    if (
        "/moodle/course/view.php" in parsed.path
        or "/moodle/mod/resource/view.php" in parsed.path
    ):
        return True

    # Allow known content domains
    if any(
        good in domain
        for good in [
            "files.wordpress.com",
            "sfia-online.org",
            "navexone.com",
            "dlsweb.rmit.edu.au",
            "mindtools.com"
        ]
    ):
        return True

    # Block known non-content domains
    if any(
        exclude in domain
        for exclude in [
            "goto.murdoch.edu.au",
            "student.unsw.edu.au",
            "copilot.microsoft.com",
            "murdochuniversity.sharepoint.com",
            "libguides.murdoch.edu.au",
        ]
    ):
        return False

    # Allow any link ending with a content file extension
    if any(
        url.lower().endswith(ext)
        for ext in [".pdf", ".doc", ".docx", ".pptx", ".xls", ".xlsx"]
    ):
        return True

    return False


# ---------- Main ----------
def downloadFilesAndCheck():
    unzipFolders()
    # scanWithClamAV()
    found_links = scan_folder_for_links(TO_PROCESS_FURTHER_PATH)

    print("\n📦 Scan Summary:")

    all_scanned_files = set()
    all_links = []  # ✅ collect all links across all files

    for root, dirs, files in os.walk(TO_PROCESS_FURTHER_PATH):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                rel_path = os.path.relpath(
                    os.path.join(root, fname), TO_PROCESS_FURTHER_PATH
                )
                all_scanned_files.add(rel_path)

    for filepath in sorted(all_scanned_files):
        links = found_links.get(filepath, [])
        print(f"\n📄 {filepath} — Found {len(links)} link(s):")
        for link in links:
            print(f"   🔗 {link}")
            all_links.append(link)  # ✅ add each link to the master list
    scrapable_links = list(filter(is_scrapable_moodle_link, all_links))
    print(scrapable_links)
    return scrapable_links  # ✅ return all collected links

    # clear_directory()


downloadFilesAndCheck()
