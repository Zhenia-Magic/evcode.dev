# evcode.dev

Personal site for Evgeniia Buzulukova. Single static page (`index.html`), served by
Caddy on Railway.

## Structure

- `index.html` — the whole site (inline CSS + JS, no build tooling for the page itself).
- `build/fetch_posts.py` — pulls the LessWrong + Substack feeds and bakes recent posts
  into the Writing section. Fails safe: if every feed is unreachable it leaves the page
  untouched, so an outage never wipes existing posts.
- `.github/workflows/refresh-writing.yml` — runs the fetch script daily and commits only
  when the writing changed.
- `Dockerfile` / `Caddyfile` — serve `index.html` with Caddy on `$PORT`.

## How deploys work

Railway is connected to this repo, so **any push to `main` auto-deploys**. The daily
Action refreshes writing on its own; you only push when you change the site itself.

Manual deploy (if ever needed):

```bash
railway up --detach --service evcode
```

## Adding writing

Posts show up automatically within a day of publishing to LessWrong or Substack. To add
one immediately, run `python build/fetch_posts.py` (or edit the `POSTS` array in
`index.html` by hand) and push:

```js
{ date: "2026-08-04", title: "…", url: "https://…", source: "LessWrong" }
```

Feeds are configured at the top of `build/fetch_posts.py`. Update the Substack URL once
the publication exists (`<name>.substack.com/feed`).
