---
title: Services pack (agency Apps)
description: Two hundred Klein, Wan, and LTX Apps for ecommerce, ads, local business, education, podcasts, real estate, fashion, B2B, events, and travel jobs.
tags: [comfyui, workflows, services, klein, wan, ltx, catalog]
---

# Services pack (agency Apps)

**What's on this page**

- **Two hundred job Apps** nested under `_lab/services/<vertical>/`
- **Agency SKUs** (product photography, paid-social, local business, courses, podcasts, listings, fashion, B2B, events, fitness/travel)
- **Silent Wan loops / I2V** and **LTX AV** plates mixed into each vertical
- **Lab sizes vs upload pixels** — Size column is the **default**. **Format / platform** retargets the same App. Match aspect; scale in an editor if a client wants more pixels

**What this enables**

- **Queuing a job-named App** (PDP on-white, UGC kitchen AV, listing walkthrough) instead of restyling a generic still
- **Keeping occupancy XOR** — Klein, Wan, and LTX still do not share a GB10 session

**Who this is for:** studio users after `stills/still-draft`. Index: [Workflow catalog](../studio-workflows.md). Occupancy and widgets: [ComfyUI Apps](../studio-apps.md).

These graphs clone the shipped Klein 4B / Wan 2.2 / LTX-2.5 printers. They do **not** add models. Empty of lettering — composite titles later. LTX feeders stay **÷32**.

Safety impact: **none**. `restart: "no"`, headroom, and download-limit are unchanged.

## Ecommerce / product

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/ecommerce/pdp-on-white](../generated/workflows/services/ecommerce/pdp-on-white.md)** | 1024×1024 | `ez_svc_pdp_white` | PDP on-white packshot 1:1 |
| **[services/ecommerce/pdp-in-use](../generated/workflows/services/ecommerce/pdp-in-use.md)** | 832×480 | `ez_svc_pdp_use` | Silent in-use product motion ~5 s |
| **[services/ecommerce/pdp-hand-scale](../generated/workflows/services/ecommerce/pdp-hand-scale.md)** | 832×480 | `ez_svc_pdp_hand` | Silent hand-scale product motion ~5 s |
| **[services/ecommerce/pdp-texture-macro](../generated/workflows/services/ecommerce/pdp-texture-macro.md)** | 1024×1024 | `ez_svc_pdp_macro` | PDP texture macro 1:1 |
| **[services/ecommerce/pdp-pack-back](../generated/workflows/services/ecommerce/pdp-pack-back.md)** | 1024×1024 | `ez_svc_pdp_back` | PDP pack-back still 1:1 |
| **[services/ecommerce/collection-banner](../generated/workflows/services/ecommerce/collection-banner.md)** | 1536×864 | `ez_svc_coll_ban` | Collection banner 16:9 |
| **[services/ecommerce/marketplace-square](../generated/workflows/services/ecommerce/marketplace-square.md)** | 1024×1024 | `ez_svc_mkt_sq` | Marketplace square packshot 1:1 |
| **[services/ecommerce/marketplace-lifestyle](../generated/workflows/services/ecommerce/marketplace-lifestyle.md)** | 832×480 | `ez_svc_mkt_life` | Silent marketplace lifestyle ~5 s |
| **[services/ecommerce/bundle-flatlay](../generated/workflows/services/ecommerce/bundle-flatlay.md)** | 1024×1024 | `ez_svc_bundle` | Bundle flatlay 1:1 |
| **[services/ecommerce/gift-set-still](../generated/workflows/services/ecommerce/gift-set-still.md)** | 1024×1280 | `ez_svc_gift` | Gift-set still 4:5 |
| **[services/ecommerce/restock-story](../generated/workflows/services/ecommerce/restock-story.md)** | 480×832 | `ez_svc_restock` | Silent restock story 9:16 |
| **[services/ecommerce/drop-tease](../generated/workflows/services/ecommerce/drop-tease.md)** | 832×480 | `ez_svc_drop` | Silent drop-tease ~5 s |
| **[services/ecommerce/cart-upsell-bg](../generated/workflows/services/ecommerce/cart-upsell-bg.md)** | 576×1024 | `ez_svc_cart` | Cart upsell background 9:16 |
| **[services/ecommerce/turntable-loop](../generated/workflows/services/ecommerce/turntable-loop.md)** | 768×768 | `ez_svc_turn` | Silent product turntable loop |
| **[services/ecommerce/drape-loop](../generated/workflows/services/ecommerce/drape-loop.md)** | 768×768 | `ez_svc_drape` | Silent fabric drape loop |
| **[services/ecommerce/pour-fill-loop](../generated/workflows/services/ecommerce/pour-fill-loop.md)** | 768×768 | `ez_svc_pour` | Silent pour-fill loop |
| **[services/ecommerce/table-unbox-av](../generated/workflows/services/ecommerce/table-unbox-av.md)** | 1280×704 | `ez_svc_unbox` | Table unbox AV ~5 s |
| **[services/ecommerce/wear-test-av](../generated/workflows/services/ecommerce/wear-test-av.md)** | 768×1280 | `ez_svc_wear` | Wear-test AV 9:16 |
| **[services/ecommerce/assemble-av](../generated/workflows/services/ecommerce/assemble-av.md)** | 1280×704 | `ez_svc_asm` | Assemble AV ~5 s |
| **[services/ecommerce/shelf-scan-av](../generated/workflows/services/ecommerce/shelf-scan-av.md)** | 1280×704 | `ez_svc_shelf` | Shelf-scan AV ~5 s |

