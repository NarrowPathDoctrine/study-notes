# Narrow Path Doctrine Ministries — Teaching Library & Study Notes

A compact, searchable teaching library for PDF-backed YouTube teachings. No older, PDF-free videos are included. The website begins with an empty-library message and a planned first teaching on **November 10, 2026**.

The site is static and needs no paid hosting, server, database, YouTube API key, or browser login. A GitHub Actions workflow checks for due draft releases and builds the public catalog.

## One-time setup

The repository is created and its website files have been installed.

1. Open **Settings → Pages → Build and deployment**, and select **Source: GitHub Actions**.
2. If GitHub Actions are disabled, enable workflows from the **Actions** tab. Under **Settings → Actions → General**, allow the workflow to write repository content when that setting is presented.
3. Open **Actions → Publish Study Notes Library → Run workflow**. Check that the run finishes successfully.
4. Visit **https://narrowpathdoctrine.github.io/study-notes/**. It will show an empty library until your first PDF-backed teaching is published.

## Adding each new teaching (no website editing)

1. Open the `study-notes` repository, then **Releases → Draft a new release**.
2. Under **Choose a tag**, enter a new unique tag, such as `study-0001`, `study-0002`, etc., and select **Create new tag** targeting `main`.
3. Enter a temporary release title, such as `Scheduled teaching`. The publishing automation replaces it with the **actual YouTube video title** once the video is available.
4. Paste this into the **release description**, changing the details to match the teaching:

   ```text
   YouTube: https://www.youtube.com/watch?v=YOUR_VIDEO_ID
   Publish (UK): 2026-11-10 15:00
   Topic: Sovereign Grace
   Scripture: John 2:23-25
   Description: An examination of what Scripture teaches about true saving faith.
   ```

   - **YouTube**: paste the real video link (standard YouTube, `youtu.be`, live or Shorts URLs are accepted).
   - **Publish (UK)**: the date and time you want the teaching to become public, using **YYYY-MM-DD HH:MM** in UK local time. The system handles GMT/BST changes.
   - **Topic** and **Scripture**: optional, but helpful for filtering and searching.
   - **Description**: optional short description for the individual teaching page.
5. Attach **one PDF** study notes file to the release's **binary attachments/assets** area.
6. Choose **Save draft**, NOT Publish release. Leave it as a draft until the automation publishes it.

The automation checks approximately every 15 minutes. It does **not** publish the release before the specified UK date and time. Once the date has arrived, it checks whether the YouTube video provides a public title; if it does not, the PDF and teaching remain hidden and the automation retries on later checks. When available, it publishes the draft release and updates the teaching library, title, thumbnail, watch link and PDF download button.

**Important**: GitHub scheduled workflow runs and Pages deployments may be delayed; publication is **not guaranteed at the exact minute**. Schedule a modest buffer if coordinating precisely with a YouTube premiere. The video is controlled separately in YouTube Studio; this automation does not change YouTube video visibility.

## How visitors use the site

- Newest-first responsive grid, with 24, 36 or 48 results per page (24 by default).
- Search the entire published teaching catalog by title, Scripture reference and topic.
- Filter by topic and year; sort by date or title.
- Thumbnail/title open the teaching's own shareable page (e.g. `?study=study-0001`).
- Watch on YouTube or download the PDF using the links on each teaching.
- PDF-free releases and unpublished draft releases are omitted entirely.

## What stays private until publication?

Draft release metadata and attached PDFs are not included in GitHub Pages and are not added to the repository's regular public files. Draft releases are not publicly visible through the ordinary Releases listing. Do not publish a release yourself early, and do not upload an unreleased PDF as a regular public repository file.

## Troubleshooting

- **The website is not visible:** check **Settings → Pages** is configured to use **GitHub Actions** and the latest `Publish study notes library` run is green.
- **Workflow permission error when saving the catalog:** allow repository Actions read/write permissions in **Settings → Actions → General**, and try **Run workflow** again.
- **A teaching didn't publish at the scheduled time:** open **Actions → Publish study notes library** and check logs for a missing PDF, incorrect metadata or a YouTube video whose title is not yet readable. You can use **Run workflow** to check again.
- **Teaching published on GitHub but not showing:** allow for GitHub Pages deployment delay, then run the workflow manually.
- **Scheduled automation stops:** GitHub may disable scheduled workflows in public repositories after 60 days without repository activity. Re-enable the workflow from the Actions tab if that occurs.
- **Different topic names result in separate filters:** use consistent topic names (e.g. `Sovereign Grace` each time).
- **Adding a new PDF to an existing release:** edit its release assets in GitHub and manually run the workflow. A published release with immutability enabled may prevent editing assets.

## Implementation

- **site/index.html**: responsive study notes website, styling, search, filters, and teaching pages.
- **site/data/studies.json**: generated public library manifest, initially empty.
- **scripts/build_library.py**: automatic publication and catalog generation.
- **.github/workflows/publish.yml**: scheduled checks and GitHub Pages publishing.

Do not upload unreleased PDFs directly to the repository: use draft release attachments as described above.
