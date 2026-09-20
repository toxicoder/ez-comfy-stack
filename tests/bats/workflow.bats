#!/usr/bin/env bats
#
# ## workflow.bats
#
# Guard lab ComfyUI graphs for the US-safe studio pack: banned models,
# required Apache/Wan/LTX-2.5 basenames, draft/hero contract, 5 s frames,
# VHS MP4 on video graphs, AABB, Notes.

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

#######################################
# Resolve a shipped lab JSON under workflows/_lab.
# Arguments:
#   $1  basename (e.g. stills/still-draft.json)
# Outputs:
#   Absolute path on stdout
#######################################
lab_wf() {
  local rel="${1:?}"
  if [[ -f ${REPO_ROOT}/workflows/_lab/${rel} ]]; then
    printf '%s\n' "${REPO_ROOT}/workflows/_lab/${rel}"
    return 0
  fi
  find "${REPO_ROOT}/workflows/_lab" -name "$(basename "${rel}")" -print -quit
}

@test "gitignore hides operator _user graphs and local media" {
  local gi="${REPO_ROOT}/.gitignore"
  run grep -F '/workflows/_user/*' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '!/workflows/_user/.gitkeep' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '!/workflows/_user/README.md' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '/workflows/*/_user/' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '**/.user-local/' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '/output/' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '/outputs/' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '/input/' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '/inputs/' "${gi}"
  [ "${status}" -eq 0 ]
  run grep -F '/comfy-state/' "${gi}"
  [ "${status}" -eq 0 ]
  cd "${REPO_ROOT}"
  run git check-ignore -q workflows/_user/keep-me.json
  [ "${status}" -eq 0 ]
  run git check-ignore -q output/ez_still_draft_00001_.png
  [ "${status}" -eq 0 ]
  run git check-ignore -q outputs/ez_gosee_90s.mp4
  [ "${status}" -eq 0 ]
  run git check-ignore -q input/start.png
  [ "${status}" -eq 0 ]
  run git check-ignore -q inputs/start.png
  [ "${status}" -eq 0 ]
  run git check-ignore -q comfy-state/ComfyUI/main.py
  [ "${status}" -eq 0 ]
  run git check-ignore -q workflows/_user/.gitkeep
  [ "${status}" -eq 1 ]
  run git check-ignore -q workflows/_user/README.md
  [ "${status}" -eq 1 ]
  run git check-ignore -q workflows/stills/still-draft.json
  [ "${status}" -eq 1 ]
  run git check-ignore -q workflows/_lab/stills/still-draft.json
  [ "${status}" -eq 1 ]
  run git check-ignore -q workflows/klein/_user/secret.json
  [ "${status}" -eq 0 ]
}

@test "lab workflows forbid MiniMax H3 nodes and filenames" {
  local dir="${REPO_ROOT}/workflows"
  run grep -R -E 'MiniMaxH3|minimax_h3|h3-go-see|h3-still-here|h3-switchyard|GO_SEE_90s_H3' "${dir}"
  [ "${status}" -ne 0 ]
  [[ ! -f ${REPO_ROOT}/scripts/utilities/download-h3.sh ]]
  [[ ! -f ${REPO_ROOT}/docs/h3-films.md ]]
}