## Performance ads

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/performance-ads/hook-face](../generated/workflows/services/performance-ads/hook-face.md)** | 480×832 | `ez_svc_hk_face` | Silent hook-face punch 9:16 |
| **[services/performance-ads/hook-problem](../generated/workflows/services/performance-ads/hook-problem.md)** | 1024×1280 | `ez_svc_hk_prob` | Problem-hook still 4:5 |
| **[services/performance-ads/hook-result](../generated/workflows/services/performance-ads/hook-result.md)** | 832×480 | `ez_svc_hk_res` | Silent result-hook ~5 s |
| **[services/performance-ads/ugc-selfie](../generated/workflows/services/performance-ads/ugc-selfie.md)** | 480×832 | `ez_svc_ugc_self` | Silent UGC selfie 9:16 |
| **[services/performance-ads/testimonial-still](../generated/workflows/services/performance-ads/testimonial-still.md)** | 1024×1280 | `ez_svc_testi` | Testimonial still 4:5 |
| **[services/performance-ads/offer-bed](../generated/workflows/services/performance-ads/offer-bed.md)** | 1280×704 | `ez_svc_offer` | Offer-bed still 16:9 |
| **[services/performance-ads/split-board](../generated/workflows/services/performance-ads/split-board.md)** | 1216×640 | `ez_svc_split` | Split-board still ~1.91:1 |
| **[services/performance-ads/talent-plain-wall](../generated/workflows/services/performance-ads/talent-plain-wall.md)** | 1024×1280 | `ez_svc_talent` | Talent on a plain wall 4:5 |
| **[services/performance-ads/reaction-still](../generated/workflows/services/performance-ads/reaction-still.md)** | 1024×1024 | `ez_svc_react` | Reaction still 1:1 |
| **[services/performance-ads/stitch-setup](../generated/workflows/services/performance-ads/stitch-setup.md)** | 480×832 | `ez_svc_stitch` | Silent stitch-setup 9:16 |
| **[services/performance-ads/story-safe-ad](../generated/workflows/services/performance-ads/story-safe-ad.md)** | 576×1024 | `ez_svc_story` | Story-safe ad still 9:16 |
| **[services/performance-ads/square-ad](../generated/workflows/services/performance-ads/square-ad.md)** | 1024×1024 | `ez_svc_sq_ad` | Square ad still 1:1 |
| **[services/performance-ads/wide-ad](../generated/workflows/services/performance-ads/wide-ad.md)** | 1216×640 | `ez_svc_wide_ad` | Wide ad still ~1.91:1 |
| **[services/performance-ads/vertical-ad](../generated/workflows/services/performance-ads/vertical-ad.md)** | 576×1024 | `ez_svc_vert_ad` | Vertical ad still 9:16 |
| **[services/performance-ads/ugc-kitchen-av](../generated/workflows/services/performance-ads/ugc-kitchen-av.md)** | 768×1280 | `ez_svc_ugc_kit` | UGC kitchen AV 9:16 |
| **[services/performance-ads/ugc-car-av](../generated/workflows/services/performance-ads/ugc-car-av.md)** | 768×1280 | `ez_svc_ugc_car` | UGC car AV 9:16 |
| **[services/performance-ads/ugc-mirror-av](../generated/workflows/services/performance-ads/ugc-mirror-av.md)** | 768×1280 | `ez_svc_ugc_mir` | UGC mirror AV 9:16 |
| **[services/performance-ads/demo-hands-av](../generated/workflows/services/performance-ads/demo-hands-av.md)** | 768×1280 | `ez_svc_demo` | Demo-hands AV 9:16 |
| **[services/performance-ads/problem-spot-av](../generated/workflows/services/performance-ads/problem-spot-av.md)** | 768×1280 | `ez_svc_prob` | Problem-spot AV 9:16 |
| **[services/performance-ads/bumper-av](../generated/workflows/services/performance-ads/bumper-av.md)** | 768×1280 | `ez_svc_bumper` | Bumper AV 9:16 |

