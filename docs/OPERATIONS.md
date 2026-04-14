# WIN Fertility -- Daily Operations Guide

## Daily Checklist
- [ ] Check scout ran (check data/logs/scout.log for today's date)
- [ ] Check digest was sent (check data/outreach/send_audit.jsonl)
- [ ] Check sequence sends (fertility-sense sequence status)
- [ ] Check for stale deals (fertility-sense pipeline-report)
- [ ] Review content queue (fertility-sense queue summary)

## Scheduling
This system runs automatically via macOS launchd:
- Scout: every 6 hours
- Digest: daily 8am -> paul@romatech.com
- Sequences: daily 9am
- Weekly digest: Monday 8am

### Install schedules
```
make install-schedules
```

### Check if running
```
launchctl list | grep winfertility
```

### View logs
```
tail -f data/logs/scout.log
tail -f data/logs/digest.log
```

## Troubleshooting

### Scout failed
Check: data/logs/scout.err
Common: SMTP down -> digest fails but scoring still works
Fix: Check .env for email credentials, run `fertility-sense scout --once` manually

### Emails not sending
Check: data/outreach/send_audit.jsonl for errors
Common: IONOS rate limit exceeded, bad credentials
Fix: Wait 1 hour (rate limit resets), verify .env credentials

### Prospect data corrupted
Fix: Check data/outreach/prospects/ for partial JSON files
Recovery: Restore from last git commit of data/

### Sequence stuck
Check: fertility-sense sequence status
Fix: fertility-sense sequence run --dry-run (see what's due)

## Backup
Data lives in data/ directory. Back up daily:
```
tar czf backup-$(date +%Y%m%d).tar.gz data/
```
