---
description: Generate images, videos, and graphics using AI (DALL-E, Midjourney, Stable Diffusion)
argument-hint: [--type <image|video|graphic>] [--style <photorealistic|artistic|cartoon>] [--prompt <description>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Media Generation Command

AI-powered image and video generation with style presets and prompt optimization.

## ROI Analysis: $65,000/year

**Value Breakdown:**

- **Stock Media Replacement**: $500-2,000/month → $15,000/year saved
- **Rapid Prototyping**: Create 50+ concept variations in minutes vs days
- **Custom Asset Creation**: Eliminates designer costs ($75-150/hour)
- **Marketing Materials**: Generate unlimited social graphics, ads, banners
- **Video Content**: Create B-roll, animations, product demos

**Time Savings:** 4-8 hours per design project → 5-10 minutes automated
**Quality Improvement:** Professional-grade outputs, consistent brand aesthetics
**Business Impact:** Faster campaign launches, unlimited creative testing

---

## Overview

The Media Generation Command creates professional images, videos, and graphics using state-of-the-art AI generation models. It handles prompt optimization, style application, batch generation, and quality enhancement to produce production-ready assets.

**Key Features:**

- Multi-model support (DALL-E, Midjourney, Stable Diffusion, RunwayML)
- Advanced prompt engineering and optimization
- Style presets and brand consistency
- Batch generation with variations
- Upscaling and enhancement
- Format conversion and optimization
- Commercial licensing guidance
- Version control and iteration tracking

**Supported Media Types:**

- **Images**: Photos, illustrations, graphics, textures, backgrounds
- **Videos**: Short clips, B-roll, animations, transitions, effects
- **Graphics**: Logos, icons, infographics, social media templates
- **3D Assets**: Product renders, environments, characters

---

## Implementation

### Step 1: Define Generation Requirements

Collect specifications for media asset:

**Core Requirements:**

- **Media Type**: Image, video, graphic, 3D render
- **Use Case**: Marketing, social media, website, product, editorial
- **Dimensions**: Resolution, aspect ratio, orientation
- **Style**: Photorealistic, artistic, cartoon, minimalist, vintage
- **Subject**: Primary focus and key elements
- **Mood/Tone**: Professional, playful, serious, energetic, calm

**Advanced Specifications:**

- Color palette preferences
- Composition requirements
- Lighting conditions
- Perspective and angle
- Background type
- Text integration needs
- Brand guidelines compliance

### Step 2: Optimize Generation Prompt

Apply prompt engineering best practices:

**Prompt Structure:**

```
[SUBJECT] + [STYLE MODIFIERS] + [COMPOSITION] + [LIGHTING] + [QUALITY TERMS]

Example: "Professional woman presenting in modern office, photorealistic style,
medium shot with shallow depth of field, natural window lighting from left,
high detail, sharp focus, 8K resolution"
```

**Quality Enhancers:**

- "highly detailed", "sharp focus", "professional photography"
- "8K resolution", "octane render", "unreal engine"
- "award-winning", "trending on artstation"
- "cinematic lighting", "studio quality"

**Style Keywords:**

- Photorealistic: "photograph", "DSLR", "35mm", "bokeh"
- Artistic: "oil painting", "watercolor", "digital art", "concept art"
- Cartoon: "3D render", "Pixar style", "anime", "vector illustration"
- Vintage: "1970s photograph", "film grain", "faded colors", "retro"

**Negative Prompts:**
Elements to avoid: "blurry", "low quality", "distorted", "artifacts", "watermark"

### Step 3: Select Generation Model

Choose optimal AI model for requirements:

**DALL-E 3 (OpenAI):**

- Best for: Photorealistic images, complex compositions, text rendering
- Strengths: Understands natural language, coherent scenes, good with people
- Limitations: Limited style control, no fine-tuning
- Resolution: Up to 1024x1024 or 1792x1024
- Speed: ~10-30 seconds per image
- Cost: $0.04-0.08 per image

**Midjourney:**

- Best for: Artistic images, concept art, creative designs
- Strengths: Exceptional aesthetics, style variety, artistic interpretation
- Limitations: Less photorealistic, requires Discord interface
- Resolution: Up to 2048x2048 (with upscale)
- Speed: ~30-60 seconds per image
- Cost: Subscription-based ($10-60/month)

**Stable Diffusion:**

- Best for: Custom fine-tuning, batch generation, specific styles
- Strengths: Open source, highly customizable, fast iteration
- Limitations: Requires technical setup, inconsistent quality without tuning
- Resolution: Up to 1024x1024 (higher with extensions)
- Speed: ~5-15 seconds per image (local GPU)
- Cost: Free (open source) or cloud compute costs

**RunwayML Gen-2:**

- Best for: Video generation, motion graphics, video editing
- Strengths: Text-to-video, image-to-video, video editing capabilities
- Limitations: Short clips (4-18 seconds), expensive for long content
- Resolution: Up to 1920x1080
- Speed: ~1-3 minutes per 4-second clip
- Cost: Credit-based ($12-95/month)

### Step 4: Configure Generation Parameters

Set technical parameters for optimal output:

**Image Generation Settings:**

- **Resolution**: 512x512 (draft), 1024x1024 (standard), 2048x2048+ (high-res)
- **Aspect Ratio**: 1:1 (square), 16:9 (landscape), 9:16 (vertical), 4:5 (social)
- **CFG Scale**: 7-15 (how closely to follow prompt)
- **Steps**: 20-50 (quality vs speed trade-off)
- **Sampler**: Euler, DPM++, DDIM (affects output style)
- **Seed**: Fixed for reproducibility or random for variety

**Video Generation Settings:**

- **Duration**: 2-18 seconds
- **Frame Rate**: 24fps (cinema), 30fps (standard), 60fps (smooth)
- **Motion Amount**: Low (subtle), Medium (moderate), High (dynamic)
- **Camera Movement**: Static, pan, zoom, dolly, orbit
- **Interpolation**: Frame blending for smooth motion

**Style Transfer Settings:**

- **Style Strength**: 0.3 (subtle) to 1.0 (strong)
- **Content Preservation**: Balance between source and style
- **Detail Level**: Fine, medium, coarse

### Step 5: Execute Batch Generation

Generate multiple variations efficiently:

**Variation Strategies:**

```
Base Prompt: "Modern minimalist living room with large windows"

Variation 1: + "sunset lighting, warm tones"
Variation 2: + "morning light, cool tones, plants"
Variation 3: + "night scene, ambient lighting, city view"
Variation 4: + "rainy day, cozy atmosphere, fireplace"
```

**Batch Parameters:**

- Number of variations: 4-16 per concept
- Seed randomization for diversity
- Parameter sweeps (CFG, steps, samplers)
- Style mixing and interpolation

**Quality Control During Generation:**

- Preview low-res versions first
- Iterative refinement based on results
- Track successful prompts and parameters
- Maintain generation log for reproducibility

### Step 6: Enhance and Upscale

Improve generated media quality:

**Upscaling Methods:**

- **AI Upscaling**: Real-ESRGAN, Topaz Gigapixel (2x, 4x, 8x)
- **Face Enhancement**: GFPGAN, CodeFormer for portraits
- **Detail Enhancement**: Clarity, sharpening, texture recovery
- **Resolution Targets**: 2K (2048px), 4K (4096px), 8K (8192px)

**Post-Processing Enhancements:**

- Color correction and grading
- Lighting adjustments
- Contrast and saturation tuning
- Noise reduction
- Artifact removal
- Background refinement

**Video Enhancement:**

- Frame interpolation (increase FPS)
- Stabilization
- Color grading
- Transitions and effects
- Audio synchronization

### Step 7: Apply Brand Consistency

Ensure assets match brand guidelines:

**Brand Elements Integration:**

- Color palette enforcement
- Typography application
- Logo placement
- Visual style consistency
- Tone and mood alignment
- Composition rules

**Consistency Techniques:**

- LoRA (Low-Rank Adaptation) training for custom styles
- ControlNet for composition control
- Style reference images
- Negative prompts for unwanted elements
- Template-based generation

**Quality Gates:**

- Brand guideline checklist
- Stakeholder review workflow
- A/B testing for effectiveness
- Legal/compliance review

### Step 8: Format and Optimize

Prepare assets for deployment:

**Format Conversion:**

- **Web**: JPG (photos), PNG (graphics), WebP (modern web)
- **Print**: TIFF, PNG (lossless), PDF (documents)
- **Video**: MP4 (H.264), WebM, MOV (editing)
- **Social Media**: Platform-specific specs

**Optimization:**

- File size reduction without quality loss
- Responsive image variants (multiple resolutions)
- Metadata embedding (copyright, usage rights)
- SEO-friendly filenames
- CDN preparation

**Platform-Specific Specs:**

**Instagram:**

- Feed: 1080x1080 (1:1), 1080x1350 (4:5)
- Stories: 1080x1920 (9:16)
- Reels: 1080x1920 (9:16), 60 seconds max

**YouTube:**

- Thumbnail: 1280x720, JPG/PNG, under 2MB
- Video: 1920x1080 (16:9), MP4, H.264 codec

**Facebook:**

- Feed Image: 1200x630 (1.91:1)
- Cover Photo: 820x312
- Video: 1280x720 minimum

**LinkedIn:**

- Post Image: 1200x627
- Banner: 1584x396
- Video: 1920x1080, max 10 minutes

### Step 9: Manage Rights and Licensing

Understand usage rights for generated content:

**DALL-E (OpenAI):**

- Commercial use: Allowed (including paid generations)
- Ownership: User owns the images created
- Attribution: Not required
- Restrictions: Cannot violate terms of service

**Midjourney:**

- Commercial use: Allowed with paid subscription
- Ownership: Shared (CC BY-NC 4.0 for free users, full rights for paid)
- Attribution: Recommended but not required
- Restrictions: Cannot create misleading content

**Stable Diffusion:**

- Commercial use: Allowed (open source model)
- Ownership: User owns outputs
- Attribution: Not required for model, check specific checkpoints
- Restrictions: Must comply with CreativeML OpenRAIL-M license

**Important Considerations:**

- Training data concerns (verify no copyrighted material reproduction)
- Model-specific terms of service
- Output review for potential copyright issues
- Documentation of generation process
- Client disclosure requirements

### Step 10: Version Control and Iteration

Track and manage generated assets:

**Asset Management:**

```
project/
├── generations/
│   ├── v1-initial-concepts/
│   ├── v2-refinements/
│   ├── v3-final-selections/
│   └── archive/
├── prompts/
│   ├── successful-prompts.txt
│   ├── prompt-variations.txt
│   └── negative-prompts.txt
├── parameters/
│   ├── generation-settings.json
│   └── model-configs.yaml
└── finals/
    ├── web-optimized/
    ├── print-ready/
    └── source-files/
```

**Version Tracking:**

- Prompt versioning
- Parameter documentation
- Model and checkpoint versions
- Seed values for reproducibility
- Generation timestamps
- Quality scores and ratings

**Iteration Log:**

- What was tried
- What worked/didn't work
- Stakeholder feedback
- Final selections and rationale

---

## Usage Examples

### Example 1: Product Photography

**Request:**
"Generate professional product photos for a luxury watch - need 5 variations with different backgrounds and lighting."

**Generated Assets:**

```
PROMPT OPTIMIZATION:
Base: "Luxury Swiss automatic watch with black leather strap, stainless steel case"

Variation 1 - Hero Shot:
"Luxury Swiss automatic watch with black leather strap and stainless steel case,
centered composition on marble surface, dramatic side lighting creating highlights
on metal, shallow depth of field, black gradient background, professional product
photography, studio lighting, 8K resolution, sharp focus, award-winning commercial
photography"

Negative: blurry, low quality, scratches, fingerprints, dust

Variation 2 - Lifestyle:
"Luxury Swiss automatic watch on wrist of businessman in modern office, natural
window lighting, shallow depth of field with blurred cityscape background,
photorealistic, professional photography, warm tones, aspirational lifestyle"

Variation 3 - Detail Shot:
"Extreme close-up of luxury watch face showing intricate details, automatic movement
visible through sapphire case back, macro photography, dramatic lighting highlighting
craftsmanship, black background, ultra high resolution, sharp focus"

Variation 4 - Flat Lay:
"Top-down flat lay of luxury watch with complementary items: leather wallet, car
keys, fountain pen on dark wood surface, professional product styling, even lighting,
commercial photography, lifestyle brand aesthetic"

Variation 5 - Dramatic:
"Luxury watch emerging from water splash, frozen motion, dramatic lighting, black
background, commercial advertising photography, high-speed photography aesthetic,
water droplets in sharp focus, cinematic quality"

MODEL: DALL-E 3 (best for product photography realism)
SETTINGS:
- Resolution: 1024x1024 → upscale to 4096x4096
- Aspect: 1:1 for social, 4:5 for e-commerce
- Enhancement: Real-ESRGAN upscaling, detail sharpening
- Format: PNG (lossless) for editing, JPG (optimized) for web

POST-PROCESSING:
1. Color correction (consistent across all shots)
2. Watch face legibility enhancement
3. Remove any AI artifacts
4. Add subtle vignette
5. Export multiple sizes for different platforms

OUTPUT FILES:
- watch-hero-8k.png (4096x4096, print-ready)
- watch-hero-web.jpg (2048x2048, 150KB)
- watch-lifestyle-4k.png
- watch-detail-macro.png
- watch-flatlay-styled.png
- watch-dramatic-splash.png
```

### Example 2: Social Media Content Series

**Request:**
"Create a week's worth of Instagram posts (7 images) for a fitness brand - motivational quotes on branded backgrounds."

**Generated Series:**

```
BRAND GUIDELINES:
- Colors: #FF6B35 (coral), #004E89 (navy), #FFFFFF (white)
- Style: Modern, energetic, minimalist
- Typography: Bold sans-serif for quotes
- Aspect: 1080x1080 (Instagram feed square)

GENERATION STRATEGY:
Use Midjourney for artistic backgrounds + text overlay in post-processing

DAY 1 - Monday Motivation:
Prompt: "Abstract gradient background in coral and navy blue, smooth flowing shapes,
modern minimalist design, energetic and uplifting mood, clean aesthetic, digital art"
Quote: "Start strong. Finish stronger."

DAY 2 - Transformation Tuesday:
Prompt: "Geometric pattern with triangular shapes, coral and navy color scheme,
dynamic movement, inspirational design, modern fitness aesthetic"
Quote: "Progress, not perfection."

DAY 3 - Workout Wednesday:
Prompt: "Motion blur effect suggesting movement and energy, abstract athletic
aesthetic, coral and navy colors, dynamic composition, motivational design"
Quote: "Sweat is just fat crying."

DAY 4 - Throwback Thursday:
Prompt: "Minimalist landscape with mountains at sunrise, coral and navy color
palette, inspirational journey concept, clean modern style"
Quote: "The only bad workout is the one you didn't do."

DAY 5 - Fitness Friday:
Prompt: "Abstract explosion of energy particles, coral sparks on navy background,
dynamic movement, celebratory mood, modern digital art"
Quote: "Strong is the new sexy."

DAY 6 - Success Saturday:
Prompt: "Upward trending abstract graph visualization, coral line on navy background,
achievement and progress concept, modern infographic style"
Quote: "Results happen over time, not overnight."

DAY 7 - Sunday Reset:
Prompt: "Calm abstract waves, gentle coral and navy gradients, peaceful yet
energizing mood, recovery and rest concept, soothing modern design"
Quote: "Rest, recover, repeat."

POST-GENERATION WORKFLOW:
1. Generate all 7 backgrounds in Midjourney
2. Upscale to 2048x2048 for quality
3. Apply brand color correction (ensure exact hex values)
4. Add text overlays in Photoshop/Figma:
   - Quote in bold sans-serif, white text
   - Brand logo in corner
   - Call-to-action (#FitnessJourney)
5. Export optimized JPGs (1080x1080, under 1MB each)
6. Schedule in content calendar

BATCH SETTINGS:
- Model: Midjourney v6 --ar 1:1 --style raw
- CFG: 7 (balanced)
- Iterations: 2-3 per concept, select best
- Upscale: Standard Midjourney upscale
```

### Example 3: Video B-Roll Generation

**Request:**
"Generate abstract background videos for a tech product demo - need 10 seconds of futuristic digital environment."

**Generated Video:**

```
VIDEO CONCEPT:
Futuristic digital environment with floating holographic interfaces, data streams,
and particle effects - perfect for tech product overlay

GENERATION APPROACH: RunwayML Gen-2 (text-to-video)

PROMPT SEQUENCE:

Clip 1 (0-4 seconds) - Establishing:
"Futuristic digital environment with floating holographic displays showing data
visualizations, blue and purple neon colors, smooth camera dolly forward through
digital space, cinematic sci-fi aesthetic, clean modern design, high detail"

Motion: Slow dolly forward
Duration: 4 seconds
Resolution: 1920x1080, 24fps

Clip 2 (4-7 seconds) - Movement:
"Abstract data streams flowing through digital space, blue particles and light
trails, rotating camera movement, futuristic technology visualization, depth and
dimensionality, cyberpunk aesthetic without clutter"

Motion: Gentle camera rotation
Duration: 3 seconds
Resolution: 1920x1080, 24fps

Clip 3 (7-10 seconds) - Detail:
"Close-up of holographic interface elements materializing, blue and white light
effects, smooth animations, professional tech demo aesthetic, clean and modern,
particles floating in foreground"

Motion: Slow zoom in
Duration: 3 seconds
Resolution: 1920x1080, 24fps

GENERATION SETTINGS:
- Model: RunwayML Gen-2
- Duration: 4+3+3 = 10 seconds (generated as 3 clips, then stitched)
- Motion Amount: Medium (balanced movement)
- Interpolation: Enabled (smooth frames)
- Upscale: 1080p to 4K using Topaz Video Enhance AI

POST-PRODUCTION:
1. Stitch three clips seamlessly in editing software
2. Color grade for consistency (blue/purple tech aesthetic)
3. Add subtle camera shake for realism (if needed)
4. Apply motion blur where appropriate
5. Add ambient sound effects (digital hums, particle sounds)
6. Export:
   - 4K version (3840x2160, H.264, 50Mbps) for high-quality use
   - 1080p version (1920x1080, H.264, 20Mbps) for web
   - WebM version for web optimization

USAGE APPLICATIONS:
- Product demo background
- Website hero section
- Presentation backgrounds
- Social media content
- App interface demonstrations

RENDERING TIME:
- Generation: ~5-8 minutes (RunwayML processing)
- Enhancement: ~10-15 minutes (AI upscaling)
- Editing/Export: ~5 minutes
- Total: ~20-30 minutes for 10 seconds of 4K footage
```

### Example 4: Logo Variations

**Request:**
"Generate 10 logo concept variations for a sustainable coffee company called 'Green Bean Co.'"

**Generated Concepts:**

```
BRAND BRIEF:
- Name: Green Bean Co.
- Industry: Sustainable/Organic Coffee
- Values: Eco-friendly, quality, community
- Style: Modern but approachable, not too corporate
- Colors: Earth tones, greens, browns

GENERATION STRATEGY: Stable Diffusion with LoRA fine-tuning

CONCEPT 1 - Minimalist Leaf:
"Minimalist logo design, single coffee bean transforming into green leaf, simple
line art, earth tone colors, modern sustainable brand, vector style illustration,
clean professional design"

CONCEPT 2 - Circle Badge:
"Circular badge logo with coffee bean and plant sprout, vintage-modern hybrid style,
green and brown color palette, sustainable coffee brand, hand-drawn aesthetic,
professional design"

CONCEPT 3 - Abstract Geometric:
"Abstract geometric logo with coffee bean shape made from triangles, modern
sustainable design, green gradient colors, minimalist tech-forward aesthetic,
professional brand identity"

CONCEPT 4 - Nature Integration:
"Logo combining coffee cup silhouette with tree growing inside, symbolic sustainable
design, earth tones, modern illustration style, eco-friendly brand aesthetic"

CONCEPT 5 - Lettermark:
"Modern lettermark logo 'GBC' with coffee bean integrated into design, clean
sans-serif typography, green and brown colors, professional sustainable brand"

CONCEPT 6 - Vintage Stamp:
"Vintage circular stamp logo with coffee plant illustration, retro-modern style,
authentic craft aesthetic, green and cream colors, sustainable coffee brand"

CONCEPT 7 - Dynamic Swoosh:
"Dynamic logo with coffee bean and flowing leaf swoosh, energetic modern design,
movement and growth concept, green gradient, professional brand identity"

CONCEPT 8 - Iconic Symbol:
"Simple iconic logo, coffee bean with small leaf sprouting, one-color design for
versatility, modern minimalist, scalable vector style, professional brand mark"

CONCEPT 9 - Handcrafted:
"Hand-drawn style logo with coffee bean and plant elements, organic authentic feel,
sketchy artistic style, earth tones, sustainable artisan coffee brand"

CONCEPT 10 - Emblem:
"Emblem-style logo with coffee bean centered in shield shape with leaf accents,
traditional meets modern, professional sustainable brand, green and brown palette"

MODEL & SETTINGS:
- Base: Stable Diffusion XL + Logo-specific LoRA
- Resolution: 1024x1024
- Negative prompts: "text, words, letters, blurry, low quality, complex, messy"
- CFG Scale: 8
- Steps: 40
- Batch: Generate 3-4 variations of each concept

POST-GENERATION:
1. Vectorize best concepts in Illustrator
2. Refine and clean up details
3. Create variations (horizontal, vertical, icon-only)
4. Test at multiple sizes (favicon to billboard)
5. Create brand style guide with selected logos

DELIVERABLES:
- 10 concept images (PNG, 2048x2048)
- Top 3 vectorized (AI, SVG, EPS)
- Color variations (full color, black, white, single color)
- Usage guidelines document
```

### Example 5: Infographic Elements

**Request:**
"Create custom illustrated icons and graphics for a cybersecurity infographic - need 8 icons representing different security concepts."

**Generated Icon Set:**

```
INFOGRAPHIC THEME:
Cybersecurity Threats and Protections
Style: Modern, tech-forward, consistent visual language
Colors: Dark blue, electric blue, red (threat), green (secure)

ICON CONCEPTS:

ICON 1 - Firewall:
"Isometric illustration of digital firewall, protective barrier with data packets,
blue and green colors, modern tech infographic style, clean vector aesthetic"

ICON 2 - Phishing Attack:
"Stylized fishing hook catching email envelope, warning red color, modern
cybersecurity infographic icon, clear symbolic design, professional illustration"

ICON 3 - Encryption:
"Lock icon made of digital code and binary, secure encryption concept, blue and
green colors, modern tech illustration, symbolic cybersecurity design"

ICON 4 - Malware:
"Abstract virus or bug icon with digital corruption effects, red warning color,
modern cybersecurity threat illustration, clean infographic style"

ICON 5 - VPN Protection:
"Globe with secure tunnel visualization, encrypted connection concept, blue and
green colors, modern cybersecurity icon, professional infographic design"

ICON 6 - Multi-Factor Authentication:
"Smartphone with fingerprint and key symbols, layered security concept, modern
tech infographic icon, blue color scheme, clean design"

ICON 7 - Data Breach:
"Broken shield with data leaking out, security failure concept, red warning colors,
modern cybersecurity infographic, clear symbolic illustration"

ICON 8 - Security Update:
"Shield with upward arrow and checkmark, software update security concept, green
success color, modern tech infographic icon, professional design"

GENERATION SETTINGS:
- Model: DALL-E 3 (consistent style across all icons)
- Resolution: 1024x1024 per icon
- Style: "clean vector infographic illustration, professional design"
- Consistency: Include "part of cohesive icon set" in all prompts
- Background: Transparent or white (for easy extraction)

BATCH GENERATION:
1. Generate all 8 icons with consistent style parameters
2. Review for visual consistency
3. Regenerate any outliers to match set aesthetic
4. Background removal (if needed)
5. Resize and optimize for infographic use

POST-PROCESSING:
1. Remove backgrounds (transparent PNG)
2. Ensure consistent sizing (512x512 icons)
3. Color correction for brand consistency
4. Export multiple formats:
   - PNG (transparent, various sizes)
   - SVG (vector, scalable)
5. Create infographic layout using icons
6. Add labels and data visualizations

FINAL INFOGRAPHIC ASSEMBLY:
- Layout tool: Figma or Adobe Illustrator
- Format: 1080x1350 (Instagram) or 1200x1800 (Pinterest)
- Integrate icons with:
  - Statistics and data points
  - Descriptive text
  - Visual flow/hierarchy
  - Brand colors and typography
  - Call-to-action
```

---

## Quality Checklist

Before finalizing generated media:

**Visual Quality:**

- [ ] Resolution meets requirements
- [ ] No visible AI artifacts or distortions
- [ ] Sharp focus where intended
- [ ] Proper lighting and composition
- [ ] Colors are accurate and vibrant
- [ ] Meets professional standards

**Brand Compliance:**

- [ ] Matches brand guidelines
- [ ] Consistent visual style
- [ ] Appropriate tone and mood
- [ ] Color palette adherence
- [ ] Typography (if applicable) on-brand

**Technical Specifications:**

- [ ] Correct dimensions and aspect ratio
- [ ] Appropriate file format
- [ ] Optimized file size
- [ ] Proper metadata embedded
- [ ] Platform-specific requirements met

**Legal and Rights:**

- [ ] Generation complies with model ToS
- [ ] No copyright concerns
- [ ] Commercial use rights secured
- [ ] Proper documentation maintained
- [ ] Client disclosure completed

**Usability:**

- [ ] Works across intended platforms
- [ ] Scales appropriately
- [ ] Readable/visible at all sizes
- [ ] Accessible (color contrast, etc.)
- [ ] Integrates with existing materials

---

## Best Practices

### Prompt Engineering

- Be specific and detailed
- Use quality modifiers consistently
- Include negative prompts
- Reference artistic styles or photographers
- Specify technical camera/lighting terms
- Iterate based on results

### Model Selection

- Match model strengths to use case
- Consider cost vs quality trade-offs
- Use ensemble approaches for best results
- Stay updated on model improvements
- Maintain fallback options

### Batch Efficiency

- Generate variations simultaneously
- Use seeds for controlled randomization
- Parameter sweeps for optimization
- Template prompts for consistency
- Automate repetitive tasks

### Quality Control

- Preview before full generation
- Generate multiple options
- Compare against references
- Stakeholder review early
- Document successful approaches

### Asset Management

- Organized file structure
- Clear naming conventions
- Version control
- Prompt library maintenance
- Performance tracking

---

## Integration Points

**Workflow Integration:**

```bash
# Generate product images
/media/generate --type image --style photorealistic --prompt "luxury watch"

# Create matching video
/media/generate --type video --style cinematic --prompt "watch product demo"

# Generate thumbnails for content
/media/thumbnail --platform youtube --template product

# Add subtitles to generated video
/media/subtitle --video generated-video.mp4 --style modern
```

**Export to Design Tools:**

- Figma plugin integration
- Adobe Creative Cloud sync
- Canva asset library
- Brand asset management systems

---

## Success Criteria

**Media generation succeeds when:**

1. **Visual Quality:**
   - Professional-grade outputs
   - No obvious AI artifacts
   - Meets resolution requirements
   - Proper technical specifications

2. **Efficiency:**
   - Faster than traditional methods
   - Reduces costs significantly
   - Enables rapid iteration
   - Scales with demand

3. **Brand Consistency:**
   - Matches guidelines
   - Cohesive visual identity
   - Appropriate tone and style
   - Stakeholder approval

4. **Business Impact:**
   - Accelerates campaigns
   - Reduces production costs
   - Increases creative testing
   - Improves engagement metrics

---

**Pro Tip:** Maintain a "prompt library" of successful generation prompts organized by category (product, lifestyle, abstract, etc.). Include the exact prompts, models used, settings, and example outputs. This dramatically speeds up future generations and ensures consistent quality across projects.
