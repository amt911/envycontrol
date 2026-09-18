# Graph Report - envycontrol  (2026-09-18)

## Corpus Check
- 82 files · ~268,144 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1914 nodes · 10328 edges · 33 communities detected
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
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]

## God Nodes (most connected - your core abstractions)
1. `create_file()` - 505 edges
2. `execute_boot_rebuild_plan()` - 479 edges
3. `resolve_boot_rebuild_plan()` - 476 edges
4. `cleanup()` - 468 edges
5. `CachedConfig` - 376 edges
6. `exists()` - 372 edges
7. `command_exists()` - 368 edges
8. `_evidence()` - 316 edges
9. `graphics_mode_switcher()` - 312 edges
10. `create_cache_file()` - 309 edges

## Surprising Connections (you probably didn't know these)
- `test_release_workflow_version_rewrite_matches_the_real_version_line()` --calls--> `_workflow_text()`  [EXTRACTED]
  tests/test_release_workflow.py → mutants/tests/test_release_workflow.py
- `The shell of the workflow step that rewrites the version, verbatim.` --rationale_for--> `_stamp_script()`  [EXTRACTED]
  tests/test_release_workflow.py → mutants/tests/test_release_workflow.py
- `Running the workflow's own shell must leave both files, and the CLI, on the tag.` --rationale_for--> `test_stamping_a_tag_updates_every_declared_version()`  [EXTRACTED]
  tests/test_release_workflow.py → mutants/tests/test_release_workflow.py
- `flake.nix repeats the version, so a bump that misses it ships a mislabelled pack` --rationale_for--> `test_nix_package_version_matches_the_cli_version()`  [EXTRACTED]
  tests/test_release_workflow.py → mutants/tests/test_release_workflow.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.02
