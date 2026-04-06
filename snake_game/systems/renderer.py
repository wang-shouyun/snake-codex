"""All drawing code lives here."""

from __future__ import annotations

from pathlib import Path

import pygame

import settings


class Renderer:
    """Draws the board, HUD, menu, join screens, and overlays."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_path = self._find_ui_font()
        self._show_ai_status_tags = False
        self.hero_font = self._load_font(64)
        self.title_font = self._load_font(42)
        self.heading_font = self._load_font(30)
        self.main_font = self._load_font(28)
        self.small_font = self._load_font(22)
        self.briefing_title_font = self._load_font(32)
        self.briefing_heading_font = self._load_font(22)
        self.briefing_font = self._load_font(18)

    def _find_ui_font(self) -> str | None:
        """Pick a font that supports CJK text when available."""
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/SourceHanSansSC-Regular.otf",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate
        return None

    def _load_font(self, size: int) -> pygame.font.Font:
        if self.font_path is not None:
            return pygame.font.Font(self.font_path, size)
        return pygame.font.Font(None, size)

    def draw(self, game) -> None:
        self._draw_background()

        if game.state == "language_select":
            self._draw_language_select(game)
            return
        if game.state == "mode_setup":
            self._draw_mode_setup(game)
            return
        if game.state == "menu":
            self._draw_menu(game)
            return
        if game.state == "network_join_input":
            self._draw_join_prompt(game)
            return
        if game.state == "network_wait_host":
            self._draw_host_wait(game)
            return
        if game.state == "network_client_playing":
            self._draw_remote_client(game)
            return

        data = self._local_data(game)
        self._draw_match_scene(data, game.current_mode_id, game.round_message, game.stats_store.data, game)

        if game.state == "paused":
            self._draw_overlay(
                game.t("paused"),
                [game.t("paused_1"), game.t("paused_2"), game.t("paused_3")],
            )
        elif game.state == "game_over":
            self._draw_overlay(
                game.result_title,
                game.result_lines,
                actions=getattr(game, "result_actions", []),
                selected_index=getattr(game, "result_action_index", 0),
            )

    def _draw_background(self) -> None:
        self.screen.fill((8, 12, 18))
        for y in range(settings.WINDOW_HEIGHT):
            ratio = y / settings.WINDOW_HEIGHT
            color = (int(10 + 18 * ratio), int(15 + 22 * ratio), int(24 + 34 * ratio))
            pygame.draw.line(self.screen, color, (0, y), (settings.WINDOW_WIDTH, y))

        glow = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (26, 188, 156, 28), (210, 110), 200)
        pygame.draw.circle(glow, (58, 123, 213, 34), (860, 560), 280)
        pygame.draw.circle(glow, (255, 196, 88, 18), (730, 140), 150)
        self.screen.blit(glow, (0, 0))

    def _draw_language_select(self, game) -> None:
        panel = pygame.Rect(126, 158, settings.WINDOW_WIDTH - 252, 360)
        self._draw_panel(panel, (9, 12, 18), 28)
        self._blit_text(game.t("startup_title"), self.hero_font, settings.TEXT_COLOR, panel.x + 34, panel.y + 34)
        self._blit_wrapped_text(game.t("startup_subtitle"), panel.x + 36, panel.y + 112, panel.width - 72)

        lane = pygame.Rect(panel.x + 36, panel.y + 176, panel.width - 72, 96)
        pygame.draw.rect(self.screen, (13, 18, 27), lane, border_radius=22)
        pygame.draw.rect(self.screen, (52, 69, 94), lane, width=2, border_radius=22)

        item_width = 180
        spacing = 22
        total_width = len(settings.SUPPORTED_LANGUAGES) * item_width + (len(settings.SUPPORTED_LANGUAGES) - 1) * spacing
        start_x = lane.centerx - total_width // 2
        for index, code in enumerate(settings.SUPPORTED_LANGUAGES):
            card = pygame.Rect(start_x + index * (item_width + spacing), lane.y + 14, item_width, 68)
            is_selected = index == game.language_index
            fill = (20, 30, 44) if is_selected else (16, 22, 31)
            border = settings.HIGHLIGHT_COLOR if is_selected else (55, 71, 96)
            pygame.draw.rect(self.screen, fill, card, border_radius=18)
            pygame.draw.rect(self.screen, border, card, width=2, border_radius=18)
            self._blit_text(game.localizer.get_language_name(code), self.heading_font, settings.TEXT_COLOR, card.x + 26, card.y + 18)

        self._blit_text(game.t("startup_hint"), self.small_font, settings.SUBTEXT_COLOR, panel.x + 36, panel.y + 302)
        self._blit_text(game.t("startup_confirm"), self.small_font, settings.HIGHLIGHT_COLOR, panel.x + 36, panel.y + 328)

    def _draw_menu(self, game) -> None:
        hero = pygame.Rect(36, 32, settings.WINDOW_WIDTH - 72, 124)
        self._draw_panel(hero, (9, 12, 18), 28)

        title_font = self._fit_font(game.t("menu_title"), 52, 34, hero.width - 320)
        self._blit_text(game.t("menu_title"), title_font, settings.TEXT_COLOR, hero.x + 28, hero.y + 18)
        self._blit_text(game.menu_message, self.small_font, settings.SUBTEXT_COLOR, hero.x + 30, hero.y + 84)

        chip_x = hero.right - 206
        self._draw_status_chip(
            chip_x,
            hero.y + 18,
            170,
            game.localizer.get_language_name(game.localizer.language),
            settings.TEXT_COLOR,
            (20, 28, 44),
            border=(85, 118, 214),
        )
        self._draw_status_chip(
            chip_x,
            hero.y + 62,
            170,
            game.t("difficulty_value", value=game.t(f"difficulty_{game.current_difficulty_id}_label")),
            settings.HIGHLIGHT_COLOR,
            (18, 48, 46),
        )

        left = pygame.Rect(36, 176, 424, 468)
        right = pygame.Rect(480, 176, 464, 468)
        footer = pygame.Rect(36, 658, settings.WINDOW_WIDTH - 72, 38)
        self._draw_panel(left, (9, 13, 20), 24)
        self._draw_panel(right, (11, 16, 24), 24)
        self._draw_panel(footer, (10, 14, 21), 20)

        self._blit_text(
            game.t("modes_title"),
            self._fit_font(game.t("modes_title"), 30, 22, left.width - 50),
            settings.TEXT_COLOR,
            left.x + 20,
            left.y + 18,
        )
        option_y = left.y + 66
        option_count = max(1, len(settings.MODE_DEFINITIONS))
        available_height = left.height - 84
        gap = 8 if option_count <= 7 else 6
        option_height = max(38, min(52, (available_height - gap * (option_count - 1)) // option_count))
        for index, mode in enumerate(settings.MODE_DEFINITIONS):
            option_rect = pygame.Rect(left.x + 16, option_y, left.width - 32, option_height)
            is_selected = index == game.menu_index
            fill = (18, 29, 43) if is_selected else (12, 18, 27)
            border = settings.HIGHLIGHT_COLOR if is_selected else (43, 61, 88)
            pygame.draw.rect(self.screen, fill, option_rect, border_radius=16)
            pygame.draw.rect(self.screen, border, option_rect, width=2, border_radius=16)
            if is_selected:
                accent = pygame.Rect(option_rect.x + 10, option_rect.y + 8, 5, option_rect.height - 16)
                pygame.draw.rect(self.screen, settings.HIGHLIGHT_COLOR, accent, border_radius=5)
            label = self._mode_label(mode["id"], game)
            label_font = self._fit_font(label, 24, 14, option_rect.width - 56)
            label_height = label_font.get_height()
            self._blit_text(
                label,
                label_font,
                settings.TEXT_COLOR,
                option_rect.x + 26,
                option_rect.y + max(8, (option_rect.height - label_height) // 2 - 1),
            )
            option_y += option_height + gap

        selected = settings.MODE_DEFINITIONS[game.menu_index]
        self._blit_text(
            game.t("briefing_title"),
            self._fit_font(game.t("briefing_title"), 28, 20, right.width - 48),
            settings.TEXT_COLOR,
            right.x + 24,
            right.y + 20,
        )
        selected_label = self._mode_label(selected["id"], game)
        self._blit_text(
            selected_label,
            self._fit_font(selected_label, 30, 18, right.width - 48),
            settings.HIGHLIGHT_COLOR,
            right.x + 24,
            right.y + 58,
        )
        self._blit_wrapped_text(
            self._mode_description(selected["id"], game),
            right.x + 24,
            right.y + 102,
            right.width - 48,
            font=self.small_font,
            line_height=24,
        )

        feature_box = pygame.Rect(right.x + 22, right.y + 156, right.width - 44, 112)
        pygame.draw.rect(self.screen, (15, 22, 32), feature_box, border_radius=18)
        pygame.draw.rect(self.screen, (49, 72, 102), feature_box, width=2, border_radius=18)
        self._draw_status_chip(feature_box.x + 14, feature_box.y + 14, 144, game.t("chip_arcade"), settings.HIGHLIGHT_COLOR, (18, 44, 40))
        self._blit_wrapped_text(game.t("briefing_3"), feature_box.x + 14, feature_box.y + 56, feature_box.width - 28, font=self.briefing_font, line_height=20)

        rules_box = pygame.Rect(right.x + 22, right.y + 286, right.width - 44, 154)
        pygame.draw.rect(self.screen, (14, 20, 30), rules_box, border_radius=18)
        pygame.draw.rect(self.screen, (44, 63, 92), rules_box, width=2, border_radius=18)
        bullet_y = rules_box.y + 16
        for key in ("briefing_1", "briefing_2", "briefing_4"):
            self._draw_bullet(game.t(key), rules_box.x + 16, bullet_y, max_width=rules_box.width - 32, font=self.briefing_font, line_height=20)
            bullet_y += 42

        footer_lines = [game.t("footer_1"), game.t("footer_2"), game.t("footer_3")]
        column_width = (footer.width - 56) // 3
        for index, line in enumerate(footer_lines):
            x = footer.x + 18 + index * (column_width + 10)
            self._blit_wrapped_text(line, x, footer.y + 8, column_width, font=self.briefing_font, line_height=18)

    def _draw_mode_setup(self, game) -> None:
        panel = pygame.Rect(52, 58, settings.WINDOW_WIDTH - 104, settings.WINDOW_HEIGHT - 108)
        self._draw_panel(panel, (9, 13, 20), 28)
        left = pygame.Rect(panel.x + 20, panel.y + 20, 376, panel.height - 40)
        right = pygame.Rect(left.right + 20, panel.y + 20, panel.width - 436, panel.height - 40)
        pygame.draw.rect(self.screen, (12, 18, 27), left, border_radius=22)
        pygame.draw.rect(self.screen, (42, 58, 82), left, width=2, border_radius=22)
        pygame.draw.rect(self.screen, (12, 18, 27), right, border_radius=22)
        pygame.draw.rect(self.screen, (42, 58, 82), right, width=2, border_radius=22)

        self._blit_text(game.t("setup_title"), self.title_font, settings.TEXT_COLOR, left.x + 22, left.y + 18)
        mode_label = self._mode_label(game.current_mode_id, game)
        self._blit_text(
            mode_label,
            self._fit_font(mode_label, 26, 18, left.width - 44),
            settings.HIGHLIGHT_COLOR,
            left.x + 22,
            left.y + 64,
        )

        action_row = pygame.Rect(left.x + 18, left.y + 110, left.width - 36, 84)
        action_selected = game.setup_index == 0
        pygame.draw.rect(self.screen, (16, 24, 36), action_row, border_radius=18)
        pygame.draw.rect(
            self.screen,
            settings.HIGHLIGHT_COLOR if action_selected else (49, 67, 94),
            action_row,
            width=2,
            border_radius=18,
        )
        self._blit_text(game.t("setup_action"), self.small_font, settings.SUBTEXT_COLOR, action_row.x + 16, action_row.y + 12)
        pill_y = action_row.y + 38
        pill_w = (action_row.width - 42) // 2
        for idx, action_key in enumerate(("play", "demo")):
            rect = pygame.Rect(action_row.x + 14 + idx * (pill_w + 14), pill_y, pill_w, 32)
            active = game.setup_action == action_key
            fill = (31, 60, 55) if active else (20, 28, 40)
            border = settings.HIGHLIGHT_COLOR if active else (57, 75, 102)
            pygame.draw.rect(self.screen, fill, rect, border_radius=12)
            pygame.draw.rect(self.screen, border, rect, width=2, border_radius=12)
            label = game.t("setup_action_play") if action_key == "play" else game.t("setup_action_demo")
            self._blit_text(label, self._fit_font(label, 20, 14, rect.width - 20), settings.TEXT_COLOR, rect.x + 12, rect.y + 6)

        labels = [game.t("setup_hours"), game.t("setup_minutes"), game.t("setup_seconds")]
        values = [f"{game.setup_duration[0]:02d}", f"{game.setup_duration[1]:02d}", f"{game.setup_duration[2]:02d}"]
        card_y = action_row.bottom + 18
        card_gap = 12
        card_width = (left.width - 36 - card_gap * 2) // 3
        for idx, (label, value) in enumerate(zip(labels, values), start=1):
            card = pygame.Rect(left.x + 18 + (idx - 1) * (card_width + card_gap), card_y, card_width, 104)
            selected = game.setup_index == idx
            fill = (18, 27, 39) if selected else (14, 20, 29)
            border = settings.HIGHLIGHT_COLOR if selected else (49, 67, 94)
            pygame.draw.rect(self.screen, fill, card, border_radius=18)
            pygame.draw.rect(self.screen, border, card, width=2, border_radius=18)
            self._blit_text(label, self.small_font, settings.SUBTEXT_COLOR, card.x + 14, card.y + 14)
            self._blit_text(value, self._fit_font(value, 38, 24, card.width - 28), settings.TEXT_COLOR, card.x + 14, card.y + 44)

        start_button = pygame.Rect(left.x + 18, card_y + 122, left.width - 36, 58)
        button_selected = game.setup_index == 4
        pygame.draw.rect(self.screen, (22, 46, 42), start_button, border_radius=18)
        pygame.draw.rect(
            self.screen,
            settings.HIGHLIGHT_COLOR if button_selected else (62, 111, 102),
            start_button,
            width=2,
            border_radius=18,
        )
        button_label = game.t("setup_action_demo") if game.setup_action == "demo" else game.t("setup_action_play")
        button_text = f"{game.t('setup_confirm')} · {button_label}"
        self._blit_text(
            button_text,
            self._fit_font(button_text, 22, 16, start_button.width - 28),
            settings.TEXT_COLOR,
            start_button.x + 18,
            start_button.y + 16,
        )

        footer_box = pygame.Rect(left.x + 18, left.bottom - 78, left.width - 36, 54)
        pygame.draw.rect(self.screen, (13, 18, 27), footer_box, border_radius=16)
        pygame.draw.rect(self.screen, (49, 67, 94), footer_box, width=2, border_radius=16)
        self._blit_wrapped_text(game.t("setup_hint_1"), footer_box.x + 14, footer_box.y + 8, footer_box.width - 28, font=self.briefing_font, line_height=17)
        self._blit_wrapped_text(game.t("setup_hint_2"), footer_box.x + 14, footer_box.y + 28, footer_box.width - 28, font=self.briefing_font, line_height=17)

        self._blit_text(game.t("setup_guide_title"), self._fit_font(game.t("setup_guide_title"), 28, 20, right.width - 44), settings.TEXT_COLOR, right.x + 22, right.y + 20)
        self._draw_status_chip(right.x + 22, right.y + 60, min(200, right.width - 44), mode_label, settings.HIGHLIGHT_COLOR, (18, 44, 40))
        self._blit_wrapped_text(
            self._mode_description(game.current_mode_id, game),
            right.x + 22,
            right.y + 110,
            right.width - 44,
            font=self.small_font,
            line_height=24,
        )

        guide_key = f"setup_guide_{game.current_mode_id}"
        bullets = [game.t(guide_key), game.t("briefing_1"), game.t("briefing_2")]
        bullet_y = right.y + 188
        for line in bullets:
            self._draw_bullet(line, right.x + 24, bullet_y, max_width=right.width - 52, font=self.briefing_font, line_height=20)
            bullet_y += 58

        guide_box = pygame.Rect(right.x + 20, right.bottom - 140, right.width - 40, 106)
        pygame.draw.rect(self.screen, (15, 22, 32), guide_box, border_radius=18)
        pygame.draw.rect(self.screen, (49, 72, 102), guide_box, width=2, border_radius=18)
        helper_lines = [game.t("setup_hint_1"), game.t("setup_hint_2")]
        guide_y = guide_box.y + 12
        for line in helper_lines:
            self._blit_wrapped_text(line, guide_box.x + 14, guide_y, guide_box.width - 28, font=self.briefing_font, line_height=18)
            guide_y += 28

    def _draw_join_prompt(self, game) -> None:
        panel = pygame.Rect(128, 116, settings.WINDOW_WIDTH - 256, 488)
        self._draw_panel(panel, (10, 15, 22), 28)
        self._blit_text(game.t("join_title"), self.title_font, settings.TEXT_COLOR, panel.x + 34, panel.y + 30)
        self._blit_wrapped_text(game.t("join_desc"), panel.x + 34, panel.y + 84, panel.width - 68)

        input_box = pygame.Rect(panel.x + 34, panel.y + 156, panel.width - 68, 74)
        pygame.draw.rect(self.screen, (15, 24, 36), input_box, border_radius=18)
        pygame.draw.rect(self.screen, settings.HIGHLIGHT_COLOR, input_box, width=2, border_radius=18)
        self._blit_text(game.join_ip_text or "192.168.1.8", self.heading_font, settings.TEXT_COLOR, input_box.x + 20, input_box.y + 23)

        tips = [
            game.t("join_tip_1", port=settings.NETWORK_PORT),
            game.t("join_tip_2"),
            game.t("join_tip_3"),
            game.t("join_tip_4"),
            game.round_message,
        ]
        y = panel.y + 258
        for line in tips:
            self._blit_wrapped_text(line, panel.x + 34, y, panel.width - 68)
            y += 26

        list_box = pygame.Rect(panel.x + 34, panel.y + 354, panel.width - 68, 100)
        pygame.draw.rect(self.screen, (14, 20, 29), list_box, border_radius=18)
        pygame.draw.rect(self.screen, (58, 73, 98), list_box, width=2, border_radius=18)
        self._blit_text(game.t("discovery_title"), self.small_font, settings.SUBTEXT_COLOR, list_box.x + 16, list_box.y + 12)
        if not game.discovered_rooms:
            self._blit_text(game.t("discovery_empty"), self.small_font, settings.SUBTEXT_COLOR, list_box.x + 16, list_box.y + 44)
        else:
            for index, room in enumerate(game.discovered_rooms[:3]):
                row = pygame.Rect(list_box.x + 12, list_box.y + 36 + index * 22, list_box.width - 24, 20)
                if index == game.discovery_index:
                    pygame.draw.rect(self.screen, (24, 39, 58), row, border_radius=8)
                label = f"{room['room_code']}   {room['host_ip']}"
                self._blit_text(label, self.small_font, settings.TEXT_COLOR if index == game.discovery_index else settings.SUBTEXT_COLOR, row.x + 8, row.y + 1)
            self._blit_text(game.t("discovery_pick"), self.small_font, settings.HIGHLIGHT_COLOR, list_box.x + 16, list_box.bottom - 24)

    def _draw_host_wait(self, game) -> None:
        panel = pygame.Rect(84, 122, settings.WINDOW_WIDTH - 168, 456)
        self._draw_panel(panel, (10, 15, 22), 28)
        self._blit_text(game.t("host_title"), self.title_font, settings.TEXT_COLOR, panel.x + 34, panel.y + 26)
        self._blit_text(game.t("host_waiting"), self.heading_font, settings.HIGHLIGHT_COLOR, panel.x + 36, panel.y + 84)

        card = pygame.Rect(panel.x + 34, panel.y + 140, panel.width - 68, 142)
        pygame.draw.rect(self.screen, (17, 27, 40), card, border_radius=22)
        pygame.draw.rect(self.screen, (72, 117, 194), card, width=2, border_radius=22)
        self._blit_text(game.t("share_ip"), self.small_font, settings.SUBTEXT_COLOR, card.x + 22, card.y + 18)
        ip_font = self._fit_font(game.host_ip, 58, 28, card.width - 44)
        self._blit_text(game.host_ip, ip_font, settings.TEXT_COLOR, card.x + 22, card.y + 44)
        chip_label = f"{game.t('share_code')}: {game.room_code}"
        chip_width = min(220, max(132, self._fit_font(chip_label, 18, 12, 400).size(chip_label)[0] + 26))
        code_chip = pygame.Rect(card.x + 22, card.bottom - 50, chip_width, 32)
        pygame.draw.rect(self.screen, (21, 42, 40), code_chip, border_radius=12)
        pygame.draw.rect(self.screen, settings.HIGHLIGHT_COLOR, code_chip, width=2, border_radius=12)
        self._blit_text(chip_label, self._fit_font(chip_label, 16, 12, code_chip.width - 16), settings.HIGHLIGHT_COLOR, code_chip.x + 10, code_chip.y + 7)

        notes = [
            game.t("host_note_1", port=settings.NETWORK_PORT),
            game.t("host_note_2"),
            game.t("host_note_3"),
        ]
        y = card.bottom + 28
        for line in notes:
            self._draw_bullet(line, panel.x + 40, y, max_width=panel.width - 80, font=self.briefing_font, line_height=20)
            y += 44

    def _draw_remote_client(self, game) -> None:
        if not game.snapshot_view:
            panel = pygame.Rect(180, 190, settings.WINDOW_WIDTH - 360, 220)
            self._draw_panel(panel, (10, 15, 22), 26)
            self._blit_text(game.t("client_connected"), self.title_font, settings.TEXT_COLOR, panel.x + 32, panel.y + 34)
            self._blit_wrapped_text(game.t("client_waiting"), panel.x + 32, panel.y + 108, panel.width - 64)
            return

        data = self._snapshot_data(game.snapshot_view)
        mode_id = game.snapshot_view.get("mode_id", "lan_duel")
        round_message = game.snapshot_view.get("round_message", game.round_message)
        stats = game.snapshot_view.get("stats", {})
        self._draw_match_scene(data, mode_id, round_message, stats, game)
        self._draw_overlay(game.t("remote_title"), [game.t("remote_1"), game.t("remote_2"), game.t("remote_3")], compact=True)

    def _draw_match_scene(self, data, mode_id: str, round_message: str, stats: dict, game) -> None:
        self._draw_board_shell()
        self._draw_grid()
        self._draw_portals(data["portals"])
        self._draw_obstacles(data["obstacles"])
        self._draw_foods(data["foods"])
        self._draw_snakes(data["snakes"], data["show_ai_paths"])
        self._draw_top_hud(mode_id, game)
        self._draw_sidebar(mode_id, data["snakes"], round_message, stats, game)

    def _draw_top_hud(self, mode_id: str, game) -> None:
        board_rect = pygame.Rect(settings.BOARD_OFFSET_X, settings.BOARD_OFFSET_Y, settings.BOARD_WIDTH, settings.BOARD_HEIGHT)
        hud_rect = pygame.Rect(board_rect.x + 12, board_rect.y + 12, board_rect.width - 24, 52)
        self._draw_panel(hud_rect, (9, 14, 20), 18)

        mode_text = self._mode_label(mode_id, game)
        status_text = game.t("timer_label", value=self._format_time(getattr(game, "time_remaining_ms", 0)))
        speed_level = max(1, (settings.BASE_MOVE_DELAY - game._move_delay()) // 6 + 1)
        difficulty_text = game.t("difficulty_value", value=game.t(f"difficulty_{game.current_difficulty_id}_label"))
        speed_text = game.t("speed_label", value=speed_level)

        left_font = self._fit_font(mode_text, 22, 14, hud_rect.width - 260)
        right_font = self._fit_font("  ·  ".join([status_text, speed_text, difficulty_text]), 15, 11, 250)
        self._blit_text(mode_text, left_font, settings.TEXT_COLOR, hud_rect.x + 18, hud_rect.y + 10)
        self._blit_text("  ·  ".join([status_text, speed_text, difficulty_text]), right_font, settings.SUBTEXT_COLOR, hud_rect.right - 248, hud_rect.y + 18)

    def _draw_board_shell(self) -> None:
        board_rect = pygame.Rect(settings.BOARD_OFFSET_X, settings.BOARD_OFFSET_Y, settings.BOARD_WIDTH, settings.BOARD_HEIGHT)
        panel = board_rect.inflate(24, 24)
        self._draw_panel(panel, (8, 12, 18), 28)
        pygame.draw.rect(self.screen, settings.BOARD_COLOR, board_rect, border_radius=20)
        pygame.draw.rect(self.screen, (48, 64, 90), board_rect, width=2, border_radius=20)

    def _draw_grid(self) -> None:
        for col in range(settings.BOARD_COLS + 1):
            x = settings.BOARD_OFFSET_X + col * settings.GRID_SIZE
            pygame.draw.line(self.screen, settings.GRID_COLOR, (x, settings.BOARD_OFFSET_Y), (x, settings.BOARD_OFFSET_Y + settings.BOARD_HEIGHT), 1)
        for row in range(settings.BOARD_ROWS + 1):
            y = settings.BOARD_OFFSET_Y + row * settings.GRID_SIZE
            pygame.draw.line(self.screen, settings.GRID_COLOR, (settings.BOARD_OFFSET_X, y), (settings.BOARD_OFFSET_X + settings.BOARD_WIDTH, y), 1)

    def _draw_portals(self, portals) -> None:
        for position in portals:
            center = self._cell_center(tuple(position))
            glow = pygame.Surface((38, 38), pygame.SRCALPHA)
            pygame.draw.circle(glow, (104, 132, 255, 80), (19, 19), 17)
            self.screen.blit(glow, (center[0] - 19, center[1] - 19))
            pygame.draw.circle(self.screen, settings.PORTAL_COLOR, center, 10, width=3)
            pygame.draw.circle(self.screen, (206, 216, 255), center, 4)

    def _draw_obstacles(self, obstacles) -> None:
        for position in obstacles:
            rect = self._cell_rect(tuple(position)).inflate(-4, -4)
            pygame.draw.rect(self.screen, settings.OBSTACLE_COLOR, rect, border_radius=7)
            pygame.draw.rect(self.screen, (118, 128, 145), rect, width=1, border_radius=7)

    def _draw_foods(self, foods) -> None:
        for food in foods:
            position = tuple(food["position"]) if isinstance(food, dict) else food.position
            color = tuple(food["color"]) if isinstance(food, dict) else food.color
            rect = self._cell_rect(position).inflate(-6, -6)
            glow = pygame.Surface((42, 42), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 70), (21, 21), 16)
            self.screen.blit(glow, (rect.centerx - 21, rect.centery - 21))
            pygame.draw.ellipse(self.screen, color, rect)
            pygame.draw.ellipse(self.screen, (255, 255, 255), rect, width=2)

    def _draw_snakes(self, snakes, show_paths: bool) -> None:
        for snake in snakes:
            colors = snake["colors"] if isinstance(snake, dict) else snake.colors
            last_path = snake["last_path"] if isinstance(snake, dict) else snake.last_path
            ai_status = snake.get("ai_status", {}) if isinstance(snake, dict) else snake.ai_status
            is_ai = snake["is_ai"] if isinstance(snake, dict) else snake.is_ai
            alive = snake["alive"] if isinstance(snake, dict) else snake.alive

            if is_ai and show_paths and last_path:
                for index, step in enumerate(last_path[:12]):
                    center = self._cell_center(tuple(step))
                    radius = 6 if index == 0 else 4
                    pygame.draw.circle(self.screen, colors["head"], center, radius, width=1)
                    if index > 0:
                        prev = self._cell_center(tuple(last_path[index - 1]))
                        pygame.draw.line(self.screen, colors["head"], prev, center, 1)
                target = ai_status.get("target")
                if target is not None:
                    pygame.draw.circle(self.screen, settings.HIGHLIGHT_COLOR, self._cell_center(tuple(target)), 10, width=2)

            segments = snake["segments"] if isinstance(snake, dict) else snake.segments
            for index, raw_position in enumerate(segments):
                position = tuple(raw_position)
                rect = self._cell_rect(position).inflate(-3, -3)
                color = colors["head"] if index == 0 else colors["body"]
                if not alive:
                    color = tuple(max(channel - 90, 40) for channel in color)
                inner = rect.inflate(-2, -2)
                pygame.draw.rect(self.screen, color, rect, border_radius=9)
                pygame.draw.rect(self.screen, (255, 255, 255), inner, width=1, border_radius=8)

            phase_ticks = snake["phase_ticks"] if isinstance(snake, dict) else snake.phase_ticks
            if phase_ticks > 0 and alive:
                pygame.draw.circle(self.screen, (196, 157, 255), self._cell_center(tuple(segments[0])), 14, width=2)
            if is_ai and ai_status and getattr(ai_status, "get", None) and getattr(self, "_show_ai_status_tags", True):
                self._draw_ai_tag(tuple(segments[0]), ai_status, colors["head"])

    def _draw_sidebar(self, mode_id: str, snakes, round_message: str, stats: dict, game) -> None:
        sidebar_x = settings.BOARD_OFFSET_X + settings.BOARD_WIDTH + 36
        panel = pygame.Rect(sidebar_x, settings.BOARD_OFFSET_Y - 8, settings.SIDEBAR_WIDTH, settings.BOARD_HEIGHT + 16)
        self._draw_panel(panel, (9, 14, 20), 28)

        hud_extras = self._hud_extras(game)
        is_result_view = game.state == "game_over"

        sidebar_title_font = self._fit_font(game.t("sidebar_title"), 26, 18, panel.width - 44)
        mode_font = self._fit_font(self._mode_label(mode_id, game), 18, 14, panel.width - 44)
        self._blit_text(game.t("sidebar_title"), sidebar_title_font, settings.TEXT_COLOR, panel.x + 20, panel.y + 20)
        self._blit_text(self._mode_label(mode_id, game), mode_font, settings.HIGHLIGHT_COLOR, panel.x + 22, panel.y + 56)

        summary_card = pygame.Rect(panel.x + 16, panel.y + 88, panel.width - 32, 76)
        pygame.draw.rect(self.screen, (14, 21, 31), summary_card, border_radius=18)
        pygame.draw.rect(self.screen, (49, 72, 102), summary_card, width=2, border_radius=18)

        beat_info = hud_extras.get("beat") or {}
        combo = hud_extras.get("combo")
        summary_lines = []
        if beat_info:
            beat_line = f"Beat {beat_info.get('beat_in_bar', 1)}/{beat_info.get('beats_per_bar', 4)}"
            if beat_info.get("accuracy"):
                beat_line = f"{beat_line}  ·  {beat_info['accuracy']}"
            summary_lines.append(beat_line)
        if combo is not None:
            summary_lines.append(f"Combo x{combo}")
        event_line = hud_extras.get("event")
        if event_line and not is_result_view:
            summary_lines.append(str(event_line))
        if not summary_lines:
            summary_lines.append(round_message)

        summary_y = summary_card.y + 14
        for line in summary_lines[:2]:
            self._blit_wrapped_text(line, summary_card.x + 14, summary_y, summary_card.width - 24, font=self._load_font(14), line_height=15)
            summary_y += 20

        card_y = summary_card.bottom + 12
        for snake in snakes:
            self._draw_score_card(panel.x + 18, card_y, panel.width - 36, snake, game, hud_extras)
            card_y += 66

        intel_box = pygame.Rect(panel.x + 18, card_y + 2, panel.width - 36, 86 if is_result_view else 106)
        pygame.draw.rect(self.screen, (15, 22, 32), intel_box, border_radius=18)
        pygame.draw.rect(self.screen, (49, 72, 102), intel_box, width=2, border_radius=18)
        self._blit_text(game.t("intel_title"), self.small_font, settings.SUBTEXT_COLOR, intel_box.x + 14, intel_box.y + 12)

        intel_lines = [round_message]
        if event_line and event_line != round_message and not is_result_view:
            intel_lines.append(str(event_line))
        intel_y = intel_box.y + 34
        for line in intel_lines[:1 if is_result_view else 2]:
            self._blit_wrapped_text(line, intel_box.x + 14, intel_y, intel_box.width - 24, font=self._load_font(15), line_height=16)
            intel_y += 24

        stats_box = pygame.Rect(panel.x + 18, intel_box.bottom + 10, panel.width - 36, 86)
        pygame.draw.rect(self.screen, (15, 22, 32), stats_box, border_radius=18)
        pygame.draw.rect(self.screen, (49, 72, 102), stats_box, width=2, border_radius=18)
        self._blit_text(game.t("career_title"), self._fit_font(game.t("career_title"), 22, 16, stats_box.width - 20), settings.TEXT_COLOR, stats_box.x + 14, stats_box.y + 10)
        win_rates = stats.get("win_rates", {})
        stat_lines = [
            game.t("high_score", value=stats.get("high_score", 0)),
            game.t("food_eaten", value=stats.get("food_eaten", stats.get("total_food_eaten", 0))),
            f"P1 {int(win_rates.get('player_one', 0) * 100)}%  ·  P2 {int(win_rates.get('player_two', 0) * 100)}%",
        ]
        stats_y = stats_box.y + 34
        for line in stat_lines[:2 if is_result_view else 3]:
            self._blit_text(line, self._load_font(14), settings.SUBTEXT_COLOR, stats_box.x + 14, stats_y)
            stats_y += 16

        tips = [game.t("tip_pause"), game.t("tip_restart"), game.t("tip_menu")]
        tips_box = pygame.Rect(panel.x + 18, stats_box.bottom + 8, panel.width - 36, 48)
        pygame.draw.rect(self.screen, (14, 20, 30), tips_box, border_radius=16)
        pygame.draw.rect(self.screen, (44, 63, 92), tips_box, width=2, border_radius=16)
        tip_text = "  ·  ".join(tips[:2] if is_result_view else tips[:3])
        tip_font = self._fit_font(tip_text, 13, 10, tips_box.width - 20)
        self._blit_text(tip_text, tip_font, settings.SUBTEXT_COLOR, tips_box.x + 10, tips_box.y + 15)

    def _draw_score_card(self, x: int, y: int, width: int, snake, game, hud_extras: dict) -> None:
        colors = snake["colors"] if isinstance(snake, dict) else snake.colors
        name = snake["name"] if isinstance(snake, dict) else snake.name
        score = snake["score"] if isinstance(snake, dict) else snake.score
        alive = snake["alive"] if isinstance(snake, dict) else snake.alive
        phase_ticks = snake["phase_ticks"] if isinstance(snake, dict) else snake.phase_ticks
        slow_ticks = snake["slow_ticks"] if isinstance(snake, dict) else snake.slow_ticks
        haste_ticks = snake["haste_ticks"] if isinstance(snake, dict) else snake.haste_ticks
        bounce_ticks = snake["bounce_ticks"] if isinstance(snake, dict) else snake.bounce_ticks
        magnet_ticks = snake["magnet_ticks"] if isinstance(snake, dict) else snake.magnet_ticks
        is_ai = snake["is_ai"] if isinstance(snake, dict) else snake.is_ai

        card = pygame.Rect(x, y, width, 62)
        pygame.draw.rect(self.screen, (15, 22, 32), card, border_radius=18)
        pygame.draw.rect(self.screen, (49, 72, 102), card, width=2, border_radius=18)
        accent = pygame.Rect(card.x + 10, card.y + 10, 4, card.height - 20)
        pygame.draw.rect(self.screen, colors["head"], accent, border_radius=4)
        pygame.draw.circle(self.screen, colors["head"], (card.x + 28, card.y + 20), 8)
        pygame.draw.circle(self.screen, colors["body"], (card.x + 28, card.y + 38), 5)

        name_font = self._fit_font(name, 19, 13, width - 128)
        self._blit_text(name, name_font, settings.TEXT_COLOR, card.x + 46, card.y + 8)

        badge_parts = [str(score)]
        if is_ai:
            badge_parts.append("AI")
        if phase_ticks > 0:
            badge_parts.append(f"P{phase_ticks}")
        if slow_ticks > 0:
            badge_parts.append(f"S{slow_ticks}")
        if haste_ticks > 0:
            badge_parts.append(f"H{haste_ticks}")
        if bounce_ticks > 0:
            badge_parts.append(f"B{bounce_ticks}")
        if magnet_ticks > 0:
            badge_parts.append(f"M{magnet_ticks}")
        if not alive:
            badge_parts.append("OUT")
        badge_text = "  ·  ".join(badge_parts[:4])
        self._blit_text(badge_text, self._load_font(13), settings.SUBTEXT_COLOR, card.x + 46, card.y + 31)

        skill_points = hud_extras.get("skill_points", {}).get(name)
        combo = hud_extras.get("combo")
        extra_parts = []
        if skill_points is not None:
            extra_parts.append(f"SP {skill_points}")
        if combo is not None and not is_ai:
            extra_parts.append(f"Combo x{combo}")
        ai_info = hud_extras.get("ai", {}).get(name, {})
        if is_ai and ai_info.get("risk"):
            extra_parts.append(ai_info["risk"].upper())
        if extra_parts:
            extra_text = "  ·  ".join(part for part in extra_parts if part)
            extra_font = self._fit_font(extra_text, 11, 9, 104)
            self._blit_text(extra_text, extra_font, settings.SUBTEXT_COLOR, card.right - 108, card.y + 12)

    def _draw_overlay(
        self,
        title: str,
        lines: list[str],
        compact: bool = False,
        actions: list[str] | None = None,
        selected_index: int = 0,
    ) -> None:
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 8, 12, 145))
        self.screen.blit(overlay, (0, 0))

        height = 170 if compact else 252
        panel = pygame.Rect(
            settings.BOARD_OFFSET_X + 54,
            settings.BOARD_OFFSET_Y + (settings.BOARD_HEIGHT - height) // 2,
            settings.BOARD_WIDTH - 108,
            height,
        )
        self._draw_panel(panel, (9, 14, 20), 26)
        overlay_title_font = self._fit_font(title, 34, 22, panel.width - 64)
        self._blit_text(title, overlay_title_font, settings.TEXT_COLOR, panel.x + 28, panel.y + 24)
        y = panel.y + 76
        for line in lines[:3]:
            self._blit_wrapped_text(line, panel.x + 28, y, panel.width - 56, font=self.small_font, line_height=24)
            y += 28
        if actions:
            button_y = panel.bottom - 52
            gap = 12
            button_width = (panel.width - 56 - gap * (len(actions) - 1)) // len(actions)
            for index, action in enumerate(actions):
                rect = pygame.Rect(panel.x + 28 + index * (button_width + gap), button_y, button_width, 34)
                active = index == selected_index
                fill = (22, 46, 42) if active else (18, 24, 34)
                border = settings.HIGHLIGHT_COLOR if active else (49, 72, 102)
                pygame.draw.rect(self.screen, fill, rect, border_radius=12)
                pygame.draw.rect(self.screen, border, rect, width=2, border_radius=12)
                font = self._fit_font(action, 16, 12, rect.width - 12)
                self._blit_text(action, font, settings.TEXT_COLOR, rect.x + 10, rect.y + 8)

    def _draw_status_chip(
        self,
        x: int,
        y: int,
        width: int,
        text: str,
        text_color: tuple[int, int, int],
        fill: tuple[int, int, int],
        border: tuple[int, int, int] | None = None,
    ) -> None:
        rect = pygame.Rect(x, y, width, 38)
        pygame.draw.rect(self.screen, fill, rect, border_radius=14)
        pygame.draw.rect(
            self.screen,
            border or settings.HIGHLIGHT_COLOR,
            rect,
            width=2,
            border_radius=14,
        )
        font = self._fit_font(text, 22, 16, width - 28)
        self._blit_text(text, font, text_color, rect.x + 18, rect.y + 8)
        glow = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
        base_glow = border or settings.HIGHLIGHT_COLOR
        glow_color = (base_glow[0], base_glow[1], base_glow[2], 28)
        pygame.draw.rect(glow, glow_color, pygame.Rect(8, 8, rect.width, rect.height), border_radius=18)
        self.screen.blit(glow, (rect.x - 8, rect.y - 8))

    def _draw_panel(self, rect: pygame.Rect, color: tuple[int, int, int], radius: int) -> None:
        shadow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 65), pygame.Rect(12, 14, rect.width, rect.height), border_radius=radius + 4)
        self.screen.blit(shadow, (rect.x - 12, rect.y - 12))
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        pygame.draw.rect(self.screen, (42, 58, 82), rect, width=2, border_radius=radius)
        inset = rect.inflate(-10, -10)
        pygame.draw.rect(self.screen, (18, 24, 34), inset, width=1, border_radius=max(8, radius - 6))

    def _draw_bullet(
        self,
        text: str,
        x: int,
        y: int,
        max_width: int = 220,
        font: pygame.font.Font | None = None,
        line_height: int = 24,
    ) -> None:
        pygame.draw.circle(self.screen, settings.HIGHLIGHT_COLOR, (x, y + 10), 4)
        self._blit_wrapped_text(text, x + 14, y, max_width, font=font, line_height=line_height)

    def _local_data(self, game) -> dict:
        return {
            "portals": list(game.portals) if game.portals else [],
            "obstacles": list(game.obstacles),
            "foods": game.foods,
            "snakes": game.snakes,
            "show_ai_paths": game.show_ai_paths,
        }

    def _snapshot_data(self, snapshot: dict) -> dict:
        return {
            "portals": snapshot.get("portals", []),
            "obstacles": snapshot.get("obstacles", []),
            "foods": snapshot.get("foods", []),
            "snakes": snapshot.get("snakes", []),
            "show_ai_paths": snapshot.get("show_ai_paths", False),
        }

    def _hud_extras(self, game) -> dict:
        if getattr(game, "snapshot_view", None):
            return game.snapshot_view.get("hud_extras", {})
        if hasattr(game, "_hud_extras"):
            return game._hud_extras()
        return {}

    def _draw_ai_tag(self, head_position: tuple[int, int], ai_status: dict, color: tuple[int, int, int]) -> None:
        rect = self._cell_rect(head_position).move(4, -18)
        tag = pygame.Rect(rect.x, rect.y, 58, 14)
        pygame.draw.rect(self.screen, (10, 14, 22), tag, border_radius=8)
        pygame.draw.rect(self.screen, color, tag, width=1, border_radius=8)
        mode = str(ai_status.get("mode", "AI")).upper()
        risk = str(ai_status.get("risk", "")).upper()
        label = risk or mode
        self._blit_text(label[:8], self._load_font(10), color, tag.x + 5, tag.y + 2)

    def _mode_label(self, mode_id: str, game) -> str:
        return game.t(f"mode_{mode_id}_label")

    def _mode_description(self, mode_id: str, game) -> str:
        return game.t(f"mode_{mode_id}_desc")

    def _fit_font(self, text: str, start_size: int, min_size: int, max_width: int) -> pygame.font.Font:
        size = start_size
        while size > min_size:
            font = self._load_font(size)
            if font.size(text)[0] <= max_width:
                return font
            size -= 2
        return self._load_font(min_size)

    def _format_time(self, time_remaining_ms: int) -> str:
        total_seconds = max(0, time_remaining_ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _cell_rect(self, position: tuple[int, int]) -> pygame.Rect:
        return pygame.Rect(settings.BOARD_OFFSET_X + position[0] * settings.GRID_SIZE, settings.BOARD_OFFSET_Y + position[1] * settings.GRID_SIZE, settings.GRID_SIZE, settings.GRID_SIZE)

    def _cell_center(self, position: tuple[int, int]) -> tuple[int, int]:
        rect = self._cell_rect(position)
        return rect.centerx, rect.centery

    def _blit_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], x: int, y: int) -> None:
        self.screen.blit(font.render(text, True, color), (x, y))

    def _blit_wrapped_text(
        self,
        text: str,
        x: int,
        y: int,
        max_width: int,
        color: tuple[int, int, int] = settings.SUBTEXT_COLOR,
        font: pygame.font.Font | None = None,
        line_height: int = 24,
    ) -> None:
        active_font = font or self.small_font
        lines = self._wrap_text(text, max_width, active_font)
        current_y = y
        for line in lines:
            self._blit_text(line, active_font, color, x, current_y)
            current_y += line_height

    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> list[str]:
        if " " in text:
            return self._wrap_by_words(text, max_width, font)
        return self._wrap_by_characters(text, max_width, font)

    def _wrap_by_words(self, text: str, max_width: int, font: pygame.font.Font) -> list[str]:
        words = text.split()
        lines: list[str] = []
        line = ""
        for word in words:
            trial = f"{line} {word}".strip()
            width, _ = font.size(trial)
            if width <= max_width:
                line = trial
            else:
                if line:
                    lines.append(line)
                if font.size(word)[0] > max_width:
                    lines.extend(self._wrap_by_characters(word, max_width, font))
                    line = ""
                else:
                    line = word
        if line:
            lines.append(line)
        return lines

    def _wrap_by_characters(self, text: str, max_width: int, font: pygame.font.Font) -> list[str]:
        lines: list[str] = []
        line = ""
        for char in text:
            trial = f"{line}{char}"
            width, _ = font.size(trial)
            if width <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = char
        if line:
            lines.append(line)
        return lines
