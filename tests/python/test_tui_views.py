"""The view layer renders decisions, never its own.

``scripts/lib/tui/views.py`` is pure: snapshots go in, ``ViewModel`` records come
out. These tests drive it with hand-built health records, guard verdicts, and
catalog entries, and assert on the rendered *content* - substrings, badges,
styles, and enabled flags - because a pixel-exact assertion would break on every
layout tweak while these assertions break only when the console starts lying to
the operator about what is safe to run.
"""

from __future__ import annotations

from tui import contract as c
from tui import lanes as lane_lib
from tui import views


def _health(
    stack_state: str = "running",
    attention: str = "kitchen",
    host_free_gib: int = 64,
    disk_free_gib: int = 200,
    occupancy_mode: str = "idle",
    parked: bool = False,
    queue: str = "idle",
    llm_live: bool = False,
    shaping: bool = True,
    shaping_mbps: int = 400,
    downloads_running: bool = False,
    packs: tuple[tuple[str, bool], ...] = (("klein", True), ("wan", True)),
    errors: tuple[str, ...] = (),
) -> c.Health:
    """Build a fully-measured health snapshot, overriding only what matters.

    Args:
        stack_state: Compose state token.
        attention: Attention backend token.
        host_free_gib: Free RAM, or ``c.UNMEASURED``.
        disk_free_gib: Free disk, or ``c.UNMEASURED``.
        occupancy_mode: Occupancy desk mode.
        parked: Whether Comfy is parked.
        queue: Queue state token.
        llm_live: Whether the host LLM sidecar is up.
        shaping: Whether a bandwidth cap is active.
        shaping_mbps: The active cap.
        downloads_running: Whether a download pid is live.
        packs: Pack readiness pairs.
        errors: Probe failures.

    Returns:
        A health record for the views.
    """
    return c.Health(
        stack_state=stack_state,
        attention=attention,
        host_free_gib=host_free_gib,
        disk_free_gib=disk_free_gib,
        occupancy_mode=occupancy_mode,
        parked=parked,
        queue=queue,
        llm_live=llm_live,
        shaping=shaping,
        shaping_mbps=shaping_mbps,
        downloads_running=downloads_running,
        packs=packs,
        errors=errors,
    )


def _action(
    action_id: str = "stack.status",
    title: str = "Show status",
    group: c.Group = c.Group.STACK,
    summary: str = "Print the stack status.",
    tier: c.RiskTier = c.RiskTier.READ,
    confirm: c.ConfirmKind = c.ConfirmKind.NONE,
    fixed_args: tuple[str, ...] = ("status",),
    params: tuple[c.ParamSpec, ...] = (),
    keywords: tuple[str, ...] = (),
    refuse_reason: str = "",
) -> c.ActionSpec:
    """Build a catalog entry, overriding only what a test cares about.

    Args:
        action_id: Dotted id.
        title: List label.
        group: Left-rail section.
        summary: One-line effect.
        tier: Risk tier.
        confirm: Confirmation literal the child demands.
        fixed_args: Always-present arguments.
        params: Operator-supplied arguments.
        keywords: Extra palette words.
        refuse_reason: Why a refused action can never run.

    Returns:
        A catalog entry for the views.
    """
    return c.ActionSpec(
        action_id=action_id,
        title=title,
        group=group,
        summary=summary,
        runner=c.RunnerKind.MANAGE,
        target=action_id.split(".")[-1],
        fixed_args=fixed_args,
        params=params,
        tier=tier,
        confirm=confirm,
        keywords=keywords,
        refuse_reason=refuse_reason,
    )


_ALLOWED = c.GuardVerdict(allowed=True)
"""The verdict an action needs before its row lights up."""


def _blocked(reason: str, *, stale: bool = False) -> c.GuardVerdict:
    """Build a blocking verdict.

    Args:
        reason: The blocker the operator sees.
        stale: True when a reading could not be taken.

    Returns:
        A failing guard verdict.
    """
    return c.GuardVerdict(allowed=False, reasons=(reason,), stale=stale)


