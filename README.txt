Fengxi Toolbox 4.0
==================

Fengxi Toolbox is a Windows desktop toolbox for local batch processing:
watermarking, PDF/OCR, image and audio processing, archive compression,
metadata cleanup, batch rename, and file organization.

Official baseline: 4.0.0 / v4.0.0

Run from source
---------------
python -m pip install -r requirements.txt
python Fengxi_Toolbox.py

Build EXE
---------
set FX_NO_PAUSE=1
package.bat

Default output:
dist_release_ascii\fx_toolbox\
dist_release_ascii\fx_toolbox\fx_toolbox.exe

Regression checks
-----------------
python smoke_test.py
python full_debug_test.py

License
-------
Fengxi Toolbox is free and open source software licensed under the GNU Affero
General Public License version 3.0 only. See LICENSE.

Commercial use is allowed under AGPL-3.0, provided that you follow AGPL-3.0 and
all third-party license obligations. If you distribute modified versions or make
the software available over a network, you must provide the corresponding source
as required by AGPL-3.0.

Brand and official release identity
-----------------------------------
The AGPL-3.0 license covers the software code, but it does not grant trademark
or branding rights.

The names "风兮", "Fengxi Toolbox", official logos, icons, release identity,
screenshots, application imagery, and other brand identifiers are reserved by
the project rights holder unless a file states otherwise.

Forks and redistributed builds should use a different product name and clearly
state that they are not official Fengxi Toolbox releases. Do not present
modified, repackaged, mirrored, or renamed builds as official releases.

See NOTICE for details.
