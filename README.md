# The Secret Books static edition

Static HTML export of the public WordPress site at:

https://dev-the-secret-books.pantheonsite.io

The exporter uses the live Pantheon environment only as a fallback for public books
that are not currently published on dev.

## Output

- `docs/` is the GitHub Pages-ready site.
- `tools/export_wp_static.py` rebuilds the static export from the public WordPress REST API.
- `docs/data/inventory.json` records the exported books, original URLs, PDFs, and notes.

## Rebuild

```powershell
python tools/export_wp_static.py
```

## Pantheon Git

The Pantheon clone is currently blocked until the local SSH public key is added to Pantheon.
