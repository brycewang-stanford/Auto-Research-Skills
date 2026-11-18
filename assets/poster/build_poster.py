#!/usr/bin/env python3
"""Build the "Free Research Crew" poster (CN + EN) as SVG, and PNG via headless Chrome.

Same canvas (1774x887) and storybook palette as the README covers readme_cn.png /
readme.png: a greenhouse library, a parchment title scroll, and framed parchment
cards — here one card per crew role.

    python3 assets/poster/build_poster.py          # writes SVG + PNG next to this file
    python3 assets/poster/build_poster.py --svg-only
"""
from __future__ import annotations

import argparse
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 1774, 887
HERE = Path(__file__).resolve().parent

INK = "#3a2a1a"
PAPER = "#fbf5e4"
CREAM = "#f3e8cc"
TEAL = "#4f8f86"
TEAL_L = "#8cc3b5"
AMBER = "#d39a3a"
RUST = "#b8643a"
GREEN = "#6f9a45"
GREEN_D = "#4d7431"
BLUE = "#4a7aa0"
RED = "#b8463a"
BROWN = "#7a5232"
SLATE = "#3d6a8a"

TEXT = {
    "cn": {
        "font": "'PingFang SC','Hiragino Sans GB','Noto Sans CJK SC',sans-serif",
        "title": "免费助研团",
        "title_size": 104,
        "subtitle": "一支 AI 助研团队，把你的研究问题做成一篇完整论文",
        "sub_size": 31,
        "stats": "免费使用 · 自由修改 · 无需新环境 ｜ 10 个角色 · 4 道人工关卡",
        "stats_size": 25,
        "paper": "论文",
        "gates": ["① 问题", "② 设计", "③ 结果", "④ 投稿"],
        "gate_size": 22,
        "label_size": 30,
        "tag_size": 19,
        "roles": {
            "pi": ("课题负责人 PI", "你来拍板，四道关卡"),
            "scout": ("文献侦察", "每条引用都核验"),
            "designer": ("研究设计", "先锁设计，再看结果"),
            "data": ("数据助研", "数据来源可追溯"),
            "econ": ("计量助研", "识别 · 估计 · 稳健性"),
            "exp": ("实验助研", "随机种子 + 公平基线"),
            "figures": ("图表助研", "图表全由脚本生成"),
            "writer": ("写作助研", "只写有记录的结论"),
            "replicator": ("复现助研", "从零重跑一遍"),
            "reviewer": ("审稿人", "专挑毛病，永不松口"),
        },
    },
    "en": {
        "font": "'Avenir Next','Helvetica Neue',Arial,sans-serif",
        "title": "Free Research Crew",
        "title_size": 72,
        "subtitle": "AI research assistants that turn your question into a paper",
        "sub_size": 29,
        "stats": "Free to use · Free to fork · No new runtime  |  10 roles · 4 human gates",
        "stats_size": 23,
        "paper": "Paper",
        "gates": ["1 Question", "2 Design", "3 Results", "4 Submit"],
        "gate_size": 19,
        "label_size": 26,
        "tag_size": 17,
        "roles": {
            "pi": ("PI (you)", "You approve every gate"),
            "scout": ("Scout", "Every citation verified"),
            "designer": ("Designer", "Design locked before results"),
            "data": ("Data RA", "Every dataset sourced"),
            "econ": ("Econometrician", "Identification & robustness"),
            "exp": ("Experimenter", "Seeds & fair baselines"),
            "figures": ("Figures RA", "Every figure from a script"),
            "writer": ("Writer", "Only recorded claims"),
            "replicator": ("Replicator", "Reruns it all from scratch"),
            "reviewer": ("Reviewer", "Never lets up"),
        },
    },
}

# ---------------------------------------------------------------- icons
# Each icon is drawn in a box centred on (0, 0), roughly x -100..100, y -62..62.
S = f'stroke="{INK}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'


