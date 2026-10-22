# Save as repro.py in the repo root, then: python repro.py
# Needs pypdf, reportlab, pytest and pdftotext (poppler-utils), as in the task's Dockerfile.
# Runs the task's verifier/test_outputs.py the way verifier/test.sh does
# (reward 1 iff pytest exits 0). The only change to the verifier is the two
# hard-coded /root/... paths, pointed at local files. No network, no model calls.
import ast
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
from reportlab.pdfgen import canvas

TASK = Path("tasks/samples/skillsbench/court-form-filling")
required_node = next(
    node for node in ast.parse((TASK / "verifier/test_outputs.py").read_text()).body
    if isinstance(node, ast.Assign)
    and any(getattr(target, "id", None) == "REQUIRED_TEXT_VALUES" for target in node.targets)
)
REQUIRED = {desc: value for value, desc in ast.literal_eval(required_node.value)}
BLANK = TASK / "environment/sc100-blank.pdf"
TMP = Path(tempfile.mkdtemp())

P2, P3, P4 = "SC-100[0].Page2[0].", "SC-100[0].Page3[0].", "SC-100[0].Page4[0]."
TEXT = {
    P2 + "List1[0].Item1[0].PlaintiffName1[0]": REQUIRED["plaintiff_name"],
    P2 + "List1[0].Item1[0].PlaintiffPhone1[0]": REQUIRED["plaintiff_phone"],
    P2 + "List1[0].Item1[0].PlaintiffAddress1[0]": REQUIRED["plaintiff_address"],
    P2 + "List1[0].Item1[0].PlaintiffCity1[0]": "Sunnyvale",
    P2 + "List1[0].Item1[0].PlaintiffState1[0]": "CA",
    P2 + "List1[0].Item1[0].PlaintiffZip1[0]": "94086",
    P2 + "List1[0].Item1[0].EmailAdd1[0]": REQUIRED["plaintiff_email"],
    P2 + "List2[0].item2[0].DefendantName1[0]": REQUIRED["defendant_name"],
    P2 + "List2[0].item2[0].DefendantPhone1[0]": REQUIRED["defendant_phone"],
    P2 + "List2[0].item2[0].DefendantAddress1[0]": REQUIRED["defendant_address"],
    P2 + "List2[0].item2[0].DefendantCity1[0]": "Sunnyvale",
    P2 + "List2[0].item2[0].DefendantState1[0]": "CA",
    P2 + "List2[0].item2[0].DefendantZip1[0]": "94086",
    P2 + "List3[0].PlaintiffClaimAmount1[0]": "1500",
    P2 + "List3[0].Lia[0].FillField2[0]": "Failed to return my security deposit after moving out",
    P3 + "List3[0].Lib[0].Date2[0]": "2025-09-30",
    P3 + "List3[0].Lib[0].Date3[0]": "2026-01-19",
    P3 + "List3[0].Lic[0].FillField1[0]": "The amount is listed on the signed roommate sublease contract",
    P4 + "Sign[0].Date1[0]": "2026-01-19",
    P4 + "Sign[0].PlaintiffName1[0]": REQUIRED["plaintiff_name"],
}
CHECK = {  # widget full name -> on-state (Q4 yes, Q5a, Q7-Q10 no)
    P3 + "List4[0].Item4[0].Checkbox50[0]": "/1",
    P3 + "List5[0].Lia[0].Checkbox5cb[0]": "/1",
    P3 + "List7[0].item7[0].Checkbox60[1]": "/2",
    P3 + "List8[0].item8[0].Checkbox61[1]": "/2",
    P4 + "List9[0].Item9[0].Checkbox62[1]": "/2",
    P4 + "List10[0].li10[0].Checkbox63[1]": "/2",
}


def full_name(annot):
    parts, node = [], annot
    while node is not None:
        if "/T" in node:
            parts.append(str(node["/T"]))
        node = node.get("/Parent")
        node = node.get_object() if node is not None else None
    return ".".join(reversed(parts))


def fill_form(out, check):
    """Fill the real SC-100 AcroForm fields and checkboxes."""
    w = PdfWriter(clone_from=PdfReader(BLANK))
    del w._root_object["/AcroForm"][NameObject("/XFA")]  # use the AcroForm values
    for page in w.pages:
        for a in page.get("/Annots", []) or []:
            a = a.get_object()
            name = full_name(a)
            if name in TEXT:
                w.update_page_form_field_values(page, {name: TEXT[name]}, auto_regenerate=False)
            if name in check:
                a[NameObject("/AS")] = a[NameObject("/V")] = NameObject(check[name])
    w.set_need_appearances_writer(True)
    w.write(out)


def text_only_pdf(out):
    """A new one-page PDF with the expected strings. Not the SC-100 form: no fields at all."""
    c = canvas.Canvas(str(out))
    for i, line in enumerate([
        f"{REQUIRED['plaintiff_name']}, {REQUIRED['plaintiff_address']}, Sunnyvale 94086, {REQUIRED['plaintiff_phone']}, {REQUIRED['plaintiff_email']}",
        f"{REQUIRED['defendant_name']}, {REQUIRED['defendant_address']}, {REQUIRED['defendant_phone']}",
        "1500 security deposit, roommate sublease contract, 2025-09-30 2026-01-19",
        "This is not the SC-100 form. No fields or checkboxes were filled.",
    ]):
        c.drawString(40, 720 - 18 * i, line)
    c.save()


def reward(filled):
    src = (TASK / "verifier/test_outputs.py").read_text()
    src = src.replace('Path("/root/sc100-filled.pdf")', f"Path({str(filled.resolve())!r})")
    src = src.replace('Path("/root/sc100-blank.pdf")', f"Path({str(BLANK.resolve())!r})")
    test = TMP / "test_outputs.py"
    test.write_text(src)
    p = subprocess.run([sys.executable, "-m", "pytest", str(test), "-rA", "-q", "-p", "no:cacheprovider"],
                       capture_output=True, text=True, cwd=TMP)
    summary = p.stdout.strip().splitlines()[-1]
    skipped = sorted({l.split(": ", 1)[1] for l in p.stdout.splitlines() if l.startswith("SKIPPED")})
    failed = [l.split("::", 1)[1] for l in p.stdout.splitlines() if l.startswith("FAILED")]
    return (1 if p.returncode == 0 else 0), summary, skipped, failed


wrong = dict(CHECK)  # Q10 "claim over $2,500?" answered Yes instead of No
del wrong[P4 + "List10[0].li10[0].Checkbox63[1]"]
wrong[P4 + "List10[0].li10[0].Checkbox63[0]"] = "/1"

cases = {
    "blank form, unchanged": lambda out: shutil.copy(BLANK, out),
    "correct fill": lambda out: fill_form(out, CHECK),
    "correct fill, Q10 checkbox wrong": lambda out: fill_form(out, wrong),
    "text fields filled, no checkbox": lambda out: fill_form(out, {}),
    "text-only PDF, no form": text_only_pdf,
}
for i, (label, make) in enumerate(cases.items()):
    out = TMP / f"filled{i}.pdf"
    make(out)
    n_fields = len(PdfReader(out).get_fields() or {})
    r, summary, skipped, failed = reward(out)
    print(f"{label:34} form fields={n_fields:3}  reward={r}  ({summary})")
    for s in skipped:
        print(f"{'':36}skip reason: {s}")
    for f in failed[:3]:
        print(f"{'':36}FAILED {f.split(' - ')[0]}")
    if len(failed) > 3:
        print(f"{'':36}... and {len(failed) - 3} more")
