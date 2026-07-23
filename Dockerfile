# --- build stage: bake the latest LessWrong/Substack posts into the page ---
FROM python:3.12-alpine AS build
RUN apk add --no-cache ca-certificates && update-ca-certificates
WORKDIR /app
COPY index.html ./index.html
COPY build/fetch_posts.py ./build/fetch_posts.py
# never fail the deploy over a feed hiccup; the script leaves the empty state on error
RUN python build/fetch_posts.py || true

# --- serve stage: static files via Caddy ---
FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/index.html /srv/index.html
