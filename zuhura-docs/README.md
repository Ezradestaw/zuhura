# zuhura-docs

Documentation site for Zuhura Mars, built with MkDocs and the Material theme.

## Development

```bash
pip install -r requirements-docs.txt
mkdocs serve        # http://127.0.0.1:8000
mkdocs build        # writes site/
```

Pages live in `docs/` and the navigation is defined in `mkdocs.yml`. Run `mkdocs build --strict` before committing to catch broken links.

The GitHub Actions workflow publishes the site to GitHub Pages. The Vercel deployment serves the committed `site/` directory, so rebuild it when pages change.
