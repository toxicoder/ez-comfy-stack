"""Icon-pack catalog: frozen specs, the shipped default set, JSON overrides.

An entry is a neutral record: a slug, a descriptive name, the Android package
and optional component a launcher matches on, plus the recipe and palette the
generator draws from. No trademarked brand name lives here; the operator
supplies real names through their own catalog override file.

The numbers that gate an entry come from the verified requirements digest:
the adaptive sheet is 108 dp with a 66 dp artwork safe zone (48 dp minimum),
mapping is by ``component=`` / ``package=``, never by a filename convention.

Hermetic at import: stdlib only, plus :mod:`ez_raster` for hex parsing and
:mod:`ez_common.json_value` for the parsed-JSON vocabulary.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, TypeAlias

from ez_common.json_value import Json, JsonObject, JsonMap
from ez_raster import hex_to_rgba

# Vocabulary the catalog speaks: lifecycle flags, background painters, and the
# patterns every text field has to clear before a spec is accepted.
IconStatus: TypeAlias = Literal["stable", "new", "redesign"]
"""Lifecycle flag an operator sets when an app ships or gets redesigned."""

# Accepted values and the shapes every text field is matched against before a
# spec is built; an empty component is legal, an empty slug is not.
ICON_STATUSES: tuple[IconStatus, ...] = ("stable", "new", "redesign")
"""Every accepted :data:`IconStatus`, in listing order."""

BACKGROUND_STYLES: tuple[str, ...] = ("solid", "linear", "radial")
"""Background painters: flat fill, vertical gradient, corner-weighted vignette."""

_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_PACKAGE_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+")
_COMPONENT_RE = re.compile(r"\.?[A-Za-z_][A-Za-z0-9_$.]*")
_DRAWABLE_RE = re.compile(r"[a-z][a-z0-9_]{0,63}")
_SPLIT_RE = re.compile(r"[,;\s]+")


@dataclass(frozen=True)
class Background:
    """Parsed value of :attr:`IconSpec.background`.

    Args:
        style: One of :data:`BACKGROUND_STYLES`.
        top: Colour at the top (solid and linear) or at the centre (radial).
        bottom: Colour at the bottom or the corners; empty for a solid fill.
    """

    style: str
    top: str
    bottom: str = ""


@dataclass(frozen=True)
class IconSpec:
    """One icon-pack entry.

    Args:
        slug: Stable lowercase id; also the master-art filename stem.
        name: Neutral descriptive label written into ``strings.xml``.
        package: Android package the launcher matches on.
        component: Optional activity, ``.MainActivity`` or a fully qualified
            class, used to build the ``ComponentInfo{...}`` appfilter key.
        category: Grouping written into ``drawable.xml``.
        tags: Free-form search terms.
        glyph: Recipe id drawn by :mod:`ez_icons.glyphs`.
        palette: One to three hex colours, primary first.
        background: Hex, or a ``#top>#bottom`` pair with a ``linear:`` /
            ``radial:`` prefix.
        keywords: Space-separated terms for the picker search box.
        status: Lifecycle flag.
        notes: Operator-facing remark about why the entry exists.
    """

    slug: str
    name: str
    package: str
    component: str = ""
    category: str = "utilities"
    tags: tuple[str, ...] = ()
    glyph: str = "disc"
    palette: tuple[str, ...] = ("#F2F5F7", "#7FC8F8")
    background: str = "#1B2833"
    keywords: str = ""
    status: IconStatus = "stable"
    notes: str = ""

    def __post_init__(self) -> None:
        """Normalise the text fields and reject a malformed entry.

        Raises:
            ValueError: a required field is empty, a hex colour does not
                parse, a background string is not one of the accepted shapes,
                or the status is unknown.
        """
        object.__setattr__(self, "slug", _checked("slug", self.slug, _SLUG_RE))
        object.__setattr__(self, "name", _checked("name", self.name, None))
        object.__setattr__(self, "package", _checked("package", self.package, _PACKAGE_RE))
        object.__setattr__(
            self, "component", _checked("component", self.component, _COMPONENT_RE, optional=True)
        )
        object.__setattr__(self, "category", _checked("category", self.category, None))
        object.__setattr__(self, "glyph", _checked("glyph", self.glyph, _DRAWABLE_RE))
        object.__setattr__(self, "palette", _checked_palette(self.palette))
        object.__setattr__(self, "background", _checked_background(self.background))
        object.__setattr__(self, "status", _checked_status(self.status))

    @property
    def drawable(self) -> str:
        """Resource name this entry is published under.

        Returns:
            The slug with dashes folded to underscores, which is what an
            Android resource name may hold.
        """
        return self.slug.replace("-", "_")

    @property
    def themed_drawable(self) -> str:
        """Monochrome resource name for the themed-icon map.

        Returns:
            ``<drawable>_themed``, matching the ``@drawable/themed_*`` naming
            the Lawnchair grayscale map uses.
        """
        return f"{self.drawable}_themed"

    @property
    def parsed_background(self) -> Background:
        """Background of this entry as a parsed record.

        Returns:
            Parsed :class:`Background`.
        """
        return parse_background(self.background)

    @property
    def component_info(self) -> str:
        """appfilter ``component=`` value for this entry.

        Returns:
            ``ComponentInfo{package/component}``, or an empty string when the
            entry maps by package only.
        """
        if not self.component:
            return ""
        return f"ComponentInfo{{{self.package}/{self.component}}}"

    @property
    def search_terms(self) -> tuple[str, ...]:
        """Every term the in-app picker can match on.

        Returns:
            Tags, keywords, and the lowercase name words, deduplicated and
            sorted.
        """
        words = set(self.tags) | {token for token in _SPLIT_RE.split(self.keywords) if token}
        words.update(token.lower() for token in self.name.split())
        return tuple(sorted(words))


def _checked(field: str, value: str, pattern: re.Pattern[str] | None, optional: bool = False) -> str:
    """Trim one text field and match it against an optional pattern.

    Args:
        field: Field name, for the message.
        value: Raw value.
        pattern: Compiled pattern the trimmed value must fully match, or None
            for "any non-empty text".
        optional: When True an empty value is accepted.

    Returns:
        The trimmed value.

    Raises:
        ValueError: the value is empty and not optional, or it does not match
            ``pattern``.
    """
    text = value.strip()
    if text == "":
        if optional:
            return ""
        raise ValueError(f"{field} is empty")
    if pattern is not None and pattern.fullmatch(text) is None:
        raise ValueError(f"{field} {text!r} is malformed")
    return text


def _checked_palette(palette: tuple[str, ...]) -> tuple[str, ...]:
    """Validate the palette colours.

    Args:
        palette: Hex strings, primary first.

    Returns:
        The palette as given.

    Raises:
        ValueError: the palette is empty or a colour is not hex.
    """
    if not palette:
        raise ValueError("palette is empty")
    for colour in palette:
        try:
            hex_to_rgba(colour)
        except ValueError as exc:
            raise ValueError(f"palette colour {colour!r} is not hex") from exc
    return tuple(palette)


def parse_background(value: str) -> Background:
    """Parse a background string.

    Shapes: ``#RGB``, ``#RRGGBB``, ``#RRGGBBAA`` for a solid fill, or a
    ``#top>#bottom`` pair with an optional ``linear:`` / ``radial:`` prefix
    (an unprefixed pair is read as a linear gradient).

    Args:
        value: The :attr:`IconSpec.background` text.

    Returns:
        Parsed :class:`Background`.

    Raises:
        ValueError: the string is not one of the accepted shapes, or a colour
            is not hex.
    """
    text = value.strip()
    style, separator, remainder = text.partition(":")
    if separator and style in BACKGROUND_STYLES:
        body = remainder
    elif separator:
        raise ValueError(f"background style {style!r} is unknown")
    else:
        style, body = "solid", text
    parts = [part.strip() for part in body.split(">")]
    if len(parts) > 2:
        raise ValueError(f"background {value!r} carries too many colours")
    for part in parts:
        try:
            hex_to_rgba(part)
        except ValueError as exc:
            raise ValueError(f"background colour {part!r} is not hex") from exc
    if len(parts) == 1:
        return Background(style="solid", top=parts[0], bottom="")
    if style == "solid":
        style = "linear"
    return Background(style=style, top=parts[0], bottom=parts[1])


def _checked_background(value: str) -> str:
    """Validate a background string and return it trimmed.

    Args:
        value: The raw background text.

    Returns:
        The trimmed text.

    Raises:
        ValueError: :func:`parse_background` rejects it.
    """
    parse_background(value)
    return value.strip()


def _checked_status(status: str) -> IconStatus:
    """Validate a lifecycle flag.

    Args:
        status: Raw status text.

    Returns:
        The status, narrowed to :data:`IconStatus`.

    Raises:
        ValueError: the status is not in :data:`ICON_STATUSES`.
    """
    if status == "stable":
        return "stable"
    if status == "new":
        return "new"
    if status == "redesign":
        return "redesign"
    raise ValueError(f"status {status!r} is unknown, expected one of {ICON_STATUSES}")


def _s(
    slug: str,
    name: str,
    package: str,
    category: str,
    glyph: str,
    background: str,
    palette: tuple[str, ...],
    keywords: str,
    status: IconStatus = "stable",
    component: str = "",
    notes: str = "",
    tags: tuple[str, ...] = (),
) -> IconSpec:
    """Build one shipped catalog row compactly.

    Args:
        slug: Stable id.
        name: Neutral label.
        package: Android package.
        category: Picker grouping.
        glyph: Recipe id.
        background: Background string.
        palette: Palette colours, primary first.
        keywords: Space-separated picker terms.
        status: Lifecycle flag.
        component: Optional activity class.
        notes: Operator remark.
        tags: Extra search terms.

    Returns:
        A validated :class:`IconSpec`.
    """
    return IconSpec(
        slug=slug,
        name=name,
        package=package,
        component=component,
        category=category,
        tags=tags,
        glyph=glyph,
        palette=palette,
        background=background,
        keywords=keywords,
        status=status,
        notes=notes,
    )


# The shipped default set: broad launcher demand, several palette variants per
# glyph family so a fresh pack reads as a product rather than a placeholder.
# Names stay deliberately neutral; the operator's override file supplies the
# real app names they hold rights to display.
ICON_CATALOG: tuple[IconSpec, ...] = (
    _s("chat-bubble", "Chat Bubble", "com.talkline.messenger", "messaging", "speech",
       "linear:#12315A>#2E7DD1", ("#F4F7FA", "#8FD3FF"), "messaging talk dm sms inbox",
       component=".MainActivity"),
    _s("chat-pair", "Chat Pair", "net.replyloop.chat", "messaging", "speech_pair",
       "linear:#123A34>#2FA37C", ("#F2FBF7", "#9DE8C8"), "thread group conversation",
       component=".LauncherActivity"),
    _s("chat-dots", "Talking Dots", "com.pulsechat.im", "messaging", "speech",
       "radial:#3E5C7A>#101820", ("#FFFFFF", "#FFD166"), "typing presence unread",
       status="new", tags=("unread",), component=".HomeActivity"),
    _s("phone-handset", "Phone Handset", "com.wireline.dialer", "phone", "phone",
       "linear:#0F3B2E>#2C8F63", ("#F3FBF7", "#9BE3C2"), "dialer call contacts"),
    _s("phone-forward", "Call Forward", "com.wireline.forward", "phone", "phone",
       "linear:#123A34>#3AA981", ("#EAF9F2", "#B7F0D8"), "transfer divert", status="redesign",
       component=".LauncherActivity"),
    _s("camera-shutter", "Camera Shutter", "com.lensworks.camera", "camera", "camera",
       "linear:#1D2733>#40566E", ("#F7FAFC", "#7FC8F8"), "photo capture snap",
       component=".HomeActivity"),
    _s("camera-selfie", "Selfie Camera", "com.lensworks.selfie", "camera", "camera",
       "radial:#5B3A6B>#231731", ("#FDF4FF", "#F0A6FF"), "front portrait", status="new",
       component=".MainActivity"),
    _s("gallery-grid", "Photo Grid", "com.picwise.gallery", "gallery", "gallery",
       "linear:#2A2340>#6A4E9B", ("#F7F3FF", "#C6AEFF"), "photos library album"),
    _s("gallery-stack", "Photo Stack", "net.frameview.photos", "gallery", "gallery_stack",
       "linear:#23303F>#4E6E8E", ("#F5F9FD", "#9CD2FF"), "shots roll backlog",
       component=".HomeActivity"),
    _s("map-pin", "Map Pin", "com.pathfinder.maps", "maps", "pin",
       "linear:#0F2E4C>#2D7DBF", ("#F3F9FF", "#8ED0FF"), "navigation place location",
       component=".MainActivity"),
    _s("map-fold", "Folded Map", "com.pathfinder.atlas", "maps", "map",
       "linear:#12315A>#3F86C6", ("#EEF7FF", "#B7DDFF"), "directions route", status="redesign",
       component=".LauncherActivity"),
    _s("compass-needle", "Compass Needle", "net.truenorth.navigator", "navigation", "compass",
       "radial:#1E3A5F>#0A1622", ("#FFFFFF", "#FF8A5B"), "bearing heading travel"),
    _s("route-dots", "Route Dots", "net.truenorth.route", "navigation", "dot_path",
       "linear:#16283B>#33608C", ("#F2F8FF", "#7FC8F8"), "waypoints track", status="new",
       component=".MainActivity"),
    _s("weather-cloud", "Weather Cloud", "com.skycast.weather", "weather", "cloud",
       "linear:#1C3557>#5D9BD8", ("#F5FAFF", "#CFE7FF"), "forecast rain temperature",
       component=".LauncherActivity"),
    _s("weather-sun", "Clear Sky", "com.skycast.sun", "weather", "sun",
       "radial:#C9821B>#5A3306", ("#FFF9EC", "#FFD98A"), "sunny warm daylight",
       component=".HomeActivity"),
    _s("weather-rain", "Rain Showers", "com.skycast.rain", "weather", "rain",
       "linear:#14304A>#3E7EA6", ("#EFF8FF", "#8ED0FF"), "drizzle umbrella", status="redesign"),
    _s("music-note", "Music Note", "com.waveform.player", "music", "note",
       "linear:#2A1B3D>#7A3FA0", ("#FDF6FF", "#D8B4FE"), "player song audio",
       component=".LauncherActivity"),
    _s("music-wave", "Sound Wave", "com.waveform.wave", "music", "waveform",
       "linear:#101820>#3E6B8F", ("#F2F5F7", "#7FC8F8"), "equalizer spectrum tune",
       component=".HomeActivity"),
    _s("music-disc", "Vinyl Disc", "net.groovebox.library", "music", "ring",
       "radial:#33223A>#140C19", ("#FBF7FF", "#F0B8FF"), "album records dj", status="new",
       component=".MainActivity"),
    _s("podcast-mic", "Podcast Mic", "com.speechline.podcast", "podcast", "mic",
       "linear:#2B1D10>#9A6A22", ("#FFF8EC", "#FFCF7A"), "radio show recording voice"),
    _s("video-play", "Video Player", "com.reeltime.player", "video", "play",
       "linear:#2A1020>#A03A5E", ("#FFF4F8", "#FFA6C3"), "movie stream watch",
       component=".HomeActivity"),
    _s("video-strip", "Film Strip", "com.reeltime.editor", "video", "film",
       "linear:#181C24>#48525F", ("#F6F8FA", "#A8B4C2"), "clip edit timeline",
       component=".MainActivity"),
    _s("social-nodes", "Social Nodes", "com.circleline.social", "social", "share_nodes",
       "linear:#132B4A>#3B7CC4", ("#F2F8FF", "#8ED0FF"), "network feed friends",
       component=".LauncherActivity"),
    _s("social-people", "Group of People", "net.friendcircle.app", "social", "people",
       "radial:#22405C>#0C1A26", ("#FFFFFF", "#B7DDFF"), "community contacts", status="redesign"),
    _s("mail-inbox", "Mail Inbox", "com.postmark.mail", "mail", "envelope",
       "linear:#12315A>#2E6FB5", ("#F4F9FF", "#9CD2FF"), "email letter post",
       component=".MainActivity"),
    _s("mail-send", "Sent Mail", "com.postmark.outbox", "mail", "envelope",
       "linear:#1D2733>#4E6377", ("#F7FAFC", "#CBD5E1"), "outbox compose", status="new",
       component=".LauncherActivity"),
    _s("calendar-day", "Calendar Day", "com.datemark.calendar", "calendar", "calendar",
       "linear:#3A1420>#A83A55", ("#FFF5F8", "#FFB3C6"), "agenda schedule date",
       component=".HomeActivity"),
    _s("calendar-month", "Calendar Month", "com.datemark.planner", "calendar", "calendar",
       "radial:#3B2140>#160C19", ("#FDF5FF", "#E0B7FF"), "month view events", status="redesign"),
    _s("clock-analog", "Analog Clock", "com.hourmark.clock", "clock", "clock",
       "linear:#16283B>#3E6B8F", ("#F3F9FF", "#8FD3FF"), "time watch hours",
       component=".LauncherActivity"),
    _s("clock-alarm", "Alarm Clock", "com.hourmark.alarm", "clock", "alarm",
       "linear:#3A2A10>#B98A22", ("#FFF9EC", "#FFD98A"), "wake timer bell",
       component=".HomeActivity"),
    _s("notes-page", "Note Page", "com.inkline.notes", "notes", "notes",
       "linear:#26323F>#54677C", ("#F8FAFC", "#B7C6D6"), "memo write list",
       component=".MainActivity"),
    _s("notes-pencil", "Note Pencil", "com.inkline.scratch", "notes", "pencil",
       "linear:#2A2340>#6A4E9B", ("#F9F6FF", "#C6AEFF"), "draft edit sketch", status="new"),
    _s("tasks-check", "Task Check", "com.donetoday.tasks", "tasks", "check",
       "linear:#0F3B2E>#2C8F63", ("#F1FBF6", "#9BE3C2"), "todo done checklist",
       component=".HomeActivity"),
    _s("tasks-board", "Task Board", "com.donetoday.board", "tasks", "board",
       "radial:#1E3A5F>#0A1622", ("#FFFFFF", "#7FC8F8"), "kanban columns sprint",
       component=".MainActivity"),
    _s("finance-chart", "Finance Chart", "com.ledgerbook.finance", "finance", "chart",
       "linear:#102A24>#2F7F5F", ("#F0FBF6", "#8FE3BD"), "budget spend money",
       component=".LauncherActivity"),
    _s("finance-wallet", "Wallet", "com.ledgerbook.wallet", "finance", "wallet",
       "linear:#2B1D10>#9A6A22", ("#FFF8EC", "#FFCF7A"), "cards payments purse", status="redesign"),
    _s("banking-ledger", "Banking Ledger", "com.vaultkeep.banking", "finance", "bank",
       "linear:#12283F>#356B9E", ("#F2F8FF", "#9CD2FF"), "bank account statement",
       component=".MainActivity"),
    _s("banking-coin", "Coin Stack", "com.vaultkeep.coins", "finance", "coin",
       "radial:#3A2F10>#17120A", ("#FFFBEF", "#FFD98A"), "savings cash coins",
       component=".LauncherActivity"),
    _s("fitness-dumbbell", "Dumbbell", "com.repfactory.fitness", "fitness", "dumbbell",
       "linear:#1D2733>#5B6B7E", ("#F7FAFC", "#C3CEDA"), "gym weights workout",
       component=".HomeActivity"),
    _s("fitness-pulse", "Pulse Tracker", "com.repfactory.pulse", "fitness", "pulse",
       "linear:#2A1020>#A03A5E", ("#FFF4F8", "#FFA6C3"), "heart rate cardio", status="new"),
    _s("fitness-run", "Run Tracker", "com.repfactory.run", "fitness", "shoe",
       "linear:#123A34>#3AA981", ("#EEFAF4", "#B7F0D8"), "steps jog stride",
       component=".LauncherActivity"),
    _s("health-heart", "Health Heart", "com.careloop.health", "health", "heart",
       "linear:#3A1420>#C4506E", ("#FFF5F8", "#FFB3C6"), "wellness care vitals",
       component=".HomeActivity"),
    _s("health-cross", "Medical Cross", "com.careloop.clinic", "health", "cross",
       "linear:#102A24>#2F8F6F", ("#F0FBF6", "#96E8C8"), "clinic first aid",
       component=".MainActivity"),
    _s("health-leaf", "Wellness Leaf", "net.greenstate.wellness", "health", "leaf",
       "radial:#1E3A22>#0B1710", ("#FFFFFF", "#A8E6A1"), "meditation calm herbs", status="redesign"),
    _s("food-cup", "Coffee Cup", "com.brewline.coffee", "food", "cup",
       "linear:#2B1D10>#8F5F1F", ("#FFF8EC", "#FFCF7A"), "coffee tea cafe",
       component=".HomeActivity"),
    _s("food-fork", "Fork and Knife", "com.tablebook.orders", "food", "fork",
       "linear:#3A2312>#B0701F", ("#FFF7EC", "#FFD9A0"), "restaurant delivery meal",
       component=".MainActivity"),
    _s("food-basket", "Grocery Basket", "com.marketday.grocery", "food", "basket",
       "linear:#0F3B2E>#2C8F63", ("#F1FBF6", "#9BE3C2"), "groceries shopping cart",
       component=".LauncherActivity"),
    _s("travel-plane", "Airplane", "com.flightdeck.trips", "travel", "plane",
       "linear:#12315A>#3F86C6", ("#F1F8FF", "#9CD2FF"), "flight airline trips"),
    _s("travel-train", "Commuter Train", "com.railwise.transit", "travel", "train",
       "linear:#1D2733>#4E6377", ("#F7FAFC", "#B7C6D6"), "subway metro commute",
       component=".MainActivity"),
    _s("travel-hotel", "Hotel Bed", "com.stayeasy.bookings", "travel", "bed",
       "radial:#22405C>#0C1A26", ("#FFFFFF", "#B7DDFF"), "hotel stay booking", status="new",
       component=".LauncherActivity"),
    _s("shopping-bag", "Shopping Bag", "com.cartwise.market", "shopping", "bag",
       "linear:#3A1420>#A83A55", ("#FFF5F8", "#FFB3C6"), "store buy retail",
       component=".HomeActivity"),
    _s("shopping-tag", "Price Tag", "com.cartwise.deals", "shopping", "tag",
       "linear:#2A2340>#6A4E9B", ("#F9F6FF", "#C6AEFF"), "sale coupon discount"),
    _s("shopping-gift", "Gift Box", "com.cartwise.gifts", "shopping", "gift",
       "radial:#3B2140>#160C19", ("#FDF5FF", "#E0B7FF"), "present rewards",
       component=".LauncherActivity"),
    _s("news-headline", "News Headline", "com.headlinepost.news", "news", "news",
       "linear:#1D2733>#48525F", ("#F7FAFC", "#CBD5E1"), "paper headlines press",
       component=".HomeActivity"),
    _s("news-globe", "World News", "net.orbitpost.daily", "news", "globe",
       "linear:#102A3A>#2F7F8F", ("#F0FAFC", "#96E0E8"), "world international",
       component=".MainActivity"),
    _s("reading-book", "Open Book", "com.pageturn.reader", "reading", "book",
       "linear:#2B1D10>#8F5F1F", ("#FFF8EC", "#FFCF7A"), "ebook read library"),
    _s("reading-shelf", "Book Shelf", "com.pageturn.library", "reading", "bookshelf",
       "radial:#241A2E>#0F0A16", ("#FBF7FF", "#D8B4FE"), "books stack shelf", status="redesign",
       component=".HomeActivity"),
    _s("games-puzzle", "Puzzle Piece", "com.playyard.games", "games", "puzzle",
       "linear:#123A34>#3AA981", ("#EEFAF4", "#B7F0D8"), "puzzle brain casual",
       component=".MainActivity"),
    _s("games-pad", "Game Controller", "com.playyard.arcade", "games", "gamepad",
       "linear:#2A1020>#A03A5E", ("#FFF4F8", "#FFA6C3"), "controller arcade joystick",
       component=".LauncherActivity"),
    _s("games-star", "Star Reward", "com.playyard.rewards", "games", "star",
       "radial:#3A2F10>#17120A", ("#FFFBEF", "#FFD98A"), "favourite rating stars"),
    _s("utility-search", "Search Glass", "com.toolbench.utilities", "utilities", "search",
       "linear:#16283B>#3E6B8F", ("#F3F9FF", "#8FD3FF"), "find lookup magnify",
       component=".MainActivity"),
    _s("utility-bolt", "Quick Bolt", "com.toolbench.boost", "utilities", "bolt",
       "linear:#2B2410>#B99322", ("#FFFBEF", "#FFD98A"), "turbo power speed", status="new",
       component=".LauncherActivity"),
    _s("utility-calc", "Calculator", "com.toolbench.calc", "utilities", "calc",
       "linear:#26323F>#54677C", ("#F8FAFC", "#B7C6D6"), "math numbers sum",
       component=".HomeActivity"),
    _s("files-folder", "Folder", "com.vaultbox.files", "files", "folder",
       "linear:#12315A>#3F86C6", ("#F1F8FF", "#9CD2FF"), "documents directory archive"),
    _s("files-cloud", "Cloud Storage", "com.vaultbox.drive", "files", "cloud",
       "radial:#1E3A5F>#0A1622", ("#FFFFFF", "#8FD3FF"), "sync backup upload",
       component=".LauncherActivity"),
    _s("settings-gear", "Settings Gear", "com.dashpanel.system", "settings", "gear",
       "linear:#1D2733>#5B6B7E", ("#F7FAFC", "#C3CEDA"), "options config prefs",
       component=".HomeActivity"),
    _s("settings-sliders", "Tune Sliders", "com.dashpanel.tune", "settings", "sliders",
       "linear:#101820>#3E6B8F", ("#F2F5F7", "#7FC8F8"), "levels adjust mixer", status="redesign",
       component=".MainActivity"),
    _s("developer-terminal", "Terminal", "com.forgekit.terminal", "developer", "terminal",
       "linear:#0F2419>#2F7F4F", ("#F0FBF4", "#96E8B4"), "shell console code"),
    _s("developer-code", "Angle Brackets", "com.forgekit.ide", "developer", "code",
       "linear:#101820>#3E5C7A", ("#F2F5F7", "#7FC8F8"), "source editor brackets",
       component=".HomeActivity"),
    _s("smarthome-house", "Smart House", "com.hearthside.home", "smarthome", "house",
       "linear:#123A34>#3AA981", ("#EEFAF4", "#B7F0D8"), "home automation hub",
       component=".MainActivity"),
    _s("smarthome-bulb", "Smart Bulb", "com.hearthside.lights", "smarthome", "bulb",
       "radial:#3A2F10>#17120A", ("#FFFBEF", "#FFD98A"), "lighting lamp scene",
       component=".LauncherActivity"),
    _s("car-dashboard", "Car Dashboard", "com.roadlink.motor", "car", "car",
       "linear:#1D2733>#4E6377", ("#F7FAFC", "#B7C6D6"), "vehicle drive trip"),
    _s("car-charging", "Charging Plug", "com.roadlink.charge", "car", "plug",
       "linear:#102A24>#2F8F6F", ("#F0FBF6", "#96E8C8"), "ev charge energy", status="new",
       component=".MainActivity"),
    _s("kids-blocks", "Building Blocks", "com.playpen.kids", "kids", "blocks",
       "linear:#2A1020>#A03A5E", ("#FFF4F8", "#FFA6C3"), "toys toddler build",
       component=".LauncherActivity"),
    _s("kids-star", "Kids Star", "com.playpen.stars", "kids", "star",
       "radial:#C9821B>#5A3306", ("#FFF9EC", "#FFD98A"), "reward children chart",
       component=".HomeActivity"),
    _s("education-cap", "Graduation Cap", "com.lessonpath.school", "education", "cap",
       "linear:#12283F>#356B9E", ("#F2F8FF", "#9CD2FF"), "school course degree"),
    _s("education-book", "Study Book", "com.lessonpath.study", "education", "book",
       "radial:#241A2E>#0F0A16", ("#FBF7FF", "#D8B4FE"), "learn lesson textbook",
       component=".LauncherActivity"),
    _s("security-lock", "Padlock", "com.gatekeep.security", "security", "lock",
       "linear:#1D2733>#5B6B7E", ("#F7FAFC", "#C3CEDA"), "private secure password",
       component=".HomeActivity"),
    _s("security-shield", "Shield", "com.gatekeep.shield", "security", "shield",
       "linear:#102A3A>#2F7F8F", ("#F0FAFC", "#96E0E8"), "protect guard antivirus", status="redesign",
       component=".MainActivity"),
    _s("account-person", "Account Person", "com.profilesync.me", "account", "person",
       "linear:#16283B>#3E6B8F", ("#F3F9FF", "#8FD3FF"), "profile user identity"),
    _s("account-key", "Access Key", "com.profilesync.keys", "account", "key",
       "linear:#2B2410>#B99322", ("#FFFBEF", "#FFD98A"), "login signin token",
       component=".HomeActivity"),
)


def categories(catalog: Sequence[IconSpec] = ICON_CATALOG) -> tuple[str, ...]:
    """Distinct category names in first-seen order.

    Args:
        catalog: Entries to read.

    Returns:
        Category names, deduplicated, order preserved.
    """
    seen: dict[str, None] = {}
    for spec in catalog:
        seen.setdefault(spec.category, None)
    return tuple(seen)


def glyph_names(catalog: Sequence[IconSpec] = ICON_CATALOG) -> tuple[str, ...]:
    """Distinct glyph recipe ids used by a catalog.

    Args:
        catalog: Entries to read.

    Returns:
        Recipe ids, sorted.
    """
    return tuple(sorted({spec.glyph for spec in catalog}))


def by_slug(slug: str, catalog: Sequence[IconSpec] = ICON_CATALOG) -> IconSpec | None:
    """Look one entry up by slug.

    Args:
        slug: Entry slug.
        catalog: Entries to read.

    Returns:
        The matching spec, or None.
    """
    for spec in catalog:
        if spec.slug == slug:
            return spec
    return None


def icons_for(category: str, catalog: Sequence[IconSpec] = ICON_CATALOG) -> tuple[IconSpec, ...]:
    """Every entry in one category.

    Args:
        category: Category name, matched case-insensitively.
        catalog: Entries to read.

    Returns:
        Matching specs in catalog order.
    """
    wanted = category.strip().lower()
    return tuple(spec for spec in catalog if spec.category.lower() == wanted)


def select(
    catalog: Sequence[IconSpec],
    only_slugs: Sequence[str] | None = None,
    categories_filter: Sequence[str] | None = None,
) -> tuple[IconSpec, ...]:
    """Filter a catalog by slug and category.

    Args:
        catalog: Entries to filter.
        only_slugs: When given, keep only these slugs (in this order).
        categories_filter: When given, keep entries in these categories.

    Returns:
        The filtered tuple.

    Raises:
        ValueError: an asked-for slug is absent, or the filters match nothing.
    """
    chosen: list[IconSpec] = list(catalog)
    if only_slugs is not None:
        index = {spec.slug: spec for spec in catalog}
        missing = [slug for slug in only_slugs if slug not in index]
        if missing:
            raise ValueError(f"unknown slug(s): {', '.join(missing)}")
        chosen = [index[slug] for slug in only_slugs]
    if categories_filter is not None:
        wanted = {name.strip().lower() for name in categories_filter}
        chosen = [spec for spec in chosen if spec.category.lower() in wanted]
    if not chosen:
        raise ValueError("catalog filter matched no icons")
    return tuple(chosen)


def _as_str(row: JsonMap, key: str, default: str = "") -> str:
    """Read one optional string field from a parsed row.

    Args:
        row: Parsed JSON object.
        key: Field name.
        default: Value when the key is absent or null.

    Returns:
        The stripped string.

    Raises:
        ValueError: the field is present but not a string.
    """
    value = row.get(key)
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    raise ValueError(f"{key} must be a string")


def _as_text(item: Json, key: str) -> str:
    """Read one string out of a parsed array.

    Args:
        item: Array element.
        key: Field name the array came from, for the message.

    Returns:
        The stripped string.

    Raises:
        ValueError: the element is not a string.
    """
    if isinstance(item, str):
        return item.strip()
    raise ValueError(f"{key} must contain only strings")


def _as_tokens(row: JsonMap, key: str) -> tuple[str, ...]:
    """Read a list field that may be an array or a delimited string.

    Args:
        row: Parsed JSON object.
        key: Field name.

    Returns:
        Tokens, lowercased and deduplicated; empty when the key is absent.

    Raises:
        ValueError: the field holds a non-string element or a scalar that is
            neither a string nor null.
    """
    value = row.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        raw = [token for token in _SPLIT_RE.split(value) if token]
    elif isinstance(value, list):
        raw = [_as_text(element, key) for element in value]
    else:
        raise ValueError(f"{key} must be a string or a list of strings")
    return tuple(dict.fromkeys(token.lower() for token in raw if token))


def _spec_from_row(row: JsonMap) -> IconSpec:
    """Build one spec from a parsed override row.

    Args:
        row: Parsed JSON object.

    Returns:
        A validated spec; fields the row omits fall back to the defaults.

    Raises:
        ValueError: slug or package is missing, or a colour is not hex.
    """
    slug = _as_str(row, "slug")
    if slug == "":
        raise ValueError("catalog row is missing slug")
    package = _as_str(row, "package")
    if package == "":
        raise ValueError(f"catalog row {slug!r} has an empty package")
    palette_value = row.get("palette")
    palette = _as_tokens(row, "palette") if palette_value is not None else ()
    status = _as_str(row, "status", "stable")
    return IconSpec(
        slug=slug,
        name=_as_str(row, "name", slug.replace("-", " ").title()),
        package=package,
        component=_as_str(row, "component"),
        category=_as_str(row, "category", "utilities"),
        tags=_as_tokens(row, "tags"),
        glyph=_as_str(row, "glyph", "disc"),
        palette=palette or ("#F2F5F7", "#7FC8F8"),
        background=_as_str(row, "background", "#1B2833"),
        keywords=_as_str(row, "keywords"),
        status=_checked_status(status),
        notes=_as_str(row, "notes"),
    )


def _rows_from_document(document: Json) -> list[Json]:
    """Pull the row list out of a parsed catalog document.

    Args:
        document: Parsed JSON: an array of rows, an object carrying an
            ``icons`` array, or a single row object on its own.

    Returns:
        The row objects, in document order.

    Raises:
        ValueError: the document is none of those shapes, or ``icons`` is not
            a list.
    """
    if isinstance(document, list):
        return list(document)
    if isinstance(document, dict):
        icons = document.get("icons")
        if isinstance(icons, list):
            return list(icons)
        if "slug" in document:
            return [document]
        raise ValueError("catalog document needs an 'icons' array")
    raise ValueError("catalog document must be an object or an array")


def load_catalog(path: Path | str, base: Sequence[IconSpec] = ICON_CATALOG) -> tuple[IconSpec, ...]:
    """Merge an operator JSON override file over the shipped catalog.

    Rows are matched by slug: an override replaces the built-in entry in
    place, a new slug is appended. Duplicate slugs inside the file are an
    error, so a typo cannot silently drop half an operator's work.

    Args:
        path: JSON file with an ``icons`` array or a bare array of rows.
        base: Catalog to override; defaults to :data:`ICON_CATALOG`.

    Returns:
        The merged tuple.

    Raises:
        ValueError: the file is not valid JSON of the expected shape, a row
            is missing its slug, a package is empty, a colour is not hex, or
            the file repeats a slug.
        OSError: the file cannot be read.
    """
    source = Path(path)
    document = json.loads(source.read_text(encoding="utf-8"))
    overrides: dict[str, IconSpec] = {}
    for row in _rows_from_document(document):
        if not isinstance(row, dict):
            raise ValueError("every catalog row must be an object")
        spec = _spec_from_row(row)
        if spec.slug in overrides:
            raise ValueError(f"duplicate slug {spec.slug!r} in {source}")
        overrides[spec.slug] = spec
    merged: list[IconSpec] = [overrides.get(spec.slug, spec) for spec in base]
    known = {spec.slug for spec in base}
    merged.extend(spec for slug, spec in sorted(overrides.items()) if slug not in known)
    return tuple(merged)


_TEMPLATE_ROW: JsonObject = {
    "slug": "chat-bubble",
    "name": "Chat Bubble",
    "package": "com.example.messenger",
    "component": ".MainActivity",
    "category": "messaging",
    "tags": ["messaging", "chat"],
    "glyph": "speech",
    "palette": ["#F4F7FA", "#8FD3FF"],
    "background": "linear:#12315A>#2E7DD1",
    "keywords": "talk dm sms inbox",
    "status": "stable",
    "notes": "Override any built-in by reusing its slug.",
}
"""Worked example written by :func:`write_catalog_template`."""

_TEMPLATE_DOC: JsonObject = {
    "pack_name": "My Icon Pack",
    "pack_version": "1.0.0",
    "icons": [_TEMPLATE_ROW],
}
"""Starter document written by :func:`write_catalog_template`."""


def write_catalog_template(path: Path | str) -> int:
    """Write a starter override file with every field spelled out.

    Args:
        path: Destination JSON path; parents are created.

    Returns:
        Bytes written.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_TEMPLATE_DOC, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    destination.write_bytes(text.encode("utf-8"))
    return len(text.encode("utf-8"))