def _result(
    action_id: str = "stack.start",
    argv: tuple[str, ...] = ("scripts/manage.sh", "start"),
    returncode: int = 0,
    output: str = "container started",
    duration_s: float = 3.0,
    ran: bool = True,
    note: str = "",
) -> c.CommandResult:
    """Build a dispatch outcome.

    Args:
        action_id: What ran.
        argv: What was exec'd.
        returncode: Exit status.
        output: Captured output.
        duration_s: Wall clock.
        ran: Whether the child actually ran.
        note: Why it did not run.

    Returns:
        A command result for the views.
    """
    return c.CommandResult(
        action_id=action_id,
        argv=argv,
        returncode=returncode,
        output=output,
        duration_s=duration_s,
        ran=ran,
        note=note,
    )


def _detail_text(model: c.ViewModel) -> str:
    """Flatten a model's detail pane into one haystack.

    Args:
        model: The rendered screen.

    Returns:
        Every detail line joined with newlines.
    """
    return "\n".join(line.text for line in model.detail)


def _row(model: c.ViewModel, key: str) -> c.Row:
    """Look one row up by key.

    Args:
        model: The rendered screen.
        key: Row key.

    Returns:
        The matching row.

    Raises:
        AssertionError: No row carries that key.
    """
    for row in model.rows:
        if row.key == key:
            return row
    raise AssertionError(f"no row {key!r} in {model.row_keys()}")


def test_health_rows_label_every_reading_and_enable_the_measured_ones() -> None:
    """A measured machine yields one selectable row per probe."""
    rows = {row.key: row for row in views.health_rows(_health())}
    assert rows["health.stack"].badge == "ok"
    assert rows["health.stack"].enabled is True
    assert rows["health.ram"].note == "64/28 GiB"
    assert rows["health.ram"].badge == "ok"
    assert rows["health.disk"].note == "200/40 GiB"
    assert rows["health.occ"].badge == "ok"
    assert rows["health.parked"].note == "loaded"
    assert rows["health.queue"].badge == "ok"
    assert rows["health.llm"].note == "down"
    assert rows["health.cap"].note == "400 Mbps"
    assert rows["health.dl"].note == "idle"
    assert rows["health.packs"].note == "2/2 ready"
    assert rows["health.attn"].note == "kitchen"


def test_health_rows_surface_unknown_readings_as_blocked() -> None:
    """A cold console shows what it does not know instead of hiding it."""
    rows = {row.key: row for row in views.health_rows(c.empty_health())}
    for key in ("health.stack", "health.attn", "health.ram", "health.disk"):
        assert rows[key].badge == "?", key
        assert rows[key].enabled is False, key
        assert rows[key].style is c.Style.BAD, key
    assert rows["health.occ"].enabled is False
    assert rows["health.queue"].enabled is False
    assert rows["health.packs"].enabled is False
    assert rows["health.error-0"].enabled is False
    assert rows["health.error-0"].badge == "bad"
    assert "no reading yet" in rows["health.error-0"].note


def test_health_rows_warn_inside_the_margin_and_bad_under_the_floor() -> None:
    """Headroom grades against the same floors the CLI blocks on."""
    near = {row.key: row for row in views.health_rows(
        _health(host_free_gib=c.MIN_HOST_FREE_GIB + 2, disk_free_gib=c.MIN_DISK_FREE_GIB - 1)
    )}
    assert near["health.ram"].badge == "warn"
    assert near["health.ram"].style is c.Style.WARN
    assert near["health.ram"].enabled is True
    assert near["health.disk"].badge == "bad"
    assert near["health.disk"].style is c.Style.BAD
    assert near["health.disk"].enabled is True


def test_health_rows_grade_the_optional_probes() -> None:
    """A degraded but measured probe warns rather than blocks."""
    rows = {
        row.key: row
        for row in views.health_rows(
            _health(
                occupancy_mode="blender-desk",
                parked=True,
                queue="busy",
                llm_live=True,
                shaping=False,
                downloads_running=True,
                packs=(("klein", True), ("wan", False)),
            )
        )
    }
    assert rows["health.occ"].badge == "warn"
    assert rows["health.parked"].note == "parked"
    assert rows["health.queue"].badge == "warn"
    assert rows["health.llm"].badge == "warn"
    assert rows["health.cap"].note == "uncapped"
    assert rows["health.dl"].badge == "warn"
    assert rows["health.packs"].note == "1/2 ready"
    assert rows["health.packs"].badge == "warn"


