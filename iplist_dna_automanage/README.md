# iplist_dna_automanage

Automation project to maintain DNA_* IPLists from outbound FQDN traffic.

## Quick start

1. Configure `conf/global.conf`.
2. Run once manually:
   ```bash
   ./bin/cron_job.sh ./conf/global.conf
   ```
3. Add cron entry:
   ```cron
   15 2 * * * /path/to/iplist_dna_automanage/bin/cron_job.sh /path/to/iplist_dna_automanage/conf/global.conf
   ```

All run artifacts are generated under `RUNS/<YYYYmmdd-HHMMSS>/`.

## Documentation

- Markdown: `docs/TECHNICAL_DOCUMENTATION.md`
- To generate the Word file locally (without storing binaries in git):
  ```bash
  python3 docs/build_docx.py
  ```