def icon_pi() -> str:
    rows = "".join(
        f'<rect x="-40" y="{-30 + i * 24}" width="14" height="14" rx="2" fill="{PAPER}" {S}/>'
        f'<path d="M-37 {-23 + i * 24} l4 5 l8 -10" fill="none" stroke="{GREEN_D}" stroke-width="3.5"/>'
        f'<line x1="-18" y1="{-23 + i * 24}" x2="20" y2="{-23 + i * 24}" {S} stroke-width="2.5"/>'
        for i in range(3)
    )
    return (
        f'<rect x="-52" y="-56" width="104" height="118" rx="8" fill="{BROWN}" {S}/>'
        f'<rect x="-44" y="-46" width="88" height="100" rx="4" fill="{PAPER}" {S}/>'
        f'<rect x="-20" y="-62" width="40" height="16" rx="4" fill="#b9b2a2" {S}/>'
        + rows
        + f'<g transform="translate(62 30) rotate(-14)"><circle r="30" fill="none" stroke="{RED}" stroke-width="5"/>'
        f'<circle r="23" fill="none" stroke="{RED}" stroke-width="2"/>'
        f'<path d="M-12 0 l8 9 l16 -18" fill="none" stroke="{RED}" stroke-width="6" stroke-linecap="round"/></g>'
    )


def icon_scout() -> str:
    return (
        f'<path d="M-95 -30 Q-55 -45 -10 -30 L-10 45 Q-55 30 -95 45 Z" fill="{PAPER}" {S}/>'
        f'<path d="M-10 -30 Q35 -45 75 -30 L75 45 Q35 30 -10 45 Z" fill="{CREAM}" {S}/>'
        + "".join(
            f'<line x1="-82" y1="{-18 + i * 12}" x2="-24" y2="{-20 + i * 12}" stroke="{INK}" stroke-width="2" opacity=".55"/>'
            for i in range(5)
        )
        + f'<line x1="40" y1="20" x2="78" y2="58" {S} stroke-width="11" stroke="{BROWN}"/>'
        f'<circle cx="22" cy="2" r="30" fill="{TEAL_L}" fill-opacity=".55" {S} stroke-width="6"/>'
        f'<path d="M82 -50 L68 -30 M82 -50 L100 -36 M68 -30 L100 -36" stroke="{INK}" stroke-width="2"/>'
        f'<circle cx="82" cy="-50" r="7" fill="{AMBER}" {S}/><circle cx="68" cy="-30" r="6" fill="{TEAL}" {S}/>'
        f'<circle cx="100" cy="-36" r="6" fill="{RUST}" {S}/>'
    )


def icon_designer() -> str:
    grid = "".join(
        f'<line x1="{-80 + i * 20}" y1="-48" x2="{-80 + i * 20}" y2="48" stroke="#fff" stroke-width="1" opacity=".35"/>'
        for i in range(9)
    ) + "".join(
        f'<line x1="-88" y1="{-40 + i * 20}" x2="80" y2="{-40 + i * 20}" stroke="#fff" stroke-width="1" opacity=".35"/>'
        for i in range(5)
    )
    box = lambda x, y, c: f'<rect x="{x}" y="{y}" width="40" height="22" rx="4" fill="{c}" stroke="#fff" stroke-width="2.5"/>'
    return (
        f'<rect x="-92" y="-52" width="176" height="104" rx="6" fill="{BLUE}" {S}/>'
        + grid
        + box(-76, -36, TEAL) + box(-76, 14, AMBER) + box(-12, -11, RUST) + box(44, -11, GREEN)
        + '<path d="M-36 -25 L-12 0 M-36 25 L-12 0 M28 0 L44 0" stroke="#fff" stroke-width="3" fill="none"/>'
        + f'<g transform="translate(70 28) rotate(-40)"><rect x="-6" y="-60" width="13" height="78" fill="{AMBER}" {S}/>'
        f'<path d="M-6 18 L0.5 34 L7 18 Z" fill="{CREAM}" {S}/><rect x="-6" y="-68" width="13" height="10" fill="{RED}" {S}/></g>'
    )


