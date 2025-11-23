# FairMind Brand Assets

This directory contains all official FairMind brand assets including logos, icons, and favicons.

## 📁 Directory Structure

```
assets/
├── logo/
│   ├── fairmind-icon.png          # Square logo icon (512×512)
│   └── fairmind-banner.png        # Horizontal banner with text
└── favicon/
    ├── favicon-16x16.png          # Browser tab icon (16×16)
    ├── favicon-32x32.png          # Browser tab icon (32×32)
    ├── favicon-48x48.png          # Browser tab icon (48×48)
    ├── apple-touch-icon.png       # iOS home screen icon (180×180)
    ├── android-chrome-192x192.png # Android icon (192×192)
    └── android-chrome-512x512.png # Android icon (512×512)
```

## 🎨 Logo Variations

### Icon Only (Square)
**File**: `logo/fairmind-icon.png`
- **Size**: 512×512 pixels
- **Format**: PNG with transparent background
- **Usage**: Favicons, app icons, social media profiles, small UI elements

### Horizontal Banner
**File**: `logo/fairmind-banner.png`
- **Format**: PNG with transparent background
- **Usage**: GitHub README, website headers, email signatures, documentation

**Components**:
- Orange circle logo (balance scales + lightning bolt)
- "FAIRMIND" text in bold black
- "BUILD FAIR & TRUSTWORTHY AI" tagline in orange

## 📐 Logo Symbolism

The FairMind logo combines two powerful symbols:

1. **Balance Scales** ⚖️ - Represents fairness, justice, and ethical AI
2. **Lightning Bolt** ⚡ - Represents speed, power, and AI technology

**Color**: Orange (#f97316) - Conveys energy, innovation, and trustworthiness

## 🎯 Usage Guidelines

### ✅ DO

- Use the logo on white, light gray, or dark backgrounds
- Maintain aspect ratio when scaling
- Ensure adequate padding around the logo
- Use the horizontal banner for wide spaces (headers, README)
- Use the icon for square spaces (favicons, app icons)

### ❌ DON'T

- Distort or stretch the logo
- Change the colors
- Add effects (shadows, gradients, etc.)
- Place on busy or low-contrast backgrounds
- Use low-resolution versions for large displays

## 📱 Platform-Specific Usage

### GitHub
- **README Header**: Use `fairmind-banner.png` (centered, max-width: 800px)
- **Social Preview**: Use `fairmind-banner.png` (1200×630px recommended)
- **Repository Icon**: Use `fairmind-icon.png`

### Website
- **Navigation**: Use `fairmind-icon.png` (32×32 or 48×48)
- **Hero Section**: Use `fairmind-banner.png`
- **Favicon**: Use generated favicon files

### Frontend Application
- **Favicon**: `/public/favicon.ico` (32×32)
- **Apple Touch Icon**: `/public/apple-touch-icon.png` (180×180)
- **Logo**: `/public/logo.png` (512×512)
- **Manifest**: `/public/manifest.json`

### Documentation
- **Headers**: Use `fairmind-banner.png`
- **Inline References**: Use `fairmind-icon.png` (small size)

## 🌐 Favicon Implementation

### HTML Meta Tags

```html
<!-- Favicon -->
<link rel="icon" type="image/png" sizes="32x32" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="512x512" href="/logo.png">

<!-- Apple Touch Icon -->
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">

<!-- Web App Manifest -->
<link rel="manifest" href="/manifest.json">
```

### Next.js Metadata (App Router)

```typescript
export const metadata: Metadata = {
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "32x32", type: "image/png" },
      { url: "/logo.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
}
```

## 📊 Background Compatibility

The logo has been tested and works well on:

- ✅ White backgrounds
- ✅ Light gray backgrounds (#f8fafc, #f1f5f9)
- ✅ Dark backgrounds (#1e293b, #0f172a)
- ✅ Black backgrounds (#000000)
- ✅ Gradient backgrounds
- ✅ Pattern backgrounds

**Note**: The horizontal banner has black text. For very dark backgrounds, consider using the icon only or creating a light-text variant.

## 🎨 Color Palette

### Primary Brand Colors

```css
/* Orange (Primary) */
--brand-orange: #f97316;
--brand-orange-light: #fb923c;
--brand-orange-dark: #ea580c;

/* Black (Text) */
--brand-black: #000000;
--brand-gray-dark: #1e293b;

/* White (Background) */
--brand-white: #ffffff;
--brand-gray-light: #f8fafc;
```

## 📏 Sizing Recommendations

### Favicon Sizes
- **16×16**: Browser tabs (minimum)
- **32×32**: Browser tabs (standard)
- **48×48**: Browser tabs (high-DPI)
- **180×180**: Apple touch icon
- **192×192**: Android Chrome
- **512×512**: Android Chrome, PWA

### Logo Sizes
- **32×32**: Small UI elements, navigation
- **64×64**: Medium UI elements
- **128×128**: Large UI elements
- **256×256**: Hero sections (small)
- **512×512**: Hero sections (large)

### Banner Sizes
- **600px width**: Email signatures
- **800px width**: GitHub README (recommended)
- **1200px width**: Website headers
- **2400×600**: High-resolution displays

## 🔄 Generating Custom Sizes

Use `sips` (macOS) or ImageMagick to generate custom sizes:

```bash
# Using sips (macOS)
sips -z 64 64 assets/logo/fairmind-icon.png --out output-64x64.png

# Using ImageMagick
convert assets/logo/fairmind-icon.png -resize 64x64 output-64x64.png
```

## 📝 Markdown Usage

### GitHub README

```markdown
<div align="center">
  <img src="assets/logo/fairmind-banner.png" alt="FairMind - Build Fair & Trustworthy AI" width="800">
</div>
```

### Documentation

```markdown
![FairMind Logo](assets/logo/fairmind-icon.png)
```

## 🌍 Social Media Specifications

### Twitter/X
- **Profile Picture**: 400×400 (use `fairmind-icon.png`)
- **Header Image**: 1500×500 (create custom banner)

### LinkedIn
- **Logo**: 300×300 (use `fairmind-icon.png`)
- **Cover Image**: 1584×396 (create custom banner)

### Facebook
- **Profile Picture**: 180×180 (use `fairmind-icon.png`)
- **Cover Photo**: 820×312 (create custom banner)

### Open Graph (Social Sharing)
- **Image Size**: 1200×630
- **Use**: `fairmind-banner.png` or create custom OG image

## 📄 File Formats

### Current Formats
- **PNG**: All current assets (with transparency)

### Recommended Additional Formats
- **SVG**: Vector format for perfect scaling (recommended for future)
- **ICO**: Multi-size favicon file (optional)
- **WebP**: Modern web format (optional, for web optimization)

## 🔗 Quick Links

- **Preview Page**: `/logo-banner-preview.html`
- **GitHub Repository**: [github.com/adhit-r/fairmind](https://github.com/adhit-r/fairmind)
- **Website**: [fairmind.xyz](https://fairmind.xyz)

## 📞 Contact

For brand asset questions or custom variations:
- **Repository**: [github.com/adhit-r/fairmind](https://github.com/adhit-r/fairmind)
- **Issues**: [github.com/adhit-r/fairmind/issues](https://github.com/adhit-r/fairmind/issues)

---

**Last Updated**: November 2025  
**Version**: 1.0.0

---

**FairMind - Build Fair & Trustworthy AI** 🎯⚖️⚡
