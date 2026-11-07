---
title: Services pack (agency Apps)
description: Two hundred Klein, Wan, and LTX Apps for ecommerce, ads, local business, education, podcasts, real estate, fashion, B2B, events, and travel jobs.
tags: [comfyui, workflows, services, klein, wan, ltx, catalog]
---

# Services pack (agency Apps)

**What's on this page**

- **Two hundred job Apps** nested under `_lab/business/<vertical>/`
- **Agency SKUs** (product photography, paid-social, local business, courses, podcasts, listings, fashion, B2B, events, fitness/travel)
- **Silent Wan loops / I2V** and **LTX AV** plates mixed into each vertical
- **Lab sizes vs upload pixels** - Size column is the **default**. **Format / platform** retargets the same App. Match aspect; scale in an editor if a client wants more pixels
- **How to read these tables** - Size, Prefix, and the Format / platform retarget
- **Related** - what to load after the deliverable lands

**What this enables**

- **Queuing a job-named App** (PDP on-white, UGC kitchen AV, listing walkthrough) instead of restyling a generic still
- **Reading one table per vertical** so you can find the row in seconds
- **Keeping occupancy XOR** - Klein, Wan, and LTX still do not share a GB10 session

**Who this is for:** studio users after `photos/still-draft`. Index: [Workflow catalog](../studio-workflows.md). Occupancy and widgets: [ComfyUI Apps](../studio-apps.md).

**How to read these tables.** The **Workflow** column is the lab id under
`_lab/business/`, and it links to the generated node page for that graph. **Size**
is the widget default; **Format / platform** retargets the same App, so match the
client aspect and scale in an editor when the host wants more pixels. **Prefix** is
the filename stem the graph writes. Each vertical mixes three families - Klein
stills, silent ~5 s Wan clips, and LTX AV takes - so park the previous family
between Queues. These Apps clone the printers the studio already ships, so they
add no models and the plates come out empty of lettering - composite titles later.
Seeds, occupancy, sizes, and Queue rules:
[Workflow catalog](../studio-workflows.md#shared-lab-graph-rules). Safety impact:
**none**.

## Ecommerce / product

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/ecommerce/pdp-on-white](../generated/workflows/business/ecommerce/pdp-on-white.md)** | 1024x1024 | `ez_svc_pdp_white` | PDP on-white packshot 1:1 |
| **[business/ecommerce/pdp-in-use](../generated/workflows/business/ecommerce/pdp-in-use.md)** | 832x480 | `ez_svc_pdp_use` | Silent in-use product motion ~5 s |
| **[business/ecommerce/pdp-hand-scale](../generated/workflows/business/ecommerce/pdp-hand-scale.md)** | 832x480 | `ez_svc_pdp_hand` | Silent hand-scale product motion ~5 s |
| **[business/ecommerce/pdp-texture-macro](../generated/workflows/business/ecommerce/pdp-texture-macro.md)** | 1024x1024 | `ez_svc_pdp_macro` | PDP texture macro 1:1 |
| **[business/ecommerce/pdp-pack-back](../generated/workflows/business/ecommerce/pdp-pack-back.md)** | 1024x1024 | `ez_svc_pdp_back` | PDP pack-back still 1:1 |
| **[business/ecommerce/collection-banner](../generated/workflows/business/ecommerce/collection-banner.md)** | 1536x864 | `ez_svc_coll_ban` | Collection banner 16:9 |
| **[business/ecommerce/marketplace-square](../generated/workflows/business/ecommerce/marketplace-square.md)** | 1024x1024 | `ez_svc_mkt_sq` | Marketplace square packshot 1:1 |
| **[business/ecommerce/marketplace-lifestyle](../generated/workflows/business/ecommerce/marketplace-lifestyle.md)** | 832x480 | `ez_svc_mkt_life` | Silent marketplace lifestyle ~5 s |
| **[business/ecommerce/bundle-flatlay](../generated/workflows/business/ecommerce/bundle-flatlay.md)** | 1024x1024 | `ez_svc_bundle` | Bundle flatlay 1:1 |
| **[business/ecommerce/gift-set-still](../generated/workflows/business/ecommerce/gift-set-still.md)** | 1024x1280 | `ez_svc_gift` | Gift-set still 4:5 |
| **[business/ecommerce/restock-story](../generated/workflows/business/ecommerce/restock-story.md)** | 480x832 | `ez_svc_restock` | Silent restock story 9:16 |
| **[business/ecommerce/drop-tease](../generated/workflows/business/ecommerce/drop-tease.md)** | 832x480 | `ez_svc_drop` | Silent drop-tease ~5 s |
| **[business/ecommerce/cart-upsell-bg](../generated/workflows/business/ecommerce/cart-upsell-bg.md)** | 576x1024 | `ez_svc_cart` | Cart upsell background 9:16 |
| **[business/ecommerce/turntable-loop](../generated/workflows/business/ecommerce/turntable-loop.md)** | 768x768 | `ez_svc_turn` | Silent product turntable loop |
| **[business/ecommerce/drape-loop](../generated/workflows/business/ecommerce/drape-loop.md)** | 768x768 | `ez_svc_drape` | Silent fabric drape loop |
| **[business/ecommerce/pour-fill-loop](../generated/workflows/business/ecommerce/pour-fill-loop.md)** | 768x768 | `ez_svc_pour` | Silent pour-fill loop |
| **[business/ecommerce/table-unbox-av](../generated/workflows/business/ecommerce/table-unbox-av.md)** | 1280x704 | `ez_svc_unbox` | Table unbox AV ~5 s |
| **[business/ecommerce/wear-test-av](../generated/workflows/business/ecommerce/wear-test-av.md)** | 768x1280 | `ez_svc_wear` | Wear-test AV 9:16 |
| **[business/ecommerce/assemble-av](../generated/workflows/business/ecommerce/assemble-av.md)** | 1280x704 | `ez_svc_asm` | Assemble AV ~5 s |
| **[business/ecommerce/shelf-scan-av](../generated/workflows/business/ecommerce/shelf-scan-av.md)** | 1280x704 | `ez_svc_shelf` | Shelf-scan AV ~5 s |

