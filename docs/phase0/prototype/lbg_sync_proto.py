"""Phase 0 prototype: analyze + generate for one week. Not production code."""
import sys, re, unicodedata, collections, json
import openpyxl
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
from lbg_xmlpatch import patch

DAYS = [("Hai", 3, {"SÁNG": (3, 6), "CHIỀU": (7, 9)}), ("Ba", 10, {"SÁNG": (10, 13), "CHIỀU": (14, 16)}),
        ("Tư", 17, {"SÁNG": (17, 20), "CHIỀU": (21, 22)}), ("Năm", 23, {"SÁNG": (23, 26), "CHIỀU": (27, 28)}),
        ("Sáu", 29, {"SÁNG": (29, 32), "CHIỀU": (33, 34)})]
GROUPS = [["HĐTV", "HĐTT", "HĐTV/HĐTT"]]
EXCLUDED = {"Tiếng Anh", "Tin học", "Âm nhạc", "Mỹ thuật", "Công nghệ", "GDTC", "Lịch sử & Địa lí", "HĐTV/HĐTT"}

def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(s or ""))).strip()
def key(subject):
    n = norm(subject)
    for g in GROUPS:
        if n.casefold() in [x.casefold() for x in g]: return "/".join(g[:2])
    return n
def is_off(v):
    t = norm(v).casefold()
    return t == "" or "nghỉ" in t

def read_slots(ws):
    out = []
    for day, drow, sessions in DAYS:
        for sess, (a, b) in sessions.items():
            for r in range(a, b + 1):
                out.append(dict(day=day, session=sess, row=r, subject=norm(ws[f"D{r}"].value), key=key(ws[f"D{r}"].value),
                                lesson=norm(ws[f"E{r}"].value) and str(ws[f"E{r}"].value).strip(),
                                equipment=ws[f"F{r}"].value, off=is_off(ws[f"E{r}"].value) or "nghỉ" in norm(ws[f"D{r}"].value).casefold()))
    return out

def analyze(src_ws, dst_ws, selected=None):
    src, dst = read_slots(src_ws), read_slots(dst_ws)
    off_sessions = {(d, s) for d, _, ss in DAYS for s in ss
                    if all(x["off"] for x in src if x["day"] == d and x["session"] == s)}
    keys = sorted({x["key"] for x in src} | {x["key"] for x in dst})
    if selected is None: selected = [k for k in keys if k not in EXCLUDED]
    result, edits = [], {}
    for k in keys:
        if k not in selected: continue
        s = [x for x in src if x["key"] == k]; t = [x for x in dst if x["key"] == k]
        reasons = []
        off_src = [x for x in s if x["off"]]
        off_dst = [x for x in t if (x["day"], x["session"]) in off_sessions]
        if off_src: reasons.append("không có nội dung/nghỉ ở nguồn: " + ", ".join(f'{x["day"]} dòng {x["row"]}' for x in off_src))
        if off_dst: reasons.append("slot đích rơi vào buổi nghỉ: " + ", ".join(f'{x["day"]} dòng {x["row"]}' for x in off_dst))
        if len(s) != len(t): reasons.append(f"lệch số tiết nguồn {len(s)} / đích {len(t)}")
        status = "BỎ QUA" if reasons else "ĐIỀN"
        result.append((k, len(s), len(t), status, "; ".join(reasons)))
        if not reasons:
            for a, b in zip(s, t):
                edits[f"E{b['row']}"] = a["lesson"] or None
                edits[f"F{b['row']}"] = a["equipment"] or None
                if a["subject"] != b["subject"] and "/" in k: edits[f"D{b['row']}"] = a["subject"]
    for ref in ["A1", "A3", "A10", "A17", "A23", "A29", "E35"]:
        edits[ref] = src_ws[ref].value
    return result, off_sessions, edits

if __name__ == "__main__":
    src_path, src_sheet, dst_path, dst_sheet, out_path = sys.argv[1:6]
    sw = openpyxl.load_workbook(src_path)[src_sheet]; dw = openpyxl.load_workbook(dst_path)[dst_sheet]
    res, offs, edits = analyze(sw, dw, selected=(sorted({x["key"] for x in read_slots(sw)}) if len(sys.argv) > 6 and sys.argv[6] == "all" else None))
    print(f"### Nguồn {src_sheet} → Đích {dst_sheet}. Buổi nghỉ: {sorted(offs) or 'không'}")
    for r in res: print(f"  {r[0]:<16} nguồn {r[1]} | đích {r[2]} | {r[3]} {r[4]}")
    if out_path != "-":
        patch(dst_path, out_path, {dst_sheet: edits}); print("  -> ghi", out_path, "| số ô ghi:", len(edits))
