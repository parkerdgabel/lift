#!/bin/bash
# Generate different formats of the man page
# Requires: groff, ps2pdf (optional for PDF)

set -e

MAN_FILE="man/lift.1"
OUTPUT_DIR="man/generated"

if [ ! -f "$MAN_FILE" ]; then
    echo "Error: Man page file not found: $MAN_FILE"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Generating man page formats..."

# Generate ASCII text
echo "→ ASCII text (lift.1.txt)"
groff -man -Tascii "$MAN_FILE" > "$OUTPUT_DIR/lift.1.txt"

# Generate HTML
echo "→ HTML (lift.1.html)"
groff -man -Thtml "$MAN_FILE" > "$OUTPUT_DIR/lift.1.html"

# Generate PostScript
echo "→ PostScript (lift.1.ps)"
groff -man -Tps "$MAN_FILE" > "$OUTPUT_DIR/lift.1.ps"

# Generate PDF (if ps2pdf is available)
if command -v ps2pdf &> /dev/null; then
    echo "→ PDF (lift.1.pdf)"
    ps2pdf "$OUTPUT_DIR/lift.1.ps" "$OUTPUT_DIR/lift.1.pdf"
    rm "$OUTPUT_DIR/lift.1.ps"  # Clean up intermediate file
else
    echo "⚠ ps2pdf not found, skipping PDF generation"
fi

echo ""
echo "✓ Generated formats saved to: $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR/"