## Local business

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/local-business/storefront-day](../generated/workflows/services/local-business/storefront-day.md)** | 832×480 | `ez_svc_sf_day` | Silent storefront day ~5 s |
| **[services/local-business/storefront-night](../generated/workflows/services/local-business/storefront-night.md)** | 1280×704 | `ez_svc_sf_nite` | Storefront night still 16:9 |
| **[services/local-business/maps-cover](../generated/workflows/services/local-business/maps-cover.md)** | 1216×640 | `ez_svc_maps_cv` | Local maps cover ~1.91:1 |
| **[services/local-business/maps-post](../generated/workflows/services/local-business/maps-post.md)** | 1024×1024 | `ez_svc_maps_ps` | Local maps post 1:1 |
| **[services/local-business/menu-item](../generated/workflows/services/local-business/menu-item.md)** | 1024×1024 | `ez_svc_menu` | Menu-item still 1:1 |
| **[services/local-business/plated-special](../generated/workflows/services/local-business/plated-special.md)** | 480×832 | `ez_svc_plated` | Silent plated-special 9:16 |
| **[services/local-business/treatment-room](../generated/workflows/services/local-business/treatment-room.md)** | 1280×704 | `ez_svc_treat` | Treatment-room still 16:9 |
| **[services/local-business/gym-floor](../generated/workflows/services/local-business/gym-floor.md)** | 1280×704 | `ez_svc_gymfl` | Gym-floor still 16:9 |
| **[services/local-business/team-headshot](../generated/workflows/services/local-business/team-headshot.md)** | 1024×1024 | `ez_svc_team` | Team headshot 1:1 |
| **[services/local-business/owner-portrait](../generated/workflows/services/local-business/owner-portrait.md)** | 1024×1280 | `ez_svc_owner` | Owner portrait 4:5 |
| **[services/local-business/hours-bed](../generated/workflows/services/local-business/hours-bed.md)** | 832×480 | `ez_svc_hours` | Silent hours-bed ~5 s |
| **[services/local-business/interior-wide](../generated/workflows/services/local-business/interior-wide.md)** | 1280×704 | `ez_svc_int_w` | Interior wide still 16:9 |
| **[services/local-business/interior-detail](../generated/workflows/services/local-business/interior-detail.md)** | 1024×1024 | `ez_svc_int_d` | Interior detail still 1:1 |
| **[services/local-business/parking-approach](../generated/workflows/services/local-business/parking-approach.md)** | 832×480 | `ez_svc_park` | Silent parking approach ~5 s |
| **[services/local-business/walk-in-av](../generated/workflows/services/local-business/walk-in-av.md)** | 768×1280 | `ez_svc_walkin` | Walk-in AV 9:16 |
| **[services/local-business/service-broll-av](../generated/workflows/services/local-business/service-broll-av.md)** | 1280×704 | `ez_svc_svcbr` | Service B-roll AV ~5 s |
| **[services/local-business/staff-greet-av](../generated/workflows/services/local-business/staff-greet-av.md)** | 768×1280 | `ez_svc_greet` | Staff greet AV 9:16 |
| **[services/local-business/close-up-av](../generated/workflows/services/local-business/close-up-av.md)** | 768×1280 | `ez_svc_close` | Close-up service AV 9:16 |
| **[services/local-business/kitchen-pass-av](../generated/workflows/services/local-business/kitchen-pass-av.md)** | 1280×704 | `ez_svc_kpass` | Kitchen-pass AV ~5 s |
| **[services/local-business/class-in-session-av](../generated/workflows/services/local-business/class-in-session-av.md)** | 1280×704 | `ez_svc_class` | Class-in-session AV ~5 s |

## Education / courses

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/education/course-thumb](../generated/workflows/services/education/course-thumb.md)** | 1280×704 | `ez_svc_crs_th` | Course thumbnail 16:9 |
| **[services/education/module-card](../generated/workflows/services/education/module-card.md)** | 1024×1024 | `ez_svc_mod` | Module card 1:1 |
| **[services/education/lesson-title](../generated/workflows/services/education/lesson-title.md)** | 1280×704 | `ez_svc_lesson` | Lesson title plate 16:9 |
| **[services/education/instructor-still](../generated/workflows/services/education/instructor-still.md)** | 832×480 | `ez_svc_instr` | Silent instructor motion ~5 s |
| **[services/education/board-still](../generated/workflows/services/education/board-still.md)** | 1280×704 | `ez_svc_board` | Board still 16:9 |
| **[services/education/slide-break](../generated/workflows/services/education/slide-break.md)** | 832×480 | `ez_svc_slide` | Silent slide-break ~5 s |
| **[services/education/certificate-bed](../generated/workflows/services/education/certificate-bed.md)** | 1280×704 | `ez_svc_cert` | Certificate bed 16:9 |
| **[services/education/cohort-announce](../generated/workflows/services/education/cohort-announce.md)** | 1216×640 | `ez_svc_cohort` | Cohort announce still ~1.91:1 |
| **[services/education/waitlist-cover](../generated/workflows/services/education/waitlist-cover.md)** | 480×832 | `ez_svc_wait` | Silent waitlist cover 9:16 |
| **[services/education/syllabus-header](../generated/workflows/services/education/syllabus-header.md)** | 1536×864 | `ez_svc_syl` | Syllabus header 16:9 |
| **[services/education/campus-wide](../generated/workflows/services/education/campus-wide.md)** | 832×480 | `ez_svc_campus` | Silent campus-wide ~5 s |
| **[services/education/lab-bench](../generated/workflows/services/education/lab-bench.md)** | 1280×704 | `ez_svc_bench` | Lab-bench still 16:9 |
| **[services/education/student-desk](../generated/workflows/services/education/student-desk.md)** | 1280×704 | `ez_svc_desk_st` | Student-desk still 16:9 |
| **[services/education/screencast-loop](../generated/workflows/services/education/screencast-loop.md)** | 768×768 | `ez_svc_screen` | Silent screencast-bed loop |
| **[services/education/recap-sting](../generated/workflows/services/education/recap-sting.md)** | 832×480 | `ez_svc_recap` | Silent recap sting ~5 s |
| **[services/education/lecture-av](../generated/workflows/services/education/lecture-av.md)** | 1280×704 | `ez_svc_lect` | Lecture AV ~5 s |
| **[services/education/office-hours-av](../generated/workflows/services/education/office-hours-av.md)** | 1280×704 | `ez_svc_ohours` | Office-hours AV ~5 s |
| **[services/education/lab-demo-av](../generated/workflows/services/education/lab-demo-av.md)** | 1280×704 | `ez_svc_labdm` | Lab-demo AV ~5 s |
| **[services/education/course-trailer-av](../generated/workflows/services/education/course-trailer-av.md)** | 768×1280 | `ez_svc_ctrail` | Course-trailer AV 9:16 |
| **[services/education/graduation-av](../generated/workflows/services/education/graduation-av.md)** | 1280×704 | `ez_svc_grad` | Graduation AV ~5 s |