def icon_data() -> str:
    def cyl(x: float, y: float, c: str) -> str:
        return (
            f'<path d="M{x - 30} {y} v30 a30 10 0 0 0 60 0 v-30" fill="{c}" {S}/>'
            f'<ellipse cx="{x}" cy="{y}" rx="30" ry="10" fill="{TEAL_L}" {S}/>'
        )

    sheet = "".join(
        f'<line x1="22" y1="{-34 + i * 16}" x2="92" y2="{-34 + i * 16}" stroke="{INK}" stroke-width="1.8"/>'
        for i in range(6)
    )
    return (
        cyl(-50, 22, TEAL) + cyl(-50, -8, TEAL) + cyl(-50, -38, TEAL)
        + f'<rect x="22" y="-50" width="70" height="96" rx="4" fill="{PAPER}" {S}/>'
        + sheet
        + f'<line x1="46" y1="-50" x2="46" y2="46" stroke="{INK}" stroke-width="1.8"/>'
        f'<rect x="22" y="-50" width="70" height="16" fill="{AMBER}" {S}/>'
        f'<path d="M-8 -6 h22 m-7 -7 l7 7 l-7 7" fill="none" {S}/>'
    )


def icon_econ() -> str:
    rnd = random.Random(7)
    dots = ""
    for _ in range(22):
        x = rnd.uniform(-70, 80)
        y = 30 - 0.5 * (x + 70) + rnd.uniform(-16, 16)
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{TEAL}" stroke="{INK}" stroke-width="1.5"/>'
    return (
        f'<rect x="-92" y="-56" width="184" height="114" rx="6" fill="{PAPER}" {S}/>'
        f'<path d="M-76 -46 V44 H84" fill="none" {S}/>'
        f'<path d="M-70 18 L80 -60 L80 -40 L-70 44 Z" fill="{AMBER}" opacity=".3"/>'
        + dots
        + f'<line x1="-70" y1="31" x2="80" y2="-50" stroke="{RED}" stroke-width="4.5" stroke-linecap="round"/>'
        f'<text x="40" y="34" font-family="Georgia,serif" font-style="italic" font-size="24" fill="{INK}">β̂</text>'
    )


def icon_exp() -> str:
    def flask(x: float, s: float, liquid: str) -> str:
        return (
            f'<g transform="translate({x} 0) scale({s})">'
            f'<path d="M-12 -50 V-12 L-40 45 Q-42 55 -30 55 H30 Q42 55 40 45 L12 -12 V-50 Z" fill="#eef5f2" {S}/>'
            f'<path d="M-27 18 L27 18 L40 45 Q42 55 30 55 H-30 Q-42 55 -40 45 Z" fill="{liquid}" {S}/>'
            f'<rect x="-16" y="-58" width="32" height="9" rx="3" fill="{CREAM}" {S}/>'
            f'<circle cx="-6" cy="30" r="4" fill="#fff" opacity=".8"/><circle cx="8" cy="40" r="3" fill="#fff" opacity=".8"/>'
            "</g>"
        )

    return (
        flask(-58, 0.85, TEAL) + flask(4, 1.05, AMBER) + flask(66, 0.8, GREEN)
        + f'<circle cx="10" cy="-74" r="5" fill="none" {S} stroke-width="2"/><circle cx="20" cy="-88" r="3.5" fill="none" {S} stroke-width="2"/>'
    )


def icon_figures() -> str:
    bars = "".join(
        f'<rect x="{-80 + i * 24}" y="{40 - h}" width="16" height="{h}" fill="{c}" {S} stroke-width="2.5"/>'
        for i, (h, c) in enumerate([(30, TEAL), (52, AMBER), (40, TEAL), (72, RUST), (60, TEAL)])
    )
    return (
        f'<rect x="-94" y="-56" width="124" height="112" rx="6" fill="{PAPER}" {S}/>'
        f'<path d="M-86 -44 V42 H22" fill="none" {S}/>'
        + bars
        + f'<g transform="translate(64 -4)"><circle r="34" fill="{TEAL}" {S}/>'
        f'<path d="M0 0 V-34 A34 34 0 0 1 32 -11 Z" fill="{AMBER}" {S}/>'
        f'<path d="M0 0 L32 -11 A34 34 0 0 1 14 31 Z" fill="{RUST}" {S}/></g>'
    )