def test_health_rows_treat_a_still_unknown_probe_as_unknown() -> None:
    """A token that is neither a known state nor blank is not a green light."""
    rows = {
        row.key: row
        for row in views.health_rows(
            _health(stack_state="weird", queue="half", shaping=True, shaping_mbps=c.UNMEASURED)
        )
    }
    assert rows["health.stack"].badge == "?"
    assert rows["health.queue"].badge == "?"
    assert rows["health.cap"].badge == "?"
    assert rows["health.cap"].enabled is False
    present = {row.key: row for row in views.health_rows(_health(stack_state="present"))}
    assert present["health.stack"].badge == "warn"
    assert present["health.stack"].enabled is True
    assert present["health.attn"].note == "n/a"


def test_health_rows_only_judge_attention_while_the_stack_runs() -> None:
    """A stopped stack has no attention backend to grade."""
    stopped = {row.key: row for row in views.health_rows(_health(stack_state="stopped"))}
    assert stopped["health.attn"].note == "n/a"
    assert stopped["health.attn"].enabled is True
    fallback = {row.key: row for row in views.health_rows(_health(attention="pytorch-fallback"))}
    assert fallback["health.attn"].badge == "warn"
    odd = {row.key: row for row in views.health_rows(_health(attention="mystery"))}
    assert odd["health.attn"].badge == "?"
    assert odd["health.attn"].enabled is False


def test_status_bar_reads_like_the_safety_headline() -> None:
    """The bar names stack, both floors, occupancy, queue, and the cap."""
    line = views.status_bar(_health(), width=120)
    assert line.text == (
        "stack running  ram 64/28 GiB  disk 200/40 GiB  occ idle  queue idle  cap 400 Mbps"
    )
    assert line.style is c.Style.OK


def test_status_bar_is_bad_when_anything_is_blocked_or_unknown() -> None:
    """The headline goes red before the operator reaches for a heavy action."""
    assert views.status_bar(c.empty_health(), width=200).style is c.Style.BAD
    under = _health(disk_free_gib=c.MIN_DISK_FREE_GIB - 1)
    assert views.status_bar(under, width=200).style is c.Style.BAD
    queue_busy = _health(queue="busy")
    assert views.status_bar(queue_busy, width=200).style is c.Style.WARN


def test_status_bar_warns_within_four_gib_of_a_floor() -> None:
    """Near the floor the bar is yellow, not green and not yet red."""
    near = _health(host_free_gib=c.MIN_HOST_FREE_GIB + 1)
    assert views.status_bar(near, width=200).style is c.Style.WARN


def test_status_bar_truncates_to_the_terminal_width() -> None:
    """A narrow terminal never wraps, because a wrapped status line is a lie."""
    assert len(views.status_bar(_health(), width=40).text) == 40
    assert views.status_bar(_health(), width=40).text.endswith(">")
    assert views.status_bar(_health(), width=1).text == ">"
    assert views.status_bar(_health(), width=0).text == ""


def test_dashboard_leads_with_the_readings_and_offers_the_quick_actions() -> None:
    """The landing screen is the health list followed by runnable actions."""
    quick = (_action("stack.status", "Show status"), _action("stack.start", "Start", tier=c.RiskTier.HEAVY))
    verdicts = {"stack.status": _ALLOWED, "stack.start": _blocked("free RAM is unknown")}
    model = views.dashboard(_health(), verdicts, quick)
    assert model.screen is c.ScreenId.DASHBOARD
    assert model.rows[0].key == "health.stack"
    assert _row(model, "stack.status").enabled is True
    assert _row(model, "stack.start").enabled is False
    assert _row(model, "stack.start").style is c.Style.DIM
    detail = _detail_text(model)
    assert "quick actions ready 1/2" in detail
    assert "readings unknown 0/11" in detail
    assert "guard verdicts on file 2" in detail
    assert model.selected == model.row_keys().index("stack.status")


def test_dashboard_says_out_loud_when_nothing_is_ready() -> None:
    """An unmeasured dashboard is styled as a problem, not as a clean screen."""
    model = views.dashboard(c.empty_health(), {}, ())
    detail = _detail_text(model)
    assert "quick actions ready 0/0" in detail
    assert "guard verdicts on file 0" in detail
    assert any("readings unknown" in line.text for line in model.detail)
    assert model.detail[1].style is c.Style.BAD
    assert model.selected == 0