## Performance ads

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/performance-ads/hook-face](../generated/workflows/business/performance-ads/hook-face.md)** | 480x832 | `ez_svc_hk_face` | Silent hook-face punch 9:16 |
| **[business/performance-ads/hook-problem](../generated/workflows/business/performance-ads/hook-problem.md)** | 1024x1280 | `ez_svc_hk_prob` | Problem-hook still 4:5 |
| **[business/performance-ads/hook-result](../generated/workflows/business/performance-ads/hook-result.md)** | 832x480 | `ez_svc_hk_res` | Silent result-hook ~5 s |
| **[business/performance-ads/ugc-selfie](../generated/workflows/business/performance-ads/ugc-selfie.md)** | 480x832 | `ez_svc_ugc_self` | Silent UGC selfie 9:16 |
| **[business/performance-ads/testimonial-still](../generated/workflows/business/performance-ads/testimonial-still.md)** | 1024x1280 | `ez_svc_testi` | Testimonial still 4:5 |
| **[business/performance-ads/offer-bed](../generated/workflows/business/performance-ads/offer-bed.md)** | 1280x704 | `ez_svc_offer` | Offer-bed still 16:9 |
| **[business/performance-ads/split-board](../generated/workflows/business/performance-ads/split-board.md)** | 1216x640 | `ez_svc_split` | Split-board still ~1.91:1 |
| **[business/performance-ads/talent-plain-wall](../generated/workflows/business/performance-ads/talent-plain-wall.md)** | 1024x1280 | `ez_svc_talent` | Talent on a plain wall 4:5 |
| **[business/performance-ads/reaction-still](../generated/workflows/business/performance-ads/reaction-still.md)** | 1024x1024 | `ez_svc_react` | Reaction still 1:1 |
| **[business/performance-ads/stitch-setup](../generated/workflows/business/performance-ads/stitch-setup.md)** | 480x832 | `ez_svc_stitch` | Silent stitch-setup 9:16 |
| **[business/performance-ads/story-safe-ad](../generated/workflows/business/performance-ads/story-safe-ad.md)** | 576x1024 | `ez_svc_story` | Story-safe ad still 9:16 |
| **[business/performance-ads/square-ad](../generated/workflows/business/performance-ads/square-ad.md)** | 1024x1024 | `ez_svc_sq_ad` | Square ad still 1:1 |
| **[business/performance-ads/wide-ad](../generated/workflows/business/performance-ads/wide-ad.md)** | 1216x640 | `ez_svc_wide_ad` | Wide ad still ~1.91:1 |
| **[business/performance-ads/vertical-ad](../generated/workflows/business/performance-ads/vertical-ad.md)** | 576x1024 | `ez_svc_vert_ad` | Vertical ad still 9:16 |
| **[business/performance-ads/ugc-kitchen-av](../generated/workflows/business/performance-ads/ugc-kitchen-av.md)** | 768x1280 | `ez_svc_ugc_kit` | UGC kitchen AV 9:16 |
| **[business/performance-ads/ugc-car-av](../generated/workflows/business/performance-ads/ugc-car-av.md)** | 768x1280 | `ez_svc_ugc_car` | UGC car AV 9:16 |
| **[business/performance-ads/ugc-mirror-av](../generated/workflows/business/performance-ads/ugc-mirror-av.md)** | 768x1280 | `ez_svc_ugc_mir` | UGC mirror AV 9:16 |
| **[business/performance-ads/demo-hands-av](../generated/workflows/business/performance-ads/demo-hands-av.md)** | 768x1280 | `ez_svc_demo` | Demo-hands AV 9:16 |
| **[business/performance-ads/problem-spot-av](../generated/workflows/business/performance-ads/problem-spot-av.md)** | 768x1280 | `ez_svc_prob` | Problem-spot AV 9:16 |
| **[business/performance-ads/bumper-av](../generated/workflows/business/performance-ads/bumper-av.md)** | 768x1280 | `ez_svc_bumper` | Bumper AV 9:16 |