def icon_writer() -> str:
    lines = "".join(
        f'<line x1="-74" y1="{-30 + i * 13}" x2="{(-4 if i % 3 == 2 else 20)}" y2="{-30 + i * 13}" stroke="{INK}" stroke-width="2" opacity=".55"/>'
        for i in range(7)
    )
    return (
        f'<rect x="-88" y="-56" width="124" height="114" rx="4" fill="{PAPER}" {S}/>'
        f'<rect x="-74" y="-46" width="60" height="8" fill="{INK}" opacity=".75"/>'
        + lines
        + f'<path d="M70 -62 Q40 -40 18 30 Q52 0 84 -52 Z" fill="{CREAM}" {S}/>'
        f'<path d="M70 -62 Q50 -30 18 30" fill="none" {S} stroke-width="2"/>'
        f'<path d="M50 40 h40 v-14 q0 -10 -10 -10 h-20 q-10 0 -10 10 Z" fill="{SLATE}" {S}/>'
        f'<path d="M18 30 q-6 10 -14 12" fill="none" stroke="{INK}" stroke-width="2.5"/>'
    )


def icon_replicator() -> str:
    return (
        f'<path d="M-60 -10 L0 -36 L60 -10 L60 46 L0 62 L-60 46 Z" fill="#c99a61" {S}/>'
        f'<path d="M-60 -10 L0 14 L60 -10 M0 14 V62" fill="none" {S}/>'
        f'<g transform="translate(0 -40)" fill="none" stroke="{TEAL}" stroke-width="8" stroke-linecap="round">'
        f'<path d="M-34 -6 A36 26 0 0 1 30 -14"/><path d="M34 6 A36 26 0 0 1 -30 14"/></g>'
        f'<path d="M22 -66 L36 -54 L18 -48 Z" fill="{TEAL}" {S} stroke-width="2"/>'
        f'<path d="M-22 -14 L-36 -26 L-18 -32 Z" fill="{TEAL}" {S} stroke-width="2"/>'
        f'<circle cx="0" cy="-40" r="12" fill="{GREEN}" {S}/>'
        f'<path d="M-6 -40 l4 5 l8 -10" fill="none" stroke="#fff" stroke-width="3"/>'
    )


def icon_reviewer() -> str:
    lines = "".join(
        f'<line x1="-76" y1="{-32 + i * 14}" x2="4" y2="{-32 + i * 14}" stroke="{INK}" stroke-width="2" opacity=".5"/>'
        for i in range(7)
    )
    return (
        f'<rect x="-90" y="-56" width="110" height="116" rx="4" fill="{PAPER}" {S}/>'
        + lines
        + f'<path d="M-78 -14 h70" stroke="{RED}" stroke-width="3"/><path d="M-60 12 q20 8 50 -2" fill="none" stroke="{RED}" stroke-width="3"/>'
        f'<path d="M-30 34 l14 14 m0 -14 l-14 14" stroke="{RED}" stroke-width="4"/>'
        f'<g transform="translate(26 22) rotate(-35)"><rect x="-7" y="-70" width="14" height="74" rx="3" fill="{RED}" {S}/>'
        f'<path d="M-7 4 L0 20 L7 4 Z" fill="{CREAM}" {S}/></g>'
        f'<path d="M48 -60 h46 q10 0 10 10 v34 q0 10 -10 10 h-24 l-12 12 v-12 h-10 q-10 0 -10 -10 v-34 q0 -10 10 -10 Z" fill="{AMBER}" {S}/>'
        f'<rect x="66" y="-52" width="8" height="24" rx="3" fill="{INK}"/><circle cx="70" cy="-19" r="4.5" fill="{INK}"/>'
    )


ICONS = {
    "pi": icon_pi, "scout": icon_scout, "designer": icon_designer, "data": icon_data,
    "econ": icon_econ, "exp": icon_exp, "figures": icon_figures, "writer": icon_writer,
    "replicator": icon_replicator, "reviewer": icon_reviewer,
}

# ---------------------------------------------------------------- pieces


def leaf(x: float, y: float, ang: float, size: float, color: str) -> str:
    return (
        f'<path transform="translate({x:.1f} {y:.1f}) rotate({ang:.0f}) scale({size:.2f})" '
        f'd="M0 0 Q8 -10 22 0 Q8 10 0 0 Z" fill="{color}" stroke="{GREEN_D}" stroke-width="1"/>'
    )


def vine(rnd: random.Random, pts: list[tuple[float, float]], n: int) -> str:
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    out = f'<path d="{d}" fill="none" stroke="{GREEN_D}" stroke-width="3" opacity=".8"/>'
    for _ in range(n):
        i = rnd.randrange(len(pts) - 1)
        t = rnd.random()
        x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
        y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
        out += leaf(x, y, rnd.uniform(0, 360), rnd.uniform(0.7, 1.4), rnd.choice([GREEN, "#86b255", "#5d8a37"]))
    return out