def test_group_list_carries_the_tier_badge_and_the_guard_reason() -> None:
    """Every action row states its tier and, when blocked, why."""
    start = _action("stack.start", "Start the stack", tier=c.RiskTier.HEAVY, summary="Bring the stack up.")
    stop = _action("stack.stop", "Stop the stack", tier=c.RiskTier.WRITE, summary="Take the stack down.")
    verdicts = {
        "stack.start": _blocked("the ComfyUI queue still has a job in flight"),
        "stack.stop": _ALLOWED,
    }
    model = views.group_list(c.Group.STACK, (start, stop), verdicts, selected=1)
    started = _row(model, "stack.start")
    assert started.badge == "HEAVY"
    assert started.note == "the ComfyUI queue still has a job in flight"
    assert started.enabled is False
    assert started.style is c.Style.DIM
    stopped = _row(model, "stack.stop")
    assert stopped.badge == "write"
    assert stopped.note == "Take the stack down."
    assert stopped.enabled is True
    assert stopped.style is c.Style.NORMAL
    assert model.selected == 1
    assert "hotkey 2" in _detail_text(model)


def test_group_list_blocks_an_action_the_guard_never_qualified() -> None:
    """No verdict means no run: the console fails closed, not optimistic."""
    start = _action("stack.start", "Start the stack", tier=c.RiskTier.HEAVY)
    model = views.group_list(c.Group.STACK, (start,), {}, selected=99)
    assert _row(model, "stack.start").enabled is False
    assert _row(model, "stack.start").note == "waiting on a guard"
    assert model.selected == 0
    assert "0/1 runnable" in _detail_text(model)
    assert model.detail[0].style is c.Style.WARN


def test_group_list_renders_a_refused_action_as_bad_and_unselectable() -> None:
    """A policy-blocked action is red, dimmed, and never selectable."""
    refused = _action(
        "models.minimax",
        "Download MiniMax H3",
        group=c.Group.MODELS,
        tier=c.RiskTier.REFUSED,
        refuse_reason="MiniMax H3 is outside the US-safe catalog",
    )
    model = views.group_list(c.Group.MODELS, (refused,), {"models.minimax": _ALLOWED})
    row = _row(model, "models.minimax")
    assert row.badge == "REFUSED"
    assert row.note == "MiniMax H3 is outside the US-safe catalog"
    assert row.enabled is False
    assert row.style is c.Style.BAD


def test_group_list_names_a_refusal_even_without_a_reason() -> None:
    """A refused entry with no reason still says it was blocked."""
    refused = _action("models.seed", "Seedance", tier=c.RiskTier.REFUSED)
    model = views.group_list(c.Group.MODELS, (refused,), {})
    assert _row(model, "models.seed").note == "policy blocked"


def test_group_list_clamps_an_out_of_range_selection() -> None:
    """A stale focus index never indexes past the list."""
    action = _action("stack.status", "Show status")
    assert views.group_list(c.Group.STACK, (action,), {}, selected=-5).selected == 0
    assert views.group_list(c.Group.STACK, (action,), {}, selected=7).selected == 0
    assert views.group_list(c.Group.STACK, (), {}, selected=4).selected == 0


def test_palette_filters_on_every_field_and_keeps_the_blocked_rows() -> None:
    """The palette searches id, title, summary, keywords, and group."""
    still = _action("photos.still", "Print a still", group=c.Group.FILM, keywords=("klein",))
    clip = _action("video.clip", "Print a clip", group=c.Group.OCCUPANCY, summary="wan motion")
    actions = (still, clip)
    model = views.palette("klein", actions, {"photos.still": _ALLOWED, "video.clip": _ALLOWED})
    assert model.row_keys() == ("photos.still",)
    assert views.palette("wan", actions, {}).row_keys() == ("video.clip",)
    assert views.palette("film", actions, {}).row_keys() == ("photos.still",)
    assert views.palette("", actions, {}).row_keys() == ("photos.still", "video.clip")
    assert views.palette("  ", actions, {}).row_keys() == ("photos.still", "video.clip")
    assert "matches 1/2" in _detail_text(model)
    assert model.screen is c.ScreenId.PALETTE