@test "shorts lab graphs are concat-safe US-safe I2V with last-frame prefix" {
  local shorts_yaml="${REPO_ROOT}/workflows/shorts"
  local lab="${REPO_ROOT}/workflows/_lab"
  local dir="${REPO_ROOT}/workflows"
  local wf wan ltx
  [[ -f $(lab_wf films/go-see.json) ]]
  [[ -f $(lab_wf films/still-here.json) ]]
  [[ -f $(lab_wf films/switchyard.json) ]]
  [[ -f $(lab_wf motion/silent/still-to-shot.json) ]]
  [[ -f $(lab_wf motion/av/still-to-shot.json) ]]
  [[ ! -f ${dir}/still-studio-lab-example.json ]]
  [[ ! -f ${dir}/wan-shot-lab-example.json ]]
  [[ ! -f ${shorts_yaml}/bridge-wan-lab-example.json ]]
  [[ -f ${shorts_yaml}/go-see.shots.yaml ]]
  run grep -R -E 'MiniMax|Seedance|Kling' "${dir}"
  [ "${status}" -ne 0 ]
  run python3 -c "
import json, os
from pathlib import Path
lab = Path('${lab}') / 'shorts'
for wf in sorted(lab.glob('*.json')):
    d = json.loads(wf.read_text(encoding='utf-8'))
    assert d.get('id') == os.path.splitext(wf.name)[0], wf
"
  wan="$(lab_wf motion/silent/still-to-shot.json)"
  ltx="$(lab_wf motion/av/still-to-shot.json)"
  run python3 -c "
import json
w=json.load(open('${wan}'))
l=json.load(open('${ltx}'))
assert any(n.get('type')=='Wan22ImageToVideoLatent' and n['widgets_values'][2]==120 for n in w['nodes'])
assert any(n.get('type')=='LTXVImgToVideo' and n['widgets_values'][2]==121 for n in l['nodes'])
assert any(n.get('type')=='LTXVEmptyLatentAudio' and n['widgets_values'][0]==121 for n in l['nodes'])
for g in (w, l):
    vhs=next(n for n in g['nodes'] if n.get('type')=='VHS_VideoCombine')
    assert float(vhs['widgets_values']['frame_rate'])==24
    last=next(n for n in g['nodes'] if n.get('title')=='Save last frame')
    assert str(last['widgets_values'][0]).endswith('_last')
    assert not any(
        n.get('type') in ('Wan22ImageToVideoLatent','LTXVImgToVideo','EmptyLTXVLatentVideo','LTXVEmptyLatentAudio')
        and int(n['widgets_values'][2] if n['type']!='LTXVEmptyLatentAudio' else n['widgets_values'][0])>=241
        for n in g['nodes']
    )
"
  [ "${status}" -eq 0 ]
}

@test "lab workflows parse, name pattern, banned strings, no overlaps" {
  local dir="${REPO_ROOT}/workflows"
  for gone in \
    ltx-i2v-30s-lab-example.json \
    ltx-t2v-60s-lab-example.json \
    flux-txt2img-lab-example.json \
    h3-go-see-90s-lab-example.json \
    flux-to-ltx-lab-example.json \
    still-studio-lab-example.json \
    wan-shot-lab-example.json \
    still-draft-lab-example.json \
    still-app-lab-example.json \
    gif-loop-lab-example.json \
    dream-house-lab-example.json; do
    [[ ! -f ${dir}/${gone} ]]
  done
  run python3 "${REPO_ROOT}/tests/python/_audit_lab_graphs.py" "${REPO_ROOT}"
  [ "${status}" -eq 0 ]
  [[ ${output} == *"audited "* ]]
}

@test "suite lab graphs stamp App Mode linearData to live node ids" {
  run python3 -c "
import json, sys
from pathlib import Path
root = Path('${REPO_ROOT}')
sys.path.insert(0, str(root / 'tests' / 'python'))
from _stamp_app_mode import STAMP_SPECS, linear_input_node_id, suite_json_paths
paths = suite_json_paths(root / 'workflows')
assert len(paths) == len(STAMP_SPECS)
for path in paths:
    graph = json.loads(path.read_text(encoding='utf-8'))
    extra = graph['extra']
    assert extra['lab_app_mode']['enabled'] is True, path.name
    linear = extra['linearData']
    assert linear['inputs'] and linear['outputs'], path.name
    live = {int(n['id']) for n in graph['nodes']}
    for entry in linear['inputs']:
        assert isinstance(entry[0], int), (path.name, entry[0])
        nid = linear_input_node_id(entry)
        assert nid in live, (path.name, entry[0])
    for nid in linear['outputs']:
        assert int(nid) in live, (path.name, nid)
"
  [ "${status}" -eq 0 ]
}

