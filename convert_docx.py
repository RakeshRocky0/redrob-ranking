import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def get_docx_text(path):
    try:
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            text_runs = []
            for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                para_text = []
                for run in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
                    for text in run.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                        if text.text:
                            para_text.append(text.text)
                text_runs.append(''.join(para_text))
            return '\n'.join(text_runs)
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

def main():
    base_dir = Path(__file__).parent
    files = ["README.docx", "job_description.docx", "redrob_signals_doc.docx", "submission_spec.docx"]
    for f_name in files:
        docx_path = base_dir / f_name
        if not docx_path.exists():
            print(f"Skipping {f_name} (does not exist at {docx_path})")
            continue
        txt_path = base_dir / (f_name.replace(".docx", ".txt"))
        print(f"Converting {docx_path} -> {txt_path}...")
        txt = get_docx_text(docx_path)
        with open(txt_path, "w", encoding="utf-8") as f_out:
            f_out.write(txt)
        print("Done!")

if __name__ == '__main__':
    main()