def bookshelf(rnd: random.Random, x0: float, x1: float) -> str:
    out = f'<rect x="{x0}" y="0" width="{x1 - x0}" height="{H}" fill="#4a3220"/>'
    colors = ["#7a3b2e", "#2f5d58", "#8a6a2f", "#3c4f6b", "#5f7a3a", "#9a5a35", "#6b4a6b", "#c7a46a"]
    for sy in range(150, H + 1, 150):
        x = x0 + 6
        while x < x1 - 8:
            w = rnd.uniform(12, 24)
            h = rnd.uniform(86, 126)
            out += f'<rect x="{x:.1f}" y="{sy - h:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{rnd.choice(colors)}" stroke="#2a1b10" stroke-width="1.5"/>'
            x += w + rnd.uniform(0.5, 3)
        out += f'<rect x="{x0}" y="{sy}" width="{x1 - x0}" height="12" fill="#6b4a2c" stroke="#2a1b10" stroke-width="2"/>'
    return out


def greenhouse(rnd: random.Random) -> str:
    x0, x1, y1 = 392, 1382, 700
    out = (
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#eef3d6"/><stop offset=".55" stop-color="#cfe0a6"/>'
        '<stop offset="1" stop-color="#8fb36a"/></linearGradient>'
        '<radialGradient id="glow" cx=".5" cy=".42" r=".55"><stop offset="0" stop-color="#fffbe6" stop-opacity=".85"/>'
        '<stop offset="1" stop-color="#fffbe6" stop-opacity="0"/></radialGradient></defs>'
        f'<rect x="{x0}" y="0" width="{x1 - x0}" height="{y1}" fill="url(#sky)"/>'
    )
    # distant foliage
    for _ in range(70):
        cx = rnd.uniform(x0, x1)
        cy = rnd.uniform(330, 600)
        r = rnd.uniform(30, 70)
        out += f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{rnd.choice(["#9cc06f", "#86ad5c", "#b3cf86", "#749b4e"])}" opacity=".75"/>'
    out += f'<rect x="{x0}" y="0" width="{x1 - x0}" height="{y1}" fill="url(#glow)"/>'
    # glass mullions and arches
    for x in range(x0 + 40, x1, 66):
        out += f'<line x1="{x}" y1="230" x2="{x}" y2="{y1}" stroke="#6e6247" stroke-width="4" opacity=".75"/>'
    for y in (330, 470):
        out += f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#6e6247" stroke-width="4" opacity=".6"/>'
    for cx in (560, 887, 1214):
        out += f'<path d="M{cx - 160} 300 Q{cx} 120 {cx + 160} 300" fill="none" stroke="#6e6247" stroke-width="7" opacity=".8"/>'
    return out


def lamp(x: float) -> str:
    return (
        f'<line x1="{x}" y1="240" x2="{x}" y2="282" stroke="{INK}" stroke-width="3"/>'
        f'<path d="M{x - 28} 310 Q{x} 270 {x + 28} 310 Z" fill="#3b4a40" stroke="{INK}" stroke-width="3"/>'
        f'<ellipse cx="{x}" cy="312" rx="12" ry="5" fill="#ffe9a8"/>'
        f'<path d="M{x - 26} 312 L{x - 70} 420 L{x + 70} 420 L{x + 26} 312 Z" fill="#fff3c4" opacity=".22"/>'
    )