def test_palette_says_so_when_nothing_matches() -> None:
    """An empty palette is stated, not silently blank."""
    model = views.palette("zzz", (_action(),), {"stack.status": _ALLOWED})
    assert model.rows == ()
    assert model.selected == 0
    assert model.detail[0].style is c.Style.WARN
    assert "matches 0/1" in model.detail[0].text


def test_param_form_shows_each_field_and_the_argv_it_will_build() -> None:
    """The collector previews the exact argv once every answer is in."""
    action = _action(
        "models.download_music",
        "Download music pack",
        group=c.Group.MODELS,
        fixed_args=("download-music",),
        params=(
            c.ParamSpec(
                name="tier",
                label="Tier",
                kind=c.ParamKind.CHOICE,
                flag="--tier",
                choices=(c.Choice("turbo", "Turbo", "~10 GB"), c.Choice("xl", "XL")),
            ),
            c.ParamSpec(
                name="slug",
                label="Album slug",
                kind=c.ParamKind.TEXT,
                flag="--slug",
                help_text="Directory name",
            ),
        ),
    )
    model = views.param_form(action, {"tier": "turbo", "slug": "harbour"}, selected=1)
    assert model.screen is c.ScreenId.PARAM_FORM
    assert _row(model, "tier").badge == "choice"
    assert _row(model, "tier").note == "turbo [Turbo, XL]"
    assert _row(model, "slug").note == "harbour"
    detail = _detail_text(model)
    assert "argv download-music --tier turbo --slug harbour" in detail
    assert "tier read" in detail
    assert model.selected == 1


def test_param_form_states_what_is_still_missing() -> None:
    """An incomplete form says which field blocks the run."""
    action = _action(
        "film.print",
        "Print a shot",
        group=c.Group.FILM,
        params=(
            c.ParamSpec(name="film", label="Film", kind=c.ParamKind.TEXT),
            c.ParamSpec(
                name="drafts",
                label="Drafts",
                kind=c.ParamKind.INT,
                flag="--drafts",
                required=False,
            ),
            c.ParamSpec(
                name="look",
                label="Look",
                kind=c.ParamKind.CHOICE,
                flag="--look",
                choices=(c.Choice("warm", "Warm"),),
            ),
        ),
    )
    model = views.param_form(action, {})
    detail = _detail_text(model)
    assert "not ready: film: Film is required" in detail
    assert _row(model, "film").note == "required"
    assert _row(model, "drafts").note == "optional"
    assert _row(model, "look").note == "[Warm]"
    assert model.selected == 0


def test_param_form_uses_a_default_answer_and_shows_the_tier_colour() -> None:
    """A pre-filled parameter reads as answered, and a heavy tier reads as warn."""
    action = _action(
        "models.cap",
        "Set the bandwidth cap",
        group=c.Group.MODELS,
        tier=c.RiskTier.HEAVY,
        confirm=c.ConfirmKind.YES,
        params=(
            c.ParamSpec(
                name="limit",
                label="Cap",
                kind=c.ParamKind.TEXT,
                flag="--limit",
                default="auto",
            ),
        ),
    )
    model = views.param_form(action, {})
    assert _row(model, "limit").note == "auto"
    assert model.detail[1].style is c.Style.WARN
    assert "confirm yes" in model.detail[1].text


def test_param_form_colours_a_refused_entry_the_way_the_guard_meant_it() -> None:
    """Even a policy-blocked entry renders, in red, with its tier stated."""
    action = _action(
        "models.minimax",
        "Download MiniMax H3",
        group=c.Group.MODELS,
        tier=c.RiskTier.REFUSED,
        refuse_reason="MiniMax H3 is outside the US-safe catalog",
    )
    model = views.param_form(action, {})
    assert model.detail[1].style is c.Style.BAD
    assert "tier REFUSED" in model.detail[1].text


