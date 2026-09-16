from pathlib import Path


path = Path("envycontrol.py")
text = path.read_text(encoding="utf-8")

old_signature = (
    "def graphics_mode_switcher(graphics_mode, user_display_manager, enable_force_comp, "
    "coolbits_value, rtd3_value, use_nvidia_current):\n"
    "    boot_plan = resolve_boot_rebuild_plan()\n"
)
new_signature = (
    "def graphics_mode_switcher(graphics_mode, user_display_manager, enable_force_comp, "
    "coolbits_value, rtd3_value, use_nvidia_current, boot_plan=None):\n"
    "    if boot_plan is None:\n"
    "        boot_plan = resolve_boot_rebuild_plan()\n"
)
assert old_signature in text
text = text.replace(old_signature, new_signature, 1)

old_execute = (
    "    boot_plan.execute(\n"
    "        boot.SubprocessCommandRunner(),\n"
    "        verbose=logging.getLogger().level == logging.DEBUG,\n"
    "    )\n"
)
assert old_execute in text
text = text.replace(old_execute, "    execute_boot_rebuild_plan(boot_plan)\n", 1)

old_helpers = (
    "def resolve_boot_rebuild_plan():\n"
    "    probe = boot.LocalSystemProbe()\n"
    "    return boot.default_boot_rebuild_coordinator().resolve(probe)\n\n\n\n"
    "def rebuild_initramfs():\n"
    "    plan = resolve_boot_rebuild_plan()\n"
    "    print('Rebuilding boot artifacts...')\n"
    "    plan.execute(\n"
    "        boot.SubprocessCommandRunner(),\n"
    "        verbose=logging.getLogger().level == logging.DEBUG,\n"
    "    )\n"
    "    print('Successfully rebuilt boot artifacts!')\n"
)
new_helpers = (
    "def resolve_boot_rebuild_plan():\n"
    "    probe = boot.LocalSystemProbe()\n"
    "    return boot.default_boot_rebuild_coordinator().resolve(probe)\n\n\n"
    "def execute_boot_rebuild_plan(plan):\n"
    "    plan.execute(\n"
    "        boot.SubprocessCommandRunner(),\n"
    "        verbose=logging.getLogger().level == logging.DEBUG,\n"
    "    )\n\n\n"
    "def rebuild_initramfs():\n"
    "    plan = resolve_boot_rebuild_plan()\n"
    "    print('Rebuilding boot artifacts...')\n"
    "    execute_boot_rebuild_plan(plan)\n"
    "    print('Successfully rebuilt boot artifacts!')\n\n\n"
)
assert old_helpers in text
text = text.replace(old_helpers, new_helpers, 1)

old_main_lines = [
    "    if args.switch or args.reset_sddm or args.reset:",
    "        with CachedConfig(args).adapter():",
    "            if args.switch:",
    "                assert_root()",
    "                graphics_mode_switcher(",
    "                    args.switch, args.dm,",
    "                    args.force_comp, args.coolbits, args.rtd3, args.use_nvidia_current",
    "                )",
    "            elif args.reset_sddm:",
    "                assert_root()",
    "                create_file(SDDM_XSETUP_PATH, SDDM_XSETUP_CONTENT, True)",
    "                print('Operation completed successfully')",
    "            elif args.reset:",
    "                assert_root()",
    "                cleanup()",
    "                CachedConfig.delete_cache_file()",
    "                rebuild_initramfs()",
    "                print('Operation completed successfully')",
]
old_main = "\n".join(old_main_lines) + "\n"

new_main_lines = [
    "    boot_plan = None",
    "    if args.switch or args.reset:",
    "        assert_root()",
    "        try:",
    "            boot_plan = resolve_boot_rebuild_plan()",
    "        except (",
    "            boot.NoBootBackendFoundError,",
    "            boot.AmbiguousBootBackendError,",
    "            boot.UnsupportedBootIntegrationError,",
    "        ) as error:",
    "            logging.error(str(error))",
    "            print('No system files were modified.', file=sys.stderr)",
    "            raise SystemExit(1) from error",
    "",
    "    if args.switch or args.reset_sddm or args.reset:",
    "        with CachedConfig(args).adapter():",
    "            try:",
    "                if args.switch:",
    "                    graphics_mode_switcher(",
    "                        args.switch, args.dm,",
    "                        args.force_comp, args.coolbits, args.rtd3, args.use_nvidia_current,",
    "                        boot_plan=boot_plan,",
    "                    )",
    "                elif args.reset_sddm:",
    "                    assert_root()",
    "                    create_file(SDDM_XSETUP_PATH, SDDM_XSETUP_CONTENT, True)",
    "                    print('Operation completed successfully')",
    "                elif args.reset:",
    "                    cleanup()",
    "                    CachedConfig.delete_cache_file()",
    "                    execute_boot_rebuild_plan(boot_plan)",
    "                    print('Operation completed successfully')",
    "            except boot.BootRebuildCommandError as error:",
    "                logging.error(str(error))",
    "                print(",
    "                    'Boot artifact rebuild failed after system changes. '",
    "                    'Resolve the error before rebooting.',",
    "                    file=sys.stderr,",
    "                )",
    "                raise SystemExit(1) from error",
]
new_main = "\n".join(new_main_lines) + "\n"
assert old_main in text
text = text.replace(old_main, new_main, 1)

path.write_text(text, encoding="utf-8")
