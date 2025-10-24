### design_analyzer

Analyze screenshots and design mockups to extract design specifications using vision AI.
Identifies colors, typography, spacing, layout structure, component hierarchy, and design patterns.

Args:
- image_path (required): Path to design screenshot or mockup (supports PNG, JPEG, GIF, WebP)

The tool uses vision model integration to analyze the image and extract:
- Color palette (hex codes for primary, secondary, accent, background, text colors)
- Typography (font families, sizes, weights for headings, body, UI elements)
- Spacing system (base unit, padding/margin values, container widths)
- Layout structure (grid system, alignment, sections)
- Component hierarchy (navigation, content sections, interactive elements)
- Design patterns (border radius, shadows, icon usage)

Returns structured design specifications in markdown format.

Usage example:

~~~json
{
    "thoughts": [
        "User provided a design screenshot",
        "I'll use the design analyzer to extract all design specifications",
        "This will give me color palette, typography, spacing, and layout details"
    ],
    "headline": "Analyzing design mockup with vision AI",
    "tool_name": "design_analyzer",
    "tool_args": {
        "image_path": "designs/homepage-mockup.png"
    }
}
~~~

Example output includes:
- Detailed color palette with hex codes
- Font specifications with pixel sizes and weights
- Spacing values and grid systems
- Component organization and hierarchy
- Border radius, shadow, and other design token values