def test_confirm_view_shows_the_argv_and_the_exact_yes_token() -> None:
    """Nothing runs until the operator retypes what the child script reads."""
    action = _action("stack.start", "Start the stack", tier=c.RiskTier.HEAVY, confirm=c.ConfirmKind.YES)
    model = views.confirm_view(action, ("scripts/manage.sh", "start"), typed="ye")
    detail = _detail_text(model)
    assert "scripts/manage.sh start" in detail
    assert "type exactly: yes" in detail
    assert "just press enter" not in detail
    assert "typed: ye" in detail
    assert model.screen is c.ScreenId.CONFIRM
    typed = [line for line in model.detail if line.text.startswith("typed:")]
    assert typed[0].style is c.Style.DIM
    matched = views.confirm_view(action, ("scripts/manage.sh", "start"), typed="yes")
    assert [line.style for line in matched.detail if line.text.startswith("typed:")][0] is c.Style.OK


def test_confirm_view_demands_DELETE_and_names_what_is_lost() -> None:
    """A destructive run is spelled out in red, with no invented token."""
    action = _action(
        "disk.reclaim",
        "Reclaim the model cache",
        group=c.Group.DISK,
        summary="Deletes uncached weights under MODELS_DIR.",
        tier=c.RiskTier.DESTRUCTIVE,
        confirm=c.ConfirmKind.DELETE,
    )
    model = views.confirm_view(action, ("scripts/utilities", "disk-reclaim.sh", "--apply"))
    detail = _detail_text(model)
    assert "type exactly: DELETE" in detail
    assert "DESTRUCTIVE: Reclaim the model cache erases data" in detail
    assert "cannot be restored" in detail
    assert "scripts/utilities disk-reclaim.sh --apply" in detail
    token_lines = [line for line in model.detail if "type exactly" in line.text]
    assert token_lines[0].style is c.Style.BAD
    assert model.detail[1].style is c.Style.BAD


def test_confirm_view_lets_a_tier_one_action_through_with_just_enter() -> None:
    """A plain write action must not be dressed up as a typed confirmation."""
    action = _action("stack.restart", "Restart the stack", tier=c.RiskTier.WRITE)
    model = views.confirm_view(action, ("scripts/manage.sh", "restart"))
    detail = _detail_text(model)
    assert "just press enter" in detail
    assert "type exactly" not in detail
    assert "DESTRUCTIVE" not in detail
    assert "Restart the stack" in model.title


def test_confirm_view_colours_the_tier_but_quotes_the_token_verbatim() -> None:
    """The colour follows the tier; the literal always comes from ``ConfirmKind``."""
    action = _action(
        "stack.update",
        "Update the stack",
        tier=c.RiskTier.HEAVY,
        confirm=c.ConfirmKind.DELETE,
    )
    model = views.confirm_view(action, ("scripts/manage.sh", "update"))
    detail = _detail_text(model)
    assert model.detail[1].style is c.Style.WARN
    assert "type exactly: DELETE" in detail
    assert "type exactly: yes" not in detail
    assert "cannot be restored" in detail


def test_progress_view_repeats_the_tail_under_the_action() -> None:
    """The waiting screen shows what the child has said so far."""
    tail = [f"line {index}" for index in range(45)] + ["", "   "]
    model = views.progress_view(_action("stack.start", "Start the stack"), tail)
    detail = _detail_text(model)
    assert model.screen is c.ScreenId.PROGRESS
    assert "running stack.start" in detail
    assert "47 output lines" in detail
    assert "line 44" in detail
    assert "line 5" in detail
    assert "line 4\n" not in f"{detail}\n"
    assert all(line.text.strip() for line in model.detail)
    assert model.rows == ()


def test_result_view_reports_a_clean_run_and_the_argv() -> None:
    """The outcome screen repeats exactly what was executed."""
    model = views.result_view(_result(output="compose is up\nsecond line\n\n"))
    detail = _detail_text(model)
    assert model.screen is c.ScreenId.RESULT
    assert "ran yes  exit 0  3.0s" in detail
    assert "argv scripts/manage.sh start" in detail
    assert "compose is up" in detail
    assert "second line" in detail
    assert model.detail[1].style is c.Style.OK


def test_result_view_marks_a_failure_red() -> None:
    """A non-zero exit is impossible to misread."""
    model = views.result_view(_result(returncode=7, output="nope"))
    assert model.detail[1].style is c.Style.BAD
    assert "exit 7" in model.detail[1].text