## Local business

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/local-business/storefront-day](../generated/workflows/business/local-business/storefront-day.md)** | 832x480 | `ez_svc_sf_day` | Silent storefront day ~5 s |
| **[business/local-business/storefront-night](../generated/workflows/business/local-business/storefront-night.md)** | 1280x704 | `ez_svc_sf_nite` | Storefront night still 16:9 |
| **[business/local-business/maps-cover](../generated/workflows/business/local-business/maps-cover.md)** | 1216x640 | `ez_svc_maps_cv` | Local maps cover ~1.91:1 |
| **[business/local-business/maps-post](../generated/workflows/business/local-business/maps-post.md)** | 1024x1024 | `ez_svc_maps_ps` | Local maps post 1:1 |
| **[business/local-business/menu-item](../generated/workflows/business/local-business/menu-item.md)** | 1024x1024 | `ez_svc_menu` | Menu-item still 1:1 |
| **[business/local-business/plated-special](../generated/workflows/business/local-business/plated-special.md)** | 480x832 | `ez_svc_plated` | Silent plated-special 9:16 |
| **[business/local-business/treatment-room](../generated/workflows/business/local-business/treatment-room.md)** | 1280x704 | `ez_svc_treat` | Treatment-room still 16:9 |
| **[business/local-business/gym-floor](../generated/workflows/business/local-business/gym-floor.md)** | 1280x704 | `ez_svc_gymfl` | Gym-floor still 16:9 |
| **[business/local-business/team-headshot](../generated/workflows/business/local-business/team-headshot.md)** | 1024x1024 | `ez_svc_team` | Team headshot 1:1 |
| **[business/local-business/owner-portrait](../generated/workflows/business/local-business/owner-portrait.md)** | 1024x1280 | `ez_svc_owner` | Owner portrait 4:5 |
| **[business/local-business/hours-bed](../generated/workflows/business/local-business/hours-bed.md)** | 832x480 | `ez_svc_hours` | Silent hours-bed ~5 s |
| **[business/local-business/interior-wide](../generated/workflows/business/local-business/interior-wide.md)** | 1280x704 | `ez_svc_int_w` | Interior wide still 16:9 |
| **[business/local-business/interior-detail](../generated/workflows/business/local-business/interior-detail.md)** | 1024x1024 | `ez_svc_int_d` | Interior detail still 1:1 |
| **[business/local-business/parking-approach](../generated/workflows/business/local-business/parking-approach.md)** | 832x480 | `ez_svc_park` | Silent parking approach ~5 s |
| **[business/local-business/walk-in-av](../generated/workflows/business/local-business/walk-in-av.md)** | 768x1280 | `ez_svc_walkin` | Walk-in AV 9:16 |
| **[business/local-business/service-broll-av](../generated/workflows/business/local-business/service-broll-av.md)** | 1280x704 | `ez_svc_svcbr` | Service B-roll AV ~5 s |
| **[business/local-business/staff-greet-av](../generated/workflows/business/local-business/staff-greet-av.md)** | 768x1280 | `ez_svc_greet` | Staff greet AV 9:16 |
| **[business/local-business/close-up-av](../generated/workflows/business/local-business/close-up-av.md)** | 768x1280 | `ez_svc_close` | Close-up service AV 9:16 |
| **[business/local-business/kitchen-pass-av](../generated/workflows/business/local-business/kitchen-pass-av.md)** | 1280x704 | `ez_svc_kpass` | Kitchen-pass AV ~5 s |
| **[business/local-business/class-in-session-av](../generated/workflows/business/local-business/class-in-session-av.md)** | 1280x704 | `ez_svc_class` | Class-in-session AV ~5 s |

