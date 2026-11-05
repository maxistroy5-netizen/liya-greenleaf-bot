# Materials in the isolated LIA test bot

Russian and Uzbek: Tools → business card, three invitation PDFs, PDF and PNG lessons.
Other seven languages retain conversational support. The test bot explicitly reports that file translations are not available for them yet.

- Card: name, phone, Telegram, WhatsApp, MAX, email, Instagram and optional photo. Verify user-entered contacts, then create a PDF with active contact links. The QR opens the same Telegram folder as the existing production card generator; confirm regional destination and current link before a release. No contact data is sent to the model.
- Invitations: named recipient, optional sender and explicit event details. Three separate PDFs. No default time, timezone, speaker or meeting URL is inserted. The user chooses which file to share.
- Lessons: one eight-page PDF and separate PDF/PNG for each lesson. Generated from the controlled RU/UZ text catalog with questions and original examples. This is a new set of handouts, not a line-for-line localization of the legacy raster artwork. Original files remain in the repository. The market, currency, PV and conditions are not adapted by language selection.

Uzbek copy is a review draft. Before public use: have a native reader review the files, verify the QR and regional links, reconcile the lesson 4 / lesson 6 mentor examples and confirm the currency/coefficient assumptions flagged in the course review. No production migration is included.

Offline review: `python -I tools/render_material_samples.py /tmp/lia-material-review`.