def test_result_view_explains_a_run_that_never_happened() -> None:
    """A blocked dispatch reads as blocked, with the reason beside it."""
    model = views.result_view(
        _result(returncode=c.UNMEASURED, output="", ran=False, note="blocked: queue busy")
    )
    detail = _detail_text(model)
    assert "ran no  exit ?  3.0s" in detail
    assert "note blocked: queue busy" in detail
    assert model.detail[1].style is c.Style.BAD


def test_lane_list_shows_each_lane_with_its_graph_count() -> None:
    """Browsing lanes is always permitted: the console edits nothing."""
    lanes = (
        lane_lib.Lane("photos", 10, "Photos", "Single images.", 7),
        lane_lib.Lane("video", 20, "Video", "Short clips.", 0),
    )
    model = views.lane_list(lanes, selected=1)
    assert model.screen is c.ScreenId.LANES
    assert model.row_keys() == ("photos", "video")
    assert _row(model, "photos").badge == "7"
    assert _row(model, "photos").note == "Single images."
    assert _row(model, "video").enabled is True
    assert model.selected == 1


def test_lane_list_says_when_there_is_nothing_to_browse() -> None:
    """A partial checkout still renders."""
    model = views.lane_list(())
    assert model.rows == ()
    assert model.detail[0].style is c.Style.WARN


def test_graph_list_rows_the_lane_and_its_occupancy_desk() -> None:
    """Each graph is addressable by the id other tools use."""
    lane = lane_lib.Lane("photos", 10, "Photos", "Single images.", 2)
    graphs = (
        lane_lib.Graph("photos", "photos/background-swap", "background-swap", "Swap a bg.", "klein"),
        lane_lib.Graph("photos", "photos/still-draft", "still-draft", "A draft.", ""),
    )
    model = views.graph_list(lane, graphs, selected=1)
    assert model.screen is c.ScreenId.LANE_GRAPHS
    assert model.row_keys() == ("photos/background-swap", "photos/still-draft")
    assert _row(model, "photos/background-swap").badge == "klein"
    assert _row(model, "photos/still-draft").badge == "-"
    assert "2 graphs on disk" in _detail_text(model)
    assert model.title == "Lane: Photos"
    assert model.selected == 1


def test_graph_detail_shows_the_graph_and_where_a_live_copy_lives() -> None:
    """The detail pane answers lane, id, occupancy, blurb, hand-off, and _user."""
    graph = lane_lib.Graph(
        lane_id="video",
        rel_id="video/still-to-video-5s",
        title="still-to-video-5s",
        description="Five silent seconds from a still.",
        occupancy="wan",
        handoff=("film/act-one",),
        default_view="workflow",
    )
    model = views.graph_detail(graph)
    detail = _detail_text(model)
    assert model.screen is c.ScreenId.GRAPH_DETAIL
    assert "lane video" in detail
    assert "id video/still-to-video-5s" in detail
    assert "occupancy wan" in detail
    assert "Five silent seconds" in detail
    assert "hand-off film/act-one" in detail
    assert "_user" in detail
    assert "COMFY_OUTPUT_DIR" in detail


def test_graph_detail_fills_in_what_a_thin_graph_omits() -> None:
    """A graph with no blurb or hand-off still renders completely."""
    model = views.graph_detail(lane_lib.Graph("3d", "3d/turntable", "turntable", "", ""))
    detail = _detail_text(model)
    assert "occupancy unspecified" in detail
    assert "blurb none recorded" in detail
    assert "hand-off none offered" in detail
    assert "view default" in detail


def test_audit_view_colours_each_dispatch_by_how_it_ended() -> None:
    """The log distinguishes a clean run, a failure, and a block."""
    history = (
        _result("stack.start", returncode=0),
        _result("stack.stop", returncode=2),
        _result("models.cap", returncode=c.UNMEASURED, ran=False),
    )
    model = views.audit_view(history, selected=2)
    assert model.screen is c.ScreenId.AUDIT
    assert _row(model, "0").badge == "ok"
    assert _row(model, "0").style is c.Style.OK
    assert _row(model, "1").badge == "fail"
    assert _row(model, "1").style is c.Style.BAD
    assert _row(model, "2").badge == "skipped"
    assert _row(model, "2").style is c.Style.DIM
    assert "exit ?" in _row(model, "2").note
    assert "scripts/manage.sh start" in _row(model, "0").note
    assert "3 commands dispatched" in _detail_text(model)


