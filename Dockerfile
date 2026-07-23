# Static site served by Caddy. Writing is baked into index.html ahead of time by
# the "Refresh writing" GitHub Action (build/fetch_posts.py), so the deploy just
# serves the committed page — deterministic, and a feed outage can't affect it.
FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY index.html /srv/index.html
