# rss2podcast

Turn an RSS feed into a listenable podcast. Fetches each entry, extracts the article body, sends it to [gopipertts](https://github.com/nbr23/gopipertts) for Piper TTS synthesis, and publishes the resulting MP3s as a standards-compliant podcast RSS feed.

## How it works

1. Parse the source RSS feed.
2. For each entry not yet processed (tracked in `state.json`):
   - Fetch the linked article and extract the body with `trafilatura` (falls back to RSS summary).
   - Strip HTML to plain speakable text.
   - POST to gopipertts `/api/tts`, save the MP3 to disk.
   - Append the entry to `state.json` immediately (crash-safe).
3. Rewrite `feed.xml` from the full state with `feedgen` (iTunes namespace).

## Install

```bash
uv sync
```

Or install as a tool:

```bash
uv tool install .
```

## Usage

### Single feed (CLI)

**EFF Updates** (equivalent to the `config.sample.yaml` entry):
```bash
uv run rss2podcast --feed-url https://www.eff.org/rss/updates.xml --feed-name "EFF Updates" --output-dir podcasts --url-root https://podcasts.example.com --tts-endpoint http://localhost:8080/ --voice en_US-amy-medium --description "EFF updates, narrated by Piper TTS" --author EFF --limit 5
```

**Ars Technica:**
```bash
uv run rss2podcast --feed-url https://feeds.arstechnica.com/arstechnica/index --feed-name "Ars Technica" --output-dir podcasts --url-root https://podcasts.example.com --tts-endpoint http://localhost:8080/ --voice en_US-amy-medium --description "Ars Technica articles, narrated by Piper TTS" --author "Ars Technica" --limit 5 --prune-xpath '//div[contains(@class,"author-bio")]'
```

**Hackaday:**
```bash
uv run rss2podcast --feed-url https://hackaday.com/blog/feed/ --feed-name Hackaday --output-dir podcasts --url-root https://podcasts.example.com --tts-endpoint http://localhost:8080/ --voice en_US-amy-low --description "Hackaday articles, narrated by Piper TTS" --author Hackaday --prune-xpath '//div[contains(@class,"author-bio")]' --prune-xpath '//section[contains(@class,"related")]'
```

### Multi-feed (YAML)

```bash
uv run rss2podcast --config config.yaml
```

See `config.sample.yaml` for a fully annotated example.

## Output layout

```
{output_dir}/
  {feed-slug}/
    state.json
    feed.xml
    2026-04-16-abc123def456.mp3
    ...
```

Serve `{output_dir}` over HTTP at `{url_root}` and subscribe to `{url_root}/{feed-slug}/feed.xml` in a podcast app.

## Scheduling

Designed to run as a cron / scheduled job. Re-runs are idempotent — entries already in `state.json` are skipped. Long runs are fine (no time limits, state is committed after each entry).

## CLI reference

### Feed selection

| Flag | Default | Description |
|---|---|---|
| `--config PATH` | — | YAML config file; enables multi-feed mode (`--limit` may still be used to override the YAML value) |
| `--feed-url URL` | — | Source RSS feed URL (single-feed mode) |
| `--feed-name NAME` | — | Feed display name; also determines the output subdirectory slug |
| `--output-dir PATH` | — | Directory to write `state.json`, `feed.xml`, and MP3s |
| `--url-root URL` | — | Public base URL where `output-dir` is served |

### TTS

| Flag | Default | Description |
|---|---|---|
| `--tts-endpoint URL` | `http://localhost:8080` | gopipertts base URL |
| `--voice MODEL` | `en_US-amy-low` | Piper voice model name |

### Feed metadata

| Flag | Default | Description |
|---|---|---|
| `--description TEXT` | — | Channel description |
| `--author TEXT` | — | Channel author |
| `--image-url URL` | — | Channel artwork URL |

### Processing

| Flag | Default | Description |
|---|---|---|
| `--limit N` | — | Keep only the N newest articles per feed; entries that roll out of the window are evicted from state and removed from the podcast feed |
| `--save-text` | off | Persist raw/clean text in `state.json` (useful for debugging) |
| `--no-fetch` | off | Skip external crawling; use only RSS `content`/`description` |

### Extraction tuning

These control how `trafilatura` extracts article text from fetched pages. Defaults are tuned for broad recall; tighten them for noisy feeds.

| Flag | Default | Description |
|---|---|---|
| `--no-favor-recall` | recall on | Disable recall-biased extraction; fall back to trafilatura's default balanced mode |
| `--favor-precision` | off | Prefer fewer, higher-confidence text blocks; reduces sidebar/bio bleed-through at the cost of occasionally truncating real content |
| `--include-comments` | off | Include comment sections in extracted text |
| `--include-tables` | off | Include table content |
| `--deduplicate` | off | Remove duplicate text blocks (useful for feeds that repeat headlines or teasers) |
| `--fast-extraction` | off | Skip fallback extractors; faster but may miss content on harder pages |
| `--prune-xpath XPATH` | — | XPath expression to remove from the DOM before extraction; repeatable. Use this to surgically excise author bios, related-article widgets, cookie banners, etc. |

**`--prune-xpath` examples:**

```bash
# Remove Ars Technica author bio
--prune-xpath '//div[contains(@class,"author-bio")]'

# Remove multiple sections
--prune-xpath '//aside' --prune-xpath '//div[@id="related"]'
```

## YAML config reference

Top-level keys:

```yaml
output_dir: /var/www/podcasts        # required
url_root: https://podcasts.example.com  # required
tts_endpoint: http://gopipertts:8080 # default: http://localhost:8080
limit: 5                             # optional: process only N newest per feed
save_text: false                     # optional: persist text in state.json
no_fetch: false                      # optional: skip external crawling globally
```

Per-feed keys:

```yaml
feeds:
  - name: My Feed        # required
    url: https://...     # required

    # TTS
    voice: en_US-amy-medium   # default: en_US-amy-low

    # Feed metadata
    description: "..."
    author: "..."
    image_url: "https://..."

    # Processing (override top-level defaults)
    limit: 5             # optional: overrides top-level limit for this feed

    # Extraction tuning
    favor_recall: true         # default: true
    favor_precision: false     # default: false
    include_comments: false    # default: false
    include_tables: false      # default: false
    deduplicate: false         # default: false
    fast_extraction: false     # default: false
    prune_xpath:               # default: null
      - '//div[contains(@class,"author-bio")]'
      - '//section[@id="related"]'
```

`favor_recall` and `favor_precision` are independent trafilatura flags. Setting both to `true` is valid; trafilatura will apply both biases simultaneously.

## Tests

```bash
uv sync --extra test
uv run pytest
```
