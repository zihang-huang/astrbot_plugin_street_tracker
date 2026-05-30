from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .sf6_profile import (
    PlayerProfileStats,
    SF6AuthError,
    SF6ClientError,
    SF6ParseError,
    SF6ProfileClient,
    SF6ProfileNotFoundError,
)


@register(
    "astrbot_plugin_street_tracker",
    "二猫姥爷",
    "Street Fighter 6 玩家信息查询",
    "1.5.1",
)
class StreetTrackerPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config

    @staticmethod
    def _binding_key(sender_id: str) -> str:
        return f"binding:{sender_id}"

    def _build_profile_client(self) -> tuple[SF6ProfileClient | None, str | None]:
        cookie = str(self.config.get("sf6_cookie", "")).strip()
        if not cookie:
            return None, "未配置 SF6 Cookie，请在插件配置中填写 sf6_cookie。"

        try:
            timeout_seconds = int(self.config.get("request_timeout_seconds", 20) or 20)
        except (TypeError, ValueError):
            return (
                None,
                "请求超时配置 request_timeout_seconds 无法解析，请填写正整数。",
            )

        if timeout_seconds <= 0:
            return None, "请求超时配置 request_timeout_seconds 必须大于 0。"

        user_agent = str(self.config.get("user_agent", "")).strip() or None
        return (
            SF6ProfileClient(
                cookie=cookie,
                user_agent=user_agent,
                timeout_seconds=timeout_seconds,
            ),
            None,
        )

    @staticmethod
    def _format_profile_stats(stats: PlayerProfileStats) -> str:
        lines = [
            "🎮 Street Fighter 6 玩家信息",
            f"🆔 玩家ID: {stats.player_id}",
            f"👤 玩家名: {stats.player_name}",
            f"🏆 段位: {stats.rank}",
            f"🕹️ 常用角色: {stats.favorite_character}",
            f"📈 常用角色段位: {stats.favorite_character_rank}",
            f"💠 大师分MR: {stats.mr}",
            f"⌛ 总时长: {stats.total_play_time}",
            f"🎯 排位赛时长: {stats.play_time}",
            f"😎 休闲赛时长: {stats.casual_play_time}",
            f"🏠 比赛间时长: {stats.room_time}",
            f"⚔️ 排位对局场次: {stats.match_count}",
        ]
        return "\n".join(lines)

    async def _fetch_profile_stats(
        self, player_id: str
    ) -> tuple[PlayerProfileStats | None, str | None]:
        client, error_message = self._build_profile_client()
        if error_message is not None:
            return None, error_message
        if client is None:
            return None, "查询失败: 发生未知错误。"

        try:
            return await client.fetch_player_profile_stats(player_id), None
        except SF6AuthError:
            return None, "Cookie 无效或已过期，请更新插件配置中的 sf6_cookie。"
        except SF6ProfileNotFoundError:
            return None, "玩家 ID 不存在，请确认输入是否正确。"
        except SF6ParseError:
            return None, "已拿到页面，但暂时无法解析该玩家数据。"
        except SF6ClientError as exc:
            logger.warning(f"SF6 query failed for player {player_id}: {exc}")
            return None, f"查询失败: {exc}"
        except Exception:
            logger.exception("Unexpected error while querying SF6 profile")
            return None, "查询失败: 发生未知错误。"

    @staticmethod
    def _safe_error_reply(action: str, cause: str) -> str:
        if cause.startswith("查询失败:") or cause.startswith(f"{action}失败:"):
            return cause
        return f"{action}失败: {cause}"

    @staticmethod
    def _internal_error_reply(action: str) -> str:
        return f"{action}失败: 插件内部处理异常，请稍后重试。"

    @filter.command("绑定")
    async def bind_profile(self, event: AstrMessageEvent, player_id: str = ""):
        """绑定当前用户与 Street Fighter 6 玩家 ID。"""
        try:
            player_id = player_id.strip()
            if not player_id:
                yield event.plain_result("用法: /绑定 <player_id>")
                return

            stats, error_message = await self._fetch_profile_stats(player_id)
            if error_message is not None or stats is None:
                logger.info(
                    f"SF6 bind validation failed for player {player_id}: {error_message}"
                )
                if error_message in (
                    "玩家 ID 不存在，请确认输入是否正确。",
                    "已拿到页面，但暂时无法解析该玩家数据。",
                ):
                    yield event.plain_result("绑定失败，请确认玩家 ID 是否正确。")
                else:
                    yield event.plain_result(self._safe_error_reply("绑定", error_message or "发生未知错误"))
                return

            sender_id = str(event.get_sender_id()).strip()
            await self.put_kv_data(self._binding_key(sender_id), player_id)
            yield event.plain_result(
                "绑定成功，你可以直接使用 /查询 查看该玩家信息。\n\n"
                f"{self._format_profile_stats(stats)}"
            )
        except Exception:
            logger.exception(f"Unhandled error while handling /绑定 for player {player_id}")
            yield event.plain_result(self._internal_error_reply("绑定"))

    @filter.command("查询")
    async def query_profile(self, event: AstrMessageEvent, player_id: str = ""):
        """根据玩家 ID 查询 Street Fighter 6 档案数据。"""
        try:
            player_id = player_id.strip()
            if not player_id:
                sender_id = str(event.get_sender_id()).strip()
                player_id = str(
                    await self.get_kv_data(self._binding_key(sender_id), "")
                ).strip()
                if not player_id:
                    yield event.plain_result(
                        "用法: /查询 <player_id> 或先使用 /绑定 <player_id>"
                    )
                    return

            stats, error_message = await self._fetch_profile_stats(player_id)
            if error_message is not None or stats is None:
                yield event.plain_result(self._safe_error_reply("查询", error_message or "发生未知错误"))
                return

            yield event.plain_result(self._format_profile_stats(stats))
        except Exception:
            logger.exception(f"Unhandled error while handling /查询 for player {player_id}")
            yield event.plain_result(self._internal_error_reply("查询"))
