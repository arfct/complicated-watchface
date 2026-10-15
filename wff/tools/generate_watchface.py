#!/usr/bin/env python3
"""Generates res/raw/watchface.xml for Complicated.

One complication fills the screen, and a clock sits over it: digital or
analog, at the top, center or bottom. At the top or bottom the clock is
small and the complication's content moves into the rest of the screen; at
the center it is large and the content splits above and below it.

Targets Watch Face Format 5 (Wear OS 7, API 37), for auto-sized text.

Edit THIS file and re-run it; never hand-edit watchface.xml.

    python3 wff/tools/generate_watchface.py
"""

import math
import os

CANVAS = 450
CX = CANVAS / 2

# id -> (string prefix, label word, {option id: label}, default option), in
# editor page order. Option labels carry the setting's word, because the
# editor shows one option label at a time.
LIST_SETTINGS = {
    "clock": ("clock", "Clock", {
        "digital_top": "Digital top",
        "digital_center": "Digital center",
        "digital_bottom": "Digital bottom",
        "analog_top": "Analog top",
        "analog_center": "Analog center",
        "analog_bottom": "Analog bottom",
        "perimeter_4": "Perimeter 4",
        "perimeter_5": "Perimeter 5",
        "perimeter_6": "Perimeter 6",
    }, "digital_top"),
}
# Clock option -> the layout the complication's content uses around it.
LAYOUT_FOR = {option: "perimeter" if option.startswith("perimeter") else option.split("_")[-1]
              for option in LIST_SETTINGS["clock"][2]}
# ---- Perimeter divisions ----
# The Perimeter clock's rim, apart from the top time, splits into N equal
# divisions, each a text complication slot. A scene holds at most 8 slots,
# too few for separate slots per count (4 + 5 + 6), so slots 1..6 are shared:
# each draws in its division for the chosen count, and its bound covers
# every place it can draw. Neighboring bounds therefore overlap, and the
# editor gives a tap there to the later-declared slot.
#
# The count is part of the Clock list rather than a child setting: the
# runtime rejects a style schema where two settings enable complication slots
# ("at most one can be active for any permutation of UserStyle"), and the
# face then cannot be set at all. The validator does not catch this.
PERIMETER_COUNTS = {"perimeter_4": 4, "perimeter_5": 5, "perimeter_6": 6}
RIM_SLOTS = range(1, max(PERIMETER_COUNTS.values()) + 1)
# ListOption attributes (format 5): the slots each clock option enables. A
# slot no option names is always enabled, so slot 0 is named under every one.
OPTION_ATTRS = {option: {"complicationSlotIds": " ".join(
    str(i) for i in range(PERIMETER_COUNTS.get(option, 0) + 1))} for option in LAYOUT_FOR}

TEXT = "#FFFFFF"
TRACK = "#40FFFFFF"

# ---- Clock geometry, per position ----
EDGE_MARGIN = 1
# Digital time metrics as a fraction of the font size, measured on the Wear
# OS 7 emulator at 64 px: the widest time (four tabular digits and a colon)
# spans 2.37, caps are 0.70 tall, and they sit 0.035 above the text box's
# center.
TIME_WIDTH = 2.37
TIME_CAP_HEIGHT = 0.70
TIME_CAP_RISE = 0.035
SMALL_TIME_FONT = 64
SMALL_DIAL_R = 70


def edge_hugging_cy(font, top):
    """Box center for a digital time whose cap corners touch the round edge."""
    half_w = TIME_WIDTH * font / 2
    inset = CX - math.sqrt((CX - EDGE_MARGIN) ** 2 - half_w ** 2)
    cap_center = inset + TIME_CAP_HEIGHT * font / 2
    offset = TIME_CAP_RISE * font
    return cap_center + offset if top else CANVAS - cap_center + offset


# cy, font. At the top and bottom the time sits as close to the edge as its
# width allows; the analog dial's ring touches the edge.
DIGITAL = {"top": (edge_hugging_cy(SMALL_TIME_FONT, True), SMALL_TIME_FONT),
           "center": (CX, 150),
           "bottom": (edge_hugging_cy(SMALL_TIME_FONT, False), SMALL_TIME_FONT)}
