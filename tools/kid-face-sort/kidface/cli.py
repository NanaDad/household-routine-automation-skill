#!/usr/bin/env python3
"""kid-face-sort: 로컬 전용 아이 얼굴 분류 CLI (InsightFace buffalo_l / ArcFace).
모든 처리는 로컬. 모델 최초 다운로드 이후 네트워크 사용 없음.

DB 형식(v2, .npz):
  "<name>__emb"  : (N,512) float32 L2-정규화 임베딩
  "__meta__"     : JSON 문자열 {name: [ {sha1, date, bucket, score, added_at, origin, file}, ... ]}
  구버전(v1: "<name>" -> (N,512))은 로드 시 자동 변환(origin=manual, date=None).

매칭 점수(성장 반영):
  ref를 3개월 버킷(YYYY-Qn)으로 묶고, 버킷별 최대 코사인 × 가중치 중 최댓값.
  가중치 w = max(FLOOR, 1 - DECAY × 버킷거리)
    - 사진 촬영일을 알면: 버킷거리 = |사진 버킷 - ref 버킷|  (가장 가까운 시기 우선)
    - 모르면: 버킷거리 = 최신 ref 버킷 - ref 버킷              (최근 얼굴 우선)
    - 날짜 없는 ref: 거리 2로 취급
  DECAY=0.02, FLOOR=0.85 → 오래된 ref도 최대 15%만 감점되어 여전히 매칭에 기여.
"""
import argparse, csv, time, datetime as dt, hashlib, json, os, shutil, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cache import Cache, DEFAULT_CACHE, db_hash
import meta as kmeta
from PIL import Image, ImageOps

try:
    import pillow_heif; pillow_heif.register_heif_opener()
except ImportError:
    pass

EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp"}
DEFAULT_DB = Path(os.environ.get("KIDFACE_DB", Path.home() / ".kidface" / "embeddings.npz"))
DECAY, FLOOR, UNKNOWN_DIST = 0.02, 0.85, 2
_app = None

# ---------- 모델 / 이미지 ----------
def get_app(det_size=640):
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        import onnxruntime as ort
        prov = [p for p in ("CoreMLExecutionProvider", "CPUExecutionProvider") if p in ort.get_available_providers()]
        if os.environ.get("KIDFACE_CPU_ONLY"): prov = ["CPUExecutionProvider"]
        _app = FaceAnalysis(name=os.environ.get("KIDFACE_MODEL", "buffalo_l"),
                            allowed_modules=["detection", "recognition"], providers=prov)
        _app.prepare(ctx_id=0, det_size=(det_size, det_size))
    return _app

def load_bgr(path, max_side=1920):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((max_side, max_side))
    return np.asarray(im)[:, :, ::-1].copy()

def faces_in(path, min_face=40):
    out = []
    for f in get_app().get(load_bgr(path)):
        x1, y1, x2, y2 = f.bbox
        if min(x2 - x1, y2 - y1) < min_face: continue
        out.append((f.normed_embedding.astype(np.float32), float(f.det_score), [int(v) for v in f.bbox]))
    return out

def largest(fs):
    return max(fs, key=lambda f: (f[2][2]-f[2][0])*(f[2][3]-f[2][1]))

def file_sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def capture_date(p):
    """EXIF DateTimeOriginal → DateTime → 파일 mtime. 'YYYY-MM-DD' 반환."""
    try:
        ex = Image.open(p).getexif()
        v = ex.get_ifd(0x8769).get(36867) or ex.get(306)
        if v: return dt.datetime.strptime(str(v).strip()[:19], "%Y:%m:%d %H:%M:%S").date().isoformat()
    except Exception:
        pass
    try: return dt.date.fromtimestamp(Path(p).stat().st_mtime).isoformat()
    except Exception: return None

def bucket_of(date):
    if not date: return None
    y, m = int(date[:4]), int(date[5:7]); return f"{y}-Q{(m - 1) // 3 + 1}"

def bucket_idx(b):
    return None if not b else int(b[:4]) * 4 + int(b[-1]) - 1