def robot(x: float, y: float, s: float, held: str, look: float = 0) -> str:
    """A friendly crew robot, feet at (x, y)."""
    held_svg = {
        "pen": f'<g transform="translate(46 -88) rotate(25)"><rect x="-4" y="-34" width="8" height="40" fill="{AMBER}" {S} stroke-width="2"/></g>',
        "lens": f'<g transform="translate(-52 -96)"><line x1="8" y1="8" x2="22" y2="22" stroke="{BROWN}" stroke-width="7" stroke-linecap="round"/><circle r="14" fill="{TEAL_L}" fill-opacity=".6" {S} stroke-width="4"/></g>',
        "flask": f'<g transform="translate(54 -100) scale(.45)"><path d="M-12 -50 V-12 L-40 45 Q-42 55 -30 55 H30 Q42 55 40 45 L12 -12 V-50 Z" fill="#eef5f2" {S} stroke-width="5"/><path d="M-27 18 L27 18 L40 45 Q42 55 30 55 H-30 Q-42 55 -40 45 Z" fill="{AMBER}"/></g>',
        "chart": f'<g transform="translate(-56 -110)"><rect x="-20" y="-16" width="40" height="32" rx="3" fill="{PAPER}" {S} stroke-width="2"/><path d="M-14 10 L-4 0 L4 6 L14 -10" fill="none" stroke="{RED}" stroke-width="3"/></g>',
    }[held]
    return (
        f'<g transform="translate({x} {y}) scale({s})">'
        f'<ellipse cx="0" cy="0" rx="58" ry="10" fill="#000" opacity=".15"/>'
        # body
        f'<rect x="-44" y="-112" width="88" height="96" rx="30" fill="#f1ead8" {S} stroke-width="4"/>'
        f'<circle cx="0" cy="-66" r="17" fill="{TEAL}" {S}/><circle cx="0" cy="-66" r="8" fill="#bff0e2"/>'
        # arms
        f'<rect x="-66" y="-104" width="22" height="52" rx="11" fill="#e2d8c0" {S} transform="rotate(18 -55 -104)"/>'
        f'<rect x="44" y="-104" width="22" height="52" rx="11" fill="#e2d8c0" {S} transform="rotate(-18 55 -104)"/>'
        + held_svg
        # neck + head
        + f'<rect x="-12" y="-128" width="24" height="18" fill="#9a9384" {S}/>'
        f'<g transform="rotate({look} 0 -170)">'
        f'<line x1="0" y1="-222" x2="0" y2="-242" {S}/><circle cx="0" cy="-246" r="7" fill="{AMBER}" {S}/>'
        f'<circle cx="-60" cy="-172" r="14" fill="{TEAL}" {S}/><circle cx="60" cy="-172" r="14" fill="{TEAL}" {S}/>'
        f'<rect x="-58" y="-222" width="116" height="96" rx="38" fill="#f6f0e0" {S} stroke-width="4"/>'
        f'<rect x="-44" y="-208" width="88" height="66" rx="26" fill="#1f2a2e" {S}/>'
        f'<path d="M-26 -178 q8 -12 16 0 M10 -178 q8 -12 16 0" fill="none" stroke="#7fe6cf" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M-12 -164 q12 10 24 0" fill="none" stroke="#7fe6cf" stroke-width="4.5" stroke-linecap="round"/>'
        "</g></g>"
    )


def scene(t: dict) -> str:
    out = lamp(560) + lamp(1214)
    # robots behind the desk
    out += robot(612, 572, 0.86, "lens", -6)
    out += robot(774, 562, 0.95, "chart", -3)
    out += robot(1000, 562, 0.95, "flask", 3)
    out += robot(1162, 572, 0.86, "pen", 6)
    # desk
    out += (
        f'<path d="M420 560 H1354 L1380 600 H394 Z" fill="#a8743f" {S} stroke-width="4"/>'
        f'<rect x="394" y="600" width="986" height="60" fill="#8a5a2b" {S} stroke-width="4"/>'
    )
    # the paper on the desk
    out += (
        f'<g transform="translate(887 548)">'
        f'<path d="M-120 12 L-110 -46 Q-55 -58 0 -44 L0 16 Q-60 4 -120 12 Z" fill="{PAPER}" {S}/>'
        f'<path d="M120 12 L110 -46 Q55 -58 0 -44 L0 16 Q60 4 120 12 Z" fill="{PAPER}" {S}/>'
        f'<text x="-56" y="-14" text-anchor="middle" font-family="{t["font"]}" font-weight="700" font-size="22" fill="{INK}">{t["paper"]}</text>'
        + "".join(
            f'<line x1="18" y1="{-34 + i * 9}" x2="98" y2="{-36 + i * 9}" stroke="{INK}" stroke-width="2" opacity=".5"/>'
            for i in range(5)
        )
        + f'<path d="M-96 2 h80" stroke="{INK}" stroke-width="2" opacity=".5"/>'
        "</g>"
    )
    # desk props
    out += (
        f'<g transform="translate(470 560)"><rect x="-26" y="-34" width="52" height="34" rx="4" fill="{TEAL}" {S}/>'
        f'<rect x="-24" y="-52" width="48" height="18" rx="3" fill="{RUST}" {S}/><rect x="-28" y="-66" width="56" height="14" rx="3" fill="{AMBER}" {S}/></g>'
        f'<g transform="translate(1306 560)"><path d="M-20 0 h40 l-6 -40 h-28 Z" fill="{RUST}" {S}/>'
        + vine(random.Random(3), [(0, -40), (-16, -74), (6, -104)], 9)
        + "</g>"
    )
    # the four human gates on the desk front
    gx = 887 - 2 * 230 + 115
    for i, g in enumerate(t["gates"]):
        x = gx + i * 230
        out += (
            f'<rect x="{x - 92}" y="610" width="184" height="40" rx="10" fill="{CREAM}" {S}/>'
            f'<text x="{x}" y="638" text-anchor="middle" font-family="{t["font"]}" font-weight="700" font-size="{t["gate_size"]}" fill="{INK}">{g}</text>'
        )
        if i < 3:
            out += f'<path d="M{x + 98} 630 h26 m-9 -8 l9 8 l-9 8" fill="none" stroke="{CREAM}" stroke-width="4" stroke-linecap="round"/>'
    return out


