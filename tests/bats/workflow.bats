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
  local dir="${REPO_ROOT}/workflows/shorts"
  local wf
  [[ -f ${dir}/go-see-90s-lab-example.json ]]
  [[ -f ${dir}/still-here-90s-lab-example.json ]]
  [[ -f ${dir}/switchyard-90s-lab-example.json ]]
  [[ -f ${dir}/bridge-wan-lab-example.json ]]
  [[ -f ${dir}/bridge-ltx-lab-example.json ]]
  run grep -R -E 'z_image_turbo|FLUX\.2-dev|klein-9b|flux-2-klein-9b|MiniMax|Seedance|Kling' "${dir}"
  [ "${status}" -ne 0 ]
  for wf in "${dir}"/*-lab-example.json; do
    run python3 -c "import json,os; p='${wf}'; d=json.load(open(p)); assert d.get('id')==os.path.splitext(os.path.basename(p))[0]"
    [ "${status}" -eq 0 ]
  done
  run python3 -c "
import json
w=json.load(open('${dir}/bridge-wan-lab-example.json'))
l=json.load(open('${dir}/bridge-ltx-lab-example.json'))
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
  [[ ${#files[@]} -le 16 ]]

  for gone in \
    ltx-i2v-30s-lab-example.json \
    ltx-t2v-60s-lab-example.json \
    flux-txt2img-lab-example.json \
    h3-go-see-90s-lab-example.json \
    flux-to-ltx-lab-example.json; do
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
  for wf in still-draft-lab-example.json still-hero-lab-example.json still-studio-lab-example.json; do
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
  run grep -F 'ez_still_draft' "${dir}/still-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '768' "${dir}/still-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '1280' "${dir}/still-hero-lab-example.json"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${dir}/still-draft-lab-example.json'))
h=json.load(open('${dir}/still-hero-lab-example.json'))
def pos(g):
    return next(n['widgets_values'][0] for n in g['nodes'] if n.get('type')=='CLIPTextEncode' and n.get('title')=='Positive')
assert pos(d)==pos(h)
assert any(n.get('type')=='KSampler' and n['widgets_values'][2]==4 for n in d['nodes'])
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][2]==2 for n in d['nodes'])
"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${dir}/still-studio-lab-example.json'))
assert any(n.get('title')=='HERO KSampler' and n.get('mode')==4 for n in d['nodes'])
assert any(n.get('title')=='KSampler' and n.get('mode')==0 for n in d['nodes'])
assert any(g.get('title','').startswith('DRAFT') for g in d.get('groups',[]))
"
  [ "${status}" -eq 0 ]
}

@test "wan lab graphs use 5B Apache weights, 121 frames, VHS" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in wan-i2v-draft-lab-example.json wan-t2v-draft-lab-example.json wan-shot-lab-example.json; do
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
  run grep -F 'ez_shot_01' "${dir}/wan-shot-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F 'Motion / prompt' "${dir}/wan-i2v-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  run python3 -c "
import json
d=json.load(open('${dir}/wan-i2v-draft-lab-example.json'))
loads=[n for n in d['nodes'] if n.get('type')=='LoadImage']
assert loads and loads[0]['widgets_values'][0]=='example.png'
assert loads[0].get('mode')==0
t=json.load(open('${dir}/wan-t2v-draft-lab-example.json'))
tl=[n for n in t['nodes'] if n.get('type')=='LoadImage']
assert tl and tl[0].get('mode')==4
"
  [ "${status}" -eq 0 ]
}

@test "ltx hero graphs use 2.5 distilled pack, 121 frames, VHS, CLIP ltxv" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in ltx-i2v-hero-lab-example.json ltx-t2v-hero-lab-example.json; do
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
"
    [ "${status}" -eq 0 ]
  done
  run python3 -c "
import json
d=json.load(open('${dir}/ltx-i2v-hero-lab-example.json'))
loads=[n for n in d['nodes'] if n.get('type')=='LoadImage']
assert loads and loads[0]['widgets_values'][0]=='example.png'
"
  [ "${status}" -eq 0 ]
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
