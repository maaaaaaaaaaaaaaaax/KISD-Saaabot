"""
Basic usage example for pi-printer module.

Demonstrates simple text and image printing.
"""

from printer import Printer

def main():
    # Create printer instance and connect
    with Printer() as p:
        # Initialize printer
        p.initialize()
        
        # Print simple text
        p.print_text("Hello from pi-printer!")
        p.feed(1)
        
        # Print with different text styles
        p.print_heading("This is a Heading", level=1)
        p.print_text("This is normal text.")
        p.print_text("This is h2 heading", style='h2')
        p.feed(2)
        
        # Print separator
        p.print_separator('=')
        p.feed(1)
        
        # Print image (if available)
        try:
            p.print_image("examples/printer/assets/gamba.png", alignment='center')
            p.feed(1)
        except FileNotFoundError:
            p.print_text("(Image not found: examples/printer/assets/gamba.png)")
            p.feed(1)
        
        # Print two-column layout
        p.print_two_columns("Item:", "Price")
        p.print_two_columns("Coffee", "$3.50")
        p.print_two_columns("Tea", "$2.50")
        p.print_separator('-')
        p.print_two_columns("Total:", "$6.00")
        p.feed(2)
        
        # Cut paper
        p.cut()

if __name__ == "__main__":
    main()
