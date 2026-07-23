# evcode.dev

Personal site for Evgeniia Buzulukova. Single static page (`index.html`), served by
Caddy on Railway.

## Structure

- `index.html` — the whole site (inline CSS + JS, no build tooling for the page itself).
- `build/fetch_posts.py` — at deploy time, pulls the LessWrong + Substack feeds and bakes
  recent posts into the Writing section. Fails safe: any feed error leaves the "no posts
  yet" empty state.
- `Dockerfile` — two stages: run the fetch script, then serve `index.html` with Caddy.
- `Caddyfile` — static file server bound to `$PORT`.

## Adding writing

Posts appear automatically once they're published to LessWrong or Substack (refreshed on
each deploy). To add one by hand, edit the `POSTS` array in `index.html`:

```js
{ date: "2026-08-04", title: "…", url: "https://…", source: "LessWrong" }
```

## Deploy

```bash
railway up --detach
```

The feeds are configured at the top of `build/fetch_posts.py`. Update the Substack URL
once the publication exists (`<name>.substack.com/feed`).