@test "still lab graphs use Klein 4B Apache weights and flux2 CLIP" {
  local wf path draft hero
  for wf in stills/still-draft.json stills/still-hero.json stills/still-daily.json stills/still-studio.json; do
    path="$(lab_wf "${wf}")"
    [[ -f ${path} ]]
    run grep -F 'flux-2-klein-4b-fp8.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'qwen_3_4b.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'flux2-vae.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -E '"flux2"' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'EmptyFlux2LatentImage' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'SaveImage' "${path}"
    [ "${status}" -eq 0 ]
  done
  draft="$(lab_wf stills/still-draft.json)"
  hero="$(lab_wf stills/still-hero.json)"
  run grep -F 'ez_still_draft' "${draft}"
  [ "${status}" -eq 0 ]
  run grep -F '768' "${draft}"
  [ "${status}" -eq 0 ]
  run grep -F '1280' "${hero}"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${draft}'))
h=json.load(open('${hero}'))
def pos(g):
    enh=next(n for n in g['nodes'] if n.get('type')=='EZKleinPromptEnhance')
    v=enh['widgets_values']
    return v[1] if len(v)>=7 else v[0]
assert pos(d)==pos(h)
assert 'photoreal still' in pos(d)
assert 'techno wizard' in pos(d)
assert 'no logos, no text' not in pos(d)
assert any(n.get('type')=='KSampler' and n['widgets_values'][2]==4 for n in d['nodes'])
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][2]==2 for n in d['nodes'])
assert any(n.get('type')=='EZKleinPromptEnhance' and (n['widgets_values'][2] if len(n['widgets_values'])>=7 else n['widgets_values'][1]) is True for n in d['nodes'])
"
  [ "${status}" -eq 0 ]
}

@test "wan lab graphs use 5B Apache weights, 121 frames, VHS" {
  local wf path i2v t2v shot
  for wf in motion/silent/still-to-video-5s.json motion/silent/text-to-video-5s.json; do
    path="$(lab_wf "${wf}")"
    [[ -f ${path} ]]
    run grep -F 'wan2.2_ti2v_5B_fp16.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'wan2.2_vae.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'umt5_xxl_fp8_e4m3fn_scaled.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -E '"wan"' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'VHS_VideoCombine' "${path}"
    [ "${status}" -eq 0 ]
    run python3 -c "
import json
d=json.load(open('${path}'))
assert any(n.get('type')=='Wan22ImageToVideoLatent' and n['widgets_values'][2]==121 for n in d['nodes'])
vhs=[n for n in d['nodes'] if n.get('type')=='VHS_VideoCombine']
assert len(vhs)==1
assert vhs[0]['widgets_values']['format']=='video/h264-mp4'
assert float(vhs[0]['widgets_values']['frame_rate'])==24
assert vhs[0]['widgets_values']['save_output'] is True
"
    [ "${status}" -eq 0 ]
  done
  i2v="$(lab_wf motion/silent/still-to-video-5s.json)"
  t2v="$(lab_wf motion/silent/text-to-video-5s.json)"
  shot="$(lab_wf motion/silent/still-to-shot.json)"
  run grep -F 'ez_shot_01' "${shot}"
  [ "${status}" -eq 0 ]
  run grep -F 'Motion / prompt' "${i2v}"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${i2v}'))
loads=[n for n in d['nodes'] if n.get('type')=='LoadImage']
assert loads and loads[0]['widgets_values'][0]=='example.png'
assert loads[0].get('mode')==0
look=[n for n in d['nodes'] if n.get('type')=='CLIPTextEncode' and n.get('title')=='Positive']
assert not look
enh=next(n for n in d['nodes'] if n.get('type')=='EZWanPromptEnhance')
ev=enh['widgets_values']
assert (ev[2] if len(ev)>=7 else ev[1]) is True
assert (ev[3] if len(ev)>=7 else ev[2])=='i2v'
et=(ev[1] if len(ev)>=7 else ev[0]).lower()
assert 'dollies' in et or 'dolly' in et or 'push' in et
t=json.load(open('${t2v}'))
tl=[n for n in t['nodes'] if n.get('type')=='LoadImage']
assert tl and tl[0].get('mode')==4
tenh=next(n for n in t['nodes'] if n.get('type')=='EZWanPromptEnhance')
tv=tenh['widgets_values']
tt=(tv[1] if len(tv)>=7 else tv[0])
assert (tv[3] if len(tv)>=7 else tv[2])=='t2v'
assert 'dollies' in tt.lower() or 'dolly' in tt.lower() or 'camera' in tt.lower()
assert 'YouTube 16:9 still:' not in tt
assert 'score' not in tt.lower()
"
  [ "${status}" -eq 0 ]
}

