# OGCR-DCR-PRODUCT

The public website for the OGCR Digital Carbon Registry (DCR). It shows how the registry is built: OBP-API and its Dynamic Entities, OGCR-DynamicEntities, OGCR-App, the Operator Platform (OGCR-GILAB) and the Certification Platform (ogcr-certification-platform), which are both clients of the API, ogcr-tokenizer, OGCR-Smart-Contracts and OGCR-Chain-Cache.

The site is plain HTML and CSS, with no build step. Everything published is in `docs/`, so GitHub Pages can serve that folder directly.

## Seeing it locally

Open `docs/index.html` in a browser, or serve the folder:

```sh
cd docs
python3 -m http.server 8000
```

Then go to http://localhost:8000.

## Publishing

In the repository's settings on GitHub, under Pages, choose to deploy from the main branch and the `docs` folder. The site is served at https://ogcr-dcr-product.tesobe.com, set in `docs/CNAME`.

## What is here

- `docs/index.html`: the page.
- `docs/style.css`: the styles. Colours, type and radii follow the OGCR Design System tokens: navy `#0f3655`, brand green `#6db087` and the warm page colour `#f8f3ef`. Light and dark modes follow the visitor's settings.
- `docs/site.js`: reveals sections as they scroll into view.
- `docs/img/`: the OGCR logo (`ogcr-logo.svg`, and `ogcr-logo-light.svg` for dark backgrounds), the favicon (`ogcr-mark.svg`, the logo's round mark), the TESOBE logo and the EU flag for the funding notice.

The architecture on the page follows the OGCR architecture Glossary item in OGCR-DynamicEntities (`architecture_glossary_item.md`). Update both together.

## Writing for the site

Write in plain UK English: short sentences, everyday words, and the active voice. Describe what the registry does for each kind of user.

## Funding

The OGCR Project has received funding from the European Union's Horizon Europe programme under grant agreement [101218854](https://cordis.europa.eu/project/id/101218854).

## Licence

AGPL-3.0, as the rest of the Open Bank Project. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
