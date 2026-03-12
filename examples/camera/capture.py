from pathlib import Path

from camera import Camera, CameraConfig, GalleryServer


OUTPUT_DIR = Path("captures/camera_test")


def test_device_discovery():
    print("── Device Discovery ──────────────────────────────────")
    devices = Camera.list_devices()
    if devices:
        print(f"  Found camera(s) at device index: {devices}")
    else:
        print("  No cameras found. Make sure your USB camera is connected.")
    return devices


def test_single_snap(cam: Camera):
    print("\n── Single Snap ───────────────────────────────────────")
    path = cam.snap_to_dir(OUTPUT_DIR, stem="snap")
    print(f"  Saved: {path}")
    info = cam.info()
    print(f"  Resolution: {info['width']} × {info['height']}  FPS: {info['fps']:.1f}")


def test_burst(cam: Camera):
    print("\n── Burst (5 frames, 0.3 s apart) ────────────────────")
    paths = cam.burst(5, interval=0.3, directory=OUTPUT_DIR, stem="burst")
    for p in paths:
        print(f"  Saved: {p}")


def test_video(cam: Camera, duration: float = 5.0):
    print(f"\n── Video Recording ({duration:.0f} s) ──────────────────────")
    path = cam.record_for(duration, OUTPUT_DIR / "test_clip.mp4")
    print(f"  Saved: {path}")


def main():
    print("Pi-Printer · Camera Basic Test")
    print("=" * 52)

    devices = test_device_discovery()
    if not devices:
        return

    device_index = devices[0]
    config = CameraConfig(device_index=device_index, output_dir=OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with Camera(config) as cam:
        test_single_snap(cam)
        test_burst(cam)
        test_video(cam, duration=5.0)

    print("\n  Done. Files written to:", OUTPUT_DIR.resolve())

    # ── Gallery ───────────────────────────────────────────────────────────────
    print("\n── Gallery Server ────────────────────────────────────")
    print("  Open the URL below in your browser on any device on the same network.")
    print("  Press Ctrl-C to stop.\n")
    GalleryServer(root=OUTPUT_DIR, port=8080).serve()


if __name__ == "__main__":
    main()