## Education / courses

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/education/course-thumb](../generated/workflows/business/education/course-thumb.md)** | 1280x704 | `ez_svc_crs_th` | Course thumbnail 16:9 |
| **[business/education/module-card](../generated/workflows/business/education/module-card.md)** | 1024x1024 | `ez_svc_mod` | Module card 1:1 |
| **[business/education/lesson-title](../generated/workflows/business/education/lesson-title.md)** | 1280x704 | `ez_svc_lesson` | Lesson title plate 16:9 |
| **[business/education/instructor-still](../generated/workflows/business/education/instructor-still.md)** | 832x480 | `ez_svc_instr` | Silent instructor motion ~5 s |
| **[business/education/board-still](../generated/workflows/business/education/board-still.md)** | 1280x704 | `ez_svc_board` | Board still 16:9 |
| **[business/education/slide-break](../generated/workflows/business/education/slide-break.md)** | 832x480 | `ez_svc_slide` | Silent slide-break ~5 s |
| **[business/education/certificate-bed](../generated/workflows/business/education/certificate-bed.md)** | 1280x704 | `ez_svc_cert` | Certificate bed 16:9 |
| **[business/education/cohort-announce](../generated/workflows/business/education/cohort-announce.md)** | 1216x640 | `ez_svc_cohort` | Cohort announce still ~1.91:1 |
| **[business/education/waitlist-cover](../generated/workflows/business/education/waitlist-cover.md)** | 480x832 | `ez_svc_wait` | Silent waitlist cover 9:16 |
| **[business/education/syllabus-header](../generated/workflows/business/education/syllabus-header.md)** | 1536x864 | `ez_svc_syl` | Syllabus header 16:9 |
| **[business/education/campus-wide](../generated/workflows/business/education/campus-wide.md)** | 832x480 | `ez_svc_campus` | Silent campus-wide ~5 s |
| **[business/education/lab-bench](../generated/workflows/business/education/lab-bench.md)** | 1280x704 | `ez_svc_bench` | Lab-bench still 16:9 |
| **[business/education/student-desk](../generated/workflows/business/education/student-desk.md)** | 1280x704 | `ez_svc_desk_st` | Student-desk still 16:9 |
| **[business/education/screencast-loop](../generated/workflows/business/education/screencast-loop.md)** | 768x768 | `ez_svc_screen` | Silent screencast-bed loop |
| **[business/education/recap-sting](../generated/workflows/business/education/recap-sting.md)** | 832x480 | `ez_svc_recap` | Silent recap sting ~5 s |
| **[business/education/lecture-av](../generated/workflows/business/education/lecture-av.md)** | 1280x704 | `ez_svc_lect` | Lecture AV ~5 s |
| **[business/education/office-hours-av](../generated/workflows/business/education/office-hours-av.md)** | 1280x704 | `ez_svc_ohours` | Office-hours AV ~5 s |
| **[business/education/lab-demo-av](../generated/workflows/business/education/lab-demo-av.md)** | 1280x704 | `ez_svc_labdm` | Lab-demo AV ~5 s |
| **[business/education/course-trailer-av](../generated/workflows/business/education/course-trailer-av.md)** | 768x1280 | `ez_svc_ctrail` | Course-trailer AV 9:16 |
| **[business/education/graduation-av](../generated/workflows/business/education/graduation-av.md)** | 1280x704 | `ez_svc_grad` | Graduation AV ~5 s |

## Podcast clips

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/podcast-clips/clip-wide](../generated/workflows/business/podcast-clips/clip-wide.md)** | 1280x704 | `ez_svc_clip_w` | Podcast clip still 16:9 |
| **[business/podcast-clips/clip-vertical](../generated/workflows/business/podcast-clips/clip-vertical.md)** | 576x1024 | `ez_svc_clip_v` | Podcast clip still 9:16 |
| **[business/podcast-clips/quote-vert](../generated/workflows/business/podcast-clips/quote-vert.md)** | 576x1024 | `ez_svc_qte_v` | Quote-card background 9:16 |
| **[business/podcast-clips/quote-wide](../generated/workflows/business/podcast-clips/quote-wide.md)** | 1280x704 | `ez_svc_qte_w` | Quote-card background 16:9 |
| **[business/podcast-clips/guest-intro](../generated/workflows/business/podcast-clips/guest-intro.md)** | 480x832 | `ez_svc_guest` | Silent guest-intro 9:16 |
| **[business/podcast-clips/host-solo](../generated/workflows/business/podcast-clips/host-solo.md)** | 1024x1024 | `ez_svc_host` | Host-solo still 1:1 |
| **[business/podcast-clips/two-shot](../generated/workflows/business/podcast-clips/two-shot.md)** | 1280x704 | `ez_svc_twoshot` | Two-shot still 16:9 |
| **[business/podcast-clips/waveform-bed](../generated/workflows/business/podcast-clips/waveform-bed.md)** | 1280x704 | `ez_svc_wave` | Waveform bed 16:9 |
| **[business/podcast-clips/chapter-art](../generated/workflows/business/podcast-clips/chapter-art.md)** | 1024x1024 | `ez_svc_chapt` | Chapter art 1:1 |
| **[business/podcast-clips/live-badge-bed](../generated/workflows/business/podcast-clips/live-badge-bed.md)** | 480x832 | `ez_svc_live` | Silent live-badge bed 9:16 |
| **[business/podcast-clips/end-slate](../generated/workflows/business/podcast-clips/end-slate.md)** | 1280x704 | `ez_svc_endsl` | End slate 16:9 |
| **[business/podcast-clips/clip-push-loop](../generated/workflows/business/podcast-clips/clip-push-loop.md)** | 768x768 | `ez_svc_cpush` | Silent clip-push loop |
| **[business/podcast-clips/lower-third-loop](../generated/workflows/business/podcast-clips/lower-third-loop.md)** | 768x768 | `ez_svc_lthird` | Silent lower-third bed loop |
| **[business/podcast-clips/talk-clip-av](../generated/workflows/business/podcast-clips/talk-clip-av.md)** | 768x1280 | `ez_svc_talk` | Talk-clip AV 9:16 |
| **[business/podcast-clips/laugh-bed-av](../generated/workflows/business/podcast-clips/laugh-bed-av.md)** | 1280x704 | `ez_svc_laugh` | Laugh-bed AV ~5 s |
| **[business/podcast-clips/desk-mic-av](../generated/workflows/business/podcast-clips/desk-mic-av.md)** | 1280x704 | `ez_svc_dmic` | Desk-mic AV ~5 s |
| **[business/podcast-clips/remote-guest-av](../generated/workflows/business/podcast-clips/remote-guest-av.md)** | 1280x704 | `ez_svc_remote` | Remote-guest AV ~5 s |
| **[business/podcast-clips/studio-walk-av](../generated/workflows/business/podcast-clips/studio-walk-av.md)** | 1280x704 | `ez_svc_swalk` | Studio-walk AV ~5 s |
| **[business/podcast-clips/clip-montage-av](../generated/workflows/business/podcast-clips/clip-montage-av.md)** | 768x1280 | `ez_svc_mont` | Clip-montage AV 9:16 |
| **[business/podcast-clips/season-trailer-av](../generated/workflows/business/podcast-clips/season-trailer-av.md)** | 768x1280 | `ez_svc_strail` | Season-trailer AV 9:16 |