ANALOG = {"top": (SMALL_DIAL_R + EDGE_MARGIN - 2, SMALL_DIAL_R),     # cy, radius
          "center": (CX, 150),
          "bottom": (CANVAS - SMALL_DIAL_R - EDGE_MARGIN + 2, SMALL_DIAL_R)}
# At the small sizes two bare hands read as a line; a faint ring gives them
# a face to sit in.
SMALL_DIAL_RING = "#59FFFFFF"

# ---- Complication layout, per clock position ----
# Where the icon, the main text and the title sit, clear of the clock. At the
# top or bottom the content fills the rest of the screen; at the center it
# splits around the large clock. Each entry is (center y, size): the icon's
# size is its box, the texts' is their font. Widths keep each line inside the
# circle's chord at that height.
LAYOUT = {
    "top": dict(icon=(215, 80), text=(300, 56, 340), title=(358, 28, 280),
                solo=(280, 170)),
    "bottom": dict(icon=(95, 80), text=(180, 56, 340), title=(238, 28, 300),
                   solo=(170, 170)),
    "center": dict(icon=(80, 70), text=(345, 44, 300), title=(392, 26, 220),
                   solo=(80, 90)),
    "perimeter": dict(icon=(165, 80), text=(250, 56, 300), title=(305, 28, 260),
                      solo=(CX, 190)),
}

# ---- Perimeter clock ----
# Curved text flush to the round edge: the time centered at the top and again
# at the bottom, and every other value once in each half between them. Read
# counter-clockwise from either time, the values run day, date, weather,
# percent, then repeat. Nothing can measure text at runtime, so each value's
# arc is sized ahead of time from its longest likely text,
# and the space left in each half is split into equal gaps with a dot in the
# middle of each. Angles are degrees clockwise from 12 o'clock.
PERIMETER_MARGIN = 1
# How far caps reach past their TextCircular circle toward the edge, as a
# fraction of the font size. Measured on the Wear OS 7 emulator: text in the
# top half faces the edge with its cap tops, text in the bottom half with its
# baseline.
CAP_REACH_TOP = 0.385
CAP_REACH_BOTTOM = 0.31
PERIMETER_FONT = 34
PERIMETER_BAND = PERIMETER_MARGIN + PERIMETER_FONT + 4   # text reach from the edge
PERIMETER_DOT = 6
PERIMETER_DOT_COLOR = "#80FFFFFF"
# In ambient the top time stays at full brightness and everything else,
# the bottom time included, dims to this alpha.
PERIMETER_AMBIENT_SECONDARY = 140
# Advance widths as a fraction of the font size, estimated for the system
# sans at caps; anything unlisted counts as a capital.
GLYPH_WIDTHS = {"digit": 0.57, "cap": 0.66, " ": 0.26, ":": 0.26, "%": 0.86, "°": 0.40}
# name -> (template, parameters, longest likely text)
PERIMETER_VALUES = {
    "time": ("%d:%s", ["([IS_24_HOUR_MODE] ? [HOUR_0_23] : [HOUR_1_12])", "[MINUTE_Z]"],
             "23:59"),
    "weekday": ("%s", ["[DAY_OF_WEEK_S]"], "WED"),
    "date": ("%s %d", ["[MONTH_S]", "[DAY]"], "SEP 30"),
    "battery": ("%d%%", ["[BATTERY_PERCENT]"], "100%"),
    "temperature": ("%d°", ["[WEATHER.TEMPERATURE]"], "100°"),
}
# What an unset division shows, clockwise from the top time, repeating.
DIVISION_DEFAULTS = ["weekday", "date", "temperature", "battery"]

GAUGE_STROKE = 14
# Distance from the edge to the gauge ring, per layout: inside the perimeter
# clock's text band, otherwise at the bezel.
GAUGE_INSET = {"perimeter": PERIMETER_BAND + 6}
GAUGE_INSET_DEFAULT = 6
# In preference order: the system gives a provider the first of these it
# offers, so a photo fills the screen and a battery arrives as a gauge. The
# one excluded type is WEIGHTED_ELEMENTS, which sends its segments as a
# space-separated list that expressions cannot split.
SUPPORTED_TYPES = ("PHOTO_IMAGE", "RANGED_VALUE", "GOAL_PROGRESS",
                   "SHORT_TEXT", "LONG_TEXT", "SMALL_IMAGE",
                   "MONOCHROMATIC_IMAGE")