def card(x: float, y: float, w: float, h: float, role: str, color: str, t: dict) -> str:
    label, tag = t["roles"][role]
    icon_scale = min((w - 50) / 210, (h - 110) / 130)
    icon_cy = y + 18 + (h - 108) / 2
    bw = min(w - 30, max(150, len(label) * t["label_size"] * (1.0 if t is TEXT["cn"] else 0.62) + 40))
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="#d9b67a" stroke="#4a2e16" stroke-width="5"/>'
        f'<rect x="{x + 9}" y="{y + 9}" width="{w - 18}" height="{h - 18}" rx="14" fill="url(#parch)" stroke="#a87a44" stroke-width="2.5"/>'
        + "".join(
            f'<circle cx="{cx}" cy="{cy}" r="7" fill="#c99a52" stroke="#4a2e16" stroke-width="2"/>'
            for cx, cy in ((x + 9, y + 9), (x + w - 9, y + 9), (x + 9, y + h - 9), (x + w - 9, y + h - 9))
        )
        + f'<g transform="translate({x + w / 2} {icon_cy}) scale({icon_scale:.3f})">{ICONS[role]()}</g>'
        f'<text x="{x + w / 2}" y="{y + h - 52}" text-anchor="middle" font-family="{t["font"]}" font-weight="600" '
        f'font-size="{t["tag_size"]}" fill="#5a3a1c">{tag}</text>'
        f'<rect x="{x + w / 2 - bw / 2}" y="{y + h - 40}" width="{bw}" height="50" rx="10" fill="{color}" stroke="#2c1d10" stroke-width="3.5"/>'
        f'<text x="{x + w / 2}" y="{y + h - 4}" text-anchor="middle" font-family="{t["font"]}" font-weight="700" '
        f'font-size="{t["label_size"]}" fill="#fff" stroke="#1d130a" stroke-width="3" paint-order="stroke">{label}</text>'
        "</g>"
    )


def scroll(t: dict) -> str:
    x0, x1, y0, y1 = 470, 1304, 26, 236
    out = (
        f'<path d="M{x0} {y0 + 10} Q887 {y0 - 8} {x1} {y0 + 10} L{x1} {y1 - 6} Q887 {y1 + 12} {x0} {y1 - 6} Z" '
        f'fill="url(#parch)" stroke="#6b4423" stroke-width="4"/>'
    )
    for cx in (x0, x1):
        out += (
            f'<rect x="{cx - 26}" y="{y0 - 6}" width="52" height="{y1 - y0 + 18}" rx="24" fill="#e7cf9d" stroke="#6b4423" stroke-width="4"/>'
            f'<ellipse cx="{cx}" cy="{y0 + 4}" rx="20" ry="9" fill="#c9a36b" stroke="#6b4423" stroke-width="3"/>'
            f'<ellipse cx="{cx}" cy="{y1 + 2}" rx="20" ry="9" fill="#c9a36b" stroke="#6b4423" stroke-width="3"/>'
        )
    f = t["font"]
    out += (
        f'<text x="887" y="{y0 + 112}" text-anchor="middle" font-family="{f}" font-weight="800" font-size="{t["title_size"]}" '
        f'fill="#4a2c14" stroke="#fff8e6" stroke-width="10" paint-order="stroke" letter-spacing="4">{t["title"]}</text>'
        f'<text x="887" y="{y0 + 160}" text-anchor="middle" font-family="{f}" font-weight="700" font-size="{t["sub_size"]}" '
        f'fill="#4a2c14" stroke="#fff8e6" stroke-width="6" paint-order="stroke">{t["subtitle"]}</text>'
        f'<text x="887" y="{y0 + 196}" text-anchor="middle" font-family="{f}" font-weight="600" font-size="{t["stats_size"]}" '
        f'fill="#6b4423">{t["stats"]}</text>'
    )
    return out