## Podcast clips

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/podcast-clips/clip-wide](../generated/workflows/services/podcast-clips/clip-wide.md)** | 1280×704 | `ez_svc_clip_w` | Podcast clip still 16:9 |
| **[services/podcast-clips/clip-vertical](../generated/workflows/services/podcast-clips/clip-vertical.md)** | 576×1024 | `ez_svc_clip_v` | Podcast clip still 9:16 |
| **[services/podcast-clips/quote-vert](../generated/workflows/services/podcast-clips/quote-vert.md)** | 576×1024 | `ez_svc_qte_v` | Quote-card background 9:16 |
| **[services/podcast-clips/quote-wide](../generated/workflows/services/podcast-clips/quote-wide.md)** | 1280×704 | `ez_svc_qte_w` | Quote-card background 16:9 |
| **[services/podcast-clips/guest-intro](../generated/workflows/services/podcast-clips/guest-intro.md)** | 480×832 | `ez_svc_guest` | Silent guest-intro 9:16 |
| **[services/podcast-clips/host-solo](../generated/workflows/services/podcast-clips/host-solo.md)** | 1024×1024 | `ez_svc_host` | Host-solo still 1:1 |
| **[services/podcast-clips/two-shot](../generated/workflows/services/podcast-clips/two-shot.md)** | 1280×704 | `ez_svc_twoshot` | Two-shot still 16:9 |
| **[services/podcast-clips/waveform-bed](../generated/workflows/services/podcast-clips/waveform-bed.md)** | 1280×704 | `ez_svc_wave` | Waveform bed 16:9 |
| **[services/podcast-clips/chapter-art](../generated/workflows/services/podcast-clips/chapter-art.md)** | 1024×1024 | `ez_svc_chapt` | Chapter art 1:1 |
| **[services/podcast-clips/live-badge-bed](../generated/workflows/services/podcast-clips/live-badge-bed.md)** | 480×832 | `ez_svc_live` | Silent live-badge bed 9:16 |
| **[services/podcast-clips/end-slate](../generated/workflows/services/podcast-clips/end-slate.md)** | 1280×704 | `ez_svc_endsl` | End slate 16:9 |
| **[services/podcast-clips/clip-push-loop](../generated/workflows/services/podcast-clips/clip-push-loop.md)** | 768×768 | `ez_svc_cpush` | Silent clip-push loop |
| **[services/podcast-clips/lower-third-loop](../generated/workflows/services/podcast-clips/lower-third-loop.md)** | 768×768 | `ez_svc_lthird` | Silent lower-third bed loop |
| **[services/podcast-clips/talk-clip-av](../generated/workflows/services/podcast-clips/talk-clip-av.md)** | 768×1280 | `ez_svc_talk` | Talk-clip AV 9:16 |
| **[services/podcast-clips/laugh-bed-av](../generated/workflows/services/podcast-clips/laugh-bed-av.md)** | 1280×704 | `ez_svc_laugh` | Laugh-bed AV ~5 s |
| **[services/podcast-clips/desk-mic-av](../generated/workflows/services/podcast-clips/desk-mic-av.md)** | 1280×704 | `ez_svc_dmic` | Desk-mic AV ~5 s |
| **[services/podcast-clips/remote-guest-av](../generated/workflows/services/podcast-clips/remote-guest-av.md)** | 1280×704 | `ez_svc_remote` | Remote-guest AV ~5 s |
| **[services/podcast-clips/studio-walk-av](../generated/workflows/services/podcast-clips/studio-walk-av.md)** | 1280×704 | `ez_svc_swalk` | Studio-walk AV ~5 s |
| **[services/podcast-clips/clip-montage-av](../generated/workflows/services/podcast-clips/clip-montage-av.md)** | 768×1280 | `ez_svc_mont` | Clip-montage AV 9:16 |
| **[services/podcast-clips/season-trailer-av](../generated/workflows/services/podcast-clips/season-trailer-av.md)** | 768×1280 | `ez_svc_strail` | Season-trailer AV 9:16 |

