"""
Text formatting example for pi-printer module.

Demonstrates advanced text formatting with headings, bold, and alignment.
"""

from printer import Printer, ComplexTextSpan, ComplexTextBlockStyle

def main():
    with Printer() as p:
        p.initialize()
        
        # Heading levels
        p.print_heading("H1 Heading", level=1)
        p.print_heading("H2 Heading", level=2)
        p.print_heading("H3 Heading", level=3)
        p.feed(1)
        
        # Font styles using TextFormatter
        formatter = p.format_text("Bold Text").bold()
        p.print_formatted(formatter)
        p.feed(1)
        
        # Text alignment
        formatter = p.format_text("Left Aligned").align('left')
        p.print_formatted(formatter)
        p.feed(1)
        
        formatter = p.format_text("Center Aligned").align('center')
        p.print_formatted(formatter)
        p.feed(1)
        
        formatter = p.format_text("Right Aligned").align('right')
        p.print_formatted(formatter)
        p.feed(1)
        
        # Font families (TM-T88IV only has 'sans' and 'sans-b')
        formatter = p.format_text("Sans Serif Font (Font A)").font('sans')
        p.print_formatted(formatter)
        
        formatter = p.format_text("Sans B Font (Font B)").font('sans-b')
        p.print_formatted(formatter)
        p.feed(1)
        
        # Custom sizes
        formatter = p.format_text("2x Size").size(2)
        p.print_formatted(formatter)
        p.feed(1)
        
        formatter = p.format_text("3x Width, 1x Height").size(3, 1)
        p.print_formatted(formatter)
        p.feed(1)
        
        # Inverted text
        formatter = p.format_text("Inverted Text").invert()
        p.print_formatted(formatter)
        p.feed(1)
        
        # Separator
        p.print_separator('=')
        p.feed(1)
        
        # Two-column layouts
        p.print_text("Menu", style='h2')
        p.print_text("RESET")
        p.print_separator('-')
        p.print_two_columns("Espresso", "$2.50")
        p.print_two_columns("Cappuccino", "$3.50")
        p.print_two_columns("Latte", "$4.00")
        p.print_two_columns("Americano", "$3.00")
        p.print_separator('-')
        p.print_two_columns("Tax (10%):", "$1.30")
        p.print_two_columns("Total:", "$14.30")
        p.feed(1)        
        p.cut()

if __name__ == "__main__":
    main()
