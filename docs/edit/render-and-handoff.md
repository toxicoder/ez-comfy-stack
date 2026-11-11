---
title: Render and hand off
description: "Choose between the Spark's ffmpeg pass and the browser's WebCodecs pass, read the job rows, and export the cut as JSON or as CMX 3600 text an NLE imports."
tags: [editing, video-editor, render, ffmpeg, webcodecs, edl, cmx, handoff]
---

# Render and hand off

**What's on this page**

- **Which machine moves the pixels** - server ffmpeg mp4 or browser webm, side by side
- **Server render** - queue it, read the job row, find the file
- **Client render** - connect the executor, keep the tab foregrounded, and where the file lands
- **Job rows** - what `Kind`, `State`, `Mode`, and `Message` mean, and how to poll one
- **Export the EDL** - the panel select, the route body, and the MCP tool
- **CMX 3600** - a worked document, what an NLE makes of it, and what it cannot carry
- **Failures** - the job that never leaves `pending`, and every export refusal

**What this enables**

- **Rendering on whichever machine has the headroom** - the Spark's CPU for a shareable mp4, your
  laptop for a webm with the titles burned in
- **A cut that leaves the lane** - `format=cmx` writes CMX 3600 text that DaVinci Resolve,
  Premiere, Kdenlive, and Shotcut import as an edit decision list
- **A machine-readable handoff too** - `format=json` keeps every plane, gain, transition, and
  graphic, so another tool can rebuild the timeline exactly
- **No waiting on a model** - export and render are route calls; the sidecar is not involved

**Question this page answers:** how do I get a finished file, and how do I take the cut into a real
NLE? Press **Render server** for an mp4 on the Spark, or **Export EDL** with the format select set
to `cmx` and open the result in your editor. For how the cut was built, see
[Rough cut in the browser](rough-cut.md).

---

## Which machine moves the pixels

| | Server render | Client render |
| --- | --- | --- |
| Who works | ffmpeg on the Spark | your open tab: canvas plus `MediaRecorder` |
| Container | `.mp4` (libx264, yuv420p, AAC, `+faststart`) | `.webm` (vp8 or vp9 with opus) |
| Where the file lands | `${COMFY_OUTPUT_DIR}/edit/renders/<project_id>-<job_id>.mp4` | your browser's downloads folder, named `<project-slug>-<job_id>.webm` |
| Planes | stacked through one `filter_complex` | painted frame by frame |
| Per-clip gain | a `volume` filter per clip | the tab's audio graph |
| Transitions | `concat` for a cut, `xfade` for a fade or wipe | painted as the plan steps |
| Overlays and captions | not drawn | burned in |
| Tab must stay open | no | **yes** - a closed or backgrounded tab leaves the row `pending` |
| Browser | anything | Chromium-based |
| Needs ComfyUI up | yes | yes (the routes live in Comfy) |

Pick server when you want a file the whole studio can use, and client when you want the titles in
the picture or you would rather not spend the Spark's CPU.

---

## Server render

Set the **Server** chip and press **Render server**. A row appears in the Jobs table as
`render_server` / `pending`, then `running`, then `ok` with the output path in `Message`.

The single ffmpeg pass does all of it: per-clip trims as input-level `-ss` and `-to`, the planes
stacked in one `filter_complex` (the base plane through `concat` or `xfade`, higher planes through
`overlay` at the frame fractions), per-clip gain as `volume`, and a tail of libx264 / yuv420p / AAC
with `+faststart`, muxed to the base duration with `-t`.

```bash
ls -lh "${COMFY_OUTPUT_DIR}/edit/renders/"      # <project_id>-<job_id>.mp4
```

Because the pass is CPU work on the Spark, expect contention with a heavy generation. The lane
never asks for the GPU - see [Why one heavy job at a time](../learn/occupancy.md).

---

## Client render

The browser pass is a queue, not a call: the server writes a `pending` row and your tab does the
work when it claims it.

1. Press **Connect executor** in the **This browser** section. The status line adds `executor on`
   and shows the client id this tab claims jobs as.
2. Press **Render client** (or set the **Client** chip first).
3. Keep the tab foregrounded until the row reports. Decoding, painting, and recording all happen in
   that tab, and a backgrounded tab stalls the clock.

The finished webm arrives as a normal browser download. The job row records the outcome with
`Message: webm recorded in browser (download)`.

Two limits worth knowing before you render a long cut:

- The client pass stops stepping after five minutes of wall clock, so plan a long timeline as
  several client renders and join them later.
- A client job with no connected executor sits `pending` forever. Reopen the panel, press **Connect
  executor**, and the row is claimed on the next poll.

---

## Job rows