## Real estate

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/real-estate/listing-hero](../generated/workflows/services/real-estate/listing-hero.md)** | 832×480 | `ez_svc_list_h` | Silent listing-hero ~5 s |
| **[services/real-estate/listing-kitchen](../generated/workflows/services/real-estate/listing-kitchen.md)** | 1280×704 | `ez_svc_list_k` | Listing kitchen still 16:9 |
| **[services/real-estate/listing-bath](../generated/workflows/services/real-estate/listing-bath.md)** | 1280×704 | `ez_svc_list_b` | Listing bath still 16:9 |
| **[services/real-estate/listing-bedroom](../generated/workflows/services/real-estate/listing-bedroom.md)** | 1280×704 | `ez_svc_list_br` | Listing bedroom still 16:9 |
| **[services/real-estate/listing-yard](../generated/workflows/services/real-estate/listing-yard.md)** | 832×480 | `ez_svc_list_y` | Silent listing-yard ~5 s |
| **[services/real-estate/listing-twilight](../generated/workflows/services/real-estate/listing-twilight.md)** | 1280×704 | `ez_svc_list_tw` | Listing twilight still 16:9 |
| **[services/real-estate/aerial-still](../generated/workflows/services/real-estate/aerial-still.md)** | 1536×864 | `ez_svc_aerial` | Aerial listing still 16:9 |
| **[services/real-estate/agent-headshot](../generated/workflows/services/real-estate/agent-headshot.md)** | 1024×1024 | `ez_svc_agent` | Agent headshot 1:1 |
| **[services/real-estate/just-listed](../generated/workflows/services/real-estate/just-listed.md)** | 832×480 | `ez_svc_jlist` | Silent just-listed ~5 s |
| **[services/real-estate/open-house-bed](../generated/workflows/services/real-estate/open-house-bed.md)** | 1216×640 | `ez_svc_openh` | Open-house bed ~1.91:1 |
| **[services/real-estate/sold-slate](../generated/workflows/services/real-estate/sold-slate.md)** | 1024×1024 | `ez_svc_sold` | Sold slate 1:1 |
| **[services/real-estate/empty-room](../generated/workflows/services/real-estate/empty-room.md)** | 1280×704 | `ez_svc_empty` | Empty-room still 16:9 |
| **[services/real-estate/dressed-room](../generated/workflows/services/real-estate/dressed-room.md)** | 1280×704 | `ez_svc_dress` | Dressed-room still 16:9 |
| **[services/real-estate/amenity-loop](../generated/workflows/services/real-estate/amenity-loop.md)** | 768×768 | `ez_svc_amen` | Silent amenity loop |
| **[services/real-estate/key-turn-loop](../generated/workflows/services/real-estate/key-turn-loop.md)** | 768×768 | `ez_svc_key` | Silent key-turn loop |
| **[services/real-estate/walkthrough-av](../generated/workflows/services/real-estate/walkthrough-av.md)** | 1280×704 | `ez_svc_walkth` | Walkthrough AV ~5 s |
| **[services/real-estate/twilight-av](../generated/workflows/services/real-estate/twilight-av.md)** | 1280×704 | `ez_svc_twil` | Twilight AV ~5 s |
| **[services/real-estate/neighborhood-av](../generated/workflows/services/real-estate/neighborhood-av.md)** | 1280×704 | `ez_svc_nhood` | Neighborhood AV ~5 s |
| **[services/real-estate/aerial-push-av](../generated/workflows/services/real-estate/aerial-push-av.md)** | 1280×704 | `ez_svc_apush` | Aerial-push AV ~5 s |
| **[services/real-estate/handoff-av](../generated/workflows/services/real-estate/handoff-av.md)** | 1280×704 | `ez_svc_handof` | Handoff AV ~5 s |