def iter_images(root):
    root = Path(root)
    if root.is_file(): yield root; return
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTS and not p.name.startswith("."): yield p

def now(): return dt.datetime.now().isoformat(timespec="seconds")

# ---------- DB ----------
def load_db(db):
    """{name: {"emb": (N,512), "meta": [dict]}}. v1 자동 변환."""
    db = Path(db)
    if not db.exists(): return {}
    d = np.load(db, allow_pickle=False)
    meta = json.loads(str(d["__meta__"])) if "__meta__" in d.files else {}
    out = {}
    for k in d.files:
        if k == "__meta__": continue
        if k.endswith("__emb"):
            n = k[:-5]; out[n] = {"emb": d[k], "meta": meta.get(n, [])}
        else:  # v1
            out[k] = {"emb": d[k], "meta": [{"sha1": None, "date": None, "bucket": None, "score": None,
                                             "added_at": None, "origin": "manual", "file": None} for _ in d[k]]}
    for n, v in out.items():  # 길이 보정
        if len(v["meta"]) != len(v["emb"]):
            v["meta"] = (v["meta"] + [{"origin": "manual", "bucket": None}] * len(v["emb"]))[:len(v["emb"])]
    return out

def save_db(db, data):
    db = Path(db); db.parent.mkdir(parents=True, exist_ok=True)
    arrs = {f"{n}__emb": v["emb"].astype(np.float32) for n, v in data.items()}
    arrs["__meta__"] = np.array(json.dumps({n: v["meta"] for n, v in data.items()}, ensure_ascii=False))
    tmp = db.with_name(db.stem + ".tmp.npz"); np.savez(tmp, **arrs); os.replace(tmp, db); os.chmod(db, 0o600)

def backup_dir(db): return Path(db).parent / "backups"

def backup(db):
    db = Path(db)
    if not db.exists(): return None
    bd = backup_dir(db); bd.mkdir(parents=True, exist_ok=True)
    dst = bd / f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.npz"; shutil.copy2(db, dst); os.chmod(dst, 0o600)
    return dst

# ---------- 매칭 ----------
def score(emb, entry, photo_date=None, return_detail=False):
    """버킷별 max cos × 시기 가중치의 최댓값 (모듈 docstring 참고)."""
    refs, meta = entry["emb"], entry["meta"]
    sims = refs @ emb
    bidx = [bucket_idx(m.get("bucket")) for m in meta]
    known = [b for b in bidx if b is not None]
    pb = bucket_idx(bucket_of(photo_date)) if photo_date else None
    anchor = pb if pb is not None else (max(known) if known else None)
    best, best_i = -1.0, -1
    for i, (s, b) in enumerate(zip(sims, bidx)):
        dist = UNKNOWN_DIST if (b is None or anchor is None) else abs(anchor - b)
        if anchor is None: dist = 0
        v = float(s) * max(FLOOR, 1 - DECAY * dist)
        if v > best: best, best_i = v, i
    return (best, float(sims[best_i]), best_i) if return_detail else best

# ---------- 명령 ----------
def cmd_enroll(a):
    data = load_db(a.db); embs, metas = [], []
    for p in (q for s in a.photos for q in iter_images(s)):
        fs = faces_in(p, a.min_face)
        if not fs: print(f"[skip] 얼굴 없음: {p}"); continue
        if len(fs) > 1 and not a.largest:
            print(f"[skip] 얼굴 {len(fs)}개 (기준사진은 1명만, 또는 --largest): {p}"); continue
        d = capture_date(p)
        embs.append(largest(fs)[0])
        metas.append({"sha1": file_sha1(p), "date": d, "bucket": bucket_of(d), "score": None,
                      "added_at": now(), "origin": "manual", "file": p.name})
        print(f"[ok] {p.name} ({bucket_of(d)})")
    if not embs: sys.exit("등록된 얼굴이 없습니다.")
    if a.name in data and not a.replace:
        e = data[a.name]; emb = np.vstack([e["emb"], np.stack(embs)]); meta = e["meta"] + metas
    else: emb, meta = np.stack(embs), metas
    backup(a.db); data[a.name] = {"emb": emb, "meta": meta}; save_db(a.db, data)
    print(f"'{a.name}': 기준 얼굴 {len(emb)}개 저장 → {a.db} (임베딩+메타만 저장, 사진은 저장 안 함)")

