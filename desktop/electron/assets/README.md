# Agent Zero Desktop Assets

This directory contains the application icons and other assets needed for building the desktop application.

## Icon Requirements

You need to create the following icon files:

### macOS
- **icon.icns**: macOS icon bundle (1024x1024 base size)

### Windows
- **icon.ico**: Windows icon file (256x256 recommended)

### Linux
- **icon.png**: PNG icon (512x512 or 1024x1024 recommended)

## Quick Icon Generation

### Option 1: Using an existing PNG (recommended)

If you have a 1024x1024 PNG file, you can generate all formats:

```bash
# Install icon generation tool
npm install -g electron-icon-maker

# Generate all icon formats from a single PNG
electron-icon-maker --input=source-icon.png --output=./
```

### Option 2: Using ImageMagick

```bash
# For macOS .icns (requires iconutil)
mkdir icon.iconset
sips -z 16 16     source-icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     source-icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     source-icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     source-icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   source-icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   source-icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   source-icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   source-icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   source-icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 source-icon.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset -o icon.icns

# For Windows .ico (requires ImageMagick)
convert source-icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico

# For Linux .png
cp source-icon.png icon.png
```

### Option 3: Manual creation

Create the icons manually using your preferred graphics editor:
- Adobe Illustrator
- Sketch
- Figma
- GIMP

Export to the required formats and place them in this directory.

## Placeholder Icons

For development/testing, you can create simple placeholder icons:

```bash
# Create a simple colored square (macOS)
# This creates temporary development icons
sips -z 512 512 /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns --out icon.png
```

## Design Guidelines

- Use a square canvas (1:1 aspect ratio)
- Keep important elements within the center 80% of the canvas
- Use a transparent background or solid color
- Avoid fine details that won't be visible at small sizes
- Test at multiple sizes (16x16, 32x32, 64x64, etc.)

## Next Steps

1. Create or obtain your source icon (preferably 1024x1024 PNG with transparent background)
2. Generate all required formats using one of the methods above
3. Place the generated files in this directory
4. Run `npm run build:mac` to build the macOS app with your icons