def new_icon_scaffold(
    slug: str,
    name: str,
    package: str,
    glyph: str = "disc",
    category: str = "utilities",
    *,
    component: str = "",
    palette: Sequence[str] = ("#F2F5F7", "#7FC8F8"),
    background: str = "linear:#1B2833>#3E5C7A",
    keywords: str = "",
    tags: Sequence[str] = (),
    status: IconStatus = "stable",
    notes: str = "",
    path: Path | str | None = None,
) -> str:
    """Render a ready-to-paste override row for a brand-new app.

    Adding an icon that just shipped is one row like this plus an optional
    master PNG named ``<slug>.png`` in the art directory.

    Args:
        slug: New entry slug.
        name: Neutral descriptive label.
        package: Android package to match.
        glyph: Recipe id from :mod:`ez_icons.glyphs`.
        category: Picker grouping.
        component: Optional activity class.
        palette: One to three hex colours.
        background: Background string.
        keywords: Space-separated picker terms.
        tags: Extra search terms.
        status: Lifecycle flag.
        notes: Operator remark.
        path: When given, the row is also written to this file.

    Returns:
        The row as an indented JSON string, without a trailing newline.

    Raises:
        ValueError: the row is malformed or the glyph is not a recipe.
    """
    from .glyphs import GLYPH_RECIPES  # local: glyphs imports this module

    if glyph not in GLYPH_RECIPES:
        raise ValueError(f"glyph {glyph!r} is not a registered recipe")
    spec = IconSpec(
        slug=slug,
        name=name,
        package=package,
        component=component,
        category=category,
        tags=tuple(tags),
        glyph=glyph,
        palette=tuple(palette),
        background=background,
        keywords=keywords,
        status=status,
        notes=notes,
    )
    row = {
        "slug": spec.slug,
        "name": spec.name,
        "package": spec.package,
        "component": spec.component,
        "category": spec.category,
        "tags": list(spec.tags),
        "glyph": spec.glyph,
        "palette": list(spec.palette),
        "background": spec.background,
        "keywords": spec.keywords,
        "status": spec.status,
        "notes": spec.notes,
    }
    text = json.dumps(row, indent=2, sort_keys=True, ensure_ascii=True)
    if path is not None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((text + "\n").encode("utf-8"))
    return text


def apply_status(spec: IconSpec, status: IconStatus) -> IconSpec:
    """Return a copy of an entry with a new lifecycle flag.

    Args:
        spec: Entry to copy.
        status: New status.

    Returns:
        A spec carrying ``status``.

    Raises:
        ValueError: ``status`` is not one of :data:`ICON_STATUSES`.
    """
    return replace(spec, status=_checked_status(status))
