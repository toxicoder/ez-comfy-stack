"""Goal-specific Klein stills catalogs.

Three lanes read from a generic 16:9 blob today: the tall caption lanes, the
plate lanes that sit behind type, and the very wide header lanes. Each gets its
own catalog here so the operator picks a deliverable instead of a mood. The
craft each deliverable has to survive arrives with the goal clause ``_write``
appends, so rows name the place, the light, the lens, and how the frame is
built for the job, and leave the goal language to the registry.

Imported only by ``_build_sample_catalogs.py``.
"""

from __future__ import annotations

from _build_sample_catalogs import _klein, _row

WIZARD = "an original techno wizard in an unmarked dark indigo-violet suede running coat"
WIZARD_NAP = f"{WIZARD} with silk-felt nap and faint circuit-thread seams"
WIZARD_STAFF = f"{WIZARD} with a compact unmarked data-staff"
WIZARD_GLYPH = f"{WIZARD} with glyph rings at the staff"

_VERTICAL = "klein_vertical"
_PLATE = "klein_plate"
_BANNER = "klein_banner"

_VERTICAL_TAIL = "Vertical 9:16 framing."
_PLATE_TAIL = "Plate framing with the subject held off-axis."
_BANNER_TAIL = "Ultra-wide banner framing."


def klein_vertical() -> list[dict[str, str]]:
    """Thirty tall frames for the caption-headroom lanes.

    Each row carries the place, the light, the lens, and one sentence on how
    the frame reads top to bottom, since these lanes ship a tall still that has
    to keep its subject clear of whatever the player lays over it.
    """
    shots = [
        (
            "stairwell-skylight",
            "Stairwell skylight",
            f"{WIZARD_NAP}, chin level, face to camera",
            "climbs an unmarked concrete stair under a high skylight",
            "Diffuse skylight from directly above, soft shadow under the brow, pale walls returning light up the shaft.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. Tread, subject, and lit opening read one above the next. "
            + _VERTICAL_TAIL,
        ),
        (
            "rain-overpass",
            "Rain overpass",
            f"{WIZARD}, collar turned up, face to camera",
            "stands on the top landing of an unmarked pedestrian overpass in rain",
            "Sodium practicals down the stair, wet steel throwing the light back, city glow soft behind.",
            "Slightly below eyeline. 28mm-equivalent wide. The stair climbs through the whole height of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "lift-shaft",
            "Lift shaft",
            f"{WIZARD_STAFF}, face to camera",
            "rises in an unmarked glass lift through a bare concrete core",
            "Cool shaft light sweeping past from the landings, one warm practical in the car overhead.",
            "Chest height. 24mm-equivalent wide. Landings pile up behind the subject toward the ceiling of the shaft. "
            + _VERTICAL_TAIL,
        ),
        (
            "fire-escape",
            "Fire escape landing",
            f"{WIZARD}, three-quarter turn to camera",
            "stands on an unmarked fire-escape landing above a quiet street",
            "Warm window light from the floor beside, cool dawn coming up off the street below.",
            "Slightly above eyeline. 35mm-equivalent classic reportage view. Railing, subject, and street level read as three tiers. "
            + _VERTICAL_TAIL,
        ),
        (
            "quarry-cut",
            "Quarry cut",
            f"{WIZARD} mid-stride",
            "crosses the floor of a deep unmarked quarry cut",
            "Hard sun hitting the high wall first, the floor still in cool shade, dust standing in the beam.",
            "Low angle from boot height. 24mm-equivalent wide. Both walls climb clean out of the top of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "hillside-stair",
            "Hillside stair",
            f"{WIZARD_NAP}, face to camera",
            "pauses halfway up a long unmarked stone stair cut into a hillside",
            "Open shade with a warm bounce off the steps below, terraces soft behind.",
            "Match a standing eyeline. 85mm-equivalent short telephoto. The steps compress upward through the whole frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "basalt-falls",
            "Basalt falls",
            f"{WIZARD}, collar turned up",
            "stands on wet basalt beneath a tall unmarked waterfall",
            "Soft green shade with the falls blowing bright behind, spray lit close to the lens.",
            "Slightly below eyeline. 28mm-equivalent wide. Water runs the full height behind the subject. "
            + _VERTICAL_TAIL,
        ),
        (
            "sandstone-slot",
            "Sandstone slot",
            f"{WIZARD_STAFF} mid-stride",
            "walks a narrow unmarked canyon between towering sandstone walls",
            "Bounced warm light off the far wall, the slot in cool shade, one beam landing at the subject's feet.",
            "Match a standing eyeline. 24mm-equivalent wide. The walls funnel the eye upward past the subject. "
            + _VERTICAL_TAIL,
        ),
        (
            "bridge-tower",
            "Bridge tower landing",
            f"{WIZARD}, chin level, face to camera",
            "stands on a maintenance landing of an unmarked bridge tower at blue hour",
            "One warm work lamp at the shoulder, the bay and its lights falling away far below.",
            "Slightly above eyeline. 35mm-equivalent classic reportage view. Cables draw the eye up through the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "vine-house",
            "Vine house",
            f"{WIZARD}, face to camera",
            "stands in a tall unmarked glasshouse where vines climb twine to the roof",
            "Dappled glass light, humid air, leaf sheen and condensation high on the panes.",
            "Match a standing eyeline. 50mm-equivalent. Vine, subject, and glazed roof read bottom to top. "
            + _VERTICAL_TAIL,
        ),
        (
            "dock-piling",
            "Dock piling",
            f"{WIZARD_NAP} mid-stride",
            "crosses an unmarked working dock past a tall timber piling",
            "Flat morning light off the water, rigging lines catching the first sun.",
            "Low angle from knee height. 24mm-equivalent wide. The piling runs out of the top of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "silo-line",
            "Silo line",
            f"{WIZARD} mid-stride",
            "walks a corridor of tall unmarked concrete grain silos at hard noon",
            "Overhead sun, pale concrete bouncing into the shade between the cylinders, heat shimmer at ground level.",
            "Match a standing eyeline. 28mm-equivalent wide. The cylinders rise past the head of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "roof-mast",
            "Rooftop mast",
            f"{WIZARD_STAFF}, face to camera",
            "stands on the flat roof of an unmarked low block beside a tall antenna mast",
            "Strong high sun, the mast shadow crossing the deck, sky pale and clean overhead.",
            "Slightly below eyeline. 24mm-equivalent wide. Mast, subject, and open sky hold the height in order. "
            + _VERTICAL_TAIL,
        ),
        (
            "archive-stack",
            "Archive aisle",
            f"{WIZARD}, chin level, face to camera",
            "stands in a tall unmarked archive aisle of plain grey boxes",
            "Warm practical at the end of the aisle, dust lit in the beam, board returning a soft amber.",
            "Chest height. 85mm-equivalent short telephoto. Shelving runs up past the top of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "lone-pine-ridge",
            "Lone pine ridge",
            f"{WIZARD} mid-stride",
            "crosses a fogged ridge beside one tall pine",
            "Thin winter sun from the right, blue shadow in the needle litter, fog dissolving the far slope.",
            "Match a standing eyeline. 50mm-equivalent. Trunk and crown own the upper half of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "viaduct-arch",
            "Viaduct arch",
            f"{WIZARD_NAP} mid-stride",
            "passes beneath a tall unmarked viaduct arch on a gravel path",
            "Cool shade under the span with the road beyond blown bright, one sunlit band on the spandrel.",
            "Low angle from hip height. 24mm-equivalent wide. The arch springs from both sides and closes the top. "
            + _VERTICAL_TAIL,
        ),
        (
            "observatory-dome",
            "Observatory dome",
            f"{WIZARD_GLYPH}, face to camera",
            "stands on the floor of an unmarked observatory under an open dome",
            "Moonlight through the slit with one warm floor practical under the chin, the dome interior in deep shade.",
            "Slightly below eyeline. 28mm-equivalent wide. The dome curves over the subject and closes the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "reed-marsh",
            "Reed marsh",
            f"{WIZARD}, face to camera",
            "waits on an unmarked boardwalk in a marsh of tall reeds at last light",
            "Low amber sun backlighting the seed heads, the water dark and flat behind.",
            "Match a standing eyeline. 85mm-equivalent short telephoto. Reeds stand taller than the subject and fill the upper frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "column-hall",
            "Column hall",
            f"{WIZARD} mid-stride",
            "crosses an unmarked vaulted hall of plain stone columns",
            "High clerestory light falling in slabs, the floor pale, the vault lost in shade above.",
            "Match a standing eyeline. 24mm-equivalent wide. One column runs the whole height beside the subject. "
            + _VERTICAL_TAIL,
        ),
        (
            "dam-walkway",
            "Dam walkway",
            f"{WIZARD_NAP}, collar turned up",
            "stands on an unmarked dam walkway as spray drifts up from the spillway",
            "Bright open sky, mist lit from behind, wet concrete shining underfoot.",
            "Slightly below eyeline. 28mm-equivalent wide. The spillway face drops the full height of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "cableway-landing",
            "Cableway landing",
            f"{WIZARD_STAFF}, face to camera",
            "stands at an unmarked hillside cableway landing with the cable running overhead",
            "Cool shade at the landing, the valley beyond bright and hazy, the cable catching the sun.",
            "Match a standing eyeline. 50mm-equivalent. The cable draws a line up and out of the top of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "lighthouse-stair",
            "Lighthouse stair",
            f"{WIZARD}, chin level, face to camera",
            "climbs the tight unmarked stair inside a disused lighthouse",
            "One small window at each turn, warm painted iron, the lamp room dark above.",
            "Low angle from the landing below. 24mm-equivalent wide. The stair coils up through the whole height. "
            + _VERTICAL_TAIL,
        ),
        (
            "fig-court",
            "Fig courtyard",
            f"{WIZARD}, face to camera",
            "stands beneath a tall fig tree in a narrow unmarked courtyard",
            "Open shade overhead with hard sun striking the upper wall, leaf shadow moving on the plaster.",
            "Match a standing eyeline. 50mm-equivalent. Canopy, subject, and sunlit wall rise in order. "
            + _VERTICAL_TAIL,
        ),
        (
            "timber-shed",
            "Timber shed",
            f"{WIZARD_NAP} mid-stride",
            "walks the aisle of a tall unmarked timber-framed store house",
            "Shafts through gaps in the board walls, dust in every beam, cool shade between.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The roof trusses hang high above the subject. "
            + _VERTICAL_TAIL,
        ),
        (
            "bamboo-hollow",
            "Bamboo hollow",
            f"{WIZARD}, face to camera",
            "stands in a deep unmarked bamboo hollow where the stalks close overhead",
            "Green light filtered from above, bright at the crown and even at the face.",
            "Slightly below eyeline. 28mm-equivalent wide. Stalks run the full height and screen the sky. "
            + _VERTICAL_TAIL,
        ),
        (
            "spiral-ramp",
            "Spiral ramp",
            f"{WIZARD_STAFF} mid-stride",
            "walks the curve of an unmarked concrete parking ramp at dawn",
            "Low sun raking the open deck, the soffit of the turn shading the level above.",
            "Match a standing eyeline. 24mm-equivalent wide. The deck above closes the top of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "rain-canopy",
            "Rain canopy",
            f"{WIZARD}, collar turned up, face to camera",
            "stands under a tall unmarked canopy as rain falls past its edge",
            "Cool rain light on one side, a warm practical glow from the structure overhead.",
            "Chest height. 50mm-equivalent. Rain falls the whole height beside the subject. "
            + _VERTICAL_TAIL,
        ),
        (
            "turbine-track",
            "Turbine track",
            f"{WIZARD} mid-stride",
            "crosses an unmarked highland service track below one tall turbine",
            "Flat cloud light, a shadow moving across the grass, the tower pale against grey.",
            "Low angle from hip height. 24mm-equivalent wide. The tower climbs clean out of the top of the frame. "
            + _VERTICAL_TAIL,
        ),
        (
            "mangrove-boardwalk",
            "Mangrove boardwalk",
            f"{WIZARD_NAP} mid-stride",
            "walks an unmarked mangrove boardwalk at first light",
            "Soft morning light filtering through the canopy, still water mirroring the roots below.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. Roots, subject, and canopy read floor to crown. "
            + _VERTICAL_TAIL,
        ),
        (
            "vine-atrium",
            "Vine atrium",
            f"{WIZARD_GLYPH}, chin level, face to camera",
            "stands at the center of a tall unmarked atrium planted to the ceiling",
            "Skylight falling the full height, warm wall bounce at the face, planted tiers soft behind.",
            "Slightly below eyeline. 24mm-equivalent wide. Planted tiers climb the whole frame behind the subject. "
            + _VERTICAL_TAIL,
        ),
    ]
    return [
        _row(f"{_VERTICAL}-{slug}", label, _klein(subject, place, light, camera))
        for slug, label, subject, place, light, camera in shots
    ]


