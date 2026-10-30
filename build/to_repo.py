"""Положить собранную Элис в корень репо, чтобы после `git clone` сразу запускался Элис.exe.
  python -X utf8 -I build/to_repo.py
Берёт dist/Элис (make_dist.ps1): python/ и Элис.exe -> корень репо (app/ в репо и так есть).
Tesseract (OCR, Apache-2.0) с этого ПК -> tools/tesseract: tesseract.exe, его DLL и tessdata (rus, eng, osd).
В репо идёт только то, что можно честно раздавать: AutoCAD, Office, ODA сюда не кладём."""
import shutil
from pathlib import Path

repo = Path(__file__).resolve().parent.parent
dist = repo / 'dist' / 'Элис'
tess = Path(r'C:\Program Files\Tesseract-OCR')
skip = shutil.ignore_patterns('__pycache__', '*.pyc')

for name in ('python',):
    dst = repo / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(dist / name, dst, ignore=skip)
shutil.copy2(dist / 'Элис.exe', repo / 'Элис.exe')

out = repo / 'tools' / 'tesseract'
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
for f in [tess / 'tesseract.exe', *tess.glob('*.dll')]:
    shutil.copy2(f, out / f.name)
shutil.copytree(tess / 'tessdata', out / 'tessdata')

size = sum(f.stat().st_size for d in (repo / 'python', out) for f in d.rglob('*') if f.is_file())
print('ok: python/, Элис.exe, tools/tesseract ->', repo, f'· {size / 1e6:.0f} МБ')