def place(src, dst_dir, mode):
    dst_dir.mkdir(parents=True, exist_ok=True); dst = dst_dir / src.name
    if dst.is_symlink() and dst.resolve() == src.resolve(): return dst
    if mode == "copy" and dst.exists() and not dst.is_symlink() and dst.stat().st_size == src.stat().st_size: return dst
    i = 1
    while dst.exists() or dst.is_symlink():
        dst = dst_dir / f"{src.stem}_{i}{src.suffix}"; i += 1
    if mode == "symlink": dst.symlink_to(src.resolve())
    elif mode == "copy": shutil.copy2(src, dst)
    return dst

def open_cache(a):
    return None if getattr(a, "no_cache", False) else Cache(a.cache)

def get_faces_cached(p, a, cache, stat):
    """(sha1, faces, photo_date). 캐시에 있으면 검출 생략."""
    if cache is None:
        return None, faces_in(p, a.min_face), capture_date(p)
    sha = cache.sha_for(p, file_sha1, getattr(a, "rescan", False))
    g = None if getattr(a, "rescan", False) else cache.get_faces(sha)
    if g: stat["cached"] += 1; return sha, g[0], g[1]
    fs = faces_in(p, a.min_face); d = capture_date(p)
    cache.put_faces(sha, fs, d); stat["detected"] += 1
    return sha, fs, d

def decide(fs, pdate, data, t, m):
    scores, best = [], {}
    positive_names = [n for n in data if n != "__negative__"]
    accepted = set(); near = set()
    for i, (e, ds, bb) in enumerate(fs):
        face_best = {}
        for name in positive_names:
            sc = score(e, data[name], pdate); scores.append([i, name, round(sc, 4), round(ds, 3), *bb])
            best[name] = round(max(best.get(name, -1), sc), 4)
            face_best[name] = sc
        pos_name, pos_sc = max(face_best.items(), key=lambda kv: kv[1], default=(None, -1.0))
        neg_sc = score(e, data["__negative__"], pdate) if "__negative__" in data else -1.0
        # Compare the same detected face against the positive label and confirmed lookalike negatives.
        if pos_name and pos_sc >= t and neg_sc < pos_sc: accepted.add(pos_name)
        elif pos_name and pos_sc >= t - m and neg_sc < pos_sc: near.add(pos_name)
    dests = sorted(accepted)
    if not dests and near: dests = ["_unsure"]
    return scores, best, dests

def write_meta(p, best, dests, a, cache=None, sha=None):
    hits = {n: best[n] for n in dests if n in best}
    if not hits: return
    if a.write_meta == "sidecar": kmeta.write_sidecar(p, hits)
    elif a.write_meta == "inplace":
        r = kmeta.write_inplace(p, hits); print("   inplace:", r)
        if r == "ok" and cache and sha: cache.alias(sha, p, file_sha1)
    if a.finder_tag: kmeta.write_finder_tags(p, hits)