@test "ltx hero graphs use 2.5 distilled pack, 121 frames, VHS, CLIP ltxv" {
  local wf path i2v t2v
  for wf in motion/av/still-to-video-5s.json motion/av/text-to-video-5s.json; do
    path="$(lab_wf "${wf}")"
    [[ -f ${path} ]]
    run grep -F 'ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'ltx-2.5-video-vae-bf16.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'ltx-2.5-audio-vae-bf16.safetensors' "${path}"
    [ "${status}" -eq 0 ]
    run grep -E '"ltxv"' "${path}"
    [ "${status}" -eq 0 ]
    run grep -F 'DualCLIPLoader' "${path}"
    [ "${status}" -ne 0 ]
    run python3 -c "
import json
d=json.load(open('${path}'))
vlen=None
for n in d['nodes']:
    if n.get('type') in ('EmptyLTXVLatentVideo','LTXVImgToVideo'):
        vlen=int(n['widgets_values'][2]); break
assert vlen==121, vlen
ea=next(n for n in d['nodes'] if n.get('type')=='LTXVEmptyLatentAudio')
assert int(ea['widgets_values'][0])==121
vhs=[n for n in d['nodes'] if n.get('type')=='VHS_VideoCombine']
assert len(vhs)==1
assert vhs[0]['widgets_values']['format']=='video/h264-mp4'
assert vhs[0]['widgets_values']['save_output'] is True
assert any(n.get('type')=='LTXVAudioVAEDecode' for n in d['nodes'])
audio=next(i for i in vhs[0]['inputs'] if i.get('name')=='audio')
assert audio.get('link') is not None
assert 'preview' in (vhs[0].get('title') or '').lower()
"
    [ "${status}" -eq 0 ]
  done
  i2v="$(lab_wf motion/av/still-to-video-5s.json)"
  t2v="$(lab_wf motion/av/text-to-video-5s.json)"
  run python3 -c "
import json
d=json.load(open('${i2v}'))
loads=[n for n in d['nodes'] if n.get('type')=='LoadImage']
assert loads and loads[0]['widgets_values'][0]=='example.png'
enh=next(n for n in d['nodes'] if n.get('type')=='EZLTXPromptEnhance')
ev=enh['widgets_values']
assert (ev[2] if len(ev)>=8 else ev[1]) is True
assert (ev[3] if len(ev)>=8 else ev[2])=='i2v'
text=(ev[1] if len(ev)>=8 else ev[0]).lower()
assert 'footsteps' in text or 'wind' in text or 'breeze' in text
assert 'no score' in text or 'no music' in text
t=json.load(open('${t2v}'))
tenh=next(n for n in t['nodes'] if n.get('type')=='EZLTXPromptEnhance')
tv=tenh['widgets_values']
tt=(tv[1] if len(tv)>=8 else tv[0])
assert 'YouTube 16:9 still:' not in tt
assert 'wind' in tt.lower() or 'traffic' in tt.lower()
"
  [ "${status}" -eq 0 ]
}

@test "lab graph descriptions and notes are graph-specific" {
  run python3 -c "
import json
from pathlib import Path
root = Path('${REPO_ROOT}/workflows')
stale = ('~10 s', 'tea house', 'sketch', 'STILL DRAFT/HERO', 'bridge-wan')
seen = []
for p in sorted((root / '_lab').rglob('*.json')):
    d = json.loads(p.read_text())
    desc = d.get('extra', {}).get('lab_description') or ''
    note = d.get('extra', {}).get('lab_note') or ''
    blob = desc + '\n' + note
    assert desc.strip(), p.name
    assert note.strip(), p.name
    for s in stale:
        assert s not in blob, (p.name, s)
    seen.append(p.stem)
    rel = p.relative_to(root / '_lab').with_suffix('').as_posix()
    if rel == 'motion/silent/still-to-video-5s':
        assert '121' in desc
        assert 'motion/silent/still-to-shot' in note
    if rel == 'motion/silent/text-to-video-5s':
        assert 'T2V' in desc
        assert 'bypassed' in note.lower()
    if rel == 'motion/silent/still-to-shot':
        assert '120' in desc
        assert 'ez_shot_01' in note
    if rel == 'motion/av/still-to-shot':
        assert '121' in desc
    if rel == 'stills/still-draft':
        assert 'stills/still-hero' in note
    if rel == 'stills/still-studio':
        assert 'Format' in note or 'format' in note.lower()
        assert '1280' in note
    if rel == 'films/go-see':
        assert 'parkour' in desc
        assert 'one-click' in desc.lower() or 'queue once' in note.lower()
assert 'still-draft' in seen
assert 'go-see' in seen
assert 'shorts-still' in seen
assert 'broll-ambient' in seen
"
  [ "${status}" -eq 0 ]
}

