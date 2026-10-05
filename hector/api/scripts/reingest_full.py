"""
HECTOR Full Re-Ingestion v3: Embed per-PDF so crash doesn't lose chunks.
Phase 1+2 combined: for each PDF -> read -> chunk -> embed -> upsert.
"""
import os, sys, time, json, hashlib, re
sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector\api")
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(r"D:\Vs Code\VS code\Hector\.env")

from pypdf import PdfReader
from pinecone import Pinecone
import httpx
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

NIM_API_KEY = os.getenv("NIM_API_KEY", "")
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
EMBEDDING_MODEL = "nvidia/nemotron-3-embed-1b"
BOOKS_DIR = Path(r"D:\Vs Code\VS code\Hector\hector\api\data\Books")
PROGRESS_FILE = Path(r"D:\Vs Code\VS code\Hector\hector\api\scripts\reingest_progress.json")
SKIP_PDFS = {
    "fixed_Whartons_law_Lexicon.pdf",
    "fixed_The_Code_of_Criminal.pdf",
    "Textbook on The Law of Evidence (Chief Justice M Monir) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
    "The Bharatiya Sakshya Adhiniyam 2023 (N Vijayaraghavan  Sharath Chandran) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
    "Commentary on The Narcotic Drugs and Psychotropic Substances Act (Dr J N Barowalia  Abhishek Barowalia) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
    "Fighting corruption  strategies for prevention  report of the proceedings of the Public Sector Anti-corruption Conference. ( etc.) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
}

# Canonical act names — must match _KNOWN_ACTS in response_generator.py exactly
FILENAME_TO_ACT = {
    "Indian_Penal_Code_1860.pdf": ("Indian Penal Code, 1860", "IPC"),
    "Bharatiya_Nyaya_Sanhita_2023.pdf": ("Bharatiya Nyaya Sanhita, 2023", "BNS"),
    "Code_of_Criminal_Procedure_1973.pdf": ("Code of Criminal Procedure, 1973", "CrPC"),
    "Bharatiya_Nagarik_Suraksha_Sanhita_2023.pdf": ("Bharatiya Nagarik Suraksha Sanhita, 2023", "BNSS"),
    "Indian_Evidence_Act_1872.pdf": ("Indian Evidence Act, 1872", "IEA"),
    "Bharatiya_Sakshya_Adhiniyam_2023.pdf": ("Bharatiya Sakshya Adhiniyam, 2023", "BSA"),
    "Code_Of_Civil_Procedure_1908.pdf": ("Code of Civil Procedure, 1908", "CPC"),
    "Code_Of_Civil_Procedure_1908_v2.pdf": ("Code of Civil Procedure, 1908", "CPC"),
    "Indian_Contract_Act_1872.pdf": ("Indian Contract Act, 1872", ""),
    "Transfer_of_Property_Act_1882.pdf": ("Transfer of Property Act, 1882", "TPA"),
    "Negotiable_Instruments_Act_1881.pdf": ("Negotiable Instruments Act, 1881", "NI Act"),
    "Constitution_of_India.pdf": ("Constitution of India", ""),
    "Motor_Vehicles_Act_1988.pdf": ("Motor Vehicles Act, 1988", ""),
    "Hindu_Marriage_Act_1955.pdf": ("Hindu Marriage Act, 1955", ""),
    "Hindu_Succession_Act_1956.pdf": ("Hindu Succession Act, 1956", ""),
    "Hindu_Minority_And_Guardianship_Act_1956.pdf": ("Hindu Minority and Guardianship Act, 1956", ""),
    "Dowry_Prohibition_Act_1961.pdf": ("Dowry Prohibition Act, 1961", ""),
    "Protection_of_Women_from_Domestic_Violence_Act_2005.pdf": ("Protection of Women from Domestic Violence Act, 2005", ""),
    "Narcotic_Drugs_and_Psychotropic_Substances_Act_1985.pdf": ("Narcotic Drugs and Psychotropic Substances Act, 1985", "NDPS"),
    "Consumer_Protection_Act_2019.pdf": ("Consumer Protection Act, 2019", ""),
    "Information_Technology_Act_2000.pdf": ("Information Technology Act, 2000", "IT Act"),
    "Limitation_Act_1963.pdf": ("Limitation Act, 1963", ""),
    "Arbitration_and_Conciliation_Act_1996.pdf": ("Arbitration and Conciliation Act, 1996", ""),
    "Industrial_Disputes_Act_1947.pdf": ("Industrial Disputes Act, 1947", "IDA"),
    "Family_Courts_Act_1984.pdf": ("Family Courts Act, 1984", ""),
    "Competition_Act_2002.pdf": ("Competition Act, 2002", ""),
    "Juvenile_Justice_Act_2015.pdf": ("Juvenile Justice Act, 2015", "JJ Act"),
    "Forest_Act_1927.pdf": ("Forest Act, 1927", ""),
    "Specific_Relief_Act_1963.pdf": ("Specific Relief Act, 1963", ""),
    "Factories_Act_1948.pdf": ("Factories Act, 1948", ""),
    "Easements_Act_1882.pdf": ("Easements Act, 1882", ""),
    "Arms_Act_1959.pdf": ("Arms Act, 1959", ""),
    "Copyright_Act_1957.pdf": ("Copyright Act, 1957", ""),
    "Environment_Protection_Act_1986.pdf": ("Environment Protection Act, 1986", ""),
    "Right_To_Information_Act_2005.pdf": ("Right to Information Act, 2005", "RTI"),
    "Legal_Services_Authorities_Act_1987.pdf": ("Legal Services Authorities Act, 1987", ""),
    "Prevention_of_Corruption_Act_1988.pdf": ("Prevention of Corruption Act, 1988", ""),
    "Gram_Nyayalayas_Act_2008.pdf": ("Gram Nyayalayas Act, 2008", ""),
    "Trusts_Act_1882.pdf": ("Trusts Act, 1882", ""),
}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
EMBED_BATCH = 16
PDF_TIMEOUT = 120

