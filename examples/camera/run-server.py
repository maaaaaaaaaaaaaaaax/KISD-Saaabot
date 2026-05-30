from pathlib import Path

from camera import GalleryServer

OUTPUT_DIR = Path("captures/camera_test")


def main():
    # ── Gallery ───────────────────────────────────────────────────────────────
    print("\n── Gallery Server ────────────────────────────────────")
    print("  Open the URL below in your browser on any device on the same network.")
    print("  Press Ctrl-C to stop.\n")
    GalleryServer(root=OUTPUT_DIR, port=8080).serve()


if __name__ == "__main__":
    main()
