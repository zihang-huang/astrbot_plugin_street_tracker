from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

import httpx

PROFILE_URL_TEMPLATE = "https://www.streetfighter.com/6/buckler/profile/{player_id}"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
CHARACTER_LOCALIZATION = {
    "ryu": "隆",
    "ken": "肯",
    "chunli": "春丽",
    "jamie": "杰米",
    "manon": "曼侬",
    "kimberly": "金柏莉",
    "marisa": "玛丽莎",
    "lily": "莉莉",
    "jp": "JP",
    "juri": "蛛俐",
    "dejay": "迪杰",
    "cammy": "嘉米",
    "guile": "古烈",
    "zangief": "桑吉尔夫",
    "dhalsim": "达尔西姆",
    "ehonda": "本田",
    "blanka": "布兰卡",
    "luke": "卢克",
    "rashid": "拉希德",
    "aki": "阿鬼",
    "ed": "爱德",
    "akuma": "豪鬼",
    "mbison": "维加",
    "terry": "特瑞",
    "mai": "不知火舞",
    "elena": "艾琳娜",
    "c.viper": "深红毒蛇",
}


class SF6ClientError(Exception):
    """Base exception for SF6 profile fetch errors."""


class SF6AuthError(SF6ClientError):
    """Raised when cookie is missing, expired, or invalid."""


class SF6ParseError(SF6ClientError):
    """Raised when profile page structure cannot be parsed."""


@dataclass(slots=True)
class PlayerProfileStats:
    player_id: str
    rank: str
    favorite_character: str
    favorite_character_rank: str
    mr: str
    play_time: str
    match_count: str
    room_time: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