## Fashion and beauty

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/fashion-beauty/lookbook-cover](../generated/workflows/services/fashion-beauty/lookbook-cover.md)** | 1024×1280 | `ez_svc_lookbk` | Lookbook cover 4:5 |
| **[services/fashion-beauty/look-full](../generated/workflows/services/fashion-beauty/look-full.md)** | 480×832 | `ez_svc_look_f` | Silent full-look 9:16 |
| **[services/fashion-beauty/look-detail](../generated/workflows/services/fashion-beauty/look-detail.md)** | 1024×1024 | `ez_svc_look_d` | Look detail 1:1 |
| **[services/fashion-beauty/look-back](../generated/workflows/services/fashion-beauty/look-back.md)** | 1024×1280 | `ez_svc_look_b` | Look back 4:5 |
| **[services/fashion-beauty/campaign-hero](../generated/workflows/services/fashion-beauty/campaign-hero.md)** | 1280×704 | `ez_svc_camp_h` | Campaign hero 16:9 |
| **[services/fashion-beauty/beauty-pack](../generated/workflows/services/fashion-beauty/beauty-pack.md)** | 1024×1024 | `ez_svc_bpack` | Beauty packshot 1:1 |
| **[services/fashion-beauty/swatch-macro](../generated/workflows/services/fashion-beauty/swatch-macro.md)** | 1024×1024 | `ez_svc_swatch` | Swatch macro 1:1 |
| **[services/fashion-beauty/texture-fill](../generated/workflows/services/fashion-beauty/texture-fill.md)** | 1024×1024 | `ez_svc_texfil` | Texture fill 1:1 |
| **[services/fashion-beauty/street-look](../generated/workflows/services/fashion-beauty/street-look.md)** | 480×832 | `ez_svc_street` | Silent street-look 9:16 |
| **[services/fashion-beauty/makeup-step](../generated/workflows/services/fashion-beauty/makeup-step.md)** | 480×832 | `ez_svc_makeup` | Silent makeup-step 9:16 |
| **[services/fashion-beauty/editorial-still](../generated/workflows/services/fashion-beauty/editorial-still.md)** | 1024×1280 | `ez_svc_edit` | Editorial still 4:5 |
| **[services/fashion-beauty/hair-loop](../generated/workflows/services/fashion-beauty/hair-loop.md)** | 480×832 | `ez_svc_hair` | Silent hair loop 9:16 |
| **[services/fashion-beauty/glow-loop](../generated/workflows/services/fashion-beauty/glow-loop.md)** | 768×768 | `ez_svc_glow` | Silent glow loop |
| **[services/fashion-beauty/nail-loop](../generated/workflows/services/fashion-beauty/nail-loop.md)** | 768×768 | `ez_svc_nail` | Silent nail loop |
| **[services/fashion-beauty/fabric-twirl-av](../generated/workflows/services/fashion-beauty/fabric-twirl-av.md)** | 768×1280 | `ez_svc_twirl` | Fabric-twirl AV 9:16 |
| **[services/fashion-beauty/walk-av](../generated/workflows/services/fashion-beauty/walk-av.md)** | 768×1280 | `ez_svc_fwalk` | Fashion walk AV 9:16 |
| **[services/fashion-beauty/get-ready-av](../generated/workflows/services/fashion-beauty/get-ready-av.md)** | 768×1280 | `ez_svc_ready` | Get-ready AV 9:16 |
| **[services/fashion-beauty/beauty-unbox-av](../generated/workflows/services/fashion-beauty/beauty-unbox-av.md)** | 768×1280 | `ez_svc_bunbox` | Beauty unbox AV 9:16 |
| **[services/fashion-beauty/campaign-av](../generated/workflows/services/fashion-beauty/campaign-av.md)** | 1280×704 | `ez_svc_camp_v` | Campaign AV ~5 s |
| **[services/fashion-beauty/fitting-av](../generated/workflows/services/fashion-beauty/fitting-av.md)** | 768×1280 | `ez_svc_fit` | Fitting AV 9:16 |