## Real estate

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/real-estate/listing-hero](../generated/workflows/business/real-estate/listing-hero.md)** | 832x480 | `ez_svc_list_h` | Silent listing-hero ~5 s |
| **[business/real-estate/listing-kitchen](../generated/workflows/business/real-estate/listing-kitchen.md)** | 1280x704 | `ez_svc_list_k` | Listing kitchen still 16:9 |
| **[business/real-estate/listing-bath](../generated/workflows/business/real-estate/listing-bath.md)** | 1280x704 | `ez_svc_list_b` | Listing bath still 16:9 |
| **[business/real-estate/listing-bedroom](../generated/workflows/business/real-estate/listing-bedroom.md)** | 1280x704 | `ez_svc_list_br` | Listing bedroom still 16:9 |
| **[business/real-estate/listing-yard](../generated/workflows/business/real-estate/listing-yard.md)** | 832x480 | `ez_svc_list_y` | Silent listing-yard ~5 s |
| **[business/real-estate/listing-twilight](../generated/workflows/business/real-estate/listing-twilight.md)** | 1280x704 | `ez_svc_list_tw` | Listing twilight still 16:9 |
| **[business/real-estate/aerial-still](../generated/workflows/business/real-estate/aerial-still.md)** | 1536x864 | `ez_svc_aerial` | Aerial listing still 16:9 |
| **[business/real-estate/agent-headshot](../generated/workflows/business/real-estate/agent-headshot.md)** | 1024x1024 | `ez_svc_agent` | Agent headshot 1:1 |
| **[business/real-estate/just-listed](../generated/workflows/business/real-estate/just-listed.md)** | 832x480 | `ez_svc_jlist` | Silent just-listed ~5 s |
| **[business/real-estate/open-house-bed](../generated/workflows/business/real-estate/open-house-bed.md)** | 1216x640 | `ez_svc_openh` | Open-house bed ~1.91:1 |
| **[business/real-estate/sold-slate](../generated/workflows/business/real-estate/sold-slate.md)** | 1024x1024 | `ez_svc_sold` | Sold slate 1:1 |
| **[business/real-estate/empty-room](../generated/workflows/business/real-estate/empty-room.md)** | 1280x704 | `ez_svc_empty` | Empty-room still 16:9 |
| **[business/real-estate/dressed-room](../generated/workflows/business/real-estate/dressed-room.md)** | 1280x704 | `ez_svc_dress` | Dressed-room still 16:9 |
| **[business/real-estate/amenity-loop](../generated/workflows/business/real-estate/amenity-loop.md)** | 768x768 | `ez_svc_amen` | Silent amenity loop |
| **[business/real-estate/key-turn-loop](../generated/workflows/business/real-estate/key-turn-loop.md)** | 768x768 | `ez_svc_key` | Silent key-turn loop |
| **[business/real-estate/walkthrough-av](../generated/workflows/business/real-estate/walkthrough-av.md)** | 1280x704 | `ez_svc_walkth` | Walkthrough AV ~5 s |
| **[business/real-estate/twilight-av](../generated/workflows/business/real-estate/twilight-av.md)** | 1280x704 | `ez_svc_twil` | Twilight AV ~5 s |
| **[business/real-estate/neighborhood-av](../generated/workflows/business/real-estate/neighborhood-av.md)** | 1280x704 | `ez_svc_nhood` | Neighborhood AV ~5 s |
| **[business/real-estate/aerial-push-av](../generated/workflows/business/real-estate/aerial-push-av.md)** | 1280x704 | `ez_svc_apush` | Aerial-push AV ~5 s |
| **[business/real-estate/handoff-av](../generated/workflows/business/real-estate/handoff-av.md)** | 1280x704 | `ez_svc_handof` | Handoff AV ~5 s |