class SF6ProfileClient:
    def __init__(
        self,
        *,
        cookie: str,
        user_agent: str | None = None,
        timeout_seconds: int = 20,
    ) -> None:
        self.cookie = cookie.strip()
        self.user_agent = user_agent.strip() if user_agent else DEFAULT_USER_AGENT
        self.timeout_seconds = timeout_seconds

    async def fetch_player_profile_stats(self, player_id: str) -> PlayerProfileStats:
        normalized_player_id = player_id.strip()
        if not normalized_player_id:
            raise ValueError("player_id cannot be empty")
        if not self.cookie:
            raise SF6AuthError("missing cookie")

        html = await self._fetch_profile_html(normalized_player_id)
        return self._parse_stats_from_html(normalized_player_id, html)

    async def _fetch_profile_html(self, player_id: str) -> str:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
            "cache-control": "no-cache",
            "cookie": self.cookie,
            "pragma": "no-cache",
            "upgrade-insecure-requests": "1",
            "user-agent": self.user_agent,
        }
        url = PROFILE_URL_TEMPLATE.format(player_id=player_id)

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError as exc:
                raise SF6ClientError(f"request failed: {exc}") from exc

        if response.status_code in (401, 403):
            raise SF6AuthError(
                f"request blocked or unauthorized: {response.status_code}"
            )
        if response.status_code == 404:
            raise SF6ClientError("player profile not found")
        if response.status_code >= 500:
            raise SF6ClientError(f"upstream server error: {response.status_code}")

        html = response.text
        lowered = html.lower()
        if "cloudfront" in lowered and "error" in lowered:
            raise SF6AuthError("request blocked by anti-bot protection")

        return html

    def _parse_stats_from_html(self, player_id: str, html: str) -> PlayerProfileStats:
        next_data_stats = self._extract_stats_from_next_data(player_id, html)
        if next_data_stats is not None:
            return next_data_stats

        payloads = self._extract_json_payloads(html)

        key_aliases = {
            "rank": [
                "league_rank",
                "rank",
                "battle_hub_rank",
                "fighter_rank",
            ],
            "favorite_character": [
                "favorite_character",
                "favorite_character_name",
                "favorite_chara",
                "character_name",
                "character",
            ],
            "favorite_character_rank": [
                "favorite_character_rank",
                "favorite_character_league_rank",
                "character_rank",
                "character_league_rank",
            ],
            "mr": ["master_rate", "master_rating", "mr"],
            "play_time": ["play_time", "playtime"],
            "match_count": [
                "match_count",
                "battle_count",
                "battle_num",
                "total_battle_num",
            ],
            "room_time": ["room_time", "custom_room_time", "room_stay_time"],
        }

        extracted: dict[str, str] = {}
        for target_key, aliases in key_aliases.items():
            value = self._find_value(payloads, aliases)
            if value is None:
                value = self._extract_by_text_pattern(target_key, html)
            extracted[target_key] = self._normalize_value(value)

        if all(v == "N/A" for v in extracted.values()):
            raise SF6ParseError("unable to extract stats from profile page")

        return self._localize_stats(
            PlayerProfileStats(player_id=player_id, **extracted)
        )

    def _extract_stats_from_next_data(
        self, player_id: str, html: str
    ) -> PlayerProfileStats | None:
        next_data = self._extract_next_data_payload(html)
        if not isinstance(next_data, dict):
            return None

        page_props = (
            next_data.get("props", {}).get("pageProps", {})
            if isinstance(next_data.get("props"), dict)
            else {}
        )
        if not isinstance(page_props, dict):
            return None

        fighter_banner_info = page_props.get("fighter_banner_info", {})
        play = page_props.get("play", {})
        if not isinstance(fighter_banner_info, dict) or not isinstance(play, dict):
            return None

        favorite_character = self._normalize_value(
            fighter_banner_info.get("favorite_character_name")
        )

        favorite_league_info = fighter_banner_info.get(
            "favorite_character_league_info", {}
        )
        if not isinstance(favorite_league_info, dict):
            favorite_league_info = {}

        league_rank_info = favorite_league_info.get("league_rank_info", {})
        if not isinstance(league_rank_info, dict):
            league_rank_info = {}

        favorite_character_rank = self._normalize_value(
            league_rank_info.get("league_rank_name")
        )
        rank = self._normalize_value(
            fighter_banner_info.get("league_rank_name")
            or fighter_banner_info.get("rank_name")
            or favorite_character_rank
        )

        mr = self._normalize_value(
            favorite_league_info.get("master_rating")
            if favorite_league_info.get("master_league")
            else "N/A"
        )

        base_info = play.get("base_info", {})
        if not isinstance(base_info, dict):
            base_info = {}
        content_play_time_list = base_info.get("content_play_time_list", [])

        ranked_play_time_seconds = None
        if isinstance(content_play_time_list, list):
            for item in content_play_time_list:
                if not isinstance(item, dict):
                    continue
                play_time_value = item.get("play_time")
                if not isinstance(play_time_value, (int, float)):
                    continue

                content_type = item.get("content_type")
                content_type_name = (
                    str(item.get("content_type_name", "")).strip().lower()
                )
                if content_type == 2 or content_type_name == "ranked matches":
                    ranked_play_time_seconds = int(play_time_value)
                    break

        battle_stats = play.get("battle_stats", {})
        if not isinstance(battle_stats, dict):
            battle_stats = {}

        ranked_match_count = battle_stats.get("rank_match_play_count")
        if not isinstance(ranked_match_count, (int, float)):
            ranked_match_count = None

        stats = PlayerProfileStats(
            player_id=player_id,
            rank=rank,
            favorite_character=favorite_character,
            favorite_character_rank=favorite_character_rank,
            mr=mr,
            play_time=self._format_seconds_as_hours(ranked_play_time_seconds),
            match_count=self._normalize_value(ranked_match_count),
            room_time="N/A",
        )

        if all(
            value == "N/A"
            for value in (
                stats.rank,
                stats.favorite_character,
                stats.favorite_character_rank,
                stats.mr,
                stats.play_time,
                stats.match_count,
                stats.room_time,
            )
        ):
            return None

        return self._localize_stats(stats)

    def _extract_next_data_payload(self, html: str) -> dict[str, Any] | None:
        script_patterns = (
            re.compile(
                r"<script\b[^>]*\bid=(?:\"|')__NEXT_DATA__(?:\"|')[^>]*>(.*?)</script>",
                flags=re.IGNORECASE | re.DOTALL,
            ),
            re.compile(
                r"<script\b[^>]*>(.*?)</script>",
                flags=re.IGNORECASE | re.DOTALL,
            ),
        )

        for pattern in script_patterns:
            for match in pattern.finditer(html):
                script_body = match.group(1)
                if "__NEXT_DATA__" not in match.group(0):
                    continue
                parsed = self._safe_json_loads(script_body.strip())
                if isinstance(parsed, dict):
                    return parsed

        assignment_match = re.search(
            r"__NEXT_DATA__\s*=\s*(\{.*?\})\s*;",
            html,
            flags=re.DOTALL,
        )
        if assignment_match:
            parsed = self._safe_json_loads(assignment_match.group(1))
            if isinstance(parsed, dict):
                return parsed

        return None

    def _extract_json_payloads(self, html: str) -> list[Any]:
        payloads: list[Any] = []

        script_json_pattern = re.compile(
            r"<script[^>]*type=[\"']application/(?:ld\+)?json[\"'][^>]*>(.*?)</script>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in script_json_pattern.finditer(html):
            raw = match.group(1).strip()
            if not raw:
                continue
            parsed = self._safe_json_loads(raw)
            if parsed is not None:
                payloads.append(parsed)

        for var_name in ("__NEXT_DATA__", "__NUXT__", "__APOLLO_STATE__"):
            var_pattern = re.compile(
                rf"{var_name}\s*=\s*(\{{.*?\}})\s*;",
                flags=re.DOTALL,
            )
            match = var_pattern.search(html)
            if match:
                parsed = self._safe_json_loads(match.group(1))
                if parsed is not None:
                    payloads.append(parsed)

        return payloads

    def _safe_json_loads(self, raw_text: str) -> Any | None:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return None

    def _find_value(self, payloads: list[Any], aliases: list[str]) -> Any | None:
        normalized_aliases = {self._normalize_key(alias) for alias in aliases}

        for payload in payloads:
            found = self._find_value_in_node(payload, normalized_aliases)
            if found is not None:
                return found
        return None

    def _find_value_in_node(self, node: Any, aliases: set[str]) -> Any | None:
        if isinstance(node, dict):
            for key, value in node.items():
                if self._normalize_key(str(key)) in aliases and self._is_primitive(
                    value
                ):
                    return value
            for value in node.values():
                nested = self._find_value_in_node(value, aliases)
                if nested is not None:
                    return nested
            return None

        if isinstance(node, list):
            for item in node:
                nested = self._find_value_in_node(item, aliases)
                if nested is not None:
                    return nested

        return None

    def _extract_by_text_pattern(self, field_name: str, html: str) -> Any | None:
        patterns: dict[str, list[str]] = {
            "mr": [
                r"(?:Master\s*Rate|Master\s*Rating|MR)\s*[:：]?\s*([\d,.]+)",
            ],
            "match_count": [
                r"(?:Match\s*Count|Total\s*Matches|Battles?)\s*[:：]?\s*([\d,]+)",
            ],
            "play_time": [
                r"(?:Play\s*Time)\s*[:：]?\s*([^<\n]+)",
            ],
            "room_time": [
                r"(?:Room\s*Time)\s*[:：]?\s*([^<\n]+)",
            ],
            "favorite_character": [
                r"(?:Favorite\s*Character)\s*[:：]?\s*([^<\n]+)",
            ],
            "favorite_character_rank": [
                r"(?:Favorite\s*Character\s*Rank)\s*[:：]?\s*([^<\n]+)",
            ],
            "rank": [
                r"(?:Rank)\s*[:：]?\s*([^<\n]+)",
            ],
        }

        for pattern in patterns.get(field_name, []):
            match = re.search(pattern, html, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _normalize_key(self, key: str) -> str:
        return re.sub(r"[^a-z0-9]", "", key.lower())

    def _localize_stats(self, stats: PlayerProfileStats) -> PlayerProfileStats:
        return PlayerProfileStats(
            player_id=stats.player_id,
            rank=stats.rank,
            favorite_character=self._localize_character(stats.favorite_character),
            favorite_character_rank=stats.favorite_character_rank,
            mr=stats.mr,
            play_time=stats.play_time,
            match_count=stats.match_count,
            room_time=stats.room_time,
        )

    def _localize_character(self, character_name: str) -> str:
        if character_name == "N/A":
            return character_name

        key = self._normalize_key(character_name)
        return CHARACTER_LOCALIZATION.get(key, character_name)

    def _normalize_value(self, value: Any | None) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, (dict, list)):
            return "N/A"
        text = str(value).strip()
        return text if text else "N/A"

    def _format_seconds_as_hours(self, seconds: Any | None) -> str:
        if not isinstance(seconds, (int, float)):
            return "N/A"

        total_seconds = int(seconds)
        if total_seconds < 0:
            return "N/A"

        total_minutes = total_seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}:{minutes:02d} 小时"

    def _is_primitive(self, value: Any) -> bool:
        return isinstance(value, (str, int, float, bool))
