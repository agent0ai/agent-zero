---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when building web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
---

# Frontend Design Skill

## What This Skill Does

Creates **distinctive, production-grade frontend interfaces** that avoid generic "AI slop" aesthetics. Every implementation should feel intentional, polished, and visually memorable.

## When This Skill Activates

This skill automatically activates for:

- React component creation
- UI/UX design implementation
- Landing pages and marketing sites
- Dashboard and admin interfaces
- Mobile-responsive layouts
- Design system implementation

## Core Design Principles

### 1. Understand Context First

Before writing any code, analyze:

- **Purpose** - What is this interface trying to accomplish?
- **Audience** - Who will use this? What are their expectations?
- **Tone** - Professional, playful, minimal, bold, luxurious?
- **Constraints** - Technical limitations, brand guidelines, accessibility needs
- **Differentiation** - How can this stand out from generic solutions?

### 2. Choose a Bold Aesthetic Direction

Don't default to safe, generic choices. Pick an intentional style:

| Direction | Characteristics |
|-----------|-----------------|
| **Brutalist** | Raw, honest, unconventional layouts, bold typography |
| **Minimalist** | Precise spacing, restrained palette, typography-focused |
| **Maximalist** | Rich textures, layered elements, bold colors, motion |
| **Editorial** | Magazine-inspired, strong typography hierarchy, white space |
| **Tech-Forward** | Gradients, glass morphism, subtle animations, dark themes |
| **Organic** | Natural colors, soft shapes, flowing layouts, warmth |
| **Luxury** | Premium materials, sophisticated palette, refined details |
| **Playful** | Bright colors, rounded shapes, micro-interactions, personality |

**Key principle:** Bold maximalism and refined minimalism both work. The key is **intentionality, not intensity**.

### 3. Typography That Elevates

**DO:**

- Choose distinctive, characterful fonts that match the context
- Create clear hierarchy with intentional size/weight relationships
- Use font pairing that creates visual interest
- Consider variable fonts for nuanced control

**DON'T:**

- Default to Inter, Open Sans, or Roboto without consideration
- Use the same weight throughout
- Ignore line-height and letter-spacing
- Mix too many font families

**Examples:**

```tsx
// Generic (avoid)
className="text-lg font-medium"

// Distinctive (prefer)
className="font-playfair text-4xl tracking-tight leading-[1.1]"
```

### 4. Color With Purpose

**DO:**

- Build cohesive palettes with dominant colors and sharp accents
- Use CSS variables for consistency and theming
- Create atmosphere through subtle gradients and overlays
- Consider dark mode from the start

**DON'T:**

- Use random Tailwind colors without a system
- Ignore contrast ratios (accessibility)
- Over-rely on pure black/white
- Use too many competing accent colors

**Examples:**

```tsx
// Generic palette
className="bg-blue-500 text-white"

// Intentional palette
className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white/95"
```

### 5. Motion With Impact

**DO:**

- Use animation for high-impact moments (reveals, transitions, feedback)
- Implement staggered animations for lists and grids
- Add scroll-triggered effects for storytelling
- Create micro-interactions for delight

**DON'T:**

- Animate everything (motion overload)
- Use jarring or distracting transitions
- Ignore `prefers-reduced-motion`
- Add motion without purpose

**Examples:**

```tsx
// Subtle entrance
className="animate-in fade-in slide-in-from-bottom-4 duration-500"

// Staggered list
style={{ animationDelay: `${index * 100}ms` }}

// Hover interaction
className="transition-all duration-300 hover:scale-105 hover:shadow-xl"
```

### 6. Spatial Composition

**DO:**

- Break the grid intentionally for visual interest
- Use asymmetry, overlap, and diagonal flow
- Create depth with layering and shadows
- Give content room to breathe

**DON'T:**

- Align everything predictably
- Cram content without breathing room
- Use the same spacing everywhere
- Ignore visual rhythm

**Examples:**

```tsx
// Breaking the grid
className="relative -mt-20 ml-8 z-10"

// Overlap effect
className="absolute -top-4 -right-4 transform rotate-3"

// Generous spacing
className="py-24 md:py-32 lg:py-40"
```

### 7. Visual Details That Create Atmosphere

**DO:**

- Add subtle textures and patterns
- Use gradients to create depth and interest
- Implement glass morphism and blur effects
- Create custom borders and dividers

**DON'T:**

- Leave surfaces flat and lifeless
- Use default browser styling
- Ignore the background layer
- Skip dark mode considerations

**Examples:**

```tsx
// Textured background
className="bg-[url('/noise.png')] bg-repeat"

// Glass morphism
className="backdrop-blur-xl bg-white/10 border border-white/20"

// Custom divider
className="h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"
```

## Anti-Patterns to Avoid

### Generic AI Aesthetics

❌ **DO NOT:**

- Use overused font families without purpose (Inter, Roboto, Open Sans)
- Apply cliché gradient combinations (purple-to-pink on everything)
- Create predictable, symmetrical layouts
- Use cookie-cutter card designs
- Default to rounded-lg on everything
- Apply the same shadow-md to all elevated elements

✅ **INSTEAD:**

- Choose fonts that match the specific context and personality
- Build custom color palettes with intentional relationships
- Break symmetry deliberately for visual interest
- Design unique containers that serve the content
- Vary border radius based on element purpose
- Create custom shadow scales for depth hierarchy

## Implementation Checklist

Before delivering any frontend code, verify:

### Design Quality

- [ ] Aesthetic direction is clear and intentional
- [ ] Typography creates clear hierarchy
- [ ] Colors form a cohesive palette
- [ ] Spacing creates visual rhythm
- [ ] Motion enhances (not distracts)

### Production Quality

- [ ] Fully responsive (mobile-first)
- [ ] Dark mode support with `dark:` variants
- [ ] Accessible (ARIA, keyboard nav, contrast)
- [ ] Performance optimized (no layout shift, efficient renders)
- [ ] Error and loading states handled

### Code Quality

- [ ] Props-based, portable components
- [ ] TypeScript types complete
- [ ] Tailwind CSS (no inline styles)
- [ ] Clean component architecture
- [ ] Proper semantic HTML

## Output Format

When applying this skill, produce:

```tsx
// Distinctive, production-grade component
// With intentional design choices documented

/**
 * [ComponentName]
 *
 * Design Direction: [e.g., "Editorial minimalism with bold typography"]
 *
 * Key Design Choices:
 * - Typography: [font choices and why]
 * - Colors: [palette decisions]
 * - Motion: [animation approach]
 * - Layout: [spatial composition notes]
 */

export function ComponentName({ ... }: Props) {
  return (
    // Production-ready implementation
    // With distinctive aesthetic execution
  );
}
```

## Core Philosophy

> "Claude is capable of extraordinary creative work. Don't hold back. Show what can truly be created when thinking outside the box and committing fully to a distinctive vision."

Every interface should feel like it was designed by a thoughtful human with strong opinions - not generated by an AI defaulting to safe choices.

---

*This skill transforms generic UI requests into distinctive, memorable interfaces that stand out from typical AI-generated designs.*