@test "video graphs save VHS output and LTX muxes audio" {
  run python3 -c "
import json
from pathlib import Path
root = Path('${REPO_ROOT}/workflows')
video = 0
for p in sorted((root / '_lab').rglob('*.json')):
    d = json.loads(p.read_text())
    vhs_nodes = [n for n in d['nodes'] if n.get('type')=='VHS_VideoCombine']
    if not vhs_nodes:
        continue
    video += 1
    for vhs in vhs_nodes:
        wv = vhs['widgets_values']
        assert wv.get('save_output') is True, p.name
        prefix = wv.get('filename_prefix') or ''
        assert prefix.startswith('ez_'), (p.name, prefix)
        assert 'preview' in (vhs.get('title') or '').lower(), p.name
    if any(n.get('type')=='LTXVSeparateAVLatent' for n in d['nodes']):
        has_decode = any(n.get('type')=='LTXVAudioVAEDecode' for n in d['nodes'])
        has_load = any(n.get('type')=='LoadAudio' for n in d['nodes'])
        assert has_decode or has_load, p.name
        for vhs in vhs_nodes:
            audio = next(i for i in vhs['inputs'] if i.get('name')=='audio')
            assert audio.get('link') is not None, p.name
assert video >= 7, video
"
  [ "${status}" -eq 0 ]
}

@test "creator toolkit lab graphs exist" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in \
    stills/shorts-still.json \
    motion/silent/shorts-still-5s.json \
    motion/av/shorts-still-5s.json \
    stills/thumbnail.json \
    stills/product-packshot.json \
    stills/before-after.json \
    stills/style-lock.json \
    motion/loops/bumper-loop.json \
    motion/av/broll-ambient.json \
    stills/storyboard-6up.json \
    stills/endcard-cta.json \
    stills/quote-bg.json \
    stills/open-graph.json \
    stills/podcast-cover.json \
    stills/banner-wide.json \
    stills/instagram-square.json \
    stills/hook-still.json \
    stills/lower-third-bg.json \
    stills/food-tabletop.json \
    stills/lighting-trio.json \
    stills/time-of-day.json \
    stills/camera-angles.json \
    stills/color-moods.json \
    motion/silent/orbit-still-5s.json \
    motion/silent/push-in-still-5s.json \
    motion/silent/parallax-still-5s.json \
    motion/loops/sticker-loop.json \
    motion/av/weather-broll.json \
    motion/av/interior-ambience.json \
    motion/av/hook-av.json \
    motion/av/dialogue-5s.json \
    motion/av/multishot-5s.json \
    motion/av/product-hero.json \
    motion/av/first-last-5s.json \
    motion/av/audio-to-video-5s.json; do
    [[ -f $(lab_wf "${wf}") ]]
  done
}

