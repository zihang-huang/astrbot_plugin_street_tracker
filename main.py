from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .sf6_profile import SF6AuthError, SF6ClientError, SF6ParseError, SF6ProfileClient


@register(
    "astrbot_plugin_street_tracker",
    "二猫姥爷",
    "Street Fighter 6 玩家信息查询",
    "1.1.0",
)
class StreetTrackerPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config

    @staticmethod
    def _binding_key(sender_id: str) -> str:
        return f"binding:{sender_id}"

    @filter.command("绑定")
    async def bind_profile(self, event: AstrMessageEvent, player_id: str = ""):
        """绑定当前用户与 Street Fighter 6 玩家 ID。"""
        player_id = player_id.strip()
        if not player_id:
            yield event.plain_result("用法: /绑定 <player_id>")
            return

        sender_id = str(event.get_sender_id()).strip()
        await self.put_kv_data(self._binding_key(sender_id), player_id)
        yield event.plain_result(
            f"绑定成功，你可以直接使用 /查询 查看玩家 {player_id} 的信息。"
        )

    @filter.command("查询")
    async def query_profile(self, event: AstrMessageEvent, player_id: str = ""):
        """根据玩家 ID 查询 Street Fighter 6 档案数据。"""
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

        cookie = str(self.config.get("sf6_cookie", "")).strip()
        if not cookie:
            yield event.plain_result(
                "未配置 SF6 Cookie，请在插件配置中填写 sf6_cookie。"
            )
            return

        timeout_seconds = int(self.config.get("request_timeout_seconds", 20) or 20)
        user_agent = str(self.config.get("user_agent", "")).strip() or None

        client = SF6ProfileClient(
            cookie=cookie,
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
        )

        try:
            stats = await client.fetch_player_profile_stats(player_id)
        except SF6AuthError:
            yield event.plain_result(
                "Cookie 无效或已过期，请更新插件配置中的 sf6_cookie。"
            )
            return
        except SF6ParseError:
            yield event.plain_result("已拿到页面，但暂时无法解析该玩家数据。")
            return
        except SF6ClientError as exc:
            logger.warning(f"SF6 query failed for player {player_id}: {exc}")
            yield event.plain_result(f"查询失败: {exc}")
            return
        except Exception:
            logger.exception("Unexpected error while querying SF6 profile")
            yield event.plain_result("查询失败: 发生未知错误。")
            return

        lines = [
            "🎮 Street Fighter 6 玩家信息",
            f"🆔 玩家ID: {stats.player_id}",
            f"👤 玩家名: {stats.player_name}",
            f"🏆 段位: {stats.rank}",
            f"🕹️ 常用角色: {stats.favorite_character}",
            f"📈 常用角色段位: {stats.favorite_character_rank}",
            f"💠 大师分MR: {stats.mr}",
            f"⚔️ 排位对局场次: {stats.match_count}",
            f"⏱️ 排位对局时长: {stats.play_time}",
        ]
        yield event.plain_result("\n".join(lines))
