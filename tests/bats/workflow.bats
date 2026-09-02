#!/usr/bin/env bats
#
# ## workflow.bats
#
# Purpose:
#   Guard lab ComfyUI workflows track stack model basenames, use correct
#   Flux.2 Klein node types, stay free of Z-Image templates, avoid
#   optional third-party nodes not installed by this stack, use the
#   *-lab-example name pattern, and keep non-overlapping node layouts.
#   LTX lab video graphs are at least ~10 s (241 frames @ 24 fps) with
#   dedicated 30 s (721) and 60 s (1441) long-run examples.
#

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
  [[ ! -f ${REPO_ROOT}/scripts/utilities/queue-h3-film.sh ]]
  [[ ! -f ${REPO_ROOT}/docs/h3-films.md ]]
}

@test "lab-example workflows parse, name pattern, no Z-Image, no overlaps" {
  local wf dir="${REPO_ROOT}/workflows"
  local n=0
  shopt -s nullglob
  local -a files=("${dir}"/*-lab-example.json)
  shopt -u nullglob
  [[ ${#files[@]} -ge 25 ]]

  # No legacy lab-*.json names
  shopt -s nullglob
  local -a legacy=("${dir}"/lab-*.json)
  shopt -u nullglob
  [[ ${#legacy[@]} -eq 0 ]]

  # Retired sub-10 s LTX basenames must stay gone
  for gone in \
    ltx-i2v-short-lab-example.json \
    ltx-i2v-quick-lab-example.json \
    ltx-t2v-short-lab-example.json \
    ltx-t2v-quick-lab-example.json \
    flux-to-ltx-short-lab-example.json; do
    [[ ! -f ${dir}/${gone} ]]
  done

  for wf in "${files[@]}"; do
    n=$((n + 1))
    [[ -f ${wf} ]]
    run python3 -c "import json; json.load(open('${wf}'))"
    [ "${status}" -eq 0 ]
    # JSON id matches filename stem
    run python3 -c "import json,os; p='${wf}'; d=json.load(open(p)); assert d.get('id')==os.path.splitext(os.path.basename(p))[0]"
    [ "${status}" -eq 0 ]
    # No Z-Image pack basenames as model widgets
    run grep -E 'z_image_turbo|qwen_3_4b|"ae\.safetensors"' "${wf}"
    [ "${status}" -ne 0 ]
    # Flux graphs must not require VHS; LTX graphs must ship VHS_VideoCombine (MP4).
    if [[ $(basename "${wf}") == ltx-* ]]; then
      run grep -E '"type"[[:space:]]*:[[:space:]]*"VHS_VideoCombine"' "${wf}"
      [ "${status}" -eq 0 ]
    else
      run grep -E '"type"[[:space:]]*:[[:space:]]*"VHS_VideoCombine"' "${wf}"
      [ "${status}" -ne 0 ]
    fi
    # Node AABB must not overlap (20px pad) — UI layout guard
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
  [[ ${n} -ge 25 ]]
}

@test "flux lab graphs use flux2 CLIP EmptyFlux2Latent and stack weights" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in \
    flux-txt2img-lab-example.json \
    flux-txt2img-portrait-lab-example.json \
    flux-txt2img-landscape-lab-example.json \
    flux-txt2img-quick-lab-example.json \
    flux-txt2img-512-lab-example.json \
    flux-txt2img-ultrawide-lab-example.json \
    flux-txt2img-batch2-lab-example.json \
    flux-txt2img-high-steps-lab-example.json \
    flux-txt2img-product-lab-example.json \
    flux-img2img-lab-example.json \
    flux-img2img-subtle-lab-example.json \
    flux-img2img-strong-lab-example.json \
    flux-to-ltx-lab-example.json \
    flux-to-ltx-30s-lab-example.json; do
    [[ -f ${dir}/${wf} ]]
    run grep -F 'flux-2-klein-9b-nvfp4.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'qwen_3_8b_fp4mixed.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'flux2-vae.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    # CLIP type must be flux2 (not qwen_image)
    run grep -E '"flux2"' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'qwen_image' "${dir}/${wf}"
    [ "${status}" -ne 0 ]
    run grep -F 'KSampler' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'SaveImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
  done

  # Txt2img family uses EmptyFlux2LatentImage (not SD3)
  for wf in \
    flux-txt2img-lab-example.json \
    flux-txt2img-portrait-lab-example.json \
    flux-txt2img-landscape-lab-example.json \
    flux-txt2img-quick-lab-example.json \
    flux-txt2img-512-lab-example.json \
    flux-txt2img-ultrawide-lab-example.json \
    flux-txt2img-batch2-lab-example.json \
    flux-txt2img-high-steps-lab-example.json \
    flux-txt2img-product-lab-example.json \
    flux-to-ltx-lab-example.json \
    flux-to-ltx-30s-lab-example.json; do
    run grep -F 'EmptyFlux2LatentImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'EmptySD3LatentImage' "${dir}/${wf}"
    [ "${status}" -ne 0 ]
  done

  # Geometry / steps / denoise / batch variants
  run grep -F '768' "${dir}/flux-txt2img-portrait-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '1024' "${dir}/flux-txt2img-portrait-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '1280' "${dir}/flux-txt2img-landscape-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '720' "${dir}/flux-txt2img-landscape-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_flux_quick' "${dir}/flux-txt2img-quick-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_flux_to_ltx' "${dir}/flux-to-ltx-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F '1536' "${dir}/flux-txt2img-ultrawide-lab-example.json"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/flux-txt2img-batch2-lab-example.json'));
assert any(n.get('type')=='EmptyFlux2LatentImage' and n['widgets_values'][2]==2 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/flux-img2img-subtle-lab-example.json'));
assert any(n.get('type')=='KSampler' and n['widgets_values'][6]==0.35 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/flux-img2img-strong-lab-example.json'));
assert any(n.get('type')=='KSampler' and n['widgets_values'][6]==0.85 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/flux-txt2img-high-steps-lab-example.json'));
assert any(n.get('type')=='KSampler' and n['widgets_values'][2]==16 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
}

@test "flux img2img and ltx i2v keep example.png and sketch-aware prompts" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in \
    flux-img2img-lab-example.json \
    flux-img2img-subtle-lab-example.json \
    flux-img2img-strong-lab-example.json \
    ltx-i2v-lab-example.json \
    ltx-i2v-30s-lab-example.json \
    ltx-i2v-orbit-30s-lab-example.json \
    ltx-i2v-60s-lab-example.json; do
    run python3 -c "
import json,re
d=json.load(open('${dir}/${wf}'))
loads=[n for n in d['nodes'] if n.get('type')=='LoadImage']
assert loads, '${wf}: missing LoadImage'
assert loads[0]['widgets_values'][0]=='example.png', loads[0]['widgets_values']
pos=next(n for n in d['nodes'] if n.get('type')=='CLIPTextEncode' and n.get('title') in ('Positive','Motion / prompt'))
text=pos['widgets_values'][0].lower()
# Must anchor the crude doodle (dress / hair / hill / sky / sketch / doodle / example)
assert re.search(r'pink|dress|wing|hair|hill|sky|sketch|doodle|example\.png|example png', text), text[:200]
"
    [ "${status}" -eq 0 ]
  done
}

@test "ltx lab graphs use DualCLIP Gemma+projection, AV pack, and duration floors" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  shopt -s nullglob
  local -a ltx_files=("${dir}"/ltx-*-lab-example.json)
  shopt -u nullglob
  [[ ${#ltx_files[@]} -ge 14 ]]

  for wf in "${ltx_files[@]}"; do
    [[ -f ${wf} ]]
    run grep -F 'ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTX23_video_vae_bf16.safetensors' "${wf}"
    [ "${status}" -eq 0 ]
    # LTX-2.3 is joint AV — empty audio latents + concat are required for KSampler
    run grep -F 'LTX23_audio_vae_bf16.safetensors' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTXVEmptyLatentAudio' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTXVConcatAVLatent' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTXVSeparateAVLatent' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'ltx-2.3_text_projection_bf16.safetensors' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'gemma_3_12B_it_fp4_mixed.safetensors' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'DualCLIPLoader' "${wf}"
    [ "${status}" -eq 0 ]
    # DualCLIP type must be ltxv (not flux2 / SD)
    run grep -E '"ltxv"' "${wf}"
    [ "${status}" -eq 0 ]
    # Projection-only CLIPLoader is the broken 768-vs-4096 config
    run python3 -c "import json; d=json.load(open('${wf}'));
assert not any(n.get('type')=='CLIPLoader' for n in d['nodes']), 'CLIPLoader must not remain on LTX graphs'
assert any(n.get('type')=='DualCLIPLoader' and n.get('widgets_values',[''])[0]=='gemma_3_12B_it_fp4_mixed.safetensors' for n in d['nodes'])
assert any(n.get('type')=='VAELoader' and n.get('widgets_values',[''])[0]=='LTX23_audio_vae_bf16.safetensors' for n in d['nodes'])
# empty audio frames_number + fps must match video length / LTXVConditioning
vlen=None
for n in d['nodes']:
    if n.get('type') in ('EmptyLTXVLatentVideo','LTXVImgToVideo'):
        vlen=int(n['widgets_values'][2]); break
assert vlen is not None
assert vlen >= 241, (vlen, '${wf}')
fps=next(float(n['widgets_values'][0]) for n in d['nodes'] if n.get('type')=='LTXVConditioning')
ea=next(n for n in d['nodes'] if n.get('type')=='LTXVEmptyLatentAudio')
assert int(ea['widgets_values'][0])==vlen, (ea['widgets_values'], vlen)
assert float(ea['widgets_values'][1])==fps
# KSampler latent_image must come from ConcatAV; VAEDecode samples from SeparateAV
by={n['id']:n for n in d['nodes']}
ks=next(n for n in d['nodes'] if n.get('type')=='KSampler')
lat_link=next(i['link'] for i in ks['inputs'] if i.get('name')=='latent_image')
src=by[next(L[1] for L in d['links'] if L[0]==lat_link)]
assert src.get('type')=='LTXVConcatAVLatent'
vd=next(n for n in d['nodes'] if n.get('type')=='VAEDecode')
sl=next(i['link'] for i in vd['inputs'] if i.get('name')=='samples')
src=by[next(L[1] for L in d['links'] if L[0]==sl)]
assert src.get('type')=='LTXVSeparateAVLatent'"
    [ "${status}" -eq 0 ]
    run grep -F 'KSampler' "${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'SaveImage' "${wf}"
    [ "${status}" -eq 0 ]
  done

  # Duration buckets: base 241, *-30s-* 721, *-60s-* 1441; at least 5 of each long bucket
  run python3 -c "
import json,glob,os
dir='${dir}'
counts={241:0,721:0,1441:0}
for path in glob.glob(dir+'/ltx-*-lab-example.json'):
    d=json.load(open(path))
    vlen=None
    for n in d['nodes']:
        if n.get('type') in ('EmptyLTXVLatentVideo','LTXVImgToVideo'):
            vlen=int(n['widgets_values'][2]); break
    assert vlen is not None, path
    base=os.path.basename(path)
    if '-60s-' in base:
        assert vlen==1441, (base,vlen)
    elif '-30s-' in base:
        assert vlen==721, (base,vlen)
    else:
        assert vlen==241, (base,vlen)
    counts[vlen]=counts.get(vlen,0)+1
assert counts[241]>=4, counts
assert counts[721]>=5, counts
assert counts[1441]>=5, counts
print(counts)
"
  [ "${status}" -eq 0 ]

  # Portrait / landscape geometry on base + duration variants
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-portrait-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][0]==512 and n['widgets_values'][1]==768 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-landscape-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][0]==1024 and n['widgets_values'][1]==576 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-portrait-30s-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][0]==512 and n['widgets_values'][1]==768 and n['widgets_values'][2]==721 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-landscape-60s-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][0]==1024 and n['widgets_values'][1]==576 and n['widgets_values'][2]==1441 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
}

@test "lab examples have operator Notes, non-empty prompts, LTX VHS MP4 output" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  shopt -s nullglob
  local -a files=("${dir}"/*-lab-example.json)
  shopt -u nullglob
  [[ ${#files[@]} -ge 25 ]]

  for wf in "${files[@]}"; do
    run python3 -c "
import json, os
p = '${wf}'
base = os.path.basename(p)
d = json.load(open(p))
notes = [n for n in d['nodes'] if n.get('type') in ('Note', 'MarkdownNote')]
assert notes, f'{p}: missing Note/MarkdownNote node'
assert any(
    isinstance(n.get('widgets_values'), list)
    and n['widgets_values']
    and isinstance(n['widgets_values'][0], str)
    and len(n['widgets_values'][0].strip()) > 40
    for n in notes
), f'{p}: empty Note'
clips = [n for n in d['nodes'] if n.get('type') == 'CLIPTextEncode']
assert len(clips) >= 2, f'{p}: expected Positive+Negative CLIPTextEncode'
for n in clips:
    title = (n.get('title') or '').lower()
    text = (n.get('widgets_values') or [''])[0]
    assert isinstance(text, str) and text.strip(), f'{p}: empty prompt on {title!r}'
# Hidden parity with on-canvas note
assert isinstance(d.get('extra', {}).get('lab_note'), str) and d['extra']['lab_note'].strip()
"
    [ "${status}" -eq 0 ]
  done

  shopt -s nullglob
  local -a ltx_files=("${dir}"/ltx-*-lab-example.json)
  shopt -u nullglob
  for wf in "${ltx_files[@]}"; do
    run python3 -c "
import json,os
path='${wf}'
d = json.load(open(path))
base=os.path.basename(path)
vhs = [n for n in d['nodes'] if n.get('type') == 'VHS_VideoCombine']
assert len(vhs) == 1, f'{base}: expected exactly one VHS_VideoCombine'
wv = vhs[0].get('widgets_values') or {}
assert isinstance(wv, dict), f'{base}: VHS widgets_values must be a dict'
assert wv.get('format') == 'video/h264-mp4', f'{base}: expected video/h264-mp4'
assert float(wv.get('frame_rate', 0)) == 24, f'{base}: expected frame_rate 24'
assert wv.get('save_output') is True, f'{base}: save_output must be true'
assert wv.get('filename_prefix'), f'{base}: missing filename_prefix'
# IMAGE from VAEDecode must reach VHS
decode_ids = {n['id'] for n in d['nodes'] if n.get('type') == 'VAEDecode'}
vhs_id = vhs[0]['id']
assert any(
    isinstance(L, list) and len(L) >= 5 and L[1] in decode_ids and L[3] == vhs_id and L[5] == 'IMAGE'
    for L in d.get('links', [])
), f'{base}: VHS must be linked from VAEDecode IMAGE'
notes = [n for n in d['nodes'] if n.get('type') == 'Note']
body = '\n'.join((n.get('widgets_values') or [''])[0] for n in notes)
assert 'VHS' in body or 'VideoCombine' in body or 'Save video' in body, f'{base}: Note must mention VHS/video'
assert 'MP4' in body or 'mp4' in body, f'{base}: Note must mention MP4'
assert 'SaveImage' in body or 'frames' in body.lower(), f'{base}: Note should still mention frames'
"
    [ "${status}" -eq 0 ]
  done
}

@test "download-flux companions tier and includes" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/utilities/download-flux.sh"
  run tier_repo companions
  [[ "${output}" == *"Comfy-Org/flux2-klein-9B"* ]]
  run tier_include_patterns companions
  [[ "${output}" == *"qwen_3_8b_fp4mixed"* ]]
  [[ "${output}" == *"flux2-vae"* ]]
  TIER=fast
  INCLUDE_NUNCHAKU=0
  run tiers_to_process
  [[ "${output}" == *"companions"* ]]
  [[ "${output}" == *"fast"* ]]
  # TE-only dir is not ready (regression: size floor skipped VAE)
  local cdir
  cdir="$(tier_dir companions)"
  mkdir -p "${cdir}/split_files/text_encoders"
  echo te >"${cdir}/split_files/text_encoders/qwen_3_8b_fp4mixed.safetensors"
  run tier_files_ready companions
  [ "${status}" -ne 0 ]
}

@test "lab_expected_model_relpaths matches download-models pack" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib/common.sh"
  run lab_expected_model_relpaths
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux-2-klein-9b-nvfp4.safetensors"* ]]
  [[ "${output}" == *"qwen_3_8b_fp4mixed.safetensors"* ]]
  [[ "${output}" == *"flux2-vae.safetensors"* ]]
  [[ "${output}" == *"fp8_input_scaled_v3"* ]]
  [[ "${output}" == *"ltx-2.3_text_projection_bf16"* ]]
  [[ "${output}" == *"gemma_3_12B_it_fp4_mixed"* ]]
  [[ "${output}" == *"LTX23_video_vae_bf16"* ]]
  [[ "${output}" == *"LTX23_audio_vae_bf16"* ]]
}