def klein_plate() -> list[dict[str, str]]:
    """Thirty background plates for the type-overlay lanes.

    Each row keeps the subject small and off the middle and hands the rest of
    the frame to one smooth surface at a steady value, which is the whole job
    for a plate: the headline lands on picture, the picture stays out of the
    way.
    """
    plates = [
        (
            "lime-plaster-plate",
            "Lime plaster plate",
            f"{WIZARD}, small in frame at the right third, face to camera",
            "stands against a washed lime plaster wall that fills the whole frame",
            "Large soft window key from camera left, gentle falloff across the plaster, the wall held at one steady value.",
            "Chest height. 50mm-equivalent. The open two-thirds reads as a single smooth plane. " + _PLATE_TAIL,
        ),
        (
            "linen-sweep-plate",
            "Linen sweep",
            f"{WIZARD_NAP}, seated low at the left third",
            "sits on a low stool before an unmarked warm-grey linen backdrop",
            "Broad diffused key at forty-five degrees, soft fill opposite, the weave staying quiet behind the shoulder.",
            "Chest height. 85mm-equivalent short telephoto. The linen carries one soft gradient through the empty side. "
            + _PLATE_TAIL,
        ),
        (
            "charcoal-sweep-plate",
            "Charcoal sweep",
            f"{WIZARD}, three-quarter turn to camera, placed at the right edge of the middle",
            "stands on a stool against an unmarked charcoal studio sweep",
            "Soft top key with a faint rim lifting the shoulder off the sweep, the backdrop falling deep and smooth.",
            "Slightly below eyeline. 135mm-equivalent telephoto. The sweep holds one dark value where the words will go. "
            + _PLATE_TAIL,
        ),
        (
            "board-formed-wall",
            "Board-formed wall",
            f"{WIZARD_STAFF}, small in frame at the left third, face to camera",
            "stands against an unmarked board-formed concrete wall with even tie marks",
            "Even north daylight across the concrete, the form grain soft and the shadow side kept gentle.",
            "Match a standing eyeline. 50mm-equivalent. The tie marks run level and stay low in contrast. " + _PLATE_TAIL,
        ),
        (
            "salt-pan-fog",
            "Salt pan fog",
            f"{WIZARD}, small in frame at the right third, mid-stride",
            "crosses an unmarked salt pan where fog dissolves the horizon",
            "Diffuse light in every direction, the pan and sky merging into one pale sheet.",
            "Match a standing eyeline. 85mm-equivalent short telephoto. The fog leaves one open pale field beside the subject. "
            + _PLATE_TAIL,
        ),
        (
            "high-sea-horizon",
            "High sea horizon",
            f"{WIZARD}, low in frame at the left third, collar turned up",
            "stands at an unmarked sea wall with open water filling the frame behind",
            "Flat early light on the water, the horizon set high, small waves holding one mid value.",
            "Slightly below eyeline. 50mm-equivalent. Sky and sea read as one soft band above the subject. " + _PLATE_TAIL,
        ),
        (
            "pale-dune-face",
            "Pale dune face",
            f"{WIZARD_NAP}, small in frame at the left third, mid-stride",
            "climbs the lee side of an unmarked pale dune",
            "Low sun from behind the camera, ripple texture softening as it recedes, the slope lit clean from crest to toe.",
            "Match a standing eyeline. 85mm-equivalent short telephoto. The slope gives the frame one smooth ramp. "
            + _PLATE_TAIL,
        ),
        (
            "teal-wash-wall",
            "Teal wash wall",
            f"{WIZARD}, small in frame at the right third, face to camera",
            "stands against an unmarked deep teal painted wall",
            "Soft key close and large, the paint keeping one clean hue a full stop behind the subject.",
            "Chest height. 85mm-equivalent short telephoto. The paint holds one quiet hue across the open side. "
            + _PLATE_TAIL,
        ),
        (
            "condensation-glass",
            "Condensation glass",
            f"{WIZARD_STAFF}, small in frame at the left third, face to camera",
            "stands beside a plain unmarked glass wall fogged with condensation",
            "Even daylight bleeding through the glass from behind, droplets catching small soft points of light.",
            "Match a standing eyeline. 50mm-equivalent. The fogged pane gives the open side a single soft bloom. "
            + _PLATE_TAIL,
        ),
        (
            "bleached-planks",
            "Bleached planks",
            f"{WIZARD}, small in frame at the right third, three-quarter turn to camera",
            "leans against an unmarked bleached plank wall with even grain",
            "Side key off a large bounce panel, the plank grain kept low and the seams soft.",
            "Chest height. 85mm-equivalent short telephoto. The boards run level through the empty two-thirds. "
            + _PLATE_TAIL,
        ),
        (
            "terrazzo-field",
            "Terrazzo field",
            f"{WIZARD}, small in frame at the left third, mid-stride",
            "crosses a wide unmarked terrazzo floor in a bare room",
            "Overhead diffused panels, the aggregate scattering fine sparkle, the field staying even end to end.",
            "Slightly above eyeline. 35mm-equivalent classic reportage view. The floor opens into one quiet field. "
            + _PLATE_TAIL,
        ),
        (
            "still-pool",
            "Still pool",
            f"{WIZARD_NAP}, small in frame at the right third, face to camera",
            "stands at the coping of an unmarked still pool that fills the frame",
            "Cyan bounce up off the water, the surface holding one flat tone with the faintest ripple.",
            "Slightly above eyeline. 50mm-equivalent. The water gives the open side a single cool plane. " + _PLATE_TAIL,
        ),
        (
            "ivory-paper-sweep",
            "Ivory paper sweep",
            f"{WIZARD}, small in frame at the left third, chin level, face to camera",
            "sits before an unmarked ivory paper sweep in a quiet studio",
            "Large key at camera left with a feathered edge, the paper warming gently toward the far side.",
            "Chest height. 85mm-equivalent short telephoto. The sweep grades once, softly, and stops. " + _PLATE_TAIL,
        ),
        (
            "meadow-sky",
            "Meadow sky",
            f"{WIZARD_STAFF}, low in frame at the right third, mid-stride",
            "walks an unmarked meadow of short grass under a wide empty sky",
            "Open shade with a bright sky overhead, the grass texture soft from this distance.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The sky fills the frame above the horizon line. "
            + _PLATE_TAIL,
        ),
        (
            "wet-asphalt-mist",
            "Wet asphalt mist",
            f"{WIZARD}, small in frame at the left third, mid-stride",
            "crosses a wide unmarked asphalt lot held by light mist",
            "Soft overcast with the wet surface mirroring the sky, the paint lines painted out by the water.",
            "Slightly above eyeline. 28mm-equivalent wide. The lot opens into one grey reflective field. " + _PLATE_TAIL,
        ),
        (
            "snowfield-high-horizon",
            "Snowfield",
            f"{WIZARD_NAP}, small in frame at the right third, collar turned up",
            "stands at the edge of an unmarked snowfield with the horizon set high",
            "Bright flat snow light from below, the sky a clean pale cap, breath visible in cold air.",
            "Match a standing eyeline. 85mm-equivalent short telephoto. The snow holds one bright even sheet. "
            + _PLATE_TAIL,
        ),
        (
            "fog-pine-hill",
            "Fog pine hill",
            f"{WIZARD}, small in frame at the left third, mid-stride",
            "stands on an unmarked hill path where fog pads the pine rows behind",
            "Soft directional light through the fog, each ridge a step paler than the last.",
            "Slightly below eyeline. 135mm-equivalent telephoto. The fog flattens the far side into one pale tone. "
            + _PLATE_TAIL,
        ),
        (
            "glazed-tile-wall",
            "Glazed tile wall",
            f"{WIZARD_STAFF}, small in frame at the right third, face to camera",
            "stands against an unmarked wall of plain glazed tile in soft daylight",
            "Even front light with the glaze throwing small soft highlights, the grout lines staying gentle.",
            "Match a standing eyeline. 50mm-equivalent. The tiling carries the open side at one calm value. " + _PLATE_TAIL,
        ),
        (
            "long-stair-wall",
            "Long stair wall",
            f"{WIZARD}, small in frame at the left third, mid-stride",
            "climbs an unmarked concrete stair beside a plain painted wall",
            "Daylight from an unseen window ahead, the wall catching it as one bright ramp.",
            "Slightly below eyeline. 35mm-equivalent classic reportage view. The wall climbs as one clean bright plane. "
            + _PLATE_TAIL,
        ),
        (
            "dawn-lake-fog",
            "Dawn lake fog",
            f"{WIZARD_NAP}, small in frame at the right third, face to camera",
            "stands on an unmarked jetty on a lake held by dawn fog",
            "Rose-grey light lifting off the water, the far shore dissolved, the surface flat as glass.",
            "Match a standing eyeline. 85mm-equivalent short telephoto. Water and fog merge into one soft field. "
            + _PLATE_TAIL,
        ),
        (
            "dark-slate-floor",
            "Dark slate floor",
            f"{WIZARD}, small in frame at the left third, mid-stride",
            "crosses a wide unmarked slate floor in a bare hall",
            "A single soft source overhead, the slate taking a low sheen, the grain staying quiet from this height.",
            "High angle looking down. 35mm-equivalent classic reportage view. The slate gives the frame one dark sheet. "
            + _PLATE_TAIL,
        ),
        (
            "adobe-wall",
            "Adobe wall",
            f"{WIZARD_STAFF}, small in frame at the right third, face to camera",
            "stands against a sun-warmed unmarked adobe wall",
            "Warm raking light from the right, the trowel work soft, the shade side filled by the ground.",
            "Chest height. 50mm-equivalent. The wall carries one warm tone through the open two-thirds. " + _PLATE_TAIL,
        ),
        (
            "rehearsal-room",
            "Rehearsal room",
            f"{WIZARD}, small in frame at the left third, arms relaxed at the sides",
            "stands in an unmarked rehearsal room before a plain acoustic wall",
            "Even ceiling panels with a warm bounce off the sprung floor, the wall kept flat and plain.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The wall holds one even mid tone. "
            + _PLATE_TAIL,
        ),
        (
            "fogged-glasshouse",
            "Fogged glasshouse",
            f"{WIZARD_NAP}, small in frame at the right third, face to camera",
            "stands inside an unmarked glasshouse with the panes fogged over",
            "Diffuse light through the condensation, green bounce low on the coat, the framing bars soft.",
            "Slightly below eyeline. 50mm-equivalent. The fogged panes merge into one bright sheet. " + _PLATE_TAIL,
        ),
        (
            "cotton-drape",
            "Cotton drape",
            f"{WIZARD}, small in frame at the left third, three-quarter turn to camera",
            "stands before a plain unmarked cotton drape hung wall to wall",
            "Broad soft key with the folds falling gentle, the cloth taking an even warm tone.",
            "Chest height. 85mm-equivalent short telephoto. The cloth reads as one soft vertical wash. " + _PLATE_TAIL,
        ),
        (
            "low-tideline",
            "Low tideline",
            f"{WIZARD_STAFF}, low in frame at the right third, mid-stride",
            "walks an unmarked beach where the tide line sits low in the frame",
            "Bright open sky, wet sand mirroring it, the surf reduced to one soft line far behind.",
            "Slightly above eyeline. 28mm-equivalent wide. Wet sand and sky fill the frame with one bright field. "
            + _PLATE_TAIL,
        ),
        (
            "bright-salt-flat",
            "Bright salt flat",
            f"{WIZARD}, small in frame at the left third, mid-stride",
            "crosses a wide unmarked salt flat under a bright sky",
            "Bounced ground light from below, hard clean horizon, hot air shimmer held at the edges.",
            "Match a standing eyeline. 24mm-equivalent wide. The flat opens into one white even sheet. " + _PLATE_TAIL,
        ),
        (
            "unglazed-tile-stack",
            "Unglazed tiles",
            f"{WIZARD_NAP}, small in frame at the right third, face to camera",
            "stands beside a wall-high stack of unmarked unglazed tile",
            "Soft window light from the right, clay dust holding the beam, the stack edges kept soft.",
            "Chest height. 50mm-equivalent. The stack gives the open side one matte earth tone. " + _PLATE_TAIL,
        ),
        (
            "resin-floor-room",
            "Resin floor room",
            f"{WIZARD_STAFF}, small in frame at the left third, chin level, face to camera",
            "stands in a bare unmarked room with a smooth poured resin floor",
            "Even ceiling light with the floor returning a soft mirror of the panels, the walls plain.",
            "Slightly above eyeline. 35mm-equivalent classic reportage view. The floor pours into one smooth gradient. "
            + _PLATE_TAIL,
        ),
        (
            "paneled-meeting-wall",
            "Paneled wall",
            f"{WIZARD_NAP}, small in frame at the left third, shoulders square, face to camera",
            "stands in an unmarked meeting room before a plain wood panel wall",
            "Even ceiling panels with a warm bounce off the table below, the veneer grain kept soft.",
            "Chest height. 85mm-equivalent short telephoto. The veneer holds one warm mid tone across the frame. "
            + _PLATE_TAIL,
        ),
    ]
    return [
        _row(f"{_PLATE}-{slug}", label, _klein(subject, place, light, camera))
        for slug, label, subject, place, light, camera in plates
    ]