pc = Pinecone(api_key=PINECONE_API_KEY)
idx = pc.Index("hector-legal")


def chunk_text(text):
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def extract_act_name(filename):
    if filename in FILENAME_TO_ACT:
        return FILENAME_TO_ACT[filename][0]
    name = filename.replace(".pdf", "").replace("_", " ").replace("-", " ")
    name = re.sub(r'^fixed\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(z-library.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(Dr\s.*$', '', name, flags=re.IGNORECASE)
    return name.strip()


def guess_abbr(name, filename):
    if filename in FILENAME_TO_ACT:
        return FILENAME_TO_ACT[filename][1]
    return name[:20]


def is_commentary(filename):
    lower = filename.lower()
    return any(kw in lower for kw in [
        "commentary", "textbook", "ratanlal", "fixed_whartons",
        "fighting corruption", "z-library", "dr j n", "law of evidence"
    ])


def safe_extract_text(pdf_path):
    def _extract():
        reader = PdfReader(str(pdf_path))
        text = ""
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
                text += t + "\n"
            except Exception:
                pass
        return text
    with ThreadPoolExecutor(1) as executor:
        future = executor.submit(_extract)
        try:
            return future.result(timeout=PDF_TIMEOUT)
        except (FuturesTimeout, Exception):
            return None


def process_pdf(pdf_path):
    pdf_name = pdf_path.name
    act_name = extract_act_name(pdf_name)
    abbreviation = guess_abbr(act_name, pdf_name)
    source_type = "commentary" if is_commentary(pdf_name) else "bare_act"

    all_text = safe_extract_text(pdf_path)
    if not all_text or not all_text.strip():
        return []

    records = []
    section_pattern = re.compile(
        r'(?:^|\n)\s*(?:Section|Sec\.?)\s+(\d+[A-Za-z]*?)\s*[\.\-\:]*\s*'
        r'|'
        r'(?:^|\n)\s*(\d+[A-Za-z]*)\.\s+',
        re.IGNORECASE
    )
    matches = list(section_pattern.finditer(all_text))

    if len(matches) >= 2:
        preamble = all_text[:matches[0].start()].strip()
        if preamble and len(preamble) > 50:
            for chunk in chunk_text(preamble):
                records.append({"document": chunk, "metadata": {
                    "source": pdf_name, "act_name": act_name, "real_act_name": act_name,
                    "abbreviation": abbreviation, "source_type": source_type,
                    "chunk_index": len(records),
                }})
        for i, m in enumerate(matches):
            sec_num = (m.group(1) or m.group(2) or "").strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(all_text)
            body = all_text[start:end].strip()
            for chunk in chunk_text(body if body else sec_num):
                records.append({"document": chunk, "metadata": {
                    "source": pdf_name, "section_number": sec_num, "act_name": act_name,
                    "real_act_name": act_name, "abbreviation": abbreviation,
                    "source_type": source_type, "chunk_index": len(records),
                }})
    else:
        for i, chunk in enumerate(chunk_text(all_text)):
            records.append({"document": chunk, "metadata": {
                "source": pdf_name, "act_name": act_name, "real_act_name": act_name,
                "abbreviation": abbreviation, "source_type": source_type, "chunk_index": i,
            }})
    return records