GAUGE_FRACTIONS = {
    "RANGED_VALUE": (
        "([COMPLICATION.RANGED_VALUE_MAX] == [COMPLICATION.RANGED_VALUE_MIN]"
        " ? 0 : clamp(([COMPLICATION.RANGED_VALUE_VALUE] -"
        " [COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX]"
        " - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1))"),
    "GOAL_PROGRESS": (
        "([COMPLICATION.GOAL_PROGRESS_TARGET_VALUE] &lt;= 0 ? 0 :"
        " clamp([COMPLICATION.GOAL_PROGRESS_VALUE] /"
        " [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE], 0, 1))"),
}
# The complication stays up in ambient. Text and gauges are drawn unchanged.
# An image swaps to the provider's ambient version where one exists and
# otherwise dims to 25%. The runtime draws nothing for a missing ambient
# image (it does not fall back to the regular one), and an image cannot be
# tested for emptiness, so both are drawn: the regular image dims to 25% and
# the ambient image fades in over it. A photo has no ambient version and
# just dims.
AMBIENT_DIM = 64
AMBIENT_FADE = 'startOffset="0" duration="0.5" interpolation="EASE_OUT"'


def user_configurations():
    out = ['  <UserConfigurations>']
    for config_id, (prefix, _, options, default) in LIST_SETTINGS.items():
        out.append(f'    <ListConfiguration id="{config_id}"'
                   f' displayName="{prefix}_label"'
                   f' screenReaderText="{prefix}_label" defaultValue="{default}">')
        for option_id in options:
            extra = "".join(f' {k}="{v}"' for k, v in OPTION_ATTRS.get(option_id, {}).items())
            out.append(f'      <ListOption id="{option_id}"'
                       f' displayName="{prefix}_{option_id}_label"{extra} />')
        out.append('    </ListConfiguration>')
    out.append('  </UserConfigurations>')
    return "\n".join(out)


def config_strings():
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<!-- GENERATED by wff/tools/generate_watchface.py - do not edit by hand. -->',
             '<resources>']
    for prefix, word, options, _ in LIST_SETTINGS.values():
        lines.append(f'    <string name="{prefix}_label">{word}</string>')
        for option_id, label in options.items():
            lines.append(f'    <string name="{prefix}_{option_id}_label">'
                         f'{word}: {label}</string>')
    lines.append('</resources>')
    return "\n".join(lines) + "\n"


def list_switch(config_id, options, indent):
    """ListConfiguration over {option id: element}. A ListOption holds
    exactly one child, so callers pass a single element per option."""
    pad = " " * indent
    out = [f'{pad}<ListConfiguration id="{config_id}">']
    for option_id, body in options.items():
        out += [f'{pad}  <ListOption id="{option_id}">', body,
                f'{pad}  </ListOption>']
    out.append(f'{pad}</ListConfiguration>')
    return "\n".join(out)


def group(name, children, indent):
    pad = " " * indent
    return "\n".join([f'{pad}<Group x="0" y="0" width="{CANVAS}" height="{CANVAS}"'
                      f' name="{name}">', *children, f'{pad}</Group>'])


# ---- Complication parts ----

def ambient_alpha(value, pad):
    return (f'{pad}  <Variant mode="AMBIENT" target="alpha" value="{value}"'
            f' {AMBIENT_FADE} />\n')


def image(cx, cy, size, resource, tint=None, indent=10, alpha=255, ambient=None):
    """`ambient` is the alpha this image takes in ambient mode, if it changes."""
    pad = " " * indent
    tint_attr = f' tintColor="{tint}"' if tint else ""
    variant = "" if ambient is None else ambient_alpha(ambient, pad)
    return (f'{pad}<PartImage x="{cx - size / 2:.0f}" y="{cy - size / 2:.0f}"'
            f' width="{size:.0f}" height="{size:.0f}" alpha="{alpha}"{tint_attr}>\n'
            f'{variant}'
            f'{pad}  <Image resource="{resource}" />\n'
            f'{pad}</PartImage>')