## Fashion and beauty

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/fashion-beauty/lookbook-cover](../generated/workflows/business/fashion-beauty/lookbook-cover.md)** | 1024x1280 | `ez_svc_lookbk` | Lookbook cover 4:5 |
| **[business/fashion-beauty/look-full](../generated/workflows/business/fashion-beauty/look-full.md)** | 480x832 | `ez_svc_look_f` | Silent full-look 9:16 |
| **[business/fashion-beauty/look-detail](../generated/workflows/business/fashion-beauty/look-detail.md)** | 1024x1024 | `ez_svc_look_d` | Look detail 1:1 |
| **[business/fashion-beauty/look-back](../generated/workflows/business/fashion-beauty/look-back.md)** | 1024x1280 | `ez_svc_look_b` | Look back 4:5 |
| **[business/fashion-beauty/campaign-hero](../generated/workflows/business/fashion-beauty/campaign-hero.md)** | 1280x704 | `ez_svc_camp_h` | Campaign hero 16:9 |
| **[business/fashion-beauty/beauty-pack](../generated/workflows/business/fashion-beauty/beauty-pack.md)** | 1024x1024 | `ez_svc_bpack` | Beauty packshot 1:1 |
| **[business/fashion-beauty/swatch-macro](../generated/workflows/business/fashion-beauty/swatch-macro.md)** | 1024x1024 | `ez_svc_swatch` | Swatch macro 1:1 |
| **[business/fashion-beauty/texture-fill](../generated/workflows/business/fashion-beauty/texture-fill.md)** | 1024x1024 | `ez_svc_texfil` | Texture fill 1:1 |
| **[business/fashion-beauty/street-look](../generated/workflows/business/fashion-beauty/street-look.md)** | 480x832 | `ez_svc_street` | Silent street-look 9:16 |
| **[business/fashion-beauty/makeup-step](../generated/workflows/business/fashion-beauty/makeup-step.md)** | 480x832 | `ez_svc_makeup` | Silent makeup-step 9:16 |
| **[business/fashion-beauty/editorial-still](../generated/workflows/business/fashion-beauty/editorial-still.md)** | 1024x1280 | `ez_svc_edit` | Editorial still 4:5 |
| **[business/fashion-beauty/hair-loop](../generated/workflows/business/fashion-beauty/hair-loop.md)** | 480x832 | `ez_svc_hair` | Silent hair loop 9:16 |
| **[business/fashion-beauty/glow-loop](../generated/workflows/business/fashion-beauty/glow-loop.md)** | 768x768 | `ez_svc_glow` | Silent glow loop |
| **[business/fashion-beauty/nail-loop](../generated/workflows/business/fashion-beauty/nail-loop.md)** | 768x768 | `ez_svc_nail` | Silent nail loop |
| **[business/fashion-beauty/fabric-twirl-av](../generated/workflows/business/fashion-beauty/fabric-twirl-av.md)** | 768x1280 | `ez_svc_twirl` | Fabric-twirl AV 9:16 |
| **[business/fashion-beauty/walk-av](../generated/workflows/business/fashion-beauty/walk-av.md)** | 768x1280 | `ez_svc_fwalk` | Fashion walk AV 9:16 |
| **[business/fashion-beauty/get-ready-av](../generated/workflows/business/fashion-beauty/get-ready-av.md)** | 768x1280 | `ez_svc_ready` | Get-ready AV 9:16 |
| **[business/fashion-beauty/beauty-unbox-av](../generated/workflows/business/fashion-beauty/beauty-unbox-av.md)** | 768x1280 | `ez_svc_bunbox` | Beauty unbox AV 9:16 |
| **[business/fashion-beauty/campaign-av](../generated/workflows/business/fashion-beauty/campaign-av.md)** | 1280x704 | `ez_svc_camp_v` | Campaign AV ~5 s |
| **[business/fashion-beauty/fitting-av](../generated/workflows/business/fashion-beauty/fitting-av.md)** | 768x1280 | `ez_svc_fit` | Fitting AV 9:16 |