def klein_banner() -> list[dict[str, str]]:
    """Thirty very wide frames for the header lanes.

    Each row puts one subject to a flank, hands the middle to a smooth run of
    scene, and keeps the flanks free of anything a device crop would miss,
    because these lanes ship a header that gets cropped differently on every
    screen.
    """
    banners = [
        (
            "concourse-run",
            "Concourse run",
            f"{WIZARD} mid-stride, weighted at the right third",
            "crosses a vast unmarked concourse of concrete and glass",
            "Cool overhead banks in a long row, the far plane hazy, the floor carrying the line of light back.",
            "Hip height. 24mm-equivalent wide. The middle of the frame stays smooth and the flanks stay empty. "
            + _BANNER_TAIL,
        ),
        (
            "salt-pan-wide",
            "Salt pan wide",
            f"{WIZARD_NAP} mid-stride, weighted at the left third",
            "crosses a wide unmarked salt pan under a bright sky",
            "Bounced ground light from below, one clean horizon, shimmer held far off at the flanks.",
            "Match a standing eyeline. 28mm-equivalent wide. One focal point only, with open pan either side. "
            + _BANNER_TAIL,
        ),
        (
            "harbor-quay-dusk",
            "Harbor quay",
            f"{WIZARD_STAFF}, weighted at the right third, collar turned up",
            "stands on a long unmarked harbor quay at blue hour",
            "Cool sky above the water with warm ship lights low along the line, wet asphalt returning them.",
            "Slightly below eyeline. 24mm-equivalent wide. The quay runs level through the middle and the ends stay plain. "
            + _BANNER_TAIL,
        ),
        (
            "apron-gantries",
            "Freight apron",
            f"{WIZARD}, weighted at the left third, mid-stride",
            "crosses a wide unmarked freight apron under standing gantries",
            "Flat overcast with the gantry paint pale, floodlights still burning low along the apron.",
            "Match a standing eyeline. 24mm-equivalent wide. The gantries sit far back so the middle reads clear. "
            + _BANNER_TAIL,
        ),
        (
            "long-beach-low-sun",
            "Long beach",
            f"{WIZARD_NAP} mid-stride, weighted at the left third",
            "walks a long unmarked tropical beach as the sun sits low",
            "Low sun along the water, wet sand mirroring the sky, surf broken to one soft line.",
            "Match a standing eyeline. 28mm-equivalent wide. The tideline draws the eye across from flank to flank. "
            + _BANNER_TAIL,
        ),
        (
            "playa-road",
            "Playa road",
            f"{WIZARD} mid-stride, weighted at the right third",
            "walks the shoulder of an unmarked road crossing a flat playa",
            "Hard sun, heat shimmer on the horizon, the flats pale on both sides of the strip.",
            "Hip height. 24mm-equivalent wide. The road runs dead level and the shoulders stay bare. " + _BANNER_TAIL,
        ),
        (
            "viaduct-side",
            "Viaduct side",
            f"{WIZARD_STAFF} mid-stride, weighted at the left third",
            "crosses an unmarked viaduct seen from a low field beside it",
            "Late sun raking the spandrels, the arches repeating, the field in front soft and low.",
            "Slightly below eyeline. 24mm-equivalent wide. The arches repeat evenly with the subject breaking the run once. "
            + _BANNER_TAIL,
        ),
        (
            "glasshouse-bench-row",
            "Glasshouse bench row",
            f"{WIZARD}, weighted at the right third, face to camera",
            "stands beside a long bench row in a wide unmarked glasshouse",
            "Dappled glass light, humid air, benches and trays repeating into a soft haze.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The bench line runs level with the middle kept low. "
            + _BANNER_TAIL,
        ),
        (
            "reading-hall-long-tables",
            "Long tables",
            f"{WIZARD_NAP}, weighted at the left third, face to camera",
            "pauses beside long plain tables in a wide unmarked reading hall",
            "Green-shaded practicals along the tables, dust lit in a side window shaft, the far end soft.",
            "Chest height. 35mm-equivalent classic reportage view. The table line carries the frame with one subject only. "
            + _BANNER_TAIL,
        ),
        (
            "plant-room-pipes",
            "Plant room",
            f"{WIZARD_STAFF} mid-stride, weighted at the right third",
            "crosses a long unmarked plant room of plain insulated pipes",
            "Cool ceiling banks with warm status points in a row, the polished floor echoing both.",
            "Hip height. 24mm-equivalent wide. The pipe run stretches end to end with the subject breaking it once. "
            + _BANNER_TAIL,
        ),
        (
            "cyclorama-sky",
            "Cyclorama sky",
            f"{WIZARD}, weighted at the left third, face to camera",
            "stands on an unmarked studio cyclorama painted with a soft graded sky",
            "Broad even wash across the curve, the floor blending into the sky in one unbroken sweep.",
            "Match a standing eyeline. 28mm-equivalent wide. One gradient covers the whole frame with nothing else in it. "
            + _BANNER_TAIL,
        ),
        (
            "factory-benches",
            "Factory benches",
            f"{WIZARD_NAP} mid-stride, weighted at the right third",
            "walks a long unmarked factory floor of plain teak benches",
            "North windows in a row on one side, bench tops pale, swarf hooks empty along the rails.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The bench rows run level and the aisles stay clear. "
            + _BANNER_TAIL,
        ),
        (
            "mangrove-flats",
            "Mangrove flats",
            f"{WIZARD} mid-stride, weighted at the left third",
            "crosses wide unmarked mangrove flats at low tide",
            "Early light across the mud, roots repeating, mist sitting low a long way back.",
            "Slightly below eyeline. 24mm-equivalent wide. The flats open wide with the roots held far behind. "
            + _BANNER_TAIL,
        ),
        (
            "sports-hall-floor",
            "Sports hall",
            f"{WIZARD_STAFF}, weighted at the right third, arms relaxed at the sides",
            "stands on the wide plain floor of an unmarked sports hall",
            "Even high ceiling banks, the varnish taking a soft sheen, the far wall plain and pale.",
            "Slightly above eyeline. 28mm-equivalent wide. The floor gives the frame one even reflective field. "
            + _BANNER_TAIL,
        ),
        (
            "colonnade-arches",
            "Colonnade",
            f"{WIZARD_NAP} mid-stride, weighted at the left third",
            "walks a long unmarked colonnade of plain stone arches",
            "Sunlight raking the columns from the open side, the arcade in cool shade, shadows evenly spaced.",
            "Match a standing eyeline. 24mm-equivalent wide. The columns repeat evenly with one subject in the run. "
            + _BANNER_TAIL,
        ),
        (
            "rail-canopy-platform",
            "Rail canopy",
            f"{WIZARD}, weighted at the right third, collar turned up",
            "waits on an unmarked rail platform under a long canopy",
            "Sodium lights along the canopy spine, cool dawn beyond the far rail, wet edge of the platform shining.",
            "Hip height. 35mm-equivalent classic reportage view. The canopy spine runs level with the ends left plain. "
            + _BANNER_TAIL,
        ),
        (
            "vineyard-rows",
            "Vineyard rows",
            f"{WIZARD_STAFF} mid-stride, weighted at the left third",
            "walks the headland of an unmarked vineyard on flat ground",
            "Low morning sun along the rows, posts repeating, a soft haze standing over the far parcel.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The rows draw across the frame and the headland stays bare. "
            + _BANNER_TAIL,
        ),
        (
            "turbine-line",
            "Turbine line",
            f"{WIZARD_NAP} mid-stride, weighted at the right third",
            "crosses an unmarked moor with a line of turbines far behind",
            "Flat cloud light, grass in one mid tone, the towers pale and set well back.",
            "Match a standing eyeline. 24mm-equivalent wide. The towers sit far behind so the middle stays open. "
            + _BANNER_TAIL,
        ),
        (
            "museum-plinths",
            "Museum hall",
            f"{WIZARD}, weighted at the left third, face to camera",
            "stands among low plain plinths in a wide unmarked museum hall",
            "Soft skylight from the roof grid, pale plaster, the floor a single matte field.",
            "Match a standing eyeline. 28mm-equivalent wide. The plinths sit low and the wall behind holds one tone. "
            + _BANNER_TAIL,
        ),
        (
            "auditorium-house",
            "Auditorium",
            f"{WIZARD_STAFF}, weighted at the right third, face to camera",
            "stands at the apron of an unmarked auditorium of plain seats",
            "One warm booth spot on the apron, house lights down, seat rows receding into soft dark.",
            "Slightly below eyeline. 35mm-equivalent classic reportage view. The seat rows run level and dim toward the ends. "
            + _BANNER_TAIL,
        ),
        (
            "boardwalk-night",
            "Boardwalk at night",
            f"{WIZARD_NAP} mid-stride, weighted at the left third",
            "walks a long unmarked timber boardwalk at night",
            "Warm lamps set at even intervals, the sea dark on one side, the planks shining underfoot.",
            "Match a standing eyeline. 24mm-equivalent wide. The lamps repeat along one level line with the subject holding the near third. "
            + _BANNER_TAIL,
        ),
        (
            "river-flat",
            "Canyon river flat",
            f"{WIZARD} mid-stride, weighted at the right third",
            "crosses a wide unmarked river flat with canyon walls far behind",
            "Hard sun on the far walls, the flat in open shade, dust fine in the air.",
            "Match a standing eyeline. 24mm-equivalent wide. The walls stay far back and the flat stays empty. "
            + _BANNER_TAIL,
        ),
        (
            "deck-roof-dawn",
            "Deck roof",
            f"{WIZARD_STAFF} mid-stride, weighted at the left third",
            "crosses the open roof deck of an unmarked parking structure at dawn",
            "Low sun along the parapet, the deck pale, the stair block sitting well back.",
            "Hip height. 24mm-equivalent wide. The parapet runs level across the whole frame. " + _BANNER_TAIL,
        ),
        (
            "office-floor-glass",
            "Office floor",
            f"{WIZARD_NAP}, weighted at the right third, face to camera",
            "stands in a long unmarked office floor of plain desks and glass",
            "Even ceiling panels with daylight from a ribbon window, the carpet holding one quiet tone.",
            "Chest height. 35mm-equivalent classic reportage view. The window band stays level and unbroken. "
            + _BANNER_TAIL,
        ),
        (
            "orchard-fog",
            "Orchard fog",
            f"{WIZARD} mid-stride, weighted at the left third",
            "walks the headland of an unmarked orchard in morning fog",
            "Soft diffused light, the rows dissolving a long way back, grass damp and pale.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The fog pads the ends and the middle stays clear. "
            + _BANNER_TAIL,
        ),
        (
            "breakwater-dawn",
            "Breakwater",
            f"{WIZARD_STAFF}, weighted at the right third, collar turned up",
            "stands on a long unmarked concrete breakwater at dawn",
            "Flat rose-grey light, the sea low and calm, the blocks marching level on the sea side.",
            "Match a standing eyeline. 24mm-equivalent wide. The breakwater draws one clean line across. "
            + _BANNER_TAIL,
        ),
        (
            "hangar-glider",
            "Hangar bay",
            f"{WIZARD_NAP} mid-stride, weighted at the left third",
            "walks the floor of a wide unmarked hangar beside a plain unmarked glider",
            "High door light flooding in from one end, dust in the beam, the rafters lost in shade above.",
            "Hip height. 24mm-equivalent wide. The glider sits well back and the floor stays clear. " + _BANNER_TAIL,
        ),
        (
            "market-hall-stalls",
            "Market hall",
            f"{WIZARD}, weighted at the right third, face to camera",
            "stands in a wide unmarked market hall of empty plain stalls",
            "Sky light through the roof glazing, shutter fronts pale, the aisle a single run of stone.",
            "Match a standing eyeline. 35mm-equivalent classic reportage view. The shutters repeat evenly with the aisle kept open. "
            + _BANNER_TAIL,
        ),
        (
            "plaza-shallow-pool",
            "Plaza pool",
            f"{WIZARD_STAFF} mid-stride, weighted at the left third",
            "crosses a wide unmarked plaza beside a long shallow pool",
            "Bright open day, the pool mirroring the sky, the paving pale and plain.",
            "Slightly above eyeline. 28mm-equivalent wide. The pool edge runs level with the sky filling the middle. "
            + _BANNER_TAIL,
        ),
        (
            "salt-work-pans",
            "Salt works",
            f"{WIZARD_NAP}, weighted at the right third, mid-stride",
            "walks the edge of shallow unmarked evaporation pans at a salt work",
            "Low sun raking the water sheets, each pan a mirror, the banks level and pale.",
            "Match a standing eyeline. 24mm-equivalent wide. The pan edges run level and the banks stay empty. "
            + _BANNER_TAIL,
        ),
    ]
    return [
        _row(f"{_BANNER}-{slug}", label, _klein(subject, place, light, camera))
        for slug, label, subject, place, light, camera in banners
    ]


def goal_catalogs() -> dict[str, list[dict[str, str]]]:
    """Return the three goal-specific Klein stills catalogs."""
    return {
        "klein_vertical": klein_vertical(),
        "klein_plate": klein_plate(),
        "klein_banner": klein_banner(),
    }
