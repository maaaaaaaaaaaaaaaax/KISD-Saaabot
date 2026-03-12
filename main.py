"""
Test script for pi-printer module.

This demonstrates the new high-level API replacing direct escpos usage.
"""

from printer import Printer

def main():
    """Run basic printer test with new module."""
    with Printer() as p:
        # Initialize printer
        p.initialize()
        p.print_separator('a', 4)
        
        p.layout.spacer(10)
        
        p.print_separator('#')
        
        p.layout.spacer(10)
        
        p.print_separator()

if __name__ == "__main__":
    main()