Nodes (59): _active_hook(), AmbiguousBootBackendError, _BaseBackend, BoosterBackend, BootBackendResolver, BootRebuildError, command_exists(), DetectionEvidence (+51 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (313): adapter(), assert_root(), CachedConfig, create_cache_file(), delete_cache_file(), get_current_mode(), graphics_mode_switcher(), main() (+305 more)

### Community 2 - "Community 2"
Cohesion: 0.01
Nodes (69): get_amd_igpu_name(), __init__(), rebuild_initramfs(), x_cleanup__mutmut_1(), x_cleanup__mutmut_10(), x_cleanup__mutmut_11(), x_cleanup__mutmut_12(), x_cleanup__mutmut_13() (+61 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (168): cleanup(), create_file(), execute_boot_rebuild_plan(), generate_xrandr_script(), get_display_manager(), get_igpu_vendor(), x_graphics_mode_switcher__mutmut_1(), x_graphics_mode_switcher__mutmut_10() (+160 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (16): _backend_from_name(), BootRebuildCommandError, BootRebuildCoordinator, BootRebuildPlan, BootStage, build_command(), CommandResult, detect() (+8 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (29): default_backend_resolver(), default_boot_rebuild_coordinator(), is_file(), is_masked(), KernelInstallConfig, KernelInstallStrategy, LimineIntegration, LocalSystemProbe (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (49): _active_hook(), AmbiguousBootBackendError, _backend_from_name(), _BaseBackend, BoosterBackend, BootArtifactStrategy, BootBackendResolver, BootRebuildCommandError (+41 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (4): create_cache_obj(), is_hybrid(), read_cache_file(), write_cache_file()

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (18): adapter(), assert_root(), CachedConfig, cleanup(), create_file(), delete_cache_file(), execute_boot_rebuild_plan(), generate_xrandr_script() (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.2
Nodes (9): FakeBackend, FakeProbe, test_arch_booster_configuration_selects_booster_over_mkinitcpio_default(), test_arch_dracut_configuration_beats_mkinitcpio_default(), test_arch_mkinitcpio_active_hook_selects_mkinitcpio(), test_default_resolver_preserves_existing_distribution_backends(), test_equal_authoritative_candidates_are_rejected_as_ambiguous(), test_no_detected_backend_is_an_explicit_error() (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.27
Nodes (15): _install_fake_cached_config(), test_assert_root_rejects_non_root(), test_cache_query_dispatches_without_root(), test_help_is_safe_and_successful(), test_invalid_switch_is_rejected_by_argparse(), test_main_cache_create_checks_root_and_dispatches(), test_main_cache_delete_checks_root_and_dispatches(), test_main_reset_preflight_failure_happens_before_cache_adapter() (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.24
Nodes (9): FakeProbe, kinds(), test_arch_active_mkinitcpio_hook_is_strong_evidence(), test_arch_dracut_active_with_mkinitcpio_still_installed_detects_dracut(), test_booster_configuration_outweighs_binary_presence(), test_dracut_binary_without_configuration_is_only_weak_evidence(), test_empty_dracut_override_disables_packaged_dracut_hook(), test_endeavouros_dracut_rebuild_preserves_native_rebuild_command() (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.23
Nodes (13): The shell of the workflow step that rewrites the version, verbatim., The shell of the workflow step that rewrites the version, verbatim., Running the workflow's own shell must move every declared version onto the tag., Running the workflow's own shell must leave both files, and the CLI, on the tag., flake.nix repeats the version, so a bump that misses it ships a mislabelled pack, flake.nix repeats the version, so a bump that misses it ships a mislabelled pack, _stamp_script(), test_nix_package_version_matches_the_cli_version() (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.37
Nodes (12): _configure_cache(), test_adapter_uses_existing_cache_for_detection(), test_cache_creation_requires_hybrid_mode(), test_create_cache_writes_pci_bus_json(), test_create_file_can_mark_temporary_script_executable(), test_delete_cache_removes_file_and_cache_directories(), test_hybrid_adapter_refreshes_cache(), test_read_cache_restores_cached_bus() (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.24
Nodes (5): FakeProbe, test_explicit_kernel_install_pipeline_runs_once_without_duplicate_ukify(), test_kernel_install_config_parses_explicit_generators_and_comments(), test_missing_kernel_install_config_returns_empty_config(), test_unsupported_explicit_kernel_install_generator_fails_closed()

### Community 15 - "Community 15"
Cohesion: 0.24
Nodes (5): FakeProbe, test_known_dracut_limine_hook_is_treated_as_native_and_not_duplicated(), test_known_mkinitcpio_limine_hook_is_treated_as_native_and_not_duplicated(), test_manual_limine_configuration_without_known_native_hook_fails_preflight(), test_no_limine_configuration_requires_no_integration_stage()

### Community 16 - "Community 16"
Cohesion: 0.3
Nodes (10): test_mutation_runner_preserves_python_interpreter_across_systemd_boundary(), test_mutation_runner_resolves_mutmut_before_sudo_systemd_boundary(), test_mutation_runner_restores_ci_sandbox_ownership_before_export(), test_pr_verifier_exists_and_keeps_destructive_vm_verification_opt_in(), test_safe_smoke_script_passes_without_privileged_operations(), test_system_vm_guard_runs_before_mutating_commands(), test_system_vm_script_has_no_host_force_escape_hatch(), test_system_vm_script_refuses_without_explicit_vm_opt_in() (+2 more)

### Community 17 - "Community 17"
Cohesion: 0.33
Nodes (9): test_amd_provider_name_is_read_from_xrandr(), test_current_mode_is_inferred_from_marker_files(), test_display_manager_is_parsed_from_execstart(), test_igpu_vendor_detection(), test_missing_display_manager_returns_none(), test_missing_nvidia_gpu_exits_with_guidance(), test_missing_xrandr_returns_none(), test_nvidia_pci_bus_is_converted_to_xorg_decimal() (+1 more)

### Community 18 - "Community 18"
Cohesion: 0.53
Nodes (9): _run_guard_function(), test_executable_guard_rejects_attempted_path_or_detector_override(), test_guard_script_exists_before_any_system_verifier_is_added(), test_vm_guard_accepts_all_three_independent_gates(), test_vm_guard_refuses_ambiguous_virtualization_result(), test_vm_guard_refuses_bare_metal_result(), test_vm_guard_refuses_missing_opt_in(), test_vm_guard_refuses_missing_sentinel() (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.27
Nodes (4): NullProbe, test_backend_commands_preserve_supported_rebuild_contracts(), test_backend_names_are_stable_and_unique(), test_setup_packages_boot_runtime_module()

### Community 20 - "Community 20"
Cohesion: 0.38
Nodes (6): RecordingRunner, test_boot_rebuild_plan_is_immutable(), test_boot_stage_rejects_empty_command(), test_inhibit_wraps_only_an_existing_valid_stage(), test_nonzero_stage_result_raises_domain_error(), test_plan_executes_direct_command_without_inhibit()

### Community 21 - "Community 21"
Cohesion: 0.39
Nodes (7): test_amd_xorg_template_embeds_pci_bus(), test_amd_xrandr_script_falls_back_to_modesetting(), test_amd_xrandr_script_uses_detected_provider(), test_intel_xorg_template_embeds_pci_bus(), test_intel_xrandr_script_uses_modesetting_provider(), test_modeset_rtd3_templates_preserve_requested_value(), test_unknown_igpu_falls_back_to_modesetting()

### Community 22 - "Community 22"
Cohesion: 0.39
Nodes (7): test_mode_switch_can_replace_dangerous_boundaries_with_fakes(), test_new_boot_tool_execution_is_blocked_even_by_absolute_path(), test_new_boot_tools_are_classified_as_dangerous_before_execution(), test_real_etc_write_is_blocked(), test_real_lspci_is_blocked(), test_real_systemctl_is_blocked(), test_tmp_path_write_is_allowed()

### Community 23 - "Community 23"
Cohesion: 0.61
Nodes (7): _fake_boot_plan(), _fake_run_recorder(), test_cleanup_removes_only_redirected_files_and_restores_sddm_backup(), test_hybrid_mode_can_generate_nvidia_current_config(), test_hybrid_mode_with_rtd3_writes_power_management_rules(), test_integrated_mode_records_expected_side_effects(), test_nvidia_mode_writes_intel_lightdm_and_optional_settings()

### Community 24 - "Community 24"
Cohesion: 0.61
Nodes (6): _run_checker(), test_checker_derives_survivors_when_export_omits_field(), test_checker_fails_below_threshold(), test_checker_passes_at_sixty_percent_excluding_timeouts(), test_checker_rejects_blocking_threshold_below_sixty(), test_checker_requires_real_mutants()

### Community 25 - "Community 25"
Cohesion: 0.48
Nodes (5): test_boot_module_exposes_domain_boundaries(), test_detection_evidence_is_immutable(), test_detection_result_reports_strongest_evidence(), test_local_probe_detects_hook_masked_to_dev_null(), test_local_probe_reads_text_and_detects_commands()

### Community 26 - "Community 26"
Cohesion: 0.48
Nodes (5): test_dependabot_uses_monthly_python_and_actions_updates(), test_local_quality_scripts_cover_both_runtime_modules_and_block_mutation(), test_mutation_workflow_is_blocking_and_covers_both_runtime_modules(), test_precommit_covers_whitespace_yaml_markdown_and_project_gates(), test_security_workflow_is_blocking_and_checks_installed_environment()

### Community 27 - "Community 27"
Cohesion: 0.53
Nodes (4): test_rebuild_initramfs_executes_one_resolved_plan(), test_rebuild_initramfs_propagates_preflight_failure_before_command_execution(), test_rebuild_initramfs_propagates_stage_failure(), test_rebuild_initramfs_uses_verbose_runner_when_debugging()

### Community 28 - "Community 28"
Cohesion: 0.8
Nodes (3): load_stats(), main(), _non_negative_int()

### Community 29 - "Community 29"
Cohesion: 0.6
Nodes (3): test_arch_dracut_hybrid_never_runs_mkinitcpio(), test_one_preflight_plan_is_reused_for_hybrid_mode(), test_preflight_failure_has_zero_system_side_effects()

### Community 30 - "Community 30"
Cohesion: 0.67
Nodes (2): test_mode_inference_always_returns_supported_mode(), test_valid_hex_pci_components_round_trip_to_decimal()

### Community 31 - "Community 31"
Cohesion: 0.67
Nodes (2): test_claude_md_is_a_shim_that_imports_agents_md(), test_legacy_template_directory_is_removed_after_migration()

### Community 32 - "Community 32"
Cohesion: 0.67
Nodes (1): test_verbose_switch_reports_selected_boot_backend_and_evidence()

## Knowledge Gaps
- **9 isolated node(s):** `Adapter for config from CACHE_FILE_PATH`, `Raised when a normal test tries to reach a real machine-global boundary.`, `The shell of the workflow step that rewrites the version, verbatim.`, `Running the workflow's own shell must move every declared version onto the tag.`, `flake.nix repeats the version, so a bump that misses it ships a mislabelled pack` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 30`** (4 nodes): `test_properties.py`, `test_properties.py`, `test_mode_inference_always_returns_supported_mode()`, `test_valid_hex_pci_components_round_trip_to_decimal()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (4 nodes): `test_agent_docs.py`, `test_agent_docs.py`, `test_claude_md_is_a_shim_that_imports_agents_md()`, `test_legacy_template_directory_is_removed_after_migration()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (3 nodes): `test_boot_verbose.py`, `test_boot_verbose.py`, `test_verbose_switch_reports_selected_boot_backend_and_evidence()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CachedConfig` connect `Community 1` to `Community 2`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `exists()` connect `Community 0` to `Community 4`, `Community 5`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `command_exists()` connect `Community 0` to `Community 4`, `Community 5`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `Adapter for config from CACHE_FILE_PATH`, `Raised when a normal test tries to reach a real machine-global boundary.`, `The shell of the workflow step that rewrites the version, verbatim.` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.02 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._