def image_layers(cx, cy, size, field, tint=None, indent=10):
    """The regular image, dimming to 25% in ambient, under the provider's
    ambient image, which fades in over it."""
    return [image(cx, cy, size, f"[COMPLICATION.{field}]", tint, indent,
                  ambient=AMBIENT_DIM),
            image(cx, cy, size, f"[COMPLICATION.{field}_AMBIENT]", tint, indent,
                  alpha=0, ambient=255)]


def text(cy, font, width, source, max_lines=1, indent=10):
    """Auto-sized text: it shrinks to fit its box, down to minSize, rather
    than being clipped. The Font content stays inline: whitespace around it
    renders as an empty first line and hides the text."""
    pad = " " * indent
    height = font * 1.3 * max_lines
    return (f'{pad}<PartText x="{CX - width / 2:.0f}" y="{cy - height / 2:.0f}"'
            f' width="{width:.0f}" height="{height:.0f}">\n'
            f'{pad}  <Text align="CENTER" ellipsis="TRUE" maxLines="{max_lines}"'
            f' isAutoSize="TRUE">'
            f'<Font family="SYNC_TO_DEVICE" size="{font:.0f}" minSize="16"'
            f' color="{TEXT}">'
            f'<Template>%s<Parameter expression="[COMPLICATION.{source}]" /></Template>'
            f'</Font></Text>\n'
            f'{pad}</PartText>')


def ring(end_expr, color, layout, indent=10):
    pad = " " * indent
    d = CANVAS - 2 * GAUGE_INSET.get(layout, GAUGE_INSET_DEFAULT) - GAUGE_STROKE
    return (f'{pad}<PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
            f'{pad}  <Arc centerX="{CX:.1f}" centerY="{CX:.1f}" width="{d:.1f}"'
            f' height="{d:.1f}" startAngle="0" endAngle="359.9">\n'
            f'{pad}    <Transform target="endAngle" value="{end_expr}" />\n'
            f'{pad}    <Stroke color="{color}" thickness="{GAUGE_STROKE}" cap="ROUND" />\n'
            f'{pad}  </Arc>\n'
            f'{pad}</PartDraw>')


def scrim(position, indent=10):
    """Darkens the photo under the clock so white time stays readable. It
    fades out in ambient, where the photo is already dimmed."""
    pad = " " * indent
    fade = ambient_alpha(0, pad)
    if position == "perimeter":
        return perimeter_scrim(pad, fade)
    if position == "center":
        return (f'{pad}<PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
                f'{fade}'
                f'{pad}  <Rectangle x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
                f'{pad}    <Fill color="#59000000" />\n'
                f'{pad}  </Rectangle>\n'
                f'{pad}</PartDraw>')
    edge, clear = (0, 200) if position == "top" else (CANVAS, CANVAS - 200)
    return (f'{pad}<PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
            f'{fade}'
            f'{pad}  <Rectangle x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
            f'{pad}    <Fill color="#FF000000">\n'
            f'{pad}      <LinearGradient startX="{CX:.0f}" startY="{edge}"'
            f' endX="{CX:.0f}" endY="{clear}" colors="#B3000000 #00000000"'
            f' positions="0 1" />\n'
            f'{pad}    </Fill>\n'
            f'{pad}  </Rectangle>\n'
            f'{pad}</PartDraw>')


# The perimeter scrim darkens only the text band at the edge. Stops are evenly
# spaced by construction, because the Wear OS 7 runtime ignores `positions`
# and spreads gradient stops evenly (arcminute measured this on a Pixel Watch
# 5). N stops put the ramp in the last 1/(N-1) of the radius.
PERIMETER_SCRIM_STOPS = 5


def perimeter_scrim(pad, fade):
    n = PERIMETER_SCRIM_STOPS
    colors = " ".join(["#00000000"] * (n - 1) + ["#B3000000"])
    positions = " ".join(f"{i / (n - 1):.2f}" for i in range(n))
    return (f'{pad}<PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
            f'{fade}'
            f'{pad}  <Ellipse x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
            f'{pad}    <Fill color="#FF000000">\n'
            f'{pad}      <RadialGradient centerX="{CX:.0f}" centerY="{CX:.0f}"'
            f' radius="{CX:.0f}" colors="{colors}" positions="{positions}" />\n'
            f'{pad}    </Fill>\n'
            f'{pad}  </Ellipse>\n'
            f'{pad}</PartDraw>')


