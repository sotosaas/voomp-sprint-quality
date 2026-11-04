"""SVG icons following Greenn/Voomp design system.

All icons are stroke-based (21x21) with consistent styling.
"""

# Menu hamburger icon
ICON_MENU = '''<svg width="21" height="15" viewBox="0 0 21 15" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1 7.5H20M1 1.5H20M1 13.5H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Dashboard icon
ICON_DASHBOARD = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1.5 7.5H19.5M7.5 19.5V7.5M3.5 1.5H17.5C18.6 1.5 19.5 2.4 19.5 3.5V17.5C19.5 18.6 18.6 19.5 17.5 19.5H3.5C2.4 19.5 1.5 18.6 1.5 17.5V3.5C1.5 2.4 2.4 1.5 3.5 1.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Play icon
ICON_PLAY = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M5.5 3.5L17.5 10.5L5.5 17.5V3.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Card/Payment icon
ICON_CARD = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1.5 8.5H19.5M3.5 3.5H17.5C18.6 3.5 19.5 4.4 19.5 5.5V15.5C19.5 16.6 18.6 17.5 17.5 17.5H3.5C2.4 17.5 1.5 16.6 1.5 15.5V5.5C1.5 4.4 2.4 3.5 3.5 3.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Settings/Wrench icon
ICON_SETTINGS = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M13.5 6.5L17.5 2.5M19 4L17.5 2.5M17.5 2.5L15.5 4.5L17.5 2.5ZM10 8C10 8 8.5 6.5 6.5 6.5C4.5 6.5 2.5 8.5 2.5 10.5C2.5 12.5 4.5 14.5 6.5 14.5C8.5 14.5 10 13 10 13L14.5 17.5C15 18 15.7 18.3 16.5 18.3C18 18.3 19.3 17 19.3 15.5C19.3 14.7 19 14 18.5 13.5L14 9C14 9 15.5 7.5 15.5 5.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Chart/Report icon
ICON_CHART = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M17.5 17.5V7.5M10.5 17.5V3.5M3.5 17.5V11.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Refresh icon
ICON_REFRESH = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1.5 3.5V8.5H6.5M19.5 17.5V12.5H14.5M17.5 7.5C16.9 5.8 15.8 4.3 14.3 3.3C12.8 2.3 11 1.8 9.2 2C5.4 2.4 2.3 5.5 2 9.3M3.5 13.5C4.1 15.2 5.2 16.7 6.7 17.7C8.2 18.7 10 19.2 11.8 19C15.6 18.6 18.7 15.5 19 11.7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Overview/Globe icon
ICON_OVERVIEW = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M10.5 19.5C15.4706 19.5 19.5 15.4706 19.5 10.5C19.5 5.52944 15.4706 1.5 10.5 1.5C5.52944 1.5 1.5 5.52944 1.5 10.5C1.5 15.4706 5.52944 19.5 10.5 19.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M1.5 10.5H19.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M10.5 1.5C12.6 3.8 13.8 7.1 13.8 10.5C13.8 13.9 12.6 17.2 10.5 19.5C8.4 17.2 7.2 13.9 7.2 10.5C7.2 7.1 8.4 3.8 10.5 1.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''


# Product icon mapping
PRODUCT_ICONS = {
    "VADM": ICON_DASHBOARD,
    "VPLY": ICON_PLAY,
    "VMPG": ICON_CARD,
    "VSUS": ICON_SETTINGS,
    "VBEP": ICON_CHART,
}

# Emoji fallback for headers
PRODUCT_EMOJIS = {
    "VADM": "⚙️",
    "VPLY": "▶️",
    "VMPG": "💳",
    "VSUS": "🔧",
    "VBEP": "📊",
}


def get_icon(project_key: str) -> str:
    """Get SVG icon for a project."""
    return PRODUCT_ICONS.get(project_key, ICON_DASHBOARD)


def get_emoji(project_key: str) -> str:
    """Get emoji for a project."""
    return PRODUCT_EMOJIS.get(project_key, "📁")


def colorize_icon(icon_svg: str, color: str) -> str:
    """Colorize an SVG icon."""
    return icon_svg.replace('stroke="currentColor"', f'stroke="{color}"')
