"""Recalculate every formula in an .xlsx with LibreOffice and save the values into the file.

    python tools/recalc_excel.py outputs/payment_failure_analysis.xlsx

Excel recalculates the workbook when it opens it, so this is only needed for LibreOffice users,
for pandas/openpyxl readers, or to check the workbook headlessly. The full workbook takes
several minutes.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
Sub RecalculateAndSave()
  ThisComponent.calculateAll()
  ThisComponent.store()
  ThisComponent.close(True)
End Sub
</script:module>"""


def recalc(path: Path, timeout: int = 1800) -> None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("LibreOffice (soffice) not found.")
    with tempfile.TemporaryDirectory() as prof:
        url = Path(prof).as_uri()
        subprocess.run([soffice, f"-env:UserInstallation={url}", "--headless", "--terminate_after_init"],
                       capture_output=True, timeout=120)
        basic = Path(prof) / "user" / "basic" / "Standard"
        basic.mkdir(parents=True, exist_ok=True)
        (basic / "Module1.xba").write_text(MACRO, encoding="utf-8")
        if not (basic / "script.xlb").exists():
            (basic / "script.xlb").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE library:library PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "library.dtd">\n'
                '<library:library xmlns:library="http://openoffice.org/2000/library" library:name="Standard" library:readonly="false" '
                'library:passwordprotected="false">\n <library:element library:name="Module1"/>\n</library:library>\n', encoding="utf-8")
        subprocess.run([soffice, f"-env:UserInstallation={url}", "--headless", "--norestore", str(path.resolve()),
                        "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application"],
                       capture_output=True, timeout=timeout)
    print(f"Recalculated {path}")


if __name__ == "__main__":
    recalc(Path(sys.argv[1]))