def photo(resource, position, indent=10):
    return [image(CX, CX, CANVAS, resource, indent=indent, ambient=AMBIENT_DIM),
            scrim(position, indent)]


def icon_and_texts(position, long_text=False):
    lay = LAYOUT[position]
    icon_cy, icon_size = lay["icon"]
    text_cy, text_font, text_w = lay["text"]
    title_cy, title_font, title_w = lay["title"]
    # Providers put a text complication's icon in either field (an app
    # shortcut sends SMALL_IMAGE); the empty one draws nothing.
    parts = (image_layers(CX, icon_cy, icon_size, "MONOCHROMATIC_IMAGE", TEXT)
             + image_layers(CX, icon_cy, icon_size, "SMALL_IMAGE"))
    if long_text:
        # Two lines in the main slot; the title moves down by half a line.
        parts.append(text(text_cy + text_font * 0.3, text_font * 0.7, text_w,
                          "TEXT", max_lines=2))
        parts.append(text(title_cy + text_font * 0.5, title_font, title_w, "TITLE"))
    else:
        parts.append(text(text_cy, text_font, text_w, "TEXT"))
        parts.append(text(title_cy, title_font, title_w, "TITLE"))
    return parts


def small_image(option, position):
    """IMAGE_STYLE 1 is a photo, which fills the screen; an icon sits where
    a lone icon goes. Expression names must be unique across the document."""
    name = f"photo_style_{option}"
    solo_cy, solo_size = LAYOUT[position]["solo"]
    resource = "[COMPLICATION.SMALL_IMAGE]"
    return ["\n".join([
        '          <Condition>',
        '            <Expressions>',
        f'              <Expression name="{name}">[COMPLICATION.IMAGE_STYLE] == 1</Expression>',
        '            </Expressions>',
        f'            <Compare expression="{name}">',
        group(f"small_photo_{option}", photo(resource, position, 16), 14),
        '            </Compare>',
        '            <Default>',
        group(f"small_icon_{option}",
              image_layers(CX, solo_cy, solo_size, "SMALL_IMAGE", indent=16), 14),
        '            </Default>',
        '          </Condition>',
    ])]


def complication_parts(complication_type, option):
    position = LAYOUT_FOR[option]
    if complication_type == "PHOTO_IMAGE":
        return photo("[COMPLICATION.PHOTO_IMAGE]", position)
    if complication_type == "SMALL_IMAGE":
        return small_image(option, position)
    if complication_type == "MONOCHROMATIC_IMAGE":
        solo_cy, solo_size = LAYOUT[position]["solo"]
        return image_layers(CX, solo_cy, solo_size, "MONOCHROMATIC_IMAGE", TEXT)
    parts = []
    if complication_type in GAUGE_FRACTIONS:
        parts += [ring("359.9", TRACK, position),
                  ring(f"(359.9 * {GAUGE_FRACTIONS[complication_type]})", TEXT, position)]
    return parts + icon_and_texts(position, complication_type == "LONG_TEXT")


def complication(complication_type):
    by_option = {o: group(f"{complication_type.lower()}_{o}",
                          complication_parts(complication_type, o), 8)
                 for o in LAYOUT_FOR}
    return "\n".join([
        f'      <Complication type="{complication_type}">',
        group(f"{complication_type.lower()}_layout",
              [list_switch("clock", by_option, 8)], 6),
        '      </Complication>',
    ])


def complication_slot():
    return "\n".join([
        f'    <ComplicationSlot slotId="0" supportedTypes="{" ".join(SUPPORTED_TYPES)} EMPTY"'
        f' x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        f'      <BoundingOval x="0" y="0" width="{CANVAS}" height="{CANVAS}" />',
        *[complication(t) for t in SUPPORTED_TYPES],
        '    </ComplicationSlot>',
    ])


# ---- Clock ----

def digital(position):
    cy, font = DIGITAL[position]
    height = font * 1.3
    return (f'        <DigitalClock x="0" y="{cy - height / 2:.0f}"'
            f' width="{CANVAS}" height="{height:.0f}">\n'
            f'          <TimeText x="0" y="0" width="{CANVAS}" height="{height:.0f}"'
            f' format="h:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER">\n'
            f'            <Font family="SYNC_TO_DEVICE" size="{font}" weight="MEDIUM"'
            f' color="{TEXT}" />\n'
            f'          </TimeText>\n'
            f'        </DigitalClock>')