@test "lab examples have operator Notes, prompts, extra.lab_note" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  local -a files=()
  while IFS= read -r wf; do
    files+=("${wf}")
  done < <(find "${dir}/_lab" -name '*.json' | sort)
  [[ ${#files[@]} -gt 8 ]]
  for wf in "${files[@]}"; do
    run python3 -c "
import json, os
p='${wf}'
d=json.load(open(p))
notes=[n for n in d['nodes'] if n.get('type') in ('Note','MarkdownNote')]
assert notes
assert any(isinstance(n.get('widgets_values'), list) and n['widgets_values'] and len(str(n['widgets_values'][0]).strip())>40 for n in notes)
clips=[n for n in d['nodes'] if n.get('type')=='CLIPTextEncode']
ace=[n for n in d['nodes'] if n.get('type')=='TextEncodeAceStepAudio1.5']
zero=[n for n in d['nodes'] if n.get('type')=='ConditioningZeroOut']
unets=[n for n in d['nodes'] if n.get('type')=='UNETLoader']
trellis=[n for n in d['nodes'] if n.get('type')=='Trellis2Conditioning']
# Visual graphs use two CLIP encodes. Podcast beds use two ACE encodes.
# Rap graphs follow Comfy-Org ACE-Step 1.5: one encode + ConditioningZeroOut.
# No-UNET inspire Apps (Prompt Forge / Beat Sheet) have neither.
# Native TRELLIS uses Trellis2Conditioning, not CLIPTextEncode.
if unets and not trellis:
    assert len(clips)>=2 or len(ace)>=2 or (len(ace)>=1 and len(zero)>=1), p
for n in clips:
    text=(n.get('widgets_values') or [''])[0]
    assert isinstance(text,str) and text.strip()
for n in ace:
    tags=(n.get('widgets_values') or [''])[0]
    assert isinstance(tags,str) and tags.strip()
assert isinstance(d.get('extra',{}).get('lab_note'), str) and d['extra']['lab_note'].strip()
"
    [ "${status}" -eq 0 ]
  done
}

@test "operator app graphs: still settings, gif ping-pong loop, dream-house pack" {
  local daily gif house clay studio
  daily="$(lab_wf stills/still-daily.json)"
  gif="$(lab_wf motion/loops/gif-loop.json)"
  house="$(lab_wf stills/dream-house.json)"
  clay="$(lab_wf stills/dream-house-clay.json)"
  [[ -f ${daily} ]]
  [[ -f ${gif} ]]
  [[ -f ${house} ]]
  [[ -f ${clay} ]]
  run python3 -c "
import json
s=json.load(open('${daily}'))
assert s.get('id')=='still-daily'
assert any(n.get('type')=='UNETLoader' and n['widgets_values'][0]=='flux-2-klein-4b-fp8.safetensors' for n in s['nodes'])
assert any(n.get('type')=='CLIPLoader' and 'qwen_3_4b.safetensors' in n['widgets_values'] and 'flux2' in n['widgets_values'] for n in s['nodes'])
assert any(n.get('type')=='VAELoader' and n['widgets_values'][0]=='flux2-vae.safetensors' for n in s['nodes'])
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][:2]==[1024, 576] for n in s['nodes'])
assert any(n.get('type')=='KSampler' and n['widgets_values'][2]==4 and float(n['widgets_values'][3])==1.0 for n in s['nodes'])
assert any(n.get('type')=='SaveImage' and n['widgets_values'][0]=='ez_still_app' for n in s['nodes'])
enh=next(n for n in s['nodes'] if n.get('type')=='EZKleinPromptEnhance')
assert (enh['widgets_values'][2] if len(enh['widgets_values'])>=7 else enh['widgets_values'][1]) is True
unet=next(n for n in s['nodes'] if n.get('type')=='UNETLoader')
assert 'swap' in (unet.get('title') or '').lower()
note=next(n for n in s['nodes'] if n.get('type') in ('Note','MarkdownNote'))
ntext=str(note['widgets_values'][0]).lower()
assert 'swap' in ntext and 'steps' in ntext and 'cfg' in ntext
assert 'flux-2-klein-base-4b-fp8' in ntext or 'base' in ntext
assert any(g.get('title','').upper().startswith('MODEL') for g in s.get('groups',[]))
assert any('SETTING' in g.get('title','').upper() for g in s.get('groups',[]))
"
  [ "${status}" -eq 0 ]
  studio="$(lab_wf stills/still-studio.json)"
  [[ -f ${studio} ]]
  run python3 -c "
import json
s=json.load(open('${studio}'))
assert s.get('id')=='still-studio'
assert any(n.get('type')=='EZImageFormat' for n in s['nodes'])
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][:2]==[1280, 704] for n in s['nodes'])
assert any(n.get('type')=='SaveImage' and n['widgets_values'][0]=='ez_still_studio' for n in s['nodes'])
fmt=next(n for n in s['nodes'] if n.get('type')=='EZImageFormat')
assert fmt['widgets_values'][0].startswith('16:9')
enh=next(n for n in s['nodes'] if n.get('type')=='EZKleinPromptEnhance')
assert enh['widgets_values'][2] is True
assert enh['widgets_values'][6]=='stills/still-studio'
assert any('FORMAT' in g.get('title','').upper() for g in s.get('groups',[]))
"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
g=json.load(open('${gif}'))
assert g.get('id')=='gif-loop'
assert any(n.get('type')=='UNETLoader' and n['widgets_values'][0]=='wan2.2_ti2v_5B_fp16.safetensors' for n in g['nodes'])
assert any(n.get('type')=='VAELoader' and n['widgets_values'][0]=='wan2.2_vae.safetensors' for n in g['nodes'])
lat=next(n for n in g['nodes'] if n.get('type')=='Wan22ImageToVideoLatent')
assert int(lat['widgets_values'][2])==49
assert int(lat['widgets_values'][2])<241
load=next(n for n in g['nodes'] if n.get('type')=='LoadImage')
assert load['widgets_values'][0]=='example.png'
assert load.get('mode')==0
vhs=[n for n in g['nodes'] if n.get('type')=='VHS_VideoCombine']
assert vhs
loop=next(n for n in vhs if n.get('mode',0)==0)
wv=loop['widgets_values']
assert wv['format']=='image/gif'
assert wv['pingpong'] is True
assert int(wv['loop_count'])==0
assert float(wv['frame_rate'])==12
assert wv['save_output'] is True
assert 'ez_gif_loop' in str(wv['filename_prefix'])
enh=next(n for n in g['nodes'] if n.get('type')=='EZWanPromptEnhance')
ev=enh['widgets_values']
assert (ev[2] if len(ev)>=7 else ev[1]) is False
assert (ev[3] if len(ev)>=7 else ev[2])=='i2v'
motion=(ev[1] if len(ev)>=7 else ev[0]).lower()
assert 'locked' in motion or 'lock' in motion
assert 'dolly' not in motion and 'walk' not in motion
assert 'breeze' in motion or 'curtain' in motion or 'leaves' in motion
"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${house}'))
assert d.get('id')=='dream-house'
assert d.get('extra',{}).get('lab_flux_tier')=='fast'
assert any(n.get('type')=='UNETLoader' and n['widgets_values'][0]=='flux-2-klein-4b-fp8.safetensors' for n in d['nodes'])
assert any(n.get('type')=='CLIPLoader' and 'qwen_3_4b.safetensors' in n['widgets_values'] and 'flux2' in n['widgets_values'] for n in d['nodes'])
assert any(n.get('type')=='VAELoader' and n['widgets_values'][0]=='flux2-vae.safetensors' for n in d['nodes'])
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][:2]==[1024, 1280] for n in d['nodes'])
joins=[n for n in d['nodes'] if n.get('type')=='EZPromptJoin']
assert len(joins)==10
saves=[n for n in d['nodes'] if n.get('type')=='SaveImage']
prefs=sorted(n['widgets_values'][0] for n in saves)
assert prefs==[f'ez_dream_house_{i:02d}' for i in range(1,11)]
samplers=[n for n in d['nodes'] if n.get('type')=='KSampler']
assert len(samplers)==10
assert all(
    n['widgets_values'][0]==42
    and n['widgets_values'][1]=='fixed'
    and n['widgets_values'][2]==4
    and float(n['widgets_values'][3])==1.0
    and n['widgets_values'][4]=='euler'
    and n['widgets_values'][5]=='simple'
    and float(n['widgets_values'][6])==1.0
    for n in samplers
)
enh=[n for n in d['nodes'] if n.get('type')=='EZKleinPromptEnhance']
assert len(enh)==1
hv=enh[0]['widgets_values']
assert (hv[2] if len(hv)>=7 else hv[1]) is True
assert (hv[3] if len(hv)>=7 else hv[2])=='identity'
assert (hv[4] if len(hv)>=7 else hv[3])=='Instagram 4:5 still'
ident=(hv[1] if len(hv)>=7 else hv[0])
ident_l=ident.lower()
assert 'warm-glass' in ident_l and 'crown penthouse' in ident_l
assert 'wraparound terrace' in ident_l and 'three-bay' in ident_l
assert 'lounge' in ident_l
assert 'cook wall' in ident_l
assert 'lantern' in ident_l or 'path light' in ident_l
assert '24mm' not in ident_l
assert 'cedar' not in ident_l and 'cabin' not in ident_l
assert 'no logos, no text' not in ident
assert sum(1 for n in d['nodes'] if n.get('type')=='VAEEncode')==0
assert sum(1 for n in d['nodes'] if n.get('type')=='ReferenceLatent')==0
by_id={n['id']:n for n in d['nodes']}
incoming={}
for l in d['links']:
    incoming.setdefault((l[3], l[4]), []).append(l)
