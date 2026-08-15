"""
A very small .xlsx reader and writer, standard library only.

Written by hand rather than pulled in as a dependency because the people this exists for don't
have a Python toolchain and shouldn't need one. An .xlsx is a zip of XML; this handles the
narrow slice needed for a one-sheet review file.

Writes inline strings; reads both inline and shared strings, because Excel rewrites the file
in its own style when the user saves.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

# Style indices written into styles.xml below, in this order.
PLAIN, HEADER, LOCKED, EDIT, MONEY, FLAG = range(6)


def _esc(text) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def col_name(index: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA"""
    name = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


class Cell:
    __slots__ = ("value", "style")

    def __init__(self, value, style: int = PLAIN):
        self.value = value
        self.style = style


def write(path, rows: list[list], widths: list[int], freeze_at: str = "A2",
          sheet_name: str = "Sheet1"):
    """Write one sheet. `rows` is a list of lists of Cell or plain values."""

    def cell_xml(c, ref):
        if not isinstance(c, Cell):
            c = Cell(c)
        if c.value is None or c.value == "":
            return f'<c r="{ref}" s="{c.style}"/>'
        if isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
            return f'<c r="{ref}" s="{c.style}"><v>{c.value}</v></c>'
        return (f'<c r="{ref}" s="{c.style}" t="inlineStr">'
                f"<is><t xml:space=\"preserve\">{_esc(c.value)}</t></is></c>")

    body = []
    for r, row in enumerate(rows, start=1):
        cells = "".join(cell_xml(c, f"{col_name(i)}{r}") for i, c in enumerate(row))
        body.append(f'<row r="{r}">{cells}</row>')

    cols = "".join(
        f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
        for i, w in enumerate(widths))

    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{NS}">'
        f'<sheetViews><sheetView workbookViewId="0" tabSelected="1">'
        f'<pane ySplit="1" topLeftCell="{freeze_at}" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f"<cols>{cols}</cols>"
        f'<sheetData>{"".join(body)}</sheetData>'
        "</worksheet>"
    )

    # Six styles: plain, header, locked-grey, editable-yellow, money, flag-orange.
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<styleSheet xmlns="{NS}">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0"/></numFmts>'
        '<fonts count="3">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
        '<font><sz val="11"/><color rgb="FF808080"/><name val="Calibri"/></font>'
        "</fonts>"
        '<fills count="5">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF44546A"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFCE4D6"/></patternFill></fill>'
        "</fills>"
        '<borders count="2"><border/>'
        '<border><left style="thin"><color rgb="FFBFBFBF"/></left>'
        '<right style="thin"><color rgb="FFBFBFBF"/></right>'
        '<top style="thin"><color rgb="FFBFBFBF"/></top>'
        '<bottom style="thin"><color rgb="FFBFBFBF"/></bottom></border></borders>'
        '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="6">'
        '<xf xfId="0"/>'                                                          # PLAIN
        '<xf xfId="0" fontId="1" fillId="2" applyFont="1" applyFill="1">'
        '<alignment vertical="center" wrapText="1"/></xf>'                        # HEADER
        '<xf xfId="0" fontId="2" applyFont="1"/>'                                 # LOCKED
        '<xf xfId="0" fillId="3" borderId="1" numFmtId="164" applyFill="1" '
        'applyBorder="1" applyNumberFormat="1"/>'                                 # EDIT
        '<xf xfId="0" numFmtId="164" applyNumberFormat="1"/>'                     # MONEY
        '<xf xfId="0" fillId="4" applyFill="1"/>'                                 # FLAG
        "</cellXfs>"
        "</styleSheet>"
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   "</Types>")
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   "</Relationships>")
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   f'<sheets><sheet name="{_esc(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
                   "</workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                   "</Relationships>")
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", sheet)


def read(path) -> list[list[str]]:
    """Read the first sheet as rows of strings. Blank cells become ''."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()

        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{{{NS}}}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS}}}t")))

        sheet_path = next((n for n in names
                           if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)), None)
        if sheet_path is None:
            raise ValueError("no worksheet found in this file")

        root = ET.fromstring(z.read(sheet_path))
        rows: list[list[str]] = []
        for row in root.iter(f"{{{NS}}}row"):
            values: dict[int, str] = {}
            for c in row.findall(f"{{{NS}}}c"):
                ref = c.get("r") or ""
                letters = "".join(ch for ch in ref if ch.isalpha())
                idx = 0
                for ch in letters:
                    idx = idx * 26 + (ord(ch) - 64)
                idx -= 1

                ctype = c.get("t")
                if ctype == "inlineStr":
                    text = "".join(t.text or "" for t in c.iter(f"{{{NS}}}t"))
                elif ctype == "s":
                    v = c.find(f"{{{NS}}}v")
                    i = int(v.text) if v is not None and v.text else -1
                    text = shared[i] if 0 <= i < len(shared) else ""
                else:
                    v = c.find(f"{{{NS}}}v")
                    text = (v.text or "") if v is not None else ""
                values[idx] = text.strip()

            width = max(values) + 1 if values else 0
            rows.append([values.get(i, "") for i in range(width)])
        return rows