def hand(name, cy, r, length, width, angle_expr):
    """White hand over a black outline, so it reads on any photo."""
    lines = []
    for color, w in (("#000000", width + 4), (TEXT, width)):
        lines.append(f'              <Line startX="{r:.1f}" startY="{r:.1f}"'
                     f' endX="{r:.1f}" endY="{r - length:.1f}">\n'
                     f'                <Stroke color="{color}" thickness="{w:.1f}" cap="ROUND" />\n'
                     f'              </Line>')
    return "\n".join([
        f'          <Group x="{CX - r:.0f}" y="{cy - r:.0f}" width="{2 * r:.0f}"'
        f' height="{2 * r:.0f}" name="{name}" angle="0" pivotX="0.5" pivotY="0.5">',
        f'            <Transform target="angle" value="{angle_expr}" />',
        f'            <PartDraw x="0" y="0" width="{2 * r:.0f}" height="{2 * r:.0f}">',
        *lines,
        '            </PartDraw>',
        '          </Group>',
    ])


def analog(position):
    cy, r = ANALOG[position]
    hour_w = max(6, 0.1 * r)
    minute_w = max(4, 0.065 * r)
    dot = hour_w * 0.9
    ring_part = [] if position == "center" else [
        f'          <PartDraw x="{CX - r:.0f}" y="{cy - r:.0f}" width="{2 * r:.0f}" height="{2 * r:.0f}">\n'
        f'            <Ellipse x="2" y="2" width="{2 * r - 4:.0f}" height="{2 * r - 4:.0f}">\n'
        f'              <Stroke color="{SMALL_DIAL_RING}" thickness="2" />\n'
        f'            </Ellipse>\n'
        f'          </PartDraw>']
    return group(f"analog_{position}", [*ring_part,
        hand(f"hour_{position}", cy, r, 0.55 * r, hour_w, "(30 * [HOUR_0_11_MINUTE])"),
        hand(f"minute_{position}", cy, r, 0.9 * r, minute_w, "(6 * [MINUTE])"),
        f'          <PartDraw x="{CX - dot - 2:.0f}" y="{cy - dot - 2:.0f}"'
        f' width="{2 * dot + 4:.0f}" height="{2 * dot + 4:.0f}">\n'
        f'            <Ellipse x="0" y="0" width="{2 * dot + 4:.1f}" height="{2 * dot + 4:.1f}">\n'
        f'              <Fill color="#000000" />\n'
        f'            </Ellipse>\n'
        f'            <Ellipse x="2" y="2" width="{2 * dot:.1f}" height="{2 * dot:.1f}">\n'
        f'              <Fill color="{TEXT}" />\n'
        f'            </Ellipse>\n'
        f'          </PartDraw>',
    ], 8)


def perimeter_radius(angle):
    reach = CAP_REACH_BOTTOM if in_bottom_half(angle) else CAP_REACH_TOP
    return CX - PERIMETER_MARGIN - reach * PERIMETER_FONT


def in_bottom_half(angle):
    return 90 < angle % 360 < 270


# Circle used for sizing arcs; the two halves differ by under 3 px.
PERIMETER_DIAMETER = 2 * perimeter_radius(0)


def arc_degrees(sample):
    """Angle the sample text spans on the perimeter circle."""
    width = sum(GLYPH_WIDTHS["digit"] if c.isdigit() else GLYPH_WIDTHS.get(c, GLYPH_WIDTHS["cap"])
                for c in sample) * PERIMETER_FONT
    return math.degrees(width / (PERIMETER_DIAMETER / 2))