## B2B / SaaS

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/b2b-saas/ui-hero](../generated/workflows/services/b2b-saas/ui-hero.md)** | 1536×864 | `ez_svc_ui` | UI hero still 16:9 |
| **[services/b2b-saas/feature-card](../generated/workflows/services/b2b-saas/feature-card.md)** | 1024×1024 | `ez_svc_feat` | Feature card 1:1 |
| **[services/b2b-saas/case-cover](../generated/workflows/services/b2b-saas/case-cover.md)** | 1216×640 | `ez_svc_case` | Case-study cover ~1.91:1 |
| **[services/b2b-saas/webinar-thumb](../generated/workflows/services/b2b-saas/webinar-thumb.md)** | 1280×704 | `ez_svc_webth` | Webinar thumbnail 16:9 |
| **[services/b2b-saas/ebook-cover](../generated/workflows/services/b2b-saas/ebook-cover.md)** | 1024×1280 | `ez_svc_ebook` | Ebook cover 4:5 |
| **[services/b2b-saas/report-cover](../generated/workflows/services/b2b-saas/report-cover.md)** | 1216×640 | `ez_svc_report` | Report cover ~1.91:1 |
| **[services/b2b-saas/founder-still](../generated/workflows/services/b2b-saas/founder-still.md)** | 832×480 | `ez_svc_found` | Silent founder motion ~5 s |
| **[services/b2b-saas/office-wide](../generated/workflows/services/b2b-saas/office-wide.md)** | 832×480 | `ez_svc_off_w` | Silent office-wide ~5 s |
| **[services/b2b-saas/culture-still](../generated/workflows/services/b2b-saas/culture-still.md)** | 1280×704 | `ez_svc_cult` | Culture still 16:9 |
| **[services/b2b-saas/keynote-still](../generated/workflows/services/b2b-saas/keynote-still.md)** | 1280×704 | `ez_svc_keynt` | Keynote still 16:9 |
| **[services/b2b-saas/changelog-card](../generated/workflows/services/b2b-saas/changelog-card.md)** | 832×480 | `ez_svc_chglog` | Silent changelog card ~5 s |
| **[services/b2b-saas/pricing-bed](../generated/workflows/services/b2b-saas/pricing-bed.md)** | 1280×704 | `ez_svc_price` | Pricing bed 16:9 |
| **[services/b2b-saas/launch-still](../generated/workflows/services/b2b-saas/launch-still.md)** | 1280×704 | `ez_svc_launch` | Launch still 16:9 |
| **[services/b2b-saas/diagram-bed](../generated/workflows/services/b2b-saas/diagram-bed.md)** | 1280×704 | `ez_svc_diag` | Diagram bed 16:9 |
| **[services/b2b-saas/cursor-demo-av](../generated/workflows/services/b2b-saas/cursor-demo-av.md)** | 1280×704 | `ez_svc_cursor` | Cursor-demo AV ~5 s |
| **[services/b2b-saas/explainer-av](../generated/workflows/services/b2b-saas/explainer-av.md)** | 1280×704 | `ez_svc_expl` | Explainer AV ~5 s |
| **[services/b2b-saas/office-broll-av](../generated/workflows/services/b2b-saas/office-broll-av.md)** | 1280×704 | `ez_svc_offbr` | Office B-roll AV ~5 s |
| **[services/b2b-saas/webinar-open-av](../generated/workflows/services/b2b-saas/webinar-open-av.md)** | 1280×704 | `ez_svc_webop` | Webinar-open AV ~5 s |
| **[services/b2b-saas/customer-story-av](../generated/workflows/services/b2b-saas/customer-story-av.md)** | 768×1280 | `ez_svc_cust` | Customer-story AV 9:16 |
| **[services/b2b-saas/ship-day-av](../generated/workflows/services/b2b-saas/ship-day-av.md)** | 1280×704 | `ez_svc_ship` | Ship-day AV ~5 s |

## Events and wedding

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/events-wedding/save-the-date](../generated/workflows/services/events-wedding/save-the-date.md)** | 1024×1280 | `ez_svc_std` | Save-the-date still 4:5 |
| **[services/events-wedding/invite-bed](../generated/workflows/services/events-wedding/invite-bed.md)** | 1024×1280 | `ez_svc_invite` | Invite bed 4:5 |
| **[services/events-wedding/program-cover](../generated/workflows/services/events-wedding/program-cover.md)** | 1024×1280 | `ez_svc_prog` | Program cover 4:5 |
| **[services/events-wedding/welcome-sign](../generated/workflows/services/events-wedding/welcome-sign.md)** | 832×480 | `ez_svc_welc` | Silent welcome-sign ~5 s |
| **[services/events-wedding/table-bed](../generated/workflows/services/events-wedding/table-bed.md)** | 1280×704 | `ez_svc_table` | Table bed 16:9 |
| **[services/events-wedding/highlight-still](../generated/workflows/services/events-wedding/highlight-still.md)** | 1024×1280 | `ez_svc_hlite` | Highlight still 4:5 |
| **[services/events-wedding/first-look](../generated/workflows/services/events-wedding/first-look.md)** | 480×832 | `ez_svc_first` | Silent first-look 9:16 |
| **[services/events-wedding/venue-wide](../generated/workflows/services/events-wedding/venue-wide.md)** | 832×480 | `ez_svc_venue` | Silent venue-wide ~5 s |
| **[services/events-wedding/details-flatlay](../generated/workflows/services/events-wedding/details-flatlay.md)** | 1024×1024 | `ez_svc_detfl` | Details flatlay 1:1 |
| **[services/events-wedding/speaker-still](../generated/workflows/services/events-wedding/speaker-still.md)** | 1024×1280 | `ez_svc_speak` | Speaker still 4:5 |
| **[services/events-wedding/badge-bed](../generated/workflows/services/events-wedding/badge-bed.md)** | 1024×1024 | `ez_svc_badge` | Badge bed 1:1 |
| **[services/events-wedding/sponsor-slate](../generated/workflows/services/events-wedding/sponsor-slate.md)** | 1280×704 | `ez_svc_spon` | Sponsor slate 16:9 |
| **[services/events-wedding/processional-av](../generated/workflows/services/events-wedding/processional-av.md)** | 1280×704 | `ez_svc_proc` | Processional AV ~5 s |
| **[services/events-wedding/dance-floor-av](../generated/workflows/services/events-wedding/dance-floor-av.md)** | 1280×704 | `ez_svc_dance` | Dance-floor AV ~5 s |
| **[services/events-wedding/sparkler-exit-av](../generated/workflows/services/events-wedding/sparkler-exit-av.md)** | 1280×704 | `ez_svc_spark` | Sparkler-exit AV ~5 s |
| **[services/events-wedding/conference-av](../generated/workflows/services/events-wedding/conference-av.md)** | 1280×704 | `ez_svc_conf` | Conference AV ~5 s |
| **[services/events-wedding/recap-av](../generated/workflows/services/events-wedding/recap-av.md)** | 1280×704 | `ez_svc_erecap` | Recap AV ~5 s |
| **[services/events-wedding/aftermovie-hook-av](../generated/workflows/services/events-wedding/aftermovie-hook-av.md)** | 768×1280 | `ez_svc_after` | Aftermovie hook AV 9:16 |
| **[services/events-wedding/rehearsal-av](../generated/workflows/services/events-wedding/rehearsal-av.md)** | 1280×704 | `ez_svc_rehr` | Rehearsal AV ~5 s |
| **[services/events-wedding/trailer-av](../generated/workflows/services/events-wedding/trailer-av.md)** | 768×1280 | `ez_svc_trail` | Event trailer AV 9:16 |

