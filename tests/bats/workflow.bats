#!/usr/bin/env bats
#
# ## workflow.bats
#
# Purpose:
#   Guard lab ComfyUI workflows track stack model basenames, use correct
#   Flux.2 Klein node types, stay free of Z-Image templates, avoid
#   optional third-party nodes not installed by this stack, use the
#   *-lab-example name pattern, and keep non-overlapping node layouts.
#

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

@test "lab-example workflows parse, name pattern, no Z-Image, no overlaps" {
  local wf dir="${REPO_ROOT}/workflows"
  local n=0
  shopt -s nullglob
  local -a files=("${dir}"/*-lab-example.json)
  shopt -u nullglob
  [[ ${#files[@]} -ge 20 ]]

  # No legacy lab-*.json names
  shopt -s nullglob
  local -a legacy=("${dir}"/lab-*.json)
  shopt -u nullglob
  [[ ${#legacy[@]} -eq 0 ]]

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
    # No optional VHS (not installed by install-comfy.sh)
    run grep -F 'VHS_VideoCombine' "${wf}"
    [ "${status}" -ne 0 ]
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
  [[ ${n} -ge 20 ]]
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
    flux-to-ltx-short-lab-example.json; do
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
    flux-to-ltx-short-lab-example.json; do
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

@test "ltx lab graphs use DualCLIP Gemma+projection and balanced FP8 pack" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in \
    ltx-i2v-lab-example.json \
    ltx-i2v-short-lab-example.json \
    ltx-i2v-quick-lab-example.json \
    ltx-t2v-lab-example.json \
    ltx-t2v-short-lab-example.json \
    ltx-t2v-quick-lab-example.json \
    ltx-t2v-portrait-lab-example.json \
    ltx-t2v-landscape-lab-example.json; do
    [[ -f ${dir}/${wf} ]]
    run grep -F 'ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors' \
      "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTX23_video_vae_bf16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    # LTX-2.3 is joint AV — empty audio latents + concat are required for KSampler
    run grep -F 'LTX23_audio_vae_bf16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTXVEmptyLatentAudio' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTXVConcatAVLatent' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTXVSeparateAVLatent' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'ltx-2.3_text_projection_bf16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'gemma_3_12B_it_fp4_mixed.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'DualCLIPLoader' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    # DualCLIP type must be ltxv (not flux2 / SD)
    run grep -E '"ltxv"' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    # Projection-only CLIPLoader is the broken 768-vs-4096 config
    run python3 -c "import json; d=json.load(open('${dir}/${wf}'));
assert not any(n.get('type')=='CLIPLoader' for n in d['nodes']), 'CLIPLoader must not remain on LTX graphs'
assert any(n.get('type')=='DualCLIPLoader' and n.get('widgets_values',[''])[0]=='gemma_3_12B_it_fp4_mixed.safetensors' for n in d['nodes'])
assert any(n.get('type')=='VAELoader' and n.get('widgets_values',[''])[0]=='LTX23_audio_vae_bf16.safetensors' for n in d['nodes'])
# empty audio frames_number + fps must match video length / LTXVConditioning
vlen=None
for n in d['nodes']:
    if n.get('type') in ('EmptyLTXVLatentVideo','LTXVImgToVideo'):
        vlen=int(n['widgets_values'][2]); break
assert vlen is not None
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
    run grep -F 'KSampler' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'SaveImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
  done

  # Short demos use 33-frame length in LTX latent widgets
  run python3 -c "import json; d=json.load(open('${dir}/ltx-i2v-short-lab-example.json'));
assert any(n.get('type')=='LTXVImgToVideo' and n['widgets_values'][2]==33 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-short-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][2]==33 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  # Quick demos use 17 frames
  run python3 -c "import json; d=json.load(open('${dir}/ltx-i2v-quick-lab-example.json'));
assert any(n.get('type')=='LTXVImgToVideo' and n['widgets_values'][2]==17 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-quick-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][2]==17 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  # Portrait / landscape geometry
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-portrait-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][0]==512 and n['widgets_values'][1]==768 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/ltx-t2v-landscape-lab-example.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][0]==1024 and n['widgets_values'][1]==576 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_ltx_i2v_short' "${dir}/ltx-i2v-short-lab-example.json"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_ltx_t2v_short' "${dir}/ltx-t2v-short-lab-example.json"
  [ "${status}" -eq 0 ]
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
