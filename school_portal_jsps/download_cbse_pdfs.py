import urllib.request
import os

pdfs = [
    "cbse/others/academic-calander.pdf",
    "cbse/affidavit.pdf",
    "cbse/boys-and-girls-details.pdf",
    "cbse/bsa-recognition-letter.pdf",
    "cbse/written-declaration-regarding-book.pdf",
    "cbse/book-list.pdf",
    "cbse/building-safety.pdf",
    "cbse/cbse-grant-letter.pdf",
    "cbse/fees.pdf",
    "cbse/fire-safety.pdf",
    "cbse/health-and-sanitation.pdf",
    "cbse/infrastructure.pdf",
    "cbse/last-3-years-board-result.pdf",
    "cbse/noc.pdf",
    "cbse/parents-teachers-association.pdf",
    "cbse/smc.pdf",
    "cbse/transfer-certificate-sample.pdf",
    "cbse/trust-members-detail.pdf",
    "cbse/teaching-staff-details.pdf",
    "cbse/curriculum.pdf",
    "cbse/school-brief-history.pdf",
    "cbse/trust-deed.pdf",
    "cbse/self-declaration.pdf",
    "cbse/mandatory-public-disclosure.pdf"
]

base_url = "https://jspschandauli.com/"

for pdf in pdfs:
    url = base_url + pdf
    dest = "static/" + pdf
    
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"Saved to {dest}")
    except Exception as e:
        print(f"Failed to download {pdf}: {e}")
