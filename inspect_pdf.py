from pathlib import Path

from pypdf import PdfReader


desktop = Path(r"C:\Users\Clive\Desktop")
pdfs = sorted(desktop.glob("*.pdf"))

for pdf in pdfs:
    print(f"PDF: {pdf.name}")
    try:
        reader = PdfReader(str(pdf))
        text = ""
        for page in reader.pages[:2]:
            text += page.extract_text() or ""
        cleaned = " ".join(text.split())
        print(cleaned[:2000] or "[sin texto extraible]")
    except Exception as exc:
        print(f"[error] {exc}")
    print("-" * 40)