def test_audit_view_starts_empty() -> None:
    """A fresh session has a log, it just has nothing in it."""
    model = views.audit_view(())
    assert model.rows == ()
    assert model.selected == 0
    assert "nothing dispatched yet" in _detail_text(model)


def test_help_view_states_the_safety_contract_in_sentences() -> None:
    """An operator can read the rules without reading the source."""
    model = views.help_view()
    detail = _detail_text(model)
    assert model.screen is c.ScreenId.HELP
    assert "type yes" in detail
    assert "DELETE" in detail
    assert "every guard reports green" in detail
    assert "operator lock" in detail
    assert "Dry run" in detail
    assert all(row.enabled is False for row in model.rows)
    assert _row(model, "q").note == "quit"


def test_render_fits_a_one_row_terminal_without_crashing() -> None:
    """Even a single row of screen still says what screen you are on."""
    model = views.dashboard(_health(), {}, ())
    frame = views.render(model, width=20, height=1)
    assert len(frame.lines) == 1
    assert frame.lines[0].style is c.Style.TITLE
    assert frame.lines[0].text == "Studio dashboard"
    assert frame.title == "Studio dashboard"
    assert frame.footer == model.footer


def test_render_degrades_gracefully_below_the_minimum_height() -> None:
    """Zero rows is not a crash, and two rows still shows the key strip."""
    model = views.dashboard(_health(), {}, ())
    assert views.render(model, width=40, height=0).lines == ()
    two = views.render(model, width=80, height=2)
    assert len(two.lines) == 2
    assert two.lines[0].style is c.Style.TITLE
    assert two.lines[1].text == model.footer
    assert two.lines[1].style is c.Style.DIM
    narrow = views.render(model, width=10, height=2)
    assert narrow.lines[1].text.endswith(">")
    assert all(len(line.text) <= 10 for line in narrow.lines)


def test_render_clips_rows_rather_than_crashing_at_three_rows() -> None:
    """A tiny terminal loses rows; the title, one body line, and the footer stay."""
    model = views.dashboard(_health(), {}, (_action(),))
    frame = views.render(model, width=40, height=3)
    assert len(frame.lines) == 3
    assert [line.style for line in frame.lines][0] is c.Style.TITLE
    assert frame.lines[-1].style is c.Style.DIM
    assert all(len(line.text) <= 40 for line in frame.lines)


def test_render_fits_the_nominal_and_the_generous_geometry_exactly() -> None:
    """The frame never emits more lines than the screen has, at any height."""
    model = views.dashboard(_health(), {"stack.status": _ALLOWED}, (_action(),))
    for height in (4, 20, 200):
        frame = views.render(model, width=80, height=height)
        assert len(frame.lines) == height
        assert all(len(line.text) <= 80 for line in frame.lines)
    tiny = views.render(model, width=1, height=12)
    assert all(len(line.text) <= 1 for line in tiny.lines)


def test_render_reverses_the_focused_row_and_dims_the_disabled_one() -> None:
    """The cursor is always visible and a blocked row is always obviously dead."""
    rows = (
        c.Row(key="a", label="Alpha", badge="read", note="first", enabled=True),
        c.Row(key="b", label="Beta", badge="HEAVY", note="blocked", enabled=False),
        c.Row(key="c", label="Gamma", style=c.Style.OK, enabled=True),
    )
    model = c.ViewModel(screen=c.ScreenId.GROUP, title="T", rows=rows, selected=1)
    frame = views.render(model, width=80, height=10)
    body = frame.lines[1:4]
    assert body[0].style is c.Style.NORMAL
    assert body[1].style is c.Style.REVERSE
    assert body[2].style is c.Style.OK
    assert "Beta  [HEAVY]  - blocked" in body[1].text
    assert "Gamma" in body[2].text
    unstyled = c.ViewModel(
        screen=c.ScreenId.GROUP,
        title="T",
        rows=(c.Row(key="x", label="Bare"),),
        selected=0,
    )
    assert views.render(unstyled, width=80, height=3).lines[1].text == "Bare"
