"""사진 메타데이터 기록: XMP 사이드카(기본) / exiftool inplace / macOS Finder 태그."""
import plistlib, shutil, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape

MARK = "kidface"

def sidecar_path(p): return Path(p).with_suffix(".xmp")  # IMG_0001.HEIC -> IMG_0001.xmp (Lightroom/Photos 관례)

def write_sidecar(p, matches):
    """matches: {name: score}. 기존 xmp가 kidface가 만든 것이 아니면 덮어쓰지 않음."""
    sp = sidecar_path(p)
    if sp.exists() and MARK not in sp.read_text(errors="ignore"):
        return f"skip(기존 xmp 존재): {sp}"
    subj = "".join(f"<rdf:li>{escape(MARK + ':' + n)}</rdf:li>" for n in matches)
    sc = ";".join(f"{n}={s:.4f}" for n, s in matches.items())
    sp.write_text(f"""<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:kidface="https://kidface.local/ns/1.0/"
 kidface:Scores="{escape(sc)}" kidface:Source="{escape(Path(p).name)}">
<dc:subject><rdf:Bag>{subj}</rdf:Bag></dc:subject>
</rdf:Description></rdf:RDF></x:xmpmeta>
<?xpacket end='w'?>
""", encoding="utf-8")
    return str(sp)

def write_inplace(p, matches):
    """원본 파일 수정! exiftool 필요. 기존 kidface 키워드는 교체."""
    if not shutil.which("exiftool"): return "skip(exiftool 없음: brew install exiftool)"
    args = ["exiftool", "-q", "-overwrite_original", "-config", str(Path(__file__).with_name("exiftool_kidface.config"))]
    args += [f"-XMP-dc:Subject-={MARK}:{n}" for n in matches] + [f"-XMP-dc:Subject+={MARK}:{n}" for n in matches]
    args += [f"-XMP-kidface:Scores={';'.join(f'{n}={s:.4f}' for n, s in matches.items())}", str(p)]
    r = subprocess.run(args, capture_output=True, text=True)
    return "ok" if r.returncode == 0 else f"err: {r.stderr.strip()}"

def write_finder_tags(p, matches):
    if sys.platform != "darwin": return "skip(macOS 아님)"
    attr = "com.apple.metadata:_kMDItemUserTags"
    cur = []
    r = subprocess.run(["xattr", "-px", attr, str(p)], capture_output=True, text=True)
    if r.returncode == 0:
        try: cur = plistlib.loads(bytes.fromhex(r.stdout.replace(" ", "").replace("\n", "")))
        except Exception: cur = []
    tags = [t for t in cur if not t.startswith(MARK + ":")] + [f"{MARK}:{n}" for n in matches]
    hx = plistlib.dumps(tags, fmt=plistlib.FMT_BINARY).hex()
    r = subprocess.run(["xattr", "-wx", attr, hx, str(p)], capture_output=True, text=True)
    return "ok" if r.returncode == 0 else f"err: {r.stderr.strip()}"
