# EnvyControl user stories

These stories describe existing user-visible journeys and provide acceptance criteria for regression tests. They are not a wishlist.

## US-01 — Inspect the active graphics mode

**As a** Linux user **I want** to query EnvyControl's inferred graphics mode **so that** I can see which managed configuration is active.

Acceptance criteria:

- `--query` does not require root.
- Output is exactly one supported mode: `integrated`, `hybrid`, or `nvidia`.
- Mode is inferred from the current marker-file rules documented in `docs/CLI_CONTRACT.md`.

## US-02 — Switch to integrated mode

**As a** laptop user prioritizing power saving **I want** to switch to integrated mode **so that** NVIDIA modules/devices are disabled by EnvyControl's managed configuration.

Acceptance criteria:

- The mutating flow requires root by contract.
- Previous managed configuration is cleaned.
- NVIDIA module blacklist and integrated udev rules are generated.
- `nvidia-persistenced.service` is disabled.
- The relevant initramfs command is requested and the user is told to reboot.
- Real acceptance verification runs only in a disposable VM.

## US-03 — Switch to hybrid mode

**As a** user needing on-demand NVIDIA capability **I want** hybrid mode **so that** modesetting and optional RTD3 power management are configured.

Acceptance criteria:

- Previous managed configuration is cleaned.
- `nvidia-persistenced.service` is enabled.
- Correct `nvidia` or `nvidia-current` modeset content is generated.
- RTD3 `0..3`, when requested, generates the matching module option and udev power-management rules.
- Initramfs rebuild is requested and reboot guidance is printed.
- Real acceptance verification runs only in a disposable VM.

## US-04 — Switch to NVIDIA mode

**As a** user needing the discrete GPU as primary **I want** NVIDIA mode **so that** Xorg and NVIDIA modesetting are configured for the detected hardware.

Acceptance criteria:

- NVIDIA PCI BusID and iGPU vendor are detected from controlled inputs in automated tests.
- Intel and AMD Xorg templates use the detected PCI BusID.
- ForceCompositionPipeline and Coolbits are included only when requested.
- SDDM and LightDM integration follow their current distinct paths.
- Initramfs rebuild is requested and reboot guidance is printed.
- Real acceptance verification runs only in a disposable VM.

## US-05 — Reset EnvyControl changes

**As a** user **I want** to reset EnvyControl-managed state **so that** generated graphics configuration is removed and any SDDM backup is restored.

Acceptance criteria:

- Managed files are removed according to `cleanup()`.
- An SDDM `.bak` is restored when present.
- Cache is deleted by reset flow.
- Initramfs rebuild is requested.
- Real acceptance verification runs only in a disposable VM.

## US-06 — Manage cached PCI information

**As a** user/system flow **I want** cached NVIDIA PCI information **so that** later mode changes can work when direct detection is unavailable outside hybrid mode.

Acceptance criteria:

- Cache creation is valid only while current mode is hybrid.
- Cache JSON stores `nvidia_gpu_pci_bus`.
- Cache query is read-only and does not require root.
- Cache deletion follows current file/directory removal semantics.
- Automated tests redirect the cache path to temporary storage; real cache mutation is VM-only.