def build_svg(lang: str) -> str:
    t = TEXT[lang]
    rnd = random.Random(42)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><linearGradient id="parch" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#f8ecce"/><stop offset="1" stop-color="#ead39f"/></linearGradient></defs>',
        bookshelf(rnd, 0, 400),
        bookshelf(rnd, 1374, W),
        greenhouse(rnd),
    ]
    # vines over the greenhouse frame
    parts.append(vine(rnd, [(392, 0), (420, 80), (400, 180), (440, 300), (410, 420)], 40))
    parts.append(vine(rnd, [(1382, 0), (1354, 90), (1376, 200), (1340, 310), (1366, 430)], 40))
    parts.append(vine(rnd, [(392, 14), (600, 40), (887, 20), (1180, 44), (1382, 14)], 45))
    parts.append(scene(t))
    parts.append(scroll(t))

    side_w, side_h, gap = 330, 268, 13
    left = [("pi", SLATE), ("scout", TEAL), ("designer", BROWN)]
    right = [("reviewer", BROWN), ("econ", TEAL), ("exp", SLATE)]
    bottom = [("data", BROWN), ("figures", TEAL), ("writer", SLATE), ("replicator", BROWN)]
    for i, (role, c) in enumerate(left):
        parts.append(card(40, 22 + i * (side_h + gap), side_w, side_h, role, c, t))
    for i, (role, c) in enumerate(right):
        parts.append(card(W - 40 - side_w, 22 + i * (side_h + gap), side_w, side_h, role, c, t))
    bw, bgap = 232, 13
    bx0 = 887 - (4 * bw + 3 * bgap) / 2
    for i, (role, c) in enumerate(bottom):
        parts.append(card(bx0 + i * (bw + bgap), 668, bw, 188, role, c, t))

    # foreground leaves and the outer frame
    parts.append(vine(rnd, [(0, 887), (40, 820), (20, 760)], 18))
    parts.append(vine(rnd, [(W, 887), (W - 40, 820), (W - 20, 760)], 18))
    parts.append(
        f'<rect x="5" y="5" width="{W - 10}" height="{H - 10}" rx="22" fill="none" stroke="#2c1d10" stroke-width="10"/>'
        f'<rect x="12" y="12" width="{W - 24}" height="{H - 24}" rx="18" fill="none" stroke="#c9a36b" stroke-width="3"/>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def find_chrome() -> str | None:
    for c in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
    ):
        if c and Path(c).exists():
            return c
    return None


def render_png(svg: Path, png: Path, chrome: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "poster.html"
        html.write_text(
            f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#2c1d10}}</style>'
            f'{svg.read_text(encoding="utf-8")}',
            encoding="utf-8",
        )
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", f"--window-size={W},{H}",
             f"--user-data-dir={tmp}/profile", f"--screenshot={png}", html.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--svg-only", action="store_true")
    args = ap.parse_args()
    chrome = None if args.svg_only else find_chrome()
    if not args.svg_only and not chrome:
        print("Chrome not found; writing SVG only", file=sys.stderr)
    for lang in TEXT:
        svg = HERE / f"free-research-crew-{lang}.svg"
        svg.write_text(build_svg(lang), encoding="utf-8")
        print(f"wrote {svg.relative_to(HERE.parent.parent)}")
        if chrome:
            png = svg.with_suffix(".png")
            render_png(svg, png, chrome)
            print(f"wrote {png.relative_to(HERE.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