def curved_text(name, center, half, template, params, ambient=None):
    """TextCircular with its caps touching the screen edge. Text in the
    bottom half runs counter-clockwise so it reads upright; that direction
    traverses its angles the other way, so start and end swap."""
    bottom = in_bottom_half(center)
    direction, sign = ("COUNTER_CLOCKWISE", -1) if bottom else ("CLOCKWISE", 1)
    d = 2 * perimeter_radius(center)
    parameters = "".join(f'<Parameter expression="{p}" />' for p in params)
    variant = "" if ambient is None else ambient_alpha(ambient, "          ")
    return (f'          <PartText x="0" y="0" width="{CANVAS}" height="{CANVAS}" name="{name}">\n'
            f'{variant}'
            f'            <TextCircular centerX="{CX:.0f}" centerY="{CX:.0f}"'
            f' width="{d:.0f}" height="{d:.0f}"'
            f' startAngle="{center - sign * half:.0f}" endAngle="{center + sign * half:.0f}"'
            f' direction="{direction}" align="CENTER" ellipsis="TRUE">\n'
            f'              <Font family="SYNC_TO_DEVICE" size="{PERIMETER_FONT}"'
            f' color="{TEXT}"><Upper><Template>{template}{parameters}</Template></Upper></Font>\n'
            f'            </TextCircular>\n'
            f'          </PartText>')


def dot(angle):
    # On the line's center, which sits a cap's half-height inside the text's
    # circle's outer reach.
    r = perimeter_radius(angle) - (0.36 - (CAP_REACH_BOTTOM if in_bottom_half(angle)
                                           else CAP_REACH_TOP)) * PERIMETER_FONT
    x = CX + r * math.sin(math.radians(angle))
    y = CX - r * math.cos(math.radians(angle))
    half = PERIMETER_DOT / 2
    return (f'          <PartDraw x="{x - half:.0f}" y="{y - half:.0f}"'
            f' width="{PERIMETER_DOT}" height="{PERIMETER_DOT}">\n'
            f'            <Ellipse x="0" y="0" width="{PERIMETER_DOT}" height="{PERIMETER_DOT}">\n'
            f'              <Fill color="{PERIMETER_DOT_COLOR}" />\n'
            f'            </Ellipse>\n'
            f'          </PartDraw>')


def either(name, expression, when_true, when_false):
    """when_true if expression holds, else when_false. Expression names must
    be unique across the document."""
    return "\n".join([
        '        <Condition>',
        '          <Expressions>',
        f'            <Expression name="{name}">{expression}</Expression>',
        '          </Expressions>',
        f'          <Compare expression="{name}">',
        when_true,
        '          </Compare>',
        '          <Default>',
        when_false,
        '          </Default>',
        '        </Condition>',
    ])


def time_half():
    return arc_degrees(PERIMETER_VALUES["time"][2]) / 2


# Space between the top time and the dots beside it, in degrees.
TIME_CLEARANCE = 3


def divisions(n):
    """(start, end) angles of the n divisions, clockwise after the top time."""
    t = time_half() + TIME_CLEARANCE
    step = (360 - 2 * t) / n
    return [(t + i * step, t + (i + 1) * step) for i in range(n)]


def division_text(name, span, template, params):
    start, end = span
    return curved_text(name, (start + end) / 2, (end - start) / 2 - PERIMETER_DOT,
                       template, params, ambient=PERIMETER_AMBIENT_SECONDARY)


def division_default(slot, n, span):
    """The standard value an unset division shows. A temperature without
    weather data leaves its division empty."""
    value = DIVISION_DEFAULTS[(slot - 1) % len(DIVISION_DEFAULTS)]
    template, params, _ = PERIMETER_VALUES[value]
    part = division_text(f"division_{slot}_{n}_{value}", span, template, params)
    if value != "temperature":
        return part
    return either(f"weather_available_{slot}_{n}", "[WEATHER.IS_AVAILABLE]", part,
                  group(f"division_{slot}_{n}_no_weather", [], 10))


def division_mask(name, span):
    """Black arc over a division, hiding the default value beneath it."""
    start, end = span
    d = CANVAS - PERIMETER_BAND
    return (f'            <PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}" name="{name}">\n'
            f'              <Arc centerX="{CX:.0f}" centerY="{CX:.0f}" width="{d:.0f}" height="{d:.0f}"'
            f' startAngle="{start + PERIMETER_DOT:.1f}" endAngle="{end - PERIMETER_DOT:.1f}">\n'
            f'                <Stroke color="#FF000000" thickness="{PERIMETER_BAND + 2}" cap="BUTT" />\n'
            f'              </Arc>\n'
            f'            </PartDraw>')


