import os
import zipfile
import tempfile
from docx import Document
from oletools.olevba3 import VBA_Parser
import fitz  # PyMuPDF

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
                            if file_links:
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
                    if links:
                        all_links[display_name] = links

    recursive_scan(folder_path)
    return all_links


# ---------- Run It ----------

if __name__ == "__main__":
    folder_to_scan = os.path.join("scraper", "scraper", "toProcessFurther")
    found_links = scan_folder_for_links(folder_to_scan)

    for file, links in found_links.items():
        print(f"\n📄 {file} — Found {len(links)} link(s):")
        for link in links:
            print(f"   🔗 {link}")
