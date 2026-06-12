# Fengxi Toolbox

Fengxi Toolbox is a Windows desktop toolbox for local batch processing:
watermarking, PDF/OCR tasks, image and audio processing, archive compression,
metadata cleanup, batch rename, and file organization.

Current release baseline: `4.0.0` / `v4.0.0`

## Features

- Batch watermarking and selected watermark cleanup workflows.
- Word / PDF / PPT conversion workflows.
- PDF compression, split, encrypt, and searchable PDF OCR.
- Image-to-PDF, multi-image PDF merge, image conversion, and image compression.
- Audio extraction and audio format conversion.
- Batch archive compression.
- File timestamp, author, metadata, rename, organize, and duplicate cleanup tools.
- Task progress, history, resume support, diagnostics, and saved last settings.

## Run From Source

```powershell
python -m pip install -r requirements.txt
python Fengxi_Toolbox.py
```

Windows 10/11 and Python 3.11 are the expected development environment.
Office-related workflows require a working local Microsoft Office COM
installation.

## Build EXE

```powershell
set FX_NO_PAUSE=1
package.bat
```

Default output:

```text
dist_release_ascii\fx_toolbox\
dist_release_ascii\fx_toolbox\fx_toolbox.exe
```

## Tests

```powershell
python smoke_test.py
python full_debug_test.py
```

Some Office, OCR, drag-and-drop, and GUI behavior depends on the local Windows
environment.

## License

Fengxi Toolbox is free and open source software licensed under the GNU Affero
General Public License version 3.0 only. See [LICENSE](LICENSE).

Commercial use is allowed under AGPL-3.0, provided that you follow AGPL-3.0 and
all third-party license obligations. In particular, if you distribute modified
versions or make the software available over a network, you must provide the
corresponding source as required by AGPL-3.0.

## Brand And Official Release Identity

The AGPL-3.0 license covers the software code, but it does not grant trademark
or branding rights.

The names "风兮", "Fengxi Toolbox", official logos, icons, release identity,
screenshots, application imagery, and other brand identifiers are reserved by
the project rights holder unless a file states otherwise.

Forks and redistributed builds should use a different product name and clearly
state that they are not official Fengxi Toolbox releases. Do not present
modified, repackaged, mirrored, or renamed builds as official releases.

See [NOTICE](NOTICE).

## Third-Party Components

This project uses third-party libraries and tools. Those components remain
subject to their own licenses, notices, and attribution requirements.

## Disclaimer

The software is provided as-is. Before running destructive or large batch
operations such as overwrite, delete-source, metadata cleanup, or watermark
removal, test with sample files first.