## Fitness and travel

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[services/fitness-travel/coach-still](../generated/workflows/services/fitness-travel/coach-still.md)** | 480×832 | `ez_svc_coach` | Silent coach motion 9:16 |
| **[services/fitness-travel/move-still](../generated/workflows/services/fitness-travel/move-still.md)** | 1024×1280 | `ez_svc_move` | Move still 4:5 |
| **[services/fitness-travel/gym-wide](../generated/workflows/services/fitness-travel/gym-wide.md)** | 1280×704 | `ez_svc_gymw` | Gym wide still 16:9 |
| **[services/fitness-travel/home-gym](../generated/workflows/services/fitness-travel/home-gym.md)** | 1280×704 | `ez_svc_hgym` | Home-gym still 16:9 |
| **[services/fitness-travel/recovery-still](../generated/workflows/services/fitness-travel/recovery-still.md)** | 1024×1280 | `ez_svc_recov` | Recovery still 4:5 |
| **[services/fitness-travel/meal-prep](../generated/workflows/services/fitness-travel/meal-prep.md)** | 1024×1280 | `ez_svc_meal` | Meal-prep still 4:5 |
| **[services/fitness-travel/resort-hero](../generated/workflows/services/fitness-travel/resort-hero.md)** | 832×480 | `ez_svc_resort` | Silent resort-hero ~5 s |
| **[services/fitness-travel/room-still](../generated/workflows/services/fitness-travel/room-still.md)** | 1280×704 | `ez_svc_room` | Resort room still 16:9 |
| **[services/fitness-travel/pool-still](../generated/workflows/services/fitness-travel/pool-still.md)** | 1280×704 | `ez_svc_pool` | Pool still 16:9 |
| **[services/fitness-travel/trail-still](../generated/workflows/services/fitness-travel/trail-still.md)** | 832×480 | `ez_svc_trailf` | Silent trail ~5 s |
| **[services/fitness-travel/city-arrive](../generated/workflows/services/fitness-travel/city-arrive.md)** | 832×480 | `ez_svc_arrive` | Silent city-arrive ~5 s |
| **[services/fitness-travel/rep-loop](../generated/workflows/services/fitness-travel/rep-loop.md)** | 480×832 | `ez_svc_rep` | Silent rep loop 9:16 |
| **[services/fitness-travel/stretch-loop](../generated/workflows/services/fitness-travel/stretch-loop.md)** | 480×832 | `ez_svc_strch` | Silent stretch loop 9:16 |
| **[services/fitness-travel/waves-loop](../generated/workflows/services/fitness-travel/waves-loop.md)** | 768×768 | `ez_svc_waves` | Silent waves loop |
| **[services/fitness-travel/workout-av](../generated/workflows/services/fitness-travel/workout-av.md)** | 768×1280 | `ez_svc_work` | Workout AV 9:16 |
| **[services/fitness-travel/class-av](../generated/workflows/services/fitness-travel/class-av.md)** | 768×1280 | `ez_svc_fclass` | Fitness class AV 9:16 |
| **[services/fitness-travel/check-in-av](../generated/workflows/services/fitness-travel/check-in-av.md)** | 1280×704 | `ez_svc_check` | Check-in AV ~5 s |
| **[services/fitness-travel/tour-av](../generated/workflows/services/fitness-travel/tour-av.md)** | 1280×704 | `ez_svc_tour` | Tour AV ~5 s |
| **[services/fitness-travel/sunset-av](../generated/workflows/services/fitness-travel/sunset-av.md)** | 1280×704 | `ez_svc_sun` | Sunset AV ~5 s |
| **[services/fitness-travel/packing-av](../generated/workflows/services/fitness-travel/packing-av.md)** | 768×1280 | `ez_svc_pack` | Packing AV 9:16 |
