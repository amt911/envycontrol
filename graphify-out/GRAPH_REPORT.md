# Graph Report - envycontrol  (2026-09-18)

## Corpus Check
- 41 files · ~36,142 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 332 nodes · 515 edges · 17 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 23|Community 23]]

## God Nodes (most connected - your core abstractions)
1. `FakeProbe` - 14 edges
2. `main()` - 13 edges
3. `FakeProbe` - 13 edges
4. `FakeProbe` - 12 edges
5. `FakeProbe` - 12 edges
6. `_configure_cache()` - 11 edges
7. `graphics_mode_switcher()` - 10 edges
8. `CachedConfig` - 10 edges
9. `_evidence()` - 9 edges
10. `_BaseBackend` - 9 edges

## Surprising Connections (you probably didn't know these)
- `BootRebuildError` --inherits--> `RuntimeError`  [EXTRACTED]
  envycontrol_boot.py →   _Bridges community 0 → community 19_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (33): _active_hook(), AmbiguousBootBackendError, _backend_from_name(), _BaseBackend, BoosterBackend, BootBackendResolver, BootRebuildCommandError, BootRebuildCoordinator (+25 more)

### Community 1 - "Community 1"
Cohesion: 0.17
Nodes (18): adapter(), assert_root(), CachedConfig, cleanup(), create_file(), delete_cache_file(), execute_boot_rebuild_plan(), generate_xrandr_script() (+10 more)

### Community 2 - "Community 2"
Cohesion: 0.17
Nodes (9): FakeBackend, FakeProbe, test_arch_booster_configuration_selects_booster_over_mkinitcpio_default(), test_arch_dracut_configuration_beats_mkinitcpio_default(), test_arch_mkinitcpio_active_hook_selects_mkinitcpio(), test_default_resolver_preserves_existing_distribution_backends(), test_equal_authoritative_candidates_are_rejected_as_ambiguous(), test_no_detected_backend_is_an_explicit_error() (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.2
Nodes (8): FakeProbe, kinds(), test_arch_active_mkinitcpio_hook_is_strong_evidence(), test_arch_dracut_active_with_mkinitcpio_still_installed_detects_dracut(), test_booster_configuration_outweighs_binary_presence(), test_dracut_binary_without_configuration_is_only_weak_evidence(), test_empty_dracut_override_disables_packaged_dracut_hook(), test_endeavouros_dracut_rebuild_preserves_native_rebuild_command()

### Community 4 - "Community 4"
Cohesion: 0.18
Nodes (8): _install_fake_cached_config(), test_main_cache_create_checks_root_and_dispatches(), test_main_cache_delete_checks_root_and_dispatches(), test_main_reset_preflight_failure_happens_before_cache_adapter(), test_main_reset_preflights_before_cache_adapter_and_reuses_plan(), test_main_reset_sddm_dispatches_inside_cache_adapter(), test_main_switch_preflights_before_cache_adapter(), test_main_switch_reports_ambiguous_preflight_before_cache_adapter()

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (5): BootArtifactStrategy, CommandRunner, InitramfsBackend, SystemProbe, Protocol

### Community 6 - "Community 6"
Cohesion: 0.28
Nodes (11): _configure_cache(), test_adapter_uses_existing_cache_for_detection(), test_cache_creation_requires_hybrid_mode(), test_create_cache_writes_pci_bus_json(), test_delete_cache_removes_file_and_cache_directories(), test_hybrid_adapter_refreshes_cache(), test_read_cache_restores_cached_bus(), test_read_missing_cache_in_hybrid_detects_bus() (+3 more)

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (5): FakeProbe, test_explicit_kernel_install_pipeline_runs_once_without_duplicate_ukify(), test_kernel_install_config_parses_explicit_generators_and_comments(), test_missing_kernel_install_config_returns_empty_config(), test_unsupported_explicit_kernel_install_generator_fails_closed()

### Community 8 - "Community 8"
Cohesion: 0.22
Nodes (5): FakeProbe, test_known_dracut_limine_hook_is_treated_as_native_and_not_duplicated(), test_known_mkinitcpio_limine_hook_is_treated_as_native_and_not_duplicated(), test_manual_limine_configuration_without_known_native_hook_fails_preflight(), test_no_limine_configuration_requires_no_integration_stage()

### Community 10 - "Community 10"
Cohesion: 0.27
Nodes (10): The shell of the workflow step that rewrites the version, verbatim., Running the workflow's own shell must leave both files, and the CLI, on the tag., flake.nix repeats the version, so a bump that misses it ships a mislabelled pack, _stamp_script(), test_nix_package_version_matches_the_cli_version(), test_release_workflow_can_write_releases(), test_release_workflow_triggers_only_on_semver_tags(), test_release_workflow_version_rewrite_matches_the_real_version_line() (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.44
Nodes (8): _run_guard_function(), test_executable_guard_rejects_attempted_path_or_detector_override(), test_vm_guard_accepts_all_three_independent_gates(), test_vm_guard_refuses_ambiguous_virtualization_result(), test_vm_guard_refuses_bare_metal_result(), test_vm_guard_refuses_missing_opt_in(), test_vm_guard_refuses_missing_sentinel(), _write_detector()

### Community 13 - "Community 13"
Cohesion: 0.24
Nodes (3): NullProbe, test_backend_commands_preserve_supported_rebuild_contracts(), test_setup_packages_boot_runtime_module()

### Community 14 - "Community 14"
Cohesion: 0.31
Nodes (4): RecordingRunner, test_inhibit_wraps_only_an_existing_valid_stage(), test_nonzero_stage_result_raises_domain_error(), test_plan_executes_direct_command_without_inhibit()

### Community 17 - "Community 17"
Cohesion: 0.54
Nodes (6): _fake_boot_plan(), _fake_run_recorder(), test_hybrid_mode_can_generate_nvidia_current_config(), test_hybrid_mode_with_rtd3_writes_power_management_rules(), test_integrated_mode_records_expected_side_effects(), test_nvidia_mode_writes_intel_lightdm_and_optional_settings()

### Community 18 - "Community 18"
Cohesion: 0.52
Nodes (6): _run_checker(), test_checker_derives_survivors_when_export_omits_field(), test_checker_fails_below_threshold(), test_checker_passes_at_sixty_percent_excluding_timeouts(), test_checker_rejects_blocking_threshold_below_sixty(), test_checker_requires_real_mutants()

### Community 19 - "Community 19"
Cohesion: 0.29
Nodes (3): RuntimeError, Raised when a normal test tries to reach a real machine-global boundary., UnsafeHostMutation

### Community 23 - "Community 23"
Cohesion: 0.83
Nodes (3): load_stats(), main(), _non_negative_int()

## Knowledge Gaps
- **5 isolated node(s):** `Adapter for config from CACHE_FILE_PATH`, `Raised when a normal test tries to reach a real machine-global boundary.`, `The shell of the workflow step that rewrites the version, verbatim.`, `Running the workflow's own shell must leave both files, and the CLI, on the tag.`, `flake.nix repeats the version, so a bump that misses it ships a mislabelled pack`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BootRebuildError` connect `Community 0` to `Community 19`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Why does `SystemProbe` connect `Community 5` to `Community 0`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **What connects `Adapter for config from CACHE_FILE_PATH`, `Raised when a normal test tries to reach a real machine-global boundary.`, `The shell of the workflow step that rewrites the version, verbatim.` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._