## B2B / SaaS

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/b2b-saas/ui-hero](../generated/workflows/business/b2b-saas/ui-hero.md)** | 1536x864 | `ez_svc_ui` | UI hero still 16:9 |
| **[business/b2b-saas/feature-card](../generated/workflows/business/b2b-saas/feature-card.md)** | 1024x1024 | `ez_svc_feat` | Feature card 1:1 |
| **[business/b2b-saas/case-cover](../generated/workflows/business/b2b-saas/case-cover.md)** | 1216x640 | `ez_svc_case` | Case-study cover ~1.91:1 |
| **[business/b2b-saas/webinar-thumb](../generated/workflows/business/b2b-saas/webinar-thumb.md)** | 1280x704 | `ez_svc_webth` | Webinar thumbnail 16:9 |
| **[business/b2b-saas/ebook-cover](../generated/workflows/business/b2b-saas/ebook-cover.md)** | 1024x1280 | `ez_svc_ebook` | Ebook cover 4:5 |
| **[business/b2b-saas/report-cover](../generated/workflows/business/b2b-saas/report-cover.md)** | 1216x640 | `ez_svc_report` | Report cover ~1.91:1 |
| **[business/b2b-saas/founder-still](../generated/workflows/business/b2b-saas/founder-still.md)** | 832x480 | `ez_svc_found` | Silent founder motion ~5 s |
| **[business/b2b-saas/office-wide](../generated/workflows/business/b2b-saas/office-wide.md)** | 832x480 | `ez_svc_off_w` | Silent office-wide ~5 s |
| **[business/b2b-saas/culture-still](../generated/workflows/business/b2b-saas/culture-still.md)** | 1280x704 | `ez_svc_cult` | Culture still 16:9 |
| **[business/b2b-saas/keynote-still](../generated/workflows/business/b2b-saas/keynote-still.md)** | 1280x704 | `ez_svc_keynt` | Keynote still 16:9 |
| **[business/b2b-saas/changelog-card](../generated/workflows/business/b2b-saas/changelog-card.md)** | 832x480 | `ez_svc_chglog` | Silent changelog card ~5 s |
| **[business/b2b-saas/pricing-bed](../generated/workflows/business/b2b-saas/pricing-bed.md)** | 1280x704 | `ez_svc_price` | Pricing bed 16:9 |
| **[business/b2b-saas/launch-still](../generated/workflows/business/b2b-saas/launch-still.md)** | 1280x704 | `ez_svc_launch` | Launch still 16:9 |
| **[business/b2b-saas/diagram-bed](../generated/workflows/business/b2b-saas/diagram-bed.md)** | 1280x704 | `ez_svc_diag` | Diagram bed 16:9 |
| **[business/b2b-saas/cursor-demo-av](../generated/workflows/business/b2b-saas/cursor-demo-av.md)** | 1280x704 | `ez_svc_cursor` | Cursor-demo AV ~5 s |
| **[business/b2b-saas/explainer-av](../generated/workflows/business/b2b-saas/explainer-av.md)** | 1280x704 | `ez_svc_expl` | Explainer AV ~5 s |
| **[business/b2b-saas/office-broll-av](../generated/workflows/business/b2b-saas/office-broll-av.md)** | 1280x704 | `ez_svc_offbr` | Office B-roll AV ~5 s |
| **[business/b2b-saas/webinar-open-av](../generated/workflows/business/b2b-saas/webinar-open-av.md)** | 1280x704 | `ez_svc_webop` | Webinar-open AV ~5 s |
| **[business/b2b-saas/customer-story-av](../generated/workflows/business/b2b-saas/customer-story-av.md)** | 768x1280 | `ez_svc_cust` | Customer-story AV 9:16 |
| **[business/b2b-saas/ship-day-av](../generated/workflows/business/b2b-saas/ship-day-av.md)** | 1280x704 | `ez_svc_ship` | Ship-day AV ~5 s |

## Events and wedding

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/events-wedding/save-the-date](../generated/workflows/business/events-wedding/save-the-date.md)** | 1024x1280 | `ez_svc_std` | Save-the-date still 4:5 |
| **[business/events-wedding/invite-bed](../generated/workflows/business/events-wedding/invite-bed.md)** | 1024x1280 | `ez_svc_invite` | Invite bed 4:5 |
| **[business/events-wedding/program-cover](../generated/workflows/business/events-wedding/program-cover.md)** | 1024x1280 | `ez_svc_prog` | Program cover 4:5 |
| **[business/events-wedding/welcome-sign](../generated/workflows/business/events-wedding/welcome-sign.md)** | 832x480 | `ez_svc_welc` | Silent welcome-sign ~5 s |
| **[business/events-wedding/table-bed](../generated/workflows/business/events-wedding/table-bed.md)** | 1280x704 | `ez_svc_table` | Table bed 16:9 |
| **[business/events-wedding/highlight-still](../generated/workflows/business/events-wedding/highlight-still.md)** | 1024x1280 | `ez_svc_hlite` | Highlight still 4:5 |
| **[business/events-wedding/first-look](../generated/workflows/business/events-wedding/first-look.md)** | 480x832 | `ez_svc_first` | Silent first-look 9:16 |
| **[business/events-wedding/venue-wide](../generated/workflows/business/events-wedding/venue-wide.md)** | 832x480 | `ez_svc_venue` | Silent venue-wide ~5 s |
| **[business/events-wedding/details-flatlay](../generated/workflows/business/events-wedding/details-flatlay.md)** | 1024x1024 | `ez_svc_detfl` | Details flatlay 1:1 |
| **[business/events-wedding/speaker-still](../generated/workflows/business/events-wedding/speaker-still.md)** | 1024x1280 | `ez_svc_speak` | Speaker still 4:5 |
| **[business/events-wedding/badge-bed](../generated/workflows/business/events-wedding/badge-bed.md)** | 1024x1024 | `ez_svc_badge` | Badge bed 1:1 |
| **[business/events-wedding/sponsor-slate](../generated/workflows/business/events-wedding/sponsor-slate.md)** | 1280x704 | `ez_svc_spon` | Sponsor slate 16:9 |
| **[business/events-wedding/processional-av](../generated/workflows/business/events-wedding/processional-av.md)** | 1280x704 | `ez_svc_proc` | Processional AV ~5 s |
| **[business/events-wedding/dance-floor-av](../generated/workflows/business/events-wedding/dance-floor-av.md)** | 1280x704 | `ez_svc_dance` | Dance-floor AV ~5 s |
| **[business/events-wedding/sparkler-exit-av](../generated/workflows/business/events-wedding/sparkler-exit-av.md)** | 1280x704 | `ez_svc_spark` | Sparkler-exit AV ~5 s |
| **[business/events-wedding/conference-av](../generated/workflows/business/events-wedding/conference-av.md)** | 1280x704 | `ez_svc_conf` | Conference AV ~5 s |
| **[business/events-wedding/recap-av](../generated/workflows/business/events-wedding/recap-av.md)** | 1280x704 | `ez_svc_erecap` | Recap AV ~5 s |
| **[business/events-wedding/aftermovie-hook-av](../generated/workflows/business/events-wedding/aftermovie-hook-av.md)** | 768x1280 | `ez_svc_after` | Aftermovie hook AV 9:16 |
| **[business/events-wedding/rehearsal-av](../generated/workflows/business/events-wedding/rehearsal-av.md)** | 1280x704 | `ez_svc_rehr` | Rehearsal AV ~5 s |
| **[business/events-wedding/trailer-av](../generated/workflows/business/events-wedding/trailer-av.md)** | 768x1280 | `ez_svc_trail` | Event trailer AV 9:16 |