banned=('pier','courtyard','pavilion','two-story','a-frame','glass box','outdoor kitchen','outdoor tub','cedar','alpine','gravel','hip roof')
tour=('SHOT 01 tower','SHOT 02 foyer','SHOT 03 lounge','SHOT 04 kitchen','SHOT 05 dining','SHOT 06 bedroom','SHOT 07 bath','SHOT 08 terrace','SHOT 09 drone','SHOT 10 study')
assert [n.get('title') for n in sorted(joins, key=lambda n: n['id'])]==list(tour)
for i, join in enumerate(sorted(joins, key=lambda n: n['id'])):
    shot=join['widgets_values'][0]
    inv=join['widgets_values'][1]
    lock=join['widgets_values'][2]
    assert lock=='view'
    assert inv.strip()==''
    full=shot+' '+ident
    assert len(full.split())<=220, (join.get('title'), len(full.split()))
    sl=shot.lower()
    assert 'penthouse' not in sl
    assert 'techno wizard' not in sl
    assert 'data-staff' not in sl
    assert not any(b in sl for b in banned)
    pos=next(n for n in d['nodes'] if n.get('title')==f'Positive {i+1:02d}')
    assert pos['widgets_values'][0].startswith(shot)
    assert 'walkthrough' in pos['widgets_values'][0]
    ks_id=12+i*5
    pos_src=by_id[incoming[(ks_id,1)][0][1]]['type']
    lat_src=by_id[incoming[(ks_id,3)][0][1]]['type']
    assert lat_src=='EmptyFlux2LatentImage'
    assert pos_src=='CLIPTextEncode'
