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

@test "lab workflows forbid MiniMax H3 nodes and filenames" {
  local dir="${REPO_ROOT}/workflows"
  run grep -R -E 'MiniMaxH3|minimax_h3|h3-go-see|h3-still-here|h3-switchyard|GO_SEE_90s_H3' "${dir}"
  [ "${status}" -ne 0 ]
  [[ ! -f ${REPO_ROOT}/scripts/utilities/download-h3.sh ]]
  [[ ! -f ${REPO_ROOT}/docs/h3-films.md ]]
}

@test "shorts lab graphs are 120-frame US-safe I2V with last-frame prefix" {
  local shorts="${REPO_ROOT}/workflows/shorts"
  local dir="${REPO_ROOT}/workflows"
  local wf
  [[ -f ${shorts}/film-go-see-90s-run-lab-example.json ]]
  [[ -f ${shorts}/film-still-here-90s-lab-example.json ]]
  [[ -f ${shorts}/film-switchyard-90s-lab-example.json ]]
  [[ -f ${dir}/wan-i2v-shot-lab-example.json ]]
  [[ -f ${dir}/ltx-i2v-shot-lab-example.json ]]
  [[ ! -f ${dir}/still-studio-lab-example.json ]]
  [[ ! -f ${dir}/wan-shot-lab-example.json ]]
  [[ ! -f ${shorts}/bridge-wan-lab-example.json ]]
  run grep -R -E 'z_image_turbo|FLUX\.2-dev|klein-9b|flux-2-klein-9b|MiniMax|Seedance|Kling' "${dir}"
  [ "${status}" -ne 0 ]
  for wf in "${shorts}"/*-lab-example.json; do
    run python3 -c "import json,os; p='${wf}'; d=json.load(open(p)); assert d.get('id')==os.path.splitext(os.path.basename(p))[0]"
    [ "${status}" -eq 0 ]
  done
  run python3 -c "
import json
w=json.load(open('${dir}/wan-i2v-shot-lab-example.json'))
l=json.load(open('${dir}/ltx-i2v-shot-lab-example.json'))
assert any(n.get('type')=='Wan22ImageToVideoLatent' and n['widgets_values'][2]==120 for n in w['nodes'])
assert any(n.get('type')=='LTXVImgToVideo' and n['widgets_values'][2]==120 for n in l['nodes'])
assert any(n.get('type')=='LTXVEmptyLatentAudio' and n['widgets_values'][0]==120 for n in l['nodes'])
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

@test "lab-example workflows parse, name pattern, banned strings, no overlaps" {
  local wf dir="${REPO_ROOT}/workflows"
  local n=0
  shopt -s nullglob
  local -a files=("${dir}"/*-lab-example.json)
  shopt -u nullglob
  [[ ${#files[@]} -ge 8 ]]
  [[ ${#files[@]} -le 64 ]]

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

  for wf in "${files[@]}"; do
    n=$((n + 1))
    run python3 -c "import json; json.load(open('${wf}'))"
    [ "${status}" -eq 0 ]
    run python3 -c "import json,os; p='${wf}'; d=json.load(open(p)); assert d.get('id')==os.path.splitext(os.path.basename(p))[0]"
    [ "${status}" -eq 0 ]
    run grep -E 'z_image_turbo|FLUX\.2-dev|klein-9b|flux-2-klein-9b|MiniMax|Seedance|Kling' "${wf}"
    [ "${status}" -ne 0 ]
    run python3 -c "
import json
pad = 20
d = json.load(open('${wf}'))
boxes = []
for n in d['nodes']:
    x, y = n['pos']
    s = n.get('size', [200, 100])
    if isinstance(s, dict):
        w, h = float(s.get('0', 200)), float(s.get('1', 100))
    else:
        w, h = float(s[0]), float(s[1])
    boxes.append((n['id'], n['type'], x - pad, y - pad, x + w + pad, y + h + pad))
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        a, b = boxes[i], boxes[j]
        if a[2] < b[4] and a[4] > b[2] and a[3] < b[5] and a[5] > b[3]:
            raise SystemExit(f'overlap {a[0]}({a[1]}) vs {b[0]}({b[1]})')
"
    [ "${status}" -eq 0 ]
  done
  [[ ${n} -ge 8 ]]
}

@test "still lab graphs use Klein 4B Apache weights and flux2 CLIP" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in klein-still-draft-lab-example.json klein-still-hero-lab-example.json klein-still-daily-lab-example.json; do
    [[ -f ${dir}/${wf} ]]
    run grep -F 'flux-2-klein-4b-fp8.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'qwen_3_4b.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'flux2-vae.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -E '"flux2"' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'EmptyFlux2LatentImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'SaveImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
  done
  run grep -F 'ez_still_draft' "${dir}/klein-still-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '768' "${dir}/klein-still-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '1280' "${dir}/klein-still-hero-lab-example.json"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${dir}/klein-still-draft-lab-example.json'))
h=json.load(open('${dir}/klein-still-hero-lab-example.json'))
def pos(g):
    enh=next(n for n in g['nodes'] if n.get('type')=='EZKleinPromptEnhance')
    return enh['widgets_values'][0]
assert pos(d)==pos(h)
assert 'photoreal still photograph' in pos(d)
assert 'no logos, no text' not in pos(d)
assert any(n.get('type')=='KSampler' and n['widgets_values'][2]==4 for n in d['nodes'])
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][2]==2 for n in d['nodes'])
assert any(n.get('type')=='EZKleinPromptEnhance' and n['widgets_values'][1] is False for n in d['nodes'])
"
  [ "${status}" -eq 0 ]
}

@test "wan lab graphs use 5B Apache weights, 121 frames, VHS" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in wan-i2v-5s-lab-example.json wan-t2v-5s-lab-example.json; do
    [[ -f ${dir}/${wf} ]]
    run grep -F 'wan2.2_ti2v_5B_fp16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'wan2.2_vae.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'umt5_xxl_fp8_e4m3fn_scaled.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -E '"wan"' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'VHS_VideoCombine' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run python3 -c "
import json
d=json.load(open('${dir}/${wf}'))
assert any(n.get('type')=='Wan22ImageToVideoLatent' and n['widgets_values'][2]==121 for n in d['nodes'])
vhs=[n for n in d['nodes'] if n.get('type')=='VHS_VideoCombine']
assert len(vhs)==1
assert vhs[0]['widgets_values']['format']=='video/h264-mp4'
assert float(vhs[0]['widgets_values']['frame_rate'])==24
assert vhs[0]['widgets_values']['save_output'] is True
"
    [ "${status}" -eq 0 ]
  done
  run grep -F 'ez_shot_01' "${dir}/wan-i2v-shot-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F 'Motion / prompt' "${dir}/wan-i2v-5s-lab-example.json"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${dir}/wan-i2v-5s-lab-example.json'))
loads=[n for n in d['nodes'] if n.get('type')=='LoadImage']
assert loads and loads[0]['widgets_values'][0]=='example.png'
assert loads[0].get('mode')==0
look=[n for n in d['nodes'] if n.get('type')=='CLIPTextEncode' and n.get('title')=='Positive']
assert not look
enh=next(n for n in d['nodes'] if n.get('type')=='EZWanPromptEnhance')
assert enh['widgets_values'][1] is False
assert enh['widgets_values'][2]=='i2v'
assert 'dollies' in enh['widgets_values'][0].lower() or 'dolly' in enh['widgets_values'][0].lower() or 'push' in enh['widgets_values'][0].lower()
t=json.load(open('${dir}/wan-t2v-5s-lab-example.json'))
tl=[n for n in t['nodes'] if n.get('type')=='LoadImage']
assert tl and tl[0].get('mode')==4
tenh=next(n for n in t['nodes'] if n.get('type')=='EZWanPromptEnhance')
assert tenh['widgets_values'][2]=='t2v'
assert 'dollies' in tenh['widgets_values'][0].lower() or 'dolly' in tenh['widgets_values'][0].lower() or 'camera' in tenh['widgets_values'][0].lower()
assert 'YouTube 16:9 still:' not in tenh['widgets_values'][0]
assert 'score' not in tenh['widgets_values'][0].lower()
"
  [ "${status}" -eq 0 ]
}

@test "ltx hero graphs use 2.5 distilled pack, 121 frames, VHS, CLIP ltxv" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in ltx-i2v-5s-lab-example.json ltx-t2v-5s-lab-example.json; do
    [[ -f ${dir}/${wf} ]]
    run grep -F 'ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'ltx-2.5-video-vae-bf16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'ltx-2.5-audio-vae-bf16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -E '"ltxv"' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'DualCLIPLoader' "${dir}/${wf}"
    [ "${status}" -ne 0 ]
    run python3 -c "
import json
d=json.load(open('${dir}/${wf}'))
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
  run python3 -c "
import json
d=json.load(open('${dir}/ltx-i2v-5s-lab-example.json'))
loads=[n for n in d['nodes'] if n.get('type')=='LoadImage']
assert loads and loads[0]['widgets_values'][0]=='example.png'
enh=next(n for n in d['nodes'] if n.get('type')=='EZLTXPromptEnhance')
assert enh['widgets_values'][1] is False
assert enh['widgets_values'][2]=='i2v'
text=enh['widgets_values'][0].lower()
assert 'footsteps' in text or 'wind' in text
assert 'no score' in text or 'no music' in text
t=json.load(open('${dir}/ltx-t2v-5s-lab-example.json'))
tenh=next(n for n in t['nodes'] if n.get('type')=='EZLTXPromptEnhance')
assert 'YouTube 16:9 still:' not in tenh['widgets_values'][0]
assert 'shop bell' in tenh['widgets_values'][0].lower() or 'footsteps' in tenh['widgets_values'][0].lower()
"
  [ "${status}" -eq 0 ]
}

@test "lab graph descriptions and notes are graph-specific" {
  run python3 -c "
import json
from pathlib import Path
root = Path('${REPO_ROOT}/workflows')
stale = ('~10 s', 'tea house', 'sketch', 'STILL DRAFT/HERO', 'bridge-wan', 'still-studio')
seen = []
for p in sorted(root.rglob('*-lab-example.json')):
    d = json.loads(p.read_text())
    desc = d.get('extra', {}).get('lab_description') or ''
    note = d.get('extra', {}).get('lab_note') or ''
    blob = desc + '\n' + note
    assert desc.strip(), p.name
    assert note.strip(), p.name
    for s in stale:
        assert s not in blob, (p.name, s)
    seen.append(p.stem)
    if p.stem == 'wan-i2v-5s-lab-example':
        assert '121' in desc
        assert 'wan-i2v-shot-lab-example' in note
    if p.stem == 'wan-t2v-5s-lab-example':
        assert 'T2V' in desc
        assert 'bypassed' in note.lower()
    if p.stem == 'wan-i2v-shot-lab-example':
        assert '120' in desc
        assert 'ez_shot_01' in note
    if p.stem == 'ltx-i2v-shot-lab-example':
        assert '120' in desc
    if p.stem == 'klein-still-draft-lab-example':
        assert 'klein-still-hero-lab-example' in note
    if p.stem == 'film-go-see-90s-run-lab-example':
        assert 'running' in desc
        assert 'Unified' in desc or 'unified' in note.lower()
assert 'klein-still-draft-lab-example' in seen
assert 'film-go-see-90s-run-lab-example' in seen
assert 'klein-shorts-still-lab-example' in seen
assert 'ltx-broll-ambient-lab-example' in seen
"
  [ "${status}" -eq 0 ]
}

@test "video graphs save VHS output and LTX muxes audio" {
  run python3 -c "
import json
from pathlib import Path
root = Path('${REPO_ROOT}/workflows')
video = 0
for p in sorted(root.rglob('*-lab-example.json')):
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
        assert any(n.get('type')=='LTXVAudioVAEDecode' for n in d['nodes']), p.name
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
    klein-shorts-still-lab-example.json \
    wan-shorts-i2v-lab-example.json \
    ltx-shorts-i2v-lab-example.json \
    klein-thumbnail-lab-example.json \
    klein-product-packshot-lab-example.json \
    klein-before-after-lab-example.json \
    klein-style-lock-lab-example.json \
    wan-bumper-loop-lab-example.json \
    ltx-broll-ambient-lab-example.json \
    klein-storyboard-6up-lab-example.json \
    klein-endcard-cta-lab-example.json \
    klein-quote-bg-lab-example.json \
    klein-og-blog-lab-example.json \
    klein-podcast-cover-lab-example.json \
    klein-banner-wide-lab-example.json \
    klein-ig-square-lab-example.json \
    klein-hook-still-lab-example.json \
    klein-lower-third-bg-lab-example.json \
    klein-food-tabletop-lab-example.json \
    klein-lighting-trio-lab-example.json \
    klein-time-of-day-lab-example.json \
    klein-camera-angles-lab-example.json \
    klein-color-moods-lab-example.json \
    wan-orbit-i2v-lab-example.json \
    wan-push-in-i2v-lab-example.json \
    wan-parallax-i2v-lab-example.json \
    wan-sticker-loop-lab-example.json \
    ltx-weather-broll-lab-example.json \
    ltx-interior-ambience-lab-example.json \
    ltx-hook-av-lab-example.json; do
    [[ -f ${dir}/${wf} ]]
  done
}

@test "lab examples have operator Notes, prompts, extra.lab_note" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  shopt -s nullglob
  local -a files=("${dir}"/*-lab-example.json)
  shopt -u nullglob
  for wf in "${files[@]}"; do
    run python3 -c "
import json, os
p='${wf}'
d=json.load(open(p))
notes=[n for n in d['nodes'] if n.get('type') in ('Note','MarkdownNote')]
assert notes
assert any(isinstance(n.get('widgets_values'), list) and n['widgets_values'] and len(str(n['widgets_values'][0]).strip())>40 for n in notes)
clips=[n for n in d['nodes'] if n.get('type')=='CLIPTextEncode']
assert len(clips)>=2, p
for n in clips:
    text=(n.get('widgets_values') or [''])[0]
    assert isinstance(text,str) and text.strip()
assert isinstance(d.get('extra',{}).get('lab_note'), str) and d['extra']['lab_note'].strip()
"
    [ "${status}" -eq 0 ]
  done
}

@test "operator app graphs: still settings, gif ping-pong loop, dream-house pack" {
  local dir="${REPO_ROOT}/workflows"
  [[ -f ${dir}/klein-still-daily-lab-example.json ]]
  [[ -f ${dir}/wan-gif-loop-lab-example.json ]]
  [[ -f ${dir}/klein-dream-house-lab-example.json ]]
  run python3 -c "
import json
s=json.load(open('${dir}/klein-still-daily-lab-example.json'))
assert s.get('id')=='klein-still-daily-lab-example'
assert any(n.get('type')=='UNETLoader' and n['widgets_values'][0]=='flux-2-klein-4b-fp8.safetensors' for n in s['nodes'])
assert any(n.get('type')=='CLIPLoader' and 'qwen_3_4b.safetensors' in n['widgets_values'] and 'flux2' in n['widgets_values'] for n in s['nodes'])
assert any(n.get('type')=='VAELoader' and n['widgets_values'][0]=='flux2-vae.safetensors' for n in s['nodes'])
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][:2]==[1024, 576] for n in s['nodes'])
assert any(n.get('type')=='KSampler' and n['widgets_values'][2]==4 and float(n['widgets_values'][3])==1.0 for n in s['nodes'])
assert any(n.get('type')=='SaveImage' and n['widgets_values'][0]=='ez_still_app' for n in s['nodes'])
enh=next(n for n in s['nodes'] if n.get('type')=='EZKleinPromptEnhance')
assert enh['widgets_values'][1] is False
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
  run python3 -c "
import json
g=json.load(open('${dir}/wan-gif-loop-lab-example.json'))
assert g.get('id')=='wan-gif-loop-lab-example'
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
assert enh['widgets_values'][1] is False
assert enh['widgets_values'][2]=='i2v'
motion=enh['widgets_values'][0].lower()
assert 'locked' in motion or 'lock' in motion
assert 'dolly' not in motion and 'walk' not in motion
assert 'breeze' in motion or 'curtain' in motion or 'leaves' in motion
"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${dir}/klein-dream-house-lab-example.json'))
assert d.get('id')=='klein-dream-house-lab-example'
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
assert enh[0]['widgets_values'][1] is False
assert enh[0]['widgets_values'][2]=='t2i'
assert enh[0]['widgets_values'][3]=='Instagram 4:5 still'
ident=enh[0]['widgets_values'][0]
ident_l=ident.lower()
assert 'cedar' in ident_l and 'lake' in ident_l
assert 'single-story' in ident_l and 'hip' in ident_l
assert 'no logos, no text' not in ident
assert sum(1 for n in d['nodes'] if n.get('type')=='VAEEncode')==1
refs=[n for n in d['nodes'] if n.get('type')=='ReferenceLatent']
assert len(refs)==10
by_id={n['id']:n for n in d['nodes']}
incoming={}
for l in d['links']:
    incoming.setdefault((l[3], l[4]), []).append(l)
banned=('pier','courtyard','pavilion','two-story','a-frame','glass box','outdoor kitchen','outdoor tub')
for i, join in enumerate(sorted(joins, key=lambda n: n['id'])):
    shot=join['widgets_values'][0]
    full=f'{ident} {shot}'
    assert len(full.split())<=155, (join.get('title'), len(full.split()))
    sl=shot.lower()
    assert 'same' in sl and 'cabin' in sl
    if i>=2 and i<=6:
        assert shot.startswith('Photographed from inside')
    assert not any(b in sl for b in banned)
    ks_id=12+i*5
    pos_src=by_id[incoming[(ks_id,1)][0][1]]['type']
    lat_src=by_id[incoming[(ks_id,3)][0][1]]['type']
    assert lat_src=='EmptyFlux2LatentImage'
    if i==0:
        assert pos_src=='CLIPTextEncode'
    else:
        assert pos_src=='ReferenceLatent'
note=next(n for n in d['nodes'] if n.get('type') in ('Note','MarkdownNote'))
ntext=str(note['widgets_values'][0]).lower()
assert 'identity plate' in ntext
assert 'do not bypass 01' in ntext or 'do not bypass 01' in d['extra']['lab_note'].lower()
assert 'queue' in ntext and 'shot 01' in ntext
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
