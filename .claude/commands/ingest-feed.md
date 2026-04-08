Trigger a manual feed ingestion. Specify the feed name or "all" to run all feeds.

Usage: /ingest-feed [feed_name|all]

Run the feed pipeline via CLI:
```bash
fertility-sense ingest --feed $ARGUMENTS
```

Check feed health after ingestion:
```bash
fertility-sense status --feeds
```
