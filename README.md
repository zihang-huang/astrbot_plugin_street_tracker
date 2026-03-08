# astrbot_plugin_street_tracker

Street Fighter 6 Buckler profile lookup plugin for AstrBot.

## Features

- `/查询 <player_id>`: fetch player profile stats by player ID
- Uses authenticated HTTP requests with a global Cookie
- Extracts rank, favorite character, favorite character rank, MR, play time, match count, and room time

## Configuration

Configure plugin settings in AstrBot WebUI (from `_conf_schema.json`):

- `sf6_cookie`: required, full Cookie header string from a logged-in `streetfighter.com` browser session
- `user_agent`: optional custom User-Agent
- `request_timeout_seconds`: request timeout in seconds

## Utility Script

You can also run standalone lookup locally:

```bash
python get_player_profile.py <player_id> --cookie "<your_cookie>"
```

Or via environment variable:

```bash
SF6_COOKIE="<your_cookie>" python get_player_profile.py <player_id> --json
```

## Notes

- Cookie is sensitive data. Do not expose it in logs or screenshots.
- If lookup fails with auth errors, refresh Cookie from browser and update config.
