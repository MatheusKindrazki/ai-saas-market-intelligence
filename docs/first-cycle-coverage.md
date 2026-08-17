# First collection coverage

Executed on 2026-08-16 with:

```sh
.venv/bin/python -m radar.run_cycle collect --db radar_runtime/radar.db
```

| Family | Attempted | Collected | Errors | Result |
| --- | ---: | ---: | ---: | --- |
| reddit | 6 | 0 | 0 | Coverage gap: Reddit Public Content Policy robots denial |
| hackernews | 10 | 200 | 0 | Data returned |
| github | 10 | 0 | 1 | Sandbox DNS could not resolve `api.github.com` |
| stackexchange | 10 | 200 | 0 | Data returned |
| forums | 1 | 0 | 1 | Sandbox DNS could not resolve `dev.to` |
| reviews | 2 | 0 | 1 | Sandbox DNS could not resolve `wordpress.org` |
| web_search | 10 | 0 | 0 | Coverage gap: public engines blocked or robots-disallowed |
| x_curated | 1 | 0 | 0 | Coverage gap: access not configured |

The source adapters use the verified public DEV, WordPress, and AMO endpoints. The three network failures above are genuine runtime errors, deliberately distinct from documented coverage gaps; re-running from a networked environment should exercise the remaining three data families.
