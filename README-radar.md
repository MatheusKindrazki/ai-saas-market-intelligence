# Deep Opportunity Radar

Run collection with `python -m radar.run_cycle collect --db /tmp/radar.db`. `GLM_API_KEY`
is optional for collection and required for mining or validation; `GITHUB_TOKEN` is optional.
Use a six-hour collect cron, a daily mine/score/report cron, and a weekly deep cycle.
Rollback by deleting those cron jobs and `radar_runtime/`; reports remain reviewable.