note=next(n for n in d['nodes'] if n.get('type') in ('Note','MarkdownNote'))
ntext=str(note['widgets_values'][0]).lower()
assert 'world bible' in ntext or 'camera-free' in ntext or 'one place' in ntext
assert 'walkthrough' in ntext or 'virtual tour' in ntext
assert 'referencelatent' in ntext or 'new views' in ntext or 'independent t2i' in ntext
"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${clay}'))
assert d.get('id')=='dream-house-clay'
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][:2]==[1024, 1280] for n in d['nodes'])
assert sum(1 for n in d['nodes'] if n.get('type')=='ReferenceLatent')==10
assert sum(1 for n in d['nodes'] if n.get('type')=='LoadImage')==10
saves=[n for n in d['nodes'] if n.get('type')=='SaveImage']
prefs=sorted(n['widgets_values'][0] for n in saves)
assert prefs==[f'ez_dream_house_clay_{i:02d}' for i in range(1,11)]
loads=sorted((n for n in d['nodes'] if n.get('type')=='LoadImage'), key=lambda n: n['id'])
assert [n['widgets_values'][0] for n in loads]==[f'ez_house_clay_{i:02d}.png' for i in range(1,11)]
enh=next(n for n in d['nodes'] if n.get('type')=='EZKleinPromptEnhance')
hv=enh['widgets_values']
assert (hv[3] if len(hv)>=7 else hv[2])=='identity'
note=str(next(n for n in d['nodes'] if n.get('type') in ('Note','MarkdownNote'))['widgets_values'][0]).lower()
assert 'house-views' in note
assert 'occupancy' in note
assert 'input' in note
assert 'install-inputs' in note
assert 'seed-inputs' in note
"
  [ "${status}" -eq 0 ]
}

@test "download-image default pack includes Klein 4B Apache companions" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/utilities/download-image.sh"
  run tier_repo fast
  [[ "${output}" == *"FLUX.2-klein-4b-fp8"* ]]
  run tier_include_patterns te
  [[ "${output}" == *"qwen_3_4b"* ]]
}

@test "lab_expected_model_relpaths matches download-models pack" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib/common.sh"
  run lab_expected_model_relpaths
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux-2-klein-4b-fp8.safetensors"* ]]
  [[ "${output}" == *"wan2.2_ti2v_5B_fp16.safetensors"* ]]
  [[ "${output}" == *"ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"* ]]
  [[ "${output}" != *"klein-9b"* ]]
}