| Column | Values |
| --- | --- |
| `Kind` | `render_server`, `exec_client`, `generate_clip` |
| `State` | `pending`, `running`, `ok`, `failed` |
| `Mode` | `server` or `client`, whichever the job was queued for |
| `Message` | the output path, the refusal reason, or the failure line |

The panel polls on a one-second tick, so a row updates without pressing **Refresh**. To poll one job
yourself:

```bash
curl -s "http://127.0.0.1:${COMFY_PORT}/ez_edit/job?job_id=<job_id>"
```

From an agent or a script, the same lookup is `edit_job_status(job_id)`.

---

## Export the EDL

Choose `json` or `cmx` in the panel's **EDL format** select and press **Export EDL**. The status
line answers with the path the route wrote. The export is a file write, so it works with the agent
sidecar down.

The same call directly:

```bash
curl -s -X POST "http://127.0.0.1:${COMFY_PORT}/ez_edit/export_edl" \
  -H 'Content-Type: application/json' \
  -d '{"project_id": "product-30s", "format": "cmx"}'
```

The body answers `{ok, path, project_id, clips, format}`, and the files land beside the project:

| Format | Path | Carries |
| --- | --- | --- |
| `json` | `edit/projects/<project_id>.edl.json` | version, id, title, fps, frame size, every clip with `in_s` / `out_s` / `duration_s` / `track` / `gain` / `timeline_start_s` / entering transition, plus the overlays and captions |
| `cmx` | `edit/projects/<project_id>.edl` | CMX 3600 text: plane `0` only, one event per clip |

From an agent, the same export is `edit_export_edl(project_id, format)`.

### The JSON handoff

Use `format=json` when the next tool is yours. Timecodes are seconds, not frames, so nothing has to
agree on a frame rate, and `timeline_start_s` is already the sequential position a viewer needs.
Graphics ride along, which the CMX text cannot do.

### CMX 3600

`format=cmx` writes the interchange format the non-linear editors all still read:

```text
TITLE: Product 30s
FCM: NON-DROP FRAME

001  A_ROLL     V     C        00:00:00:00 00:00:02:00 00:00:00:00 00:00:02:00
* FROM CLIP NAME: A_ROLL

002  B_ROLL     V     D        00:00:01:00 00:00:03:00 00:00:02:00 00:00:04:00
* FROM CLIP NAME: B_ROLL
```

Read it as: event number, reel, `V` for video, the transition code (`C` cut, `D` dissolve for a
fade, `W` wipe), then source in, source out, record in, record out, on the project's frame grid.
The reel name is the clip label, upper-cased, with anything outside `A-Z`, `0-9`, `.`, `_`, and `-`
replaced by `_`, so an NLE's media page stays readable.

To import: put the `.edl` somewhere the NLE's media page can see, then use the timeline's **Import
EDL** (Resolve and Premiere) or **File, Import, Timeline from EDL** (Kdenlive and Shotcut), and
relink the sources - they are the same files under `${COMFY_OUTPUT_DIR}`, which is what makes the
handoff short.

What CMX does not carry, by the format's own limits:

- planes above `0` - inserts and picture-in-picture stay in this lane, or come across as extra
  events you place by hand
- gain, overlays, and captions - the JSON handoff keeps those
- drop-frame timecode - the writer emits `FCM: NON-DROP FRAME`

Two refusals are worth knowing, both from the writer: a project with no plane `0` clip has nothing
to export, and a project whose fps is below 1 cannot produce a timecode.

---

## Failures

| Symptom | Cause and fix |
| --- | --- |
| A client row sits `pending` | no connected executor, or the tab was backgrounded - press **Connect executor** and keep it foregrounded |
| `MediaRecorder produced no data` | the tab lost the media stack: use a Chromium browser, keep it visible, retry |
| The client render stops early | the five-minute wall-clock cap: render the timeline in parts |
| A server row goes `failed` with an ffmpeg line | read `Message`; a missing or unreadable source is the usual cause - re-import the clip |
| `unknown edl format 'x' (want json or cmx)` | the format select only offers `json` and `cmx` |
| `project has no base-plane (track 0) clip to export` | move at least one shot to plane `0` with **Set track** |
| `project fps must be >= 1 to export CMX timecode` | recreate the project with a real frame rate |
| The mp4 has no titles | expected: only the client pass paints graphics - see [Captions and overlays](captions-and-overlays.md) |

---

## Related

| Need | Page |
| --- | --- |
| Building the cut those buttons render | [Rough cut in the browser](rough-cut.md) |
| Why only the browser burns text | [Captions and overlays](captions-and-overlays.md) |
| Rendering and polling from a script | [Agent and MCP driving](agent-and-mcp.md) |
| The op vocabulary and every guard | [Plan a cut](plan-a-cut.md) |
| The lane's routes, env knobs, and sidecar | [Editing lane](../edit-agent.md) |
| A fuller NLE in another tab | [Vlo video editor](../vlo.md) |