def division_complication(slot, complication_type):
    by_count = {}
    for option, n in PERIMETER_COUNTS.items():
        name = f"division_{slot}_{n}_{complication_type.lower()}"
        if slot > n:
            # The slot is disabled at this count; the option still needs a child.
            by_count[option] = group(name, [], 10)
            continue
        span = divisions(n)[slot - 1]
        # Title first: a calendar event reads "10:00 AM STANDUP".
        by_count[option] = group(name, [
            division_mask(f"{name}_mask", span),
            division_text(f"{name}_text", span, "%s %s",
                          ["[COMPLICATION.TITLE]", "[COMPLICATION.TEXT]"])], 10)
    by_clock = {o: by_count.get(o, group(f"division_{slot}_{complication_type.lower()}_{o}", [], 10))
                for o in LAYOUT_FOR}
    return "\n".join([
        f'      <Complication type="{complication_type}">',
        # A Complication holds parts and groups, not configurations directly.
        group(f"division_{slot}_{complication_type.lower()}",
              [list_switch("clock", by_clock, 8)], 6),
        '      </Complication>',
    ])


def division_slot(slot):
    """Rim slot `slot`: short or long text in the rim's style, drawn over the
    standard value in its division. Its bound spans every division it
    occupies across the counts.

    The standard values are a layer beneath the slots rather than the slots'
    EMPTY rendering: an unset slot can report NO_DATA, which has no rendering
    type, and after an update install every rim slot did, on both the
    emulator and the watch."""
    spans = [divisions(n)[slot - 1] for n in PERIMETER_COUNTS.values() if slot <= n]
    start, end = min(a for a, _ in spans), max(b for _, b in spans)
    return "\n".join([
        f'    <ComplicationSlot slotId="{slot}" supportedTypes="LONG_TEXT SHORT_TEXT EMPTY"'
        f' x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        f'      <BoundingArc centerX="{CX:.1f}" centerY="{CX:.1f}" width="{CANVAS}"'
        f' height="{CANVAS}" thickness="{PERIMETER_BAND}" startAngle="{start:.1f}"'
        f' endAngle="{end:.1f}" outlinePadding="2" />',
        *[division_complication(slot, t) for t in ("LONG_TEXT", "SHORT_TEXT")],
        '    </ComplicationSlot>',
    ])


def division_defaults():
    """Standard values for every division, under the rim slots."""
    by_clock = {}
    for option in LAYOUT_FOR:
        n = PERIMETER_COUNTS.get(option)
        parts = [division_default(i, n, span) for i, span in enumerate(divisions(n), 1)] if n else []
        by_clock[option] = group(f"division_defaults_{option}", parts, 6)
    return list_switch("clock", by_clock, 4)


def perimeter(n):
    """The top time and the dots between divisions; the divisions themselves
    are complication slots."""
    template, params, _ = PERIMETER_VALUES["time"]
    time = curved_text(f"perimeter_{n}_time", 0, time_half(), template, params)
    dots = [dot(a) for a, _ in divisions(n)] + [dot(divisions(n)[-1][1])]
    return group(f"perimeter_{n}", [time, *dots], 6)


def clock_layer():
    clocks = {}
    for option, position in LAYOUT_FOR.items():
        style = option.split("_")[0]
        clocks[option] = (perimeter(PERIMETER_COUNTS[option]) if style == "perimeter"
                          else digital(position) if style == "digital"
                          else analog(position))
    return list_switch("clock", clocks, 4)


def watchface():
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- GENERATED by wff/tools/generate_watchface.py - do not edit by hand. -->
<WatchFace width="{CANVAS}" height="{CANVAS}" clipShape="CIRCLE">
  <Metadata key="CLOCK_TYPE" value="DIGITAL" />
  <Metadata key="PREVIEW_TIME" value="10:08:00" />
{user_configurations()}
  <Scene backgroundColor="#000000">
{complication_slot()}
{division_defaults()}
{chr(10).join(division_slot(i) for i in RIM_SLOTS)}
{clock_layer()}
  </Scene>
</WatchFace>
'''


if __name__ == "__main__":
    res = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src", "main", "res"))
    for path, content in ((os.path.join(res, "raw", "watchface.xml"), watchface()),
                          (os.path.join(res, "values", "config_strings.xml"), config_strings())):
        with open(path, "w") as f:
            f.write(content)
        print(f"wrote {path}")