def cmd_sort(a):
    data = load_db(a.db)
    if not data: sys.exit("등록된 아이가 없습니다. 먼저 enroll 하세요.")
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    cache = open_cache(a); dbh = db_hash(a.db)
    stat = {"detected": 0, "cached": 0, "rescored": 0, "reused": 0}
    rows = []; counts = {}; t0 = time.time()
    for p in iter_images(a.input):
        if out.resolve() in p.resolve().parents: continue
        try: sha, fs, pdate = get_faces_cached(p, a, cache, stat)
        except Exception as e: print(f"[err] {p}: {e}"); continue
        r = cache.get_result(sha, dbh, a.threshold, a.margin) if cache else None
        if r: scores, best, dests = r; stat["reused"] += 1
        else:
            scores, best, dests = decide(fs, pdate, data, a.threshold, a.margin)
            if cache: cache.put_result(sha, dbh, a.threshold, a.margin, scores, best, dests); stat["rescored"] += 1
        rows += [[str(p), *x, pdate] for x in scores]
        if not dests and a.keep_others: dests = ["_noface"] if not fs else ["_others"]
        for d in dests:
            if a.mode != "dry": place(p, out / d, a.mode)
            counts[d] = counts.get(d, 0) + 1
        if a.write_meta or a.finder_tag: write_meta(p, best, dests, a, cache, sha)
        if a.verbose or not r: print(f"{p.name}: faces={len(fs)} " + " ".join(f"{n}={s:.3f}" for n, s in best.items()) + f" -> {dests or '-'}")
    if cache: cache.commit()
    with open(out / "report.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["file", "face_idx", "child", "score", "det_score", "x1", "y1", "x2", "y2", "date"]); w.writerows(rows)
    print("결과:", json.dumps(counts, ensure_ascii=False), "| 리포트:", out / "report.csv")
    print(f"캐시: 검출 {stat['detected']} / 캐시재사용 {stat['cached']} / 재채점 {stat['rescored']} / 결과재사용 {stat['reused']} | {time.time()-t0:.1f}s")

def cmd_cache(a):
    c = Cache(a.cache)
    if a.action == "stats": print(json.dumps(c.stats(), ensure_ascii=False, indent=1))
    elif a.action == "clear": c.clear(); print("캐시 삭제 완료")
    elif a.action == "export":
        out = a.out or "kidface_cache.csv"
        with open(out, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["path", "sha1", "photo_date", "n_faces", "best_scores", "decision", "db_hash", "threshold", "scored_at", "model"])
            w.writerows(c.export_rows())
        print("내보냄:", out)

def cmd_tune(a):
    entry = load_db(a.db)[a.name]
    def best_scores(folder):
        r = []
        for p in iter_images(folder):
            fs = faces_in(p, a.min_face); d = capture_date(p)
            r.append((p.name, max((score(e, entry, d) for e, _, _ in fs), default=-1)))
        return r
    pos = best_scores(a.positives); neg = best_scores(a.negatives) if a.negatives else []
    for n, s in pos: print(f"POS {s:.3f} {n}")
    for n, s in neg: print(f"NEG {s:.3f} {n}")
    pmin = min(s for _, s in pos); nmax = max((s for _, s in neg), default=0.2)
    print(f"\n양성 최소 {pmin:.3f} / 음성 최대 {nmax:.3f}")
    if pmin > nmax: print(f"추천 threshold = {(pmin + nmax) / 2:.3f}")
    else: print("양성/음성이 겹칩니다. 기준사진을 늘리거나 --margin(unsure)을 넓히세요.")

def is_unsure(p): return any(part.lower() == "_unsure" for part in Path(p).parts)

def refresh_candidates(a, entry):
    src = a.source; cache = None if a.no_cache else Cache(a.cache); stat = {"detected": 0, "cached": 0}
    def from_paths(files):
        for p in files:
            p = Path(p)
            if is_unsure(p) or not p.exists(): yield p, None, None, None, None; continue
            sha, fs, d = get_faces_cached(p, a, cache, stat)
            yield p, sha or file_sha1(p), d, fs, None
    if src == "cache":
        if cache is None: sys.exit("--no-cache 와 cache 소스는 함께 쓸 수 없습니다")
        items = cache.iter_cached()
    elif Path(src).suffix.lower() == ".csv":
        files = []
        with open(src) as f:
            for r in csv.DictReader(f):
                if r["child"] == a.name and float(r["score"]) >= a.min_score: files.append(r["file"])
        items = from_paths(dict.fromkeys(files))
    else: items = from_paths(iter_images(src))
    manual = [i for i, m in enumerate(entry["meta"]) if m.get("origin") == "manual"]
    anchor = {"emb": entry["emb"][manual], "meta": [entry["meta"][i] for i in manual]} if manual else entry
    known = {m.get("sha1") for m in entry["meta"]}
    cands, skipped = [], {"unsure": 0, "dup_file": 0, "low": 0, "ambiguous": 0, "noface": 0}
    for p, h, d, fs, decision in items:
        if fs is None or is_unsure(p) or (decision is not None and "_unsure" in decision): skipped["unsure"] += 1; continue
        if h in known: skipped["dup_file"] += 1; continue
        if not fs: skipped["noface"] += 1; continue
        sc = [(score(e, entry, d), e) for e, _, _ in fs]
        hits = [x for x in sc if x[0] >= a.min_score]
        if not hits: skipped["low"] += 1; continue
        if len(hits) > 1: skipped["ambiguous"] += 1; continue
        s_, e = hits[0]
        if score(e, anchor, d) < a.min_score: skipped["low"] += 1; continue
        known.add(h)
        cands.append({"emb": e, "meta": {"sha1": h, "date": d, "bucket": bucket_of(d), "score": round(s_, 4),
                                         "added_at": now(), "origin": "auto", "file": p.name}})
    if cache: cache.commit()
    return cands, skipped

def diverse_pick(embs, keep_fixed, k):
    """farthest-point: 고정 인덱스(수동)는 유지하고 나머지에서 가장 다른 것부터 k개까지."""
    chosen = list(keep_fixed); rest = [i for i in range(len(embs)) if i not in chosen]
    if not chosen and rest: chosen.append(rest.pop(0))
    while len(chosen) < k and rest:
        sims = embs[rest] @ embs[chosen].T
        j = int(np.argmin(sims.max(1))); chosen.append(rest.pop(j))
    return chosen

def cmd_refresh(a):
    data = load_db(a.db)
    if a.name not in data: sys.exit(f"'{a.name}' 미등록")
    entry = data[a.name]
    cands, skipped = refresh_candidates(a, entry)
    emb = list(entry["emb"]); meta = list(entry["meta"]); new = []
    for c in cands:  # 근접중복 제거
        if emb and float(np.max(np.stack(emb) @ c["emb"])) > a.dup_cos: skipped["dup_cos"] = skipped.get("dup_cos", 0) + 1; continue
        emb.append(c["emb"]); meta.append(c["meta"]); new.append(len(meta) - 1)
    emb = np.stack(emb)
    keep = []
    for b in sorted({m.get("bucket") for m in meta}, key=lambda x: x or ""):
        idx = [i for i, m in enumerate(meta) if m.get("bucket") == b]
        if len(idx) <= a.cap: keep += idx; continue
        fixed = [j for j, i in enumerate(idx) if meta[i].get("origin") == "manual" or i not in new]
        sel = diverse_pick(emb[idx], fixed, max(a.cap, len(fixed)))
        dropped = len(idx) - len(sel); skipped["cap"] = skipped.get("cap", 0) + dropped
        keep += [idx[j] for j in sel]
    keep = sorted(keep); added = [i for i in new if i in keep]
    print(f"[{a.name}] 기존 {len(entry['emb'])}개, 추가 후보 {len(added)}개, 제외 {skipped}")
    for i in added: m = meta[i]; print(f"  + {m['file']}  score={m['score']}  {m['bucket']}")
    if not a.apply: print("(dry-run) 적용하려면 --apply"); return
    if not added: print("추가할 항목 없음"); return
    b = backup(a.db)
    data[a.name] = {"emb": emb[keep], "meta": [meta[i] for i in keep]}; save_db(a.db, data)
    print(f"적용 완료: {len(keep)}개 | 백업: {b}")

def cmd_rollback(a):
    bks = sorted(backup_dir(a.db).glob("*.npz"))
    if not bks: sys.exit("백업 없음")
    src = bks[-1]; cur = load_db(a.db); old = load_db(src)
    backup(a.db)  # 롤백 전 상태도 백업
    if a.name == "all": cur = old
    elif a.name in old: cur[a.name] = old[a.name]
    else: cur.pop(a.name, None)
    save_db(a.db, cur); src.rename(src.with_suffix(".used"))
    print(f"롤백 완료 ← {src.name} ({a.name})")

def cmd_list(a):
    for n, v in load_db(a.db).items():
        bs = {}
        for m in v["meta"]: k = (m.get("bucket") or "날짜없음", m.get("origin", "manual")); bs[k] = bs.get(k, 0) + 1
        print(f"{n}: {len(v['emb'])}개  " + ", ".join(f"{b}/{o}={c}" for (b, o), c in sorted(bs.items())))

def cmd_forget(a):
    d = load_db(a.db); backup(a.db); d.pop(a.name, None); save_db(a.db, d); print(f"'{a.name}' 삭제")

def cmd_migrate(a):
    d = load_db(a.db); backup(a.db); save_db(a.db, d); print(f"v2 형식으로 저장: {a.db}")

def main():
    ap = argparse.ArgumentParser(prog="kidface", description="로컬 아이 얼굴 분류 (InsightFace)")
    ap.add_argument("--db", default=str(DEFAULT_DB)); ap.add_argument("--cache", default=str(DEFAULT_CACHE)); ap.add_argument("--no-cache", action="store_true"); ap.add_argument("--min-face", type=int, default=40)
    sp = ap.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("enroll"); e.add_argument("name"); e.add_argument("photos", nargs="+")
    e.add_argument("--largest", action="store_true", help="여러 얼굴이면 가장 큰 얼굴 사용"); e.add_argument("--replace", action="store_true"); e.set_defaults(f=cmd_enroll)
    s = sp.add_parser("sort"); s.add_argument("input"); s.add_argument("-o", "--output", default="sorted")
    s.add_argument("-t", "--threshold", type=float, default=0.55); s.add_argument("--margin", type=float, default=0.10)
    s.add_argument("--mode", choices=["symlink", "copy", "dry"], default="symlink"); s.add_argument("--keep-others", action="store_true")
    s.add_argument("--no-cache", action="store_true", default=argparse.SUPPRESS); s.add_argument("--rescan", action="store_true", help="캐시 무시하고 다시 검출"); s.add_argument("-v", "--verbose", action="store_true")
    s.add_argument("--write-meta", nargs="?", const="sidecar", choices=["sidecar", "inplace"], help="XMP 사이드카(기본) 또는 exiftool로 원본에 기록")
    s.add_argument("--finder-tag", action="store_true", help="macOS Finder 태그(kidface:이름)"); s.set_defaults(f=cmd_sort)
    t = sp.add_parser("tune"); t.add_argument("name"); t.add_argument("positives"); t.add_argument("negatives", nargs="?"); t.set_defaults(f=cmd_tune)
    r = sp.add_parser("refresh", help="고신뢰 매칭으로 기준 얼굴 자동 보강 (기본 dry-run)")
    r.add_argument("name"); r.add_argument("source", help="사진 폴더, sort의 report.csv, 또는 cache")
    r.add_argument("--min-score", type=float, default=0.65); r.add_argument("--dup-cos", type=float, default=0.95)
    r.add_argument("--cap", type=int, default=20, help="버킷(3개월)당 최대 ref 수"); r.add_argument("--apply", action="store_true"); r.add_argument("--no-cache", action="store_true", default=argparse.SUPPRESS); r.set_defaults(f=cmd_refresh)
    rb = sp.add_parser("rollback"); rb.add_argument("name", help="아이 이름 또는 all"); rb.set_defaults(f=cmd_rollback)
    c = sp.add_parser("cache"); c.add_argument("action", choices=["stats", "clear", "export"]); c.add_argument("out", nargs="?"); c.set_defaults(f=cmd_cache)
    sp.add_parser("list").set_defaults(f=cmd_list)
    sp.add_parser("migrate").set_defaults(f=cmd_migrate)
    fg = sp.add_parser("forget"); fg.add_argument("name"); fg.set_defaults(f=cmd_forget)
    a = ap.parse_args(); a.f(a)

if __name__ == "__main__": main()
