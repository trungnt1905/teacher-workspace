"""Prototype: patch cell values directly in the xlsx package, touching nothing else."""
import sys, zipfile, re
from lxml import etree
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
M = "{%s}" % NS["m"]

def sheet_paths(z):
    wb = etree.fromstring(z.read("xl/workbook.xml"))
    rels = etree.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid2t = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    for s in wb.iterfind("m:sheets/m:sheet", NS):
        t = rid2t[s.get("{%s}id" % NS["r"])].lstrip("/")
        out[s.get("name")] = t if t.startswith("xl/") else "xl/" + t
    return out

def set_cell(root, ref, value):
    row_n = int(re.sub(r"[A-Z]+", "", ref))
    row = root.find(f"m:sheetData/m:row[@r='{row_n}']", NS)
    c = row.find(f"m:c[@r='{ref}']", NS)
    if c is None:
        raise KeyError(f"cell {ref} not present in template (fixed layout expected)")
    for child in list(c):
        if child.tag in (M + "v", M + "is", M + "f"):
            c.remove(child)
    if value is None or value == "":
        c.attrib.pop("t", None)
        return
    c.set("t", "inlineStr")
    is_ = etree.SubElement(c, M + "is"); t = etree.SubElement(is_, M + "t")
    t.text = value
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

def patch(src, dst, edits):  # edits: {sheet_name: {ref: value}}
    with zipfile.ZipFile(src) as zin:
        paths = sheet_paths(zin)
        targets = {paths[s]: e for s, e in edits.items()}
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename in targets:
                    root = etree.fromstring(data)
                    for ref, v in targets[info.filename].items():
                        set_cell(root, ref, v)
                    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                zout.writestr(info, data)

if __name__ == "__main__":
    edits = {"TUẦN 9": {**{f"E{r}": None for r in range(3, 35)}, **{f"F{r}": None for r in range(3, 35)},
                        "E4": "Bài thử nghiệm round-trip", "A1": " TUẦN 09 (thử)"}}
    patch(sys.argv[1], sys.argv[2], edits)
