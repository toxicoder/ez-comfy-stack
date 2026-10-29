#!/usr/bin/env python3
"""Write the four hand-authored creator sample catalogs.

These four shipped as the same thirty rows with only the platform noun
swapped, and each row ended in a mechanical "Framed for a <platform> still."
tail that said nothing about the deliverable. Rows here are written per
deliverable instead: a cover tile, a vertical, a banner, and a plate each get
the craft language that job actually needs.

Not imported by pytest collection. Run from repo root:

  python3 tests/python/_build_hand_catalogs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

DEST = CUSTOM / "ez_prompt_enhance" / "js" / "samples"

PERSON = (
    "an original techno wizard in an unmarked dark indigo-violet suede running "
    "coat with silk-felt nap and faint circuit-thread seams"
)
GOODS = "an unmarked charcoal canvas weekender bag with cobalt webbing handles"
UNMARKED = "Unmarked surfaces, empty of lettering."

# Craft language per deliverable. This is the layer the old copy never had:
# what the finished asset has to survive, not which platform it is for.
CRAFT: dict[str, str] = {
    "cover": (
        "One dominant subject fills the frame, lit hard enough to separate from "
        "the backdrop, with the face high in the frame and the lower band kept "
        "open for a title later."
    ),
    "vertical": (
        "Built 9:16 with the subject held in the middle third, the upper area "
        "left clear for a hook line and the lower area clear for captions and "
        "player chrome."
    ),
    "banner": (
        "Wide composition with the subject weighted off centre, the middle held "
        "calm for a channel name, and nothing load-bearing near the edges where "
        "a device crop will land."
    ),
    "icon": (
        "Tight centred mark with bold shape and strong contrast, since a circle "
        "mask trims the corners and it has to hold at avatar size."
    ),
    "plate": (
        "Subject pushed to one third with a broad, even, low-detail region "
        "beside it where a call to action can sit later without fighting the "
        "background."
    ),
    "post": (
        "Square-friendly composition with one clear focal point that still reads "
        "at feed size, and a simple background that stays quiet beside overlaid "
        "text."
    ),
    "marker": (
        "Marker frame built from one large simple shape and a generous flat "
        "area, so a chapter number can be dropped in later and stay legible."
    ),
    "mockup": (
        "The piece presented flat and square on a neutral ground, product "
        "filling most of the frame, true material colour and a soft honest "
        "shadow beneath it."
    ),
    "apparel": (
        "The garment worn and lit so the print reads as fabric ink rather than "
        "a sticker, chest area flat and uncreased and facing the lens."
    ),
}

# slug, display thing, scene text, deliverable key
YOUTUBE: list[tuple[str, str, str, str]] = [
    ("harbor-crane", "Harbor crane cover", f"{PERSON} stands on a high unmarked crane catwalk above a tropical harbor at late day", "cover"),
    ("tram-interior", "Tram cover", f"{PERSON} rides an unmarked tram, wet streets sliding past the glass", "cover"),
    ("quarry-noon", "Quarry cover", f"{PERSON} walks a pale unmarked quarry floor at hard noon, dust in the air", "cover"),
    ("clock-hall", "Clock hall cover", f"{PERSON} pauses in an unmarked civic clock hall, dust in a high window shaft", "cover"),
    ("ferry-deck", "Ferry deck cover", f"{PERSON} stands at an unmarked ferry rail, wake water and a far island", "cover"),
    ("market-awning", "Market cover", f"{PERSON} waits under an unmarked market awning while rain sheets the street", "cover"),
    ("observatory-rail", "Observatory cover", f"{PERSON} leans on an unmarked observatory rail under a wide night sky", "cover"),
    ("dock-warehouse", "Warehouse cover", f"{PERSON} walks the aisle of an unmarked dock warehouse, high doors open to light", "cover"),
    ("shorts-stairwell", "Stairwell short", f"{PERSON} climbs an unmarked concrete stairwell, light pooling on each landing", "vertical"),
    ("shorts-rooftop", "Rooftop short", f"{PERSON} crosses a bare unmarked rooftop at golden hour, palms in the far distance", "vertical"),
    ("shorts-kitchen", "Kitchen short", f"{PERSON} works at an unmarked kitchen counter, steam lifting from a pan", "vertical"),
    ("shorts-garage", "Garage short", f"{PERSON} rolls a board out of an unmarked garage, daylight raking the floor", "vertical"),
    ("shorts-shoreline", "Shoreline short", f"{PERSON} walks a wet unmarked shoreline as the tide pulls back", "vertical"),
    ("shorts-studio", "Studio short", f"{PERSON} sits at an unmarked studio desk, practical lamps warm behind", "vertical"),
    ("channel-banner-harbor", "Harbor banner", f"{PERSON} walks a long unmarked harbor wall with cranes receding to one side", "banner"),
    ("channel-banner-field", "Field banner", f"{PERSON} crosses an unmarked dry field under a heavy weather front", "banner"),
    ("channel-banner-bridge", "Bridge banner", f"{PERSON} passes beneath an unmarked steel bridge, girders repeating overhead", "banner"),
    ("channel-banner-terminal", "Terminal banner", f"{PERSON} moves through an unmarked departures hall, long glass and low light", "banner"),
    ("channel-icon-mark", "Channel mark", f"{PERSON} faces the lens head and shoulders only against a flat unmarked backdrop", "icon"),
    ("channel-icon-glyph", "Glyph mark", f"a single unmarked geometric glyph mark on a flat indigo field, one clean bevel catching light", "icon"),
    ("community-poll", "Community post", f"{PERSON} holds up two unmarked plain cards, one in each hand, in a bright room", "post"),
    ("community-announce", "Announcement post", f"{PERSON} stands before an unmarked blank billboard lit by a work lamp", "post"),
    ("community-behind", "Behind the scenes post", f"{PERSON} reviews notes at an unmarked fold table, gear stacked behind", "post"),
    ("chapter-one", "Chapter one card", f"one large unmarked numeral slab resting on a pale stone plinth in even light", "marker"),
    ("chapter-two", "Chapter two card", f"one tall unmarked monolith shape on a matte field, soft top light", "marker"),
    ("subscribe-plate", "Subscribe plate", f"{PERSON} stands at the far third of an unmarked cyclorama, the rest an even quiet field", "plate"),
    ("end-screen", "End screen", f"{PERSON} walks out of frame at one edge of an unmarked long corridor, open wall beside", "plate"),
    ("outro-plate", "Outro plate", f"an unmarked desk at dusk with a lamp and a still mug, wide empty wall behind", "plate"),
    ("chapter-grid", "Chapter grid card", f"six unmarked flat tiles stacked on a pale wall, one tile catching a hard edge of light", "marker"),
    ("community-milestone", "Milestone post", f"{PERSON} holds an unmarked plain plaque at chest height in a bright unmarked room", "post"),
]

INSTAGRAM: list[tuple[str, str, str, str]] = [
    ("portrait-studio", "Studio portrait", f"{PERSON} faces the lens head and shoulders in a bright unmarked studio", "cover"),
    ("portrait-doorway", "Doorway portrait", f"{PERSON} stands in an unmarked doorway, side light across the face", "cover"),
    ("portrait-cafe", "Cafe portrait", f"{PERSON} sits at an unmarked cafe table, window light from one side", "cover"),
    ("portrait-street", "Street portrait", f"{PERSON} pauses on an unmarked crossing, plain facades behind", "cover"),
    ("portrait-terrace", "Terrace portrait", f"{PERSON} leans on an unmarked terrace wall at last light", "cover"),
    ("story-kitchen", "Kitchen story", f"{PERSON} plates food at an unmarked counter, steam catching the key", "vertical"),
    ("story-unbox", "Unboxing story", f"{PERSON} opens an unmarked plain box on a pale table, hands leading", "vertical"),
    ("story-walk", "Walking story", f"{PERSON} walks an unmarked colonnade, columns passing rhythmically", "vertical"),
    ("story-desk", "Desk story", f"{PERSON} writes at an unmarked desk, lamp pool on the surface", "vertical"),
    ("story-garden", "Garden story", f"{PERSON} kneels beside an unmarked raised garden bed in morning light", "vertical"),
    ("story-reel-hook", "Reel hook", f"{PERSON} turns to the lens mid-stride on an unmarked stair, one hand raised", "vertical"),
    ("story-reel-detail", "Reel detail", f"a close unmarked fabric edge with a thumb smoothing the weave, shallow focus", "vertical"),
    ("reel-cover-face", "Reel cover", f"{PERSON} fills the upper frame against an unmarked warm wall, chin lifted", "cover"),
    ("reel-cover-hands", "Reel hands cover", f"unmarked hands hold a plain object high against an even sky, wrists framing", "cover"),
    ("highlight-tool", "Tool highlight", f"an unmarked hand tool laid on a pale workbench, shadow drawn to one side", "post"),
    ("highlight-book", "Book highlight", f"an unmarked open notebook on a stone sill, page held flat by a smooth weight", "post"),
    ("highlight-mug", "Mug highlight", f"an unmarked ceramic mug on a bare table, condensation ring, single soft key", "post"),
    ("highlight-shirt", "Shirt highlight", f"an unmarked folded shirt on a pale floor, collar squared to the lens", "mockup"),
    ("profile-roundel", "Profile mark", f"a single unmarked circular mark on a flat field, one bevel lit for edge definition", "icon"),
    ("profile-monogram", "Monogram mark", f"two unmarked interlocking letterforms on a matte ground, even studio light", "icon"),
    ("landscape-dune", "Landscape post", f"{PERSON} stands small on an unmarked dune ridge under a wide clear sky", "post"),
    ("landscape-pier", "Pier post", f"{PERSON} walks an unmarked timber pier toward the lens, calm water each side", "post"),
    ("landscape-lot", "Lot post", f"{PERSON} stands in an unmarked empty lot, low sun drawing a long shadow", "post"),
    ("landscape-quarry", "Quarry post", f"{PERSON} descends an unmarked quarry stair cut into pale stone", "post"),
    ("grid-tile-one", "Grid tile one", f"the left third of an unmarked three-tile row: a plain wall and a hard shadow edge", "post"),
    ("grid-tile-two", "Grid tile two", f"the centre of an unmarked three-tile row: {PERSON} mid-stride, feet cropped clean", "post"),
    ("grid-tile-three", "Grid tile three", f"the right third of an unmarked three-tile row: an unmarked doorway throwing light", "post"),
    ("carousel-slide-one", "Carousel opener", f"{PERSON} stands at one side of an unmarked studio cyc, large calm space beside", "plate"),
    ("carousel-slide-mid", "Carousel mid slide", f"an unmarked tabletop with one object and generous flat ground around it", "plate"),
    ("carousel-slide-end", "Carousel closer", f"an unmarked bench under a high window, empty, ready for a closing line", "plate"),
]

TWITCH: list[tuple[str, str, str, str]] = [
    ("starting-desk", "Starting screen", f"{PERSON} sits at an unmarked streaming desk, practicals warm behind", "plate"),
    ("brb-desk", "Be right back", f"an unmarked streaming chair pushed back from a bare desk, monitor glow on", "plate"),
    ("ending-credits", "Stream ending", f"{PERSON} waves from the far third of an unmarked set, open wall for a name later", "plate"),
    ("offline-card", "Offline card", f"an unmarked set lit low with one lamp, chairs empty, wide even wall", "plate"),
    ("overlay-cam", "Webcam overlay", f"an unmarked room corner framed to leave a clean rectangular region for a camera box", "marker"),
    ("overlay-alerts", "Alerts overlay", f"an unmarked desk edge with a clear lower band and quiet upper frame", "marker"),
    ("overlay-hud", "HUD overlay", f"an unmarked panel wall with a broad flat margin along one side for readouts", "marker"),
    ("panel-about", "About panel", f"{PERSON} leans on an unmarked rail, body weight to one side, blank wall beside", "post"),
    ("panel-schedule", "Schedule panel", f"an unmarked pegboard with blank tiles in a tidy grid, even frontal light", "marker"),
    ("panel-gear", "Gear panel", f"unmarked gear laid out flat on a pale surface, each item spaced for a label later", "marker"),
    ("panel-social", "Social panel", f"an unmarked bench with two plain plaques side by side on a matte ground", "marker"),
    ("banner-wide-harbor", "Channel banner", f"{PERSON} walks a long unmarked harbor wall, cranes receding to one side", "banner"),
    ("banner-wide-studio", "Studio banner", f"an unmarked studio depth with softboxes marching to one side, open floor", "banner"),
    ("banner-wide-arcade", "Arcade banner", f"a row of unmarked plain cabinets under low light, one screen catching glow", "banner"),
    ("banner-wide-loft", "Loft banner", f"{PERSON} crosses an unmarked loft mezzanine, long railing running wide", "banner"),
    ("profile-avatar", "Channel avatar", f"{PERSON} faces the lens head and shoulders on a flat unmarked ground", "icon"),
    ("profile-badge", "Channel badge", f"a single unmarked shield shape on a matte field, one clean lit bevel", "icon"),
    ("emote-leaf", "Leaf emote", f"one unmarked leaf glyph drawn thick on a flat field, silhouette clean", "icon"),
    ("emote-bolt", "Bolt emote", f"one unmarked bolt glyph, heavy outline, even fill, no interior detail", "icon"),
    ("emote-mug", "Mug emote", f"one unmarked mug glyph with a bold rim and a simple steam curl", "icon"),
    ("raiding-screen", "Raid screen", f"{PERSON} stands at the edge of an unmarked set, most of the frame left calm", "plate"),
    ("milestone-screen", "Milestone screen", f"{PERSON} holds an unmarked plain plaque chest high in a bright set", "post"),
    ("clip-cover-face", "Clip cover", f"{PERSON} fills the upper frame against an unmarked warm wall, mouth mid-word", "cover"),
    ("clip-cover-hands", "Clip hands cover", f"unmarked hands slam a plain desk, motion held, shallow focus", "cover"),
    ("clip-cover-chair", "Clip chair cover", f"{PERSON} leans back in an unmarked chair, silhouette strong against a bright wall", "cover"),
    ("shorts-clip-one", "Clip short", f"{PERSON} turns to the lens mid-laugh on an unmarked set, upper area left clear", "vertical"),
    ("shorts-clip-two", "Clip short two", f"{PERSON} points at an empty lower third on an unmarked set", "vertical"),
    ("shorts-clip-three", "Clip short three", f"{PERSON} stands under a single hard spot on an unmarked stage, deep dark above", "vertical"),
    ("overlay-donation", "Donation overlay", f"an unmarked desk corner with a generous flat strip along the bottom edge", "marker"),
    ("panel-community", "Community panel", f"a row of unmarked plain chairs facing the lens in an even, quiet room", "post"),
]

MERCH: list[tuple[str, str, str, str]] = [
    ("tee-front", "Tee front", f"an unmarked charcoal tee laid flat on a pale ground, chest panel square to the lens", "mockup"),
    ("tee-worn", "Tee worn", f"{PERSON} wears an unmarked charcoal tee, chest flat and facing the lens", "apparel"),
    ("tee-hang", "Tee hang", f"an unmarked tee hangs from a plain wood peg against a matte wall", "mockup"),
    ("tee-detail", "Tee detail", f"a close unmarked tee seam with the weave readable and a soft raking key", "mockup"),
    ("tee-back", "Tee back", f"an unmarked tee shown from behind, shoulders squared, print area flat", "apparel"),
    ("mug-front", "Mug front", f"an unmarked ceramic mug on a bare table, handle turned out, single soft key", "mockup"),
    ("mug-held", "Mug held", f"unmarked hands cradle a plain mug, steam lifting, condensation on the glaze", "mockup"),
    ("mug-pair", "Mug pair", f"two unmarked mugs side by side on pale stone, matching shadow direction", "mockup"),
    ("mug-table", "Mug table", f"an unmarked mug on a honey-oak table, morning window from one side", "mockup"),
    ("bag-front", "Bag front", f"{GOODS} stands upright on a pale ground, panels flat and uncreased", "mockup"),
    ("bag-carried", "Bag carried", f"{PERSON} carries {GOODS} at the side, strap taut, walking toward the lens", "apparel"),
    ("bag-open", "Bag open", f"{GOODS} lies open on a pale floor, interior visible, contents absent", "mockup"),
    ("hoodie-front", "Hoodie front", f"an unmarked heavyweight hoodie on a plain form, hood dressed open, chest flat", "apparel"),
    ("hoodie-worn", "Hoodie worn", f"{PERSON} wears an unmarked heavyweight hoodie, sleeves pushed, chest facing the lens", "apparel"),
    ("cap-front", "Cap front", f"an unmarked six-panel cap on a plain block, brim level, front panel squared", "mockup"),
    ("cap-worn", "Cap worn", f"{PERSON} wears an unmarked six-panel cap, brim casting a clean shadow line", "apparel"),
    ("pin-set", "Pin set", f"three unmarked enamel pins on a matte card, evenly spaced, bold outlines", "mockup"),
    ("sticker-sheet", "Sticker sheet", f"an unmarked sheet of plain die-cut shapes on a pale ground, edges crisp", "mockup"),
    ("poster-wall", "Poster wall", f"an unmarked blank poster pinned flat to a matte wall, even frontal light", "mockup"),
    ("poster-room", "Poster room", f"an unmarked blank poster hangs above an unmarked bench in a quiet room", "post"),
    ("tote-front", "Tote front", f"an unmarked canvas tote hangs from a plain hook, straps squared, base flat", "mockup"),
    ("tote-carried", "Tote carried", f"{PERSON} carries an unmarked canvas tote on one shoulder, walking at ease", "apparel"),
    ("notebook-cover", "Notebook cover", f"an unmarked hardcover notebook on pale stone, lid closed, spine to the light", "mockup"),
    ("bottle-front", "Bottle front", f"an unmarked insulated bottle stands on a bare surface, condensation beading", "mockup"),
    ("sock-detail", "Sock detail", f"an unmarked ribbed sock on a pale ground, cuff ribbing readable, soft key", "mockup"),
    ("lookbook-full", "Full look", f"{PERSON} stands full length in unmarked charcoal layers against a matte wall", "cover"),
    ("lookbook-detail", "Look detail", f"a close unmarked cuff and wristwatch on {PERSON}, fabric texture leading", "cover"),
    ("shop-tile", "Shop tile", f"{GOODS} sits centred on an even field with generous margin for a price line", "post"),
    ("shop-bundle", "Shop bundle", f"an unmarked tee, mug, and cap arranged in a tight triangle on pale ground", "post"),
    ("shop-tease", "Drop tease", f"an unmarked plain box tied with cord on a matte table, one corner lit", "cover"),
]


def _rows(stem: str, platform: str, spec: list[tuple[str, str, str, str]]) -> list[dict[str, str]]:
    """Build one creator catalog.

    Arguments:
        stem: Catalog file stem, also the row id prefix.
        platform: Display noun used in the row label.
        spec: Slug, display thing, scene text, and deliverable key per row.

    Returns:
        Row dicts ready to write.
    """
    rows: list[dict[str, str]] = []
    for slug, thing, scene, deliverable in spec:
        craft = CRAFT[deliverable]
        prompt = f"A photoreal still of {scene}. {craft} {UNMARKED}"
        rows.append(
            {
                "id": f"{stem}-{slug}",
                "label": f"{platform} {thing}",
                "prompt": prompt,
            }
        )
    return rows


def hand_catalogs() -> dict[str, list[dict[str, str]]]:
    """Return the four creator catalogs the main generator does not own.

    Returns:
        Catalog stem to rows.
    """
    return {
        "creator_youtube": _rows("creator_youtube", "YouTube", YOUTUBE),
        "creator_instagram": _rows("creator_instagram", "Instagram", INSTAGRAM),
        "creator_twitch": _rows("creator_twitch", "Twitch", TWITCH),
        "creator_merch": _rows("creator_merch", "Merch", MERCH),
    }


def main() -> None:
    """Write the four creator catalogs to the shipped samples directory.

    Returns:
        None.
    """
    DEST.mkdir(parents=True, exist_ok=True)
    for name, rows in hand_catalogs().items():
        if len(rows) != 30:
            raise SystemExit(f"{name} has {len(rows)} rows, need 30")
        labels = [row["label"] for row in rows]
        if len(set(labels)) != len(labels):
            raise SystemExit(f"{name} duplicate labels")
        ids = [row["id"] for row in rows]
        if len(set(ids)) != len(ids):
            raise SystemExit(f"{name} duplicate ids")
        blob = json.dumps(rows, indent=2) + "\n"
        if not blob.isascii():
            raise SystemExit(f"{name} carries non-ascii text")
        dest = DEST / f"{name}.json"
        dest.write_text(blob, encoding="utf-8")
        print(f"wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
