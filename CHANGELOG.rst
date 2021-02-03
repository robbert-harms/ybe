*********
Changelog
*********

v0.3.3 (2021-02-03)
===================
- Small name change in the QTI converter.

v0.3.2 (2021-02-03)
===================

Added
-----
- Adds Docx, ODT, Markdown and HTML document writer.

Changed
-------
- Removed support for additional fields in the document writers.
- Refactored the QTI writer.


v0.3.1 (2021-01-30)
===================

Fixed
-----
- Fixed the QTI parser, it now correctly parses the correct answers of multiple response questions.


v0.3.0 (2021-01-29)
===================
Overhaul of the Ybe data structure, moved away from ``text_markup`` and ``text_html`` and instead
use Yaml tags for this purpose. In the new system, marking a text item as markdown is now done using ``field: !markdown text...``.

Additionally, this version supports question comments with QTI reading and writing support.

Added
-----
- Adds QTI writing support for hints and explanations.

Changed
-------
- Updated the Ybe format. Adds hints and explanations as fields.


v0.2.2 (2020-06-01)
===================

Changed
-------
- Updates to the question's meta data.


v0.2.1 (2020-05-24)
===================
- Updates to the documentation.


v0.2.0 (2020-05-24)
===================
First github release.

Added
-----
- Adds example latex template.

Changed
-------
- Changed license to GPL.


v0.1.0 (2020-04-08)
===================
Initial version.
