"""
Print a pasted or piped string on the thermal printer.

Usage:
    # Interactive — paste text, then press Ctrl+D to send:
    python print_input.py

    # Pipe a string directly:
    echo "Hello, world!" | python print_input.py

    # Pass as a command-line argument:
    python print_input.py "Hello, world!"
"""
import sys
from printer import Printer


def main():
    # 1. Command-line argument takes priority
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])

    # 2. Otherwise read from stdin (paste / pipe)
    else:
        print("Paste your text, then press Ctrl+D (Linux/Mac) or Ctrl+Z Enter (Windows):",
              file=sys.stderr)
        text = sys.stdin.read()

    text = text.strip()

    if not text:
        print("No input received — nothing to print.", file=sys.stderr)
        sys.exit(1)

    with Printer() as p:
        p.initialize()
        p.print_text(text)
        p.feed(2)
        p.cut()

    print("Printed successfully.", file=sys.stderr)


if __name__ == "__main__":
    main()