## Fitness and travel

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[business/fitness-travel/coach-still](../generated/workflows/business/fitness-travel/coach-still.md)** | 480x832 | `ez_svc_coach` | Silent coach motion 9:16 |
| **[business/fitness-travel/move-still](../generated/workflows/business/fitness-travel/move-still.md)** | 1024x1280 | `ez_svc_move` | Move still 4:5 |
| **[business/fitness-travel/gym-wide](../generated/workflows/business/fitness-travel/gym-wide.md)** | 1280x704 | `ez_svc_gymw` | Gym wide still 16:9 |
| **[business/fitness-travel/home-gym](../generated/workflows/business/fitness-travel/home-gym.md)** | 1280x704 | `ez_svc_hgym` | Home-gym still 16:9 |
| **[business/fitness-travel/recovery-still](../generated/workflows/business/fitness-travel/recovery-still.md)** | 1024x1280 | `ez_svc_recov` | Recovery still 4:5 |
| **[business/fitness-travel/meal-prep](../generated/workflows/business/fitness-travel/meal-prep.md)** | 1024x1280 | `ez_svc_meal` | Meal-prep still 4:5 |
| **[business/fitness-travel/resort-hero](../generated/workflows/business/fitness-travel/resort-hero.md)** | 832x480 | `ez_svc_resort` | Silent resort-hero ~5 s |
| **[business/fitness-travel/room-still](../generated/workflows/business/fitness-travel/room-still.md)** | 1280x704 | `ez_svc_room` | Resort room still 16:9 |
| **[business/fitness-travel/pool-still](../generated/workflows/business/fitness-travel/pool-still.md)** | 1280x704 | `ez_svc_pool` | Pool still 16:9 |
| **[business/fitness-travel/trail-still](../generated/workflows/business/fitness-travel/trail-still.md)** | 832x480 | `ez_svc_trailf` | Silent trail ~5 s |
| **[business/fitness-travel/city-arrive](../generated/workflows/business/fitness-travel/city-arrive.md)** | 832x480 | `ez_svc_arrive` | Silent city-arrive ~5 s |
| **[business/fitness-travel/rep-loop](../generated/workflows/business/fitness-travel/rep-loop.md)** | 480x832 | `ez_svc_rep` | Silent rep loop 9:16 |
| **[business/fitness-travel/stretch-loop](../generated/workflows/business/fitness-travel/stretch-loop.md)** | 480x832 | `ez_svc_strch` | Silent stretch loop 9:16 |
| **[business/fitness-travel/waves-loop](../generated/workflows/business/fitness-travel/waves-loop.md)** | 768x768 | `ez_svc_waves` | Silent waves loop |
| **[business/fitness-travel/workout-av](../generated/workflows/business/fitness-travel/workout-av.md)** | 768x1280 | `ez_svc_work` | Workout AV 9:16 |
| **[business/fitness-travel/class-av](../generated/workflows/business/fitness-travel/class-av.md)** | 768x1280 | `ez_svc_fclass` | Fitness class AV 9:16 |
| **[business/fitness-travel/check-in-av](../generated/workflows/business/fitness-travel/check-in-av.md)** | 1280x704 | `ez_svc_check` | Check-in AV ~5 s |
| **[business/fitness-travel/tour-av](../generated/workflows/business/fitness-travel/tour-av.md)** | 1280x704 | `ez_svc_tour` | Tour AV ~5 s |
| **[business/fitness-travel/sunset-av](../generated/workflows/business/fitness-travel/sunset-av.md)** | 1280x704 | `ez_svc_sun` | Sunset AV ~5 s |
| **[business/fitness-travel/packing-av](../generated/workflows/business/fitness-travel/packing-av.md)** | 768x1280 | `ez_svc_pack` | Packing AV 9:16 |

---

## Related

1. Creator platform jobs instead of client SKUs: [Creator pack](workflows-creator.md)
2. Start from a generic plate: [Stills graphs](workflows-stills.md)
3. Move a plate: [Motion graphs](workflows-motion.md)
4. Pick the graph for a different job: [Workflow catalog](../studio-workflows.md)
5. Write the prompt: [Prompting](../prompting.md)
