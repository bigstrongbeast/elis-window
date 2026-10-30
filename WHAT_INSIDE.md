# Элис — что внутри

Установка: `Install_Elis.bat` (кладёт в `C:\Elis`, ярлык «Элис» на стол). Обновление: `Update_Elis.bat` (git pull).
Или вручную: скачал папку целиком (`git clone -b release`) → открыл `Elis.exe`. Ставить ничего не надо: свой Python и все библиотеки лежат рядом.
Все пути и имена — латиницей; по-русски только ярлык.

| Папка | Что |
|---|---|
| `Elis.exe` | запускалка: стартует `python\pythonw.exe app\main.py` |
| `Install_Elis.bat`, `Update_Elis.bat` | установка и обновление |
| `app\` | код окна (открытый) |
| `python\` | Python 3.13.15 (python.org, PSF) + библиотеки в `Lib\site-packages` |
| `tools\tesseract\` | распознавание сканов (Tesseract 5, Apache-2.0), языки: русский, английский |
| `build\` | как собрать заново: `make_dist.ps1`, потом `python build\to_repo.py` |

## Библиотеки (лицензия — из их собственных файлов `METADATA`)

| Для чего | Библиотека | Лицензия |
|---|---|---|
| окно | pywebview 6.2.1, pythonnet 3.2.1, clr_loader, bottle 0.13.4, proxy_tools, cffi, pycparser | BSD-3 / MIT / MIT-0 |
| DXF-чертежи | ezdxf 1.4.5, numpy 2.5.4, fonttools 4.68, pyparsing 3.3.3 | MIT / BSD-3 |
| картинки | pillow 13.0.0 | MIT-CMU |
| Word DOCX | mammoth 1.13.0 (+cobble), python-docx 1.2.0, lxml 6.1.3 | BSD-2 / MIT / BSD-3 |
| Excel XLSX и старый XLS | openpyxl 3.1.5 (+et_xmlfile), xlrd 2.0.2 | MIT / BSD |
| старые DOC/XLS (OLE) | olefile 0.47 | BSD |
| PDF | pypdf 6.21.4, pdfplumber 0.11.10, pdfminer.six 20260107, pypdfium2 5.14.0, charset-normalizer, cryptography | BSD-3 / MIT / Apache-2.0 или BSD-3 |
| распознавание | pytesseract 0.3.13 (+packaging) | Apache-2.0 |

Тексты лицензий — в `python\Lib\site-packages\*.dist-info\`.

## Чего здесь нет (раздавать нельзя или условия не проверены)

- **AutoCAD** — платный; портабельная сборка неофициальная.
- **Microsoft Office, Project** — платные.
- **ODA File Converter** (DWG → DXF) — бесплатный, но выдаётся после регистрации на opendesign.com; условия раздачи не проверены. Скачать самому: https://www.opendesign.com/guestfiles/oda_file_converter
- **ГрандСмета** — платная.
