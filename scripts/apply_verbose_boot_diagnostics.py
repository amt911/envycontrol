from pathlib import Path


path = Path("envycontrol.py")
text = path.read_text(encoding="utf-8")

old = """            boot_plan = resolve_boot_rebuild_plan()\n        except (\n"""
new = """            boot_plan = resolve_boot_rebuild_plan()\n            if args.verbose:\n                logging.debug(f\"Selected boot rebuild backend: {boot_plan.backend}\")\n                for diagnostic in boot_plan.diagnostics:\n                    logging.debug(f\"Boot preflight evidence: {diagnostic}\")\n        except (\n"""

if text.count(old) != 1:
    raise SystemExit(f"expected one preflight insertion point, found {text.count(old)}")

path.write_text(text.replace(old, new, 1), encoding="utf-8")