def embed_batch(texts):
    for attempt in range(15):
        try:
            resp = httpx.post(
                f"{NIM_BASE_URL}/embeddings",
                headers={"Authorization": f"Bearer {NIM_API_KEY}", "Content-Type": "application/json"},
                json={"input": texts, "model": EMBEDDING_MODEL, "encoding_format": "float",
                      "input_type": "passage", "truncate": "END"},
                timeout=60.0,
            )
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 0)) or 15 * (attempt + 1)
                print(f"      429 rate limit, waiting {wait}s...", flush=True)
                time.sleep(wait)
                continue
            if resp.status_code == 503:
                time.sleep(20)
                continue
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in sorted(data.get("data", []), key=lambda x: x["index"])]
        except Exception as e:
            print(f"      Embed error: {e}", flush=True)
            time.sleep(5 * (attempt + 1))
    return None


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except Exception:
            pass
    return {"completed_pdfs": [], "total_vectors": 0}


def save_progress(data):
    PROGRESS_FILE.write_text(json.dumps(data))


def upsert_pdf_chunks(records, pdf_name):
    """Embed and upsert all chunks for one PDF."""
    total = len(records)
    upserted = 0
    vec_buffer = []

    for i in range(0, total, EMBED_BATCH):
        batch = records[i:i + EMBED_BATCH]
        texts = [r["document"] for r in batch]
        embs = embed_batch(texts)
        if embs is None:
            print(f"      FAILED embedding batch at {i}, skipping", flush=True)
            continue

        for j, (rec, emb) in enumerate(zip(batch, embs)):
            chunk_id = hashlib.md5(
                f"{pdf_name}_{rec['metadata'].get('section_number', '')}_{upserted + j}".encode()
            ).hexdigest()[:24]
            vec_buffer.append({
                "id": f"vec_{chunk_id}",
                "values": emb,
                "metadata": rec["metadata"],
            })

        if len(vec_buffer) >= 100:
            idx.upsert(vectors=vec_buffer)
            upserted += len(vec_buffer)
            vec_buffer = []
            print(f"      {upserted}/{total} chunks upserted ({upserted*100//total}%)", flush=True)

        time.sleep(1.5)

    if vec_buffer:
        idx.upsert(vectors=vec_buffer)
        upserted += len(vec_buffer)

    return upserted


def main():
    if not NIM_API_KEY:
        print("ERROR: NIM_API_KEY")
        return
    if not PINECONE_API_KEY:
        print("ERROR: PINECONE_API_KEY")
        return

    print("=" * 70, flush=True)
    print("HECTOR RE-INGESTION v3 (per-PDF embedding)", flush=True)
    print(f"Model: {EMBEDDING_MODEL}", flush=True)
    print("=" * 70, flush=True)

    progress = load_progress()
    done_pdfs = set(progress.get("completed_pdfs", []))
    total_vectors = progress.get("total_vectors", 0)

    pdfs = sorted(BOOKS_DIR.glob("*.pdf"))
    print(f"\n{len(pdfs)} PDFs found, {len(done_pdfs)} already done\n", flush=True)

    for pdf in pdfs:
        if pdf.name in done_pdfs:
            continue
        if pdf.name in SKIP_PDFS:
            done_pdfs.add(pdf.name)
            progress["completed_pdfs"] = list(done_pdfs)
            save_progress(progress)
            print(f"  SKIP: {pdf.name}", flush=True)
            continue
        if pdf.stat().st_size > 50 * 1024 * 1024:
            done_pdfs.add(pdf.name)
            progress["completed_pdfs"] = list(done_pdfs)
            save_progress(progress)
            print(f"  SKIP (large): {pdf.name}", flush=True)
            continue

        print(f"\n  Processing: {pdf.name}", flush=True)
        records = process_pdf(pdf)
        if not records:
            print("    No chunks extracted", flush=True)
            done_pdfs.add(pdf.name)
            progress["completed_pdfs"] = list(done_pdfs)
            save_progress(progress)
            continue

        print(f"    {len(records)} chunks -> embedding + upserting...", flush=True)
        upserted = upsert_pdf_chunks(records, pdf.name)
        total_vectors += upserted
        done_pdfs.add(pdf.name)
        progress["completed_pdfs"] = list(done_pdfs)
        progress["total_vectors"] = total_vectors
        save_progress(progress)
        print(f"    Done. Total vectors so far: {total_vectors}", flush=True)

    stats = idx.describe_index_stats()
    final = stats.get("total_vector_count", "?")
    print(f"\n{'=' * 70}", flush=True)
    print(f"COMPLETE! Pinecone has {final} vectors", flush=True)
    print(f"{'=' * 70}", flush=True)


if __name__ == "__main__":
    main()
