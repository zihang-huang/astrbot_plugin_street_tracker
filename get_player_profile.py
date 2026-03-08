from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from .sf6_profile import SF6AuthError, SF6ClientError, SF6ParseError, SF6ProfileClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Street Fighter 6 Buckler player stats by player ID."
    )
    parser.add_argument("player_id", help="Street Fighter 6 player ID")
    parser.add_argument(
        "--cookie",
        default=os.getenv("SF6_COOKIE", ""),
        help="Cookie string for streetfighter.com; defaults to env SF6_COOKIE",
    )
    parser.add_argument(
        "--user-agent",
        default=os.getenv("SF6_USER_AGENT", ""),
        help="Optional custom User-Agent; defaults to env SF6_USER_AGENT",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("SF6_TIMEOUT", "20")),
        help="Request timeout in seconds (default: 20)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output",
    )
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    if not args.cookie.strip():
        print(
            "Error: missing cookie. Provide --cookie or set SF6_COOKIE.",
            file=sys.stderr,
        )
        return 2

    client = SF6ProfileClient(
        cookie=args.cookie,
        user_agent=args.user_agent or None,
        timeout_seconds=args.timeout,
    )

    try:
        stats = await client.fetch_player_profile_stats(args.player_id)
    except SF6AuthError as exc:
        print(f"Auth error: {exc}", file=sys.stderr)
        return 3
    except SF6ParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 4
    except SF6ClientError as exc:
        print(f"Request error: {exc}", file=sys.stderr)
        return 5

    if args.json:
        print(json.dumps(stats.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"player_id: {stats.player_id}")
        print(f"rank: {stats.rank}")
        print(f"favorite_character: {stats.favorite_character}")
        print(f"favorite_character_rank: {stats.favorite_character_rank}")
        print(f"mr: {stats.mr}")
        print(f"play_time: {stats.play_time}")
        print(f"match_count: {stats.match_count}")
        print(f"room_time: {stats.room_time}")

    return 0


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
