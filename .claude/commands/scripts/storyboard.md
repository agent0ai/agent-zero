---
description: Create visual storyboards from scripts with shot descriptions
argument-hint: [--script <file>] [--shot-types] [--export-pdf]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Storyboard Generator

Shot-by-shot storyboards with camera angles, transitions, and visual notes.

## ROI Analysis: $35,000/year

**Value Breakdown:**

- **Professional Storyboarding**: $500-2,000/project → $150/hour saved
- **Production Efficiency**: 40% reduction in shoot time
- **Client Approval**: 85% faster stakeholder sign-off
- **Crew Coordination**: Universal visual reference for entire team
- **Budget Accuracy**: Precise shot planning reduces cost overruns by 30%

**Time Savings:** 8-16 hours per project → 5-10 minutes automated
**Quality Improvement:** Clear visual communication prevents misalignment
**Business Impact:** Fewer reshoots, faster approvals, professional deliverables

---

## Overview

The Storyboard Generator transforms video scripts into detailed visual storyboards complete with shot descriptions, camera angles, transitions, lighting notes, and technical specifications. It creates production-ready documents that align directors, cinematographers, clients, and crew.

**Key Features:**

- Shot-by-shot visual breakdowns
- Camera angle and movement specifications
- Framing and composition guidance
- Lighting and color mood notes
- Transition and pacing indicators
- Audio and dialogue synchronization
- Props, wardrobe, and location details
- Equipment requirements per shot
- Industry-standard notation

**Storyboard Types:**

- **Pre-Production**: Detailed planning storyboards for crew
- **Client Presentation**: High-level visual concepts for approval
- **Animation**: Frame-by-frame sequences with timing
- **Commercial**: Product-focused with brand guidelines
- **Narrative**: Story-driven with character blocking
- **Documentary**: Interview and B-roll shot lists

---

## Implementation

### Step 1: Initialize Storyboard Project

Gather project requirements and script details:

**Required Information:**

- **Script Source**: Video script file or written narrative
- **Project Type**: Commercial, narrative film, documentary, animation, music video
- **Video Length**: Total duration
- **Shot Count**: Estimated number of individual shots
- **Production Budget**: Tier (low/medium/high) affects shot complexity
- **Timeline**: Pre-production schedule

**Optional Parameters:**

- Visual reference images or mood boards
- Brand style guidelines
- Technical constraints (equipment available)
- Location restrictions
- Talent capabilities
- Client preferences

**Analysis Requirements:**

- Parse script for scene breaks
- Identify key story moments
- Note dialogue and action sequences
- Mark timing and pacing requirements
- Flag special effects or complex shots

### Step 2: Define Shot Types and Camera Language

Establish the visual vocabulary for the project:

**Shot Sizes:**

- **ECU** (Extreme Close-Up): Eyes, hands, specific details
- **CU** (Close-Up): Face, product detail
- **MCU** (Medium Close-Up): Head and shoulders
- **MS** (Medium Shot): Waist up
- **MWS** (Medium Wide Shot): Knees up
- **WS** (Wide Shot): Full body
- **EWS** (Extreme Wide Shot): Environmental, establishing
- **2-SHOT**: Two subjects in frame
- **OTS** (Over-the-Shoulder): Conversation angle

**Camera Angles:**

- **Eye Level**: Neutral, natural perspective
- **High Angle**: Looking down (subject appears smaller/vulnerable)
- **Low Angle**: Looking up (subject appears powerful/imposing)
- **Bird's Eye**: Directly overhead
- **Dutch/Canted**: Tilted horizon (tension, unease)
- **POV** (Point of View): Character's perspective
- **Worm's Eye**: Ground level looking up

**Camera Movements:**

- **Static**: Fixed, no movement
- **Pan**: Horizontal rotation (left/right)
- **Tilt**: Vertical rotation (up/down)
- **Dolly/Track**: Camera moves forward/backward on track
- **Truck**: Camera moves left/right parallel to subject
- **Boom**: Camera moves vertically up/down
- **Zoom**: Lens focal length changes (in/out)
- **Handheld**: Organic, documentary feel
- **Steadicam**: Smooth movement while walking
- **Crane/Jib**: Sweeping vertical movements
- **Drone**: Aerial perspectives

### Step 3: Break Script into Individual Shots

Decompose script into discrete visual units:

**Shot Breakdown Process:**

1. **Scene Identification**: Mark each distinct location/time
2. **Action Analysis**: Identify visual story beats
3. **Coverage Planning**: Determine master, medium, close-ups
4. **Pacing Calculation**: Allocate screen time per shot
5. **Continuity Notes**: Track props, wardrobe, positioning

**Example Breakdown:**

```
SCRIPT: "Sarah walks into the coffee shop, orders a latte, and sits
down at a window table while checking her phone."

SHOTS:
1. EWS - Exterior coffee shop (establish location)
2. MS - Sarah enters door (character introduction)
3. MCU - Barista greets Sarah (interaction)
4. CU - Sarah's face as she orders (emotion)
5. ECU - Hands preparing latte (product detail)
6. WS - Sarah walks to window table (movement/space)
7. MS - Sarah sits and pulls out phone (action)
8. CU - Phone screen showing message (plot point)
9. MCU - Sarah's reaction (emotional beat)
```

**Shot Duration Guidelines:**

- **Fast-paced**: 1-3 seconds per shot (action, montage)
- **Medium-paced**: 3-6 seconds per shot (standard narrative)
- **Slow-paced**: 6-12+ seconds per shot (contemplative, artistic)

### Step 4: Design Visual Composition

Plan framing and composition for each shot:

**Composition Principles:**

**Rule of Thirds:**

- Divide frame into 3x3 grid
- Place subjects on intersection points
- Create visual balance and interest

**Leading Lines:**

- Use architectural elements, roads, fences
- Guide viewer's eye to subject
- Create depth and dimension

**Headroom & Look Space:**

- Headroom: Space above subject's head
- Look space: Space in direction subject is facing
- Proper spacing prevents cramped framing

**Foreground/Background Elements:**

- Layering creates depth
- Frame subject with environmental context
- Use shallow depth-of-field strategically

**Symmetry vs Asymmetry:**

- Symmetry: Formal, balanced, stable
- Asymmetry: Dynamic, interesting, tension

**Visual Notation:**

```
SHOT 5: Product Close-Up
┌─────────────────────────────┐
│         [SKY/CEILING]       │ ← Upper third
├─────────────────────────────┤
│  ╔═══╗    [LATTE]          │ ← Middle third
│  ║CUP║  (steam rising)     │   (subject on left third)
├─────────────────────────────┤
│  [COUNTER/TABLE]            │ ← Lower third
└─────────────────────────────┘
```

### Step 5: Add Technical Specifications

Include cinematography and equipment details:

**Camera Specifications:**

- **Focal Length**: 24mm, 50mm, 85mm, 200mm
- **Aperture**: f/1.4, f/2.8, f/5.6, f/11, f/16
- **Shutter Speed**: 1/50, 1/100, 1/200 (usually 180° shutter)
- **ISO**: 100, 400, 800, 1600, 3200
- **Frame Rate**: 24fps (cinema), 30fps (video), 60fps (slow motion), 120fps+ (extreme slow-mo)
- **Resolution**: 1080p, 4K, 6K, 8K

**Lighting Specifications:**

- **Key Light**: Primary light source (direction, intensity)
- **Fill Light**: Softens shadows
- **Back/Rim Light**: Separates subject from background
- **Practical Lights**: Visible lights in scene (lamps, windows)
- **Color Temperature**: 3200K (tungsten), 5600K (daylight)
- **Lighting Ratio**: Key to fill ratio (2:1, 4:1, 8:1)
- **Mood**: High key (bright, minimal shadows) vs Low key (dark, dramatic)

**Example Technical Note:**

```
SHOT 5: Latte Preparation ECU
Camera: 100mm macro lens, f/2.8, 1/50s, ISO 400, 24fps
Lighting: Key from camera right (soft box), rim from back left,
          warm practical (overhead pendant), 5600K balanced
Depth: Shallow DOF - hands/cup sharp, background soft bokeh
```

### Step 6: Annotate Audio and Dialogue

Synchronize sound with visual elements:

**Audio Annotations:**

- **Dialogue**: On-camera spoken lines
- **Voice-Over**: Narration, character thoughts
- **Sound Effects**: Doors, footsteps, ambient sounds
- **Music**: Score, soundtrack, emotional cues
- **Room Tone**: Ambient environmental sound
- **Foley**: Synchronized sound effects

**Format:**

```
SHOT 5: Latte Preparation ECU

VISUAL: Barista's hands expertly pouring steamed milk, creating
        latte art pattern in cup

AUDIO:
  - SFX: Espresso machine steam hiss (background)
  - SFX: Milk pouring (foreground, crisp)
  - MUSIC: Upbeat indie folk (continues from previous shot)
  - AMBIENT: Coffee shop chatter (low, distant)

DIALOGUE: None (customer and barista visible in background,
          out of focus, muted conversation)
```

### Step 7: Plan Transitions and Pacing

Connect shots with transitions and rhythm:

**Transition Types:**

- **Cut**: Direct, immediate change (most common)
- **Dissolve/Crossfade**: Gentle blend between shots
- **Fade to Black**: End of scene, passage of time
- **Fade from Black**: Beginning of scene
- **Wipe**: One shot replaces another with motion
- **Match Cut**: Visual or thematic element matches across shots
- **J-Cut**: Audio from next shot begins before visual
- **L-Cut**: Audio from previous shot continues into next visual
- **Smash Cut**: Abrupt, jarring transition for effect

**Pacing Patterns:**

```
SLOW BUILD:
Shot 1: 8 sec → Shot 2: 6 sec → Shot 3: 5 sec → Shot 4: 4 sec

TENSION:
Shot 1: 3 sec → Shot 2: 2 sec → Shot 3: 2 sec → Shot 4: 1 sec

BREATHING ROOM:
Shot 1: 2 sec → Shot 2: 2 sec → Shot 3: 8 sec (moment of peace)
```

**Example Transition Note:**

```
SHOT 4 → SHOT 5 TRANSITION:
Type: Match Cut on Action
Details: As Sarah's hand reaches for cup (Shot 4), cut to barista's
         hands preparing latte (Shot 5). Hand motion matches across
         cut for seamless flow.
Audio: J-cut - espresso machine sound begins 0.5 sec before visual
```

### Step 8: Include Production Notes

Add practical guidance for shoot day:

**Production Categories:**

**Location Notes:**

- Address and parking
- Power availability
- Noise concerns
- Permits required
- Load-in logistics
- Backup locations

**Talent Notes:**

- Wardrobe requirements
- Makeup/hair notes
- Blocking and movement
- Emotional direction
- Safety considerations

**Props and Set Dressing:**

- Required items
- Backup options
- Continuity tracking
- Source/purchase info
- Set dressing details

**Equipment Checklist:**

- Camera body and lenses
- Support (tripod, gimbal, dolly)
- Lighting kit
- Audio gear
- Grip equipment
- Specialty items (crane, drone, slider)

**Timing and Schedule:**

- Setup time required
- Estimated shot duration
- Total scene time
- Critical time-of-day shots (magic hour, etc.)

**Example Production Note:**

```
SHOT 5: Latte Preparation ECU

LOCATION: Stellar Coffee, 123 Main St (confirmed booking 9am-12pm)
TALENT: Background extra as barista (casting: Maria T.)
WARDROBE: Neutral apron, black t-shirt (costume provides)
PROPS:
  - Ceramic latte cup (white, logo facing camera)
  - Stainless milk pitcher
  - BACKUP: 3 additional cups in case of spills
EQUIPMENT:
  - Canon R5 + 100mm f/2.8 macro lens
  - Tripod with fluid head
  - 2x LED panels with softboxes
  - Practical overhead pendant light (location provided)
TIMING: 10:15am (after wider shots), approx 20 min for shot
NOTES: Practice latte pour 3x before filming. Have towels ready
       for quick cleanup. Coordinate with actual cafe staff.
```

### Step 9: Create Visual Storyboard Frames

Design the actual storyboard illustrations:

**Frame Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ SHOT #5                                    DURATION: 4 SEC  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│            ┌─────────────────────────┐                      │
│            │                         │                      │
│            │   [VISUAL FRAME]        │                      │
│            │                         │                      │
│            │   Latte art being       │                      │
│            │   poured, hands ECU     │                      │
│            │                         │                      │
│            └─────────────────────────┘                      │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ SHOT TYPE: ECU                      CAMERA: 100mm, f/2.8   │
│ ANGLE: Slightly overhead            MOVEMENT: Static       │
│ LIGHTING: Soft key right, rim left  TRANSITION: Match cut  │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Barista's hands pour steamed milk into espresso,   │
│         creating rosetta pattern. Steam rises beautifully.  │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: SFX - steam hiss, milk pour | MUSIC: Indie folk     │
│ DIALOGUE: None                                              │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Coordinate with barista for perfect pour. Shoot 3x  │
│        to ensure we capture best latte art.                 │
└─────────────────────────────────────────────────────────────┘
```

**Visual Description Techniques:**

- Use simple shapes and stick figures for blocking
- Arrows indicate movement and eye flow
- Shading shows lighting direction
- Annotate key elements with labels
- Include camera position indicator
- Mark focus points

**Digital Tools Reference:**

- Storyboarder (free, open source)
- FrameForge (professional previz)
- Boords (online collaborative)
- Canva (template-based)
- Procreate/Photoshop (illustration)
- Shot Designer (blocking app)

### Step 10: Review and Finalize

Quality control and stakeholder approval:

**Review Checklist:**

**Technical Accuracy:**

- [ ] All shots numbered sequentially
- [ ] Camera specs are achievable with available equipment
- [ ] Lighting setups are practical for locations
- [ ] Shot durations add up to script timing
- [ ] Transitions are clearly marked

**Production Feasibility:**

- [ ] Locations are accessible and permitted
- [ ] Talent requirements are realistic
- [ ] Props are available or can be sourced
- [ ] Equipment is owned or rentable within budget
- [ ] Schedule allows adequate time per shot

**Story and Continuity:**

- [ ] Visual flow supports narrative
- [ ] Coverage provides editing options
- [ ] Continuity is maintained (wardrobe, props, positioning)
- [ ] Key story beats are visually emphasized
- [ ] Pacing matches intended emotional arc

**Stakeholder Alignment:**

- [ ] Client/director approves visual approach
- [ ] DP/cinematographer confirms technical feasibility
- [ ] Producer validates budget implications
- [ ] Editor provides input on coverage
- [ ] Department heads understand requirements

---

## Usage Examples

### Example 1: Commercial Product Shoot (30 seconds)

**Request:**
"Create a storyboard for a 30-second coffee maker commercial. Script focuses on morning routine, showing the ease and speed of the product. Target is upscale consumers, polished aesthetic."

**Generated Storyboard:**

```
═══════════════════════════════════════════════════════════════
                    RAPIDBREW COFFEE MAKER
              30-Second Commercial Storyboard
                  Total Shots: 12 | Duration: 30s
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ SHOT 1                                     DURATION: 2 SEC  │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │    ╔══════╗             │                      │
│            │    ║ BED  ║  Person     │                      │
│            │    ║      ║  sleeping   │                      │
│            │    ╚══════╝  peacefully │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: WS                            CAMERA: 35mm, f/2.0     │
│ ANGLE: Slightly high, bedroom       MOVEMENT: Slow push in │
│ LIGHTING: Soft morning light        TRANSITION: Fade from  │
│           through curtains                      black       │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Morning bedroom scene, alarm about to go off.      │
│         Golden hour light streams through curtains.         │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: MUSIC - Gentle piano (begins)                       │
│        SFX - Gentle alarm beep (end of shot)               │
│ DIALOGUE: None                                              │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Shoot during actual golden hour (6:30-7:00am).      │
│        Practical curtains must diffuse light beautifully.   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SHOT 2                                     DURATION: 1.5SEC │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │      ┌─┐                │                      │
│            │      │ │ Hand reaching  │                      │
│            │      └─┘ for alarm      │                      │
│            │    [ALARM CLOCK]        │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: CU                            CAMERA: 50mm, f/1.8     │
│ ANGLE: Eye level                    MOVEMENT: Static        │
│ LIGHTING: Same soft morning         TRANSITION: Cut         │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Hand enters frame and taps alarm clock off.        │
│         Focus on hand, clock slightly soft.                 │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: SFX - Alarm tap, silence                            │
│ DIALOGUE: None                                              │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Manicured hand (female, 30-45 demo), elegant.       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SHOT 3                                     DURATION: 3 SEC  │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │  Person  →→→            │                      │
│            │  walking    Kitchen     │                      │
│            │  ├─┤      [COUNTER]     │                      │
│            │  └─┘  [RAPIDBREW]       │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: MS → MCU                      CAMERA: 35mm, f/2.8     │
│ ANGLE: Eye level                    MOVEMENT: Dolly forward │
│                                                with subject │
│ LIGHTING: Bright modern kitchen     TRANSITION: Cut         │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Person walks into kitchen (bathrobe, relaxed),     │
│         approaches counter where RapidBrew sits. Camera     │
│         dollies forward to MCU as they reach coffee maker.  │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: MUSIC - Tempo slightly increases                    │
│        SFX - Soft footsteps on hardwood                     │
│ DIALOGUE: None                                              │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Modern, bright kitchen (white/gray palette). Ensure │
│        RapidBrew is prominently displayed, product lit.     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SHOT 4                                     DURATION: 2 SEC  │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │       ┌─┐  ↓            │                      │
│            │  ╔════╧═╧════╗          │                      │
│            │  ║ RAPIDBREW ║          │                      │
│            │  ║  [button] ║ PRESS    │                      │
│            │  ╚═══════════╝          │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: ECU                           CAMERA: 85mm, f/2.0     │
│ ANGLE: Slightly overhead            MOVEMENT: Static        │
│ LIGHTING: Key from left, product    TRANSITION: Cut on     │
│           beautifully lit                       action      │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Finger presses the single button on RapidBrew.     │
│         Button illuminates blue. Focus on button/logo.      │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: SFX - Satisfying button click, gentle beep          │
│        SFX - Machine begins to hum (transition)             │
│ DIALOGUE: None                                              │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Product close-up hero shot. Logo must be visible,   │
│        pristine. Blue LED practical light built into unit.  │
└─────────────────────────────────────────────────────────────┘

[Continue with Shots 5-12, showing:
- Coffee brewing in detail
- Person doing light morning tasks (60 sec timer visible)
- Coffee finishing
- Perfect pour into cup
- Steam rising
- First sip with satisfied expression
- Product shot with "RapidBrew: 60 seconds to perfect coffee"
- Logo and website]

═══════════════════════════════════════════════════════════════
PRODUCTION SUMMARY
═══════════════════════════════════════════════════════════════

LOCATIONS:
- Bedroom: Upscale modern bedroom with east-facing windows
- Kitchen: Contemporary kitchen, white/gray palette, excellent light

TALENT:
- Principal: Female, 30-45, professional, relatable
- Wardrobe: Elegant bathrobe (beginning), casual chic (later)

KEY PROPS:
- RapidBrew coffee maker (hero unit + backup)
- Modern alarm clock
- Coffee mug (brand approved design)
- Kitchen set dressing (minimal, high-end)

EQUIPMENT:
- Camera: Canon R5 or Sony A7S III
- Lenses: 35mm, 50mm, 85mm (all f/1.8-f/2.8)
- Dolly track (Shot 3)
- LED panels for product lighting
- Circular polarizer for reducing glare

SCHEDULE:
- Shoot Day: Golden hour start (6:30am bedroom shots)
- Kitchen scenes: 8:00am-12:00pm
- Total estimated: 6 hours including setup

SPECIAL NOTES:
- Coffee brewing shots may require multiple takes for perfect foam
- Product must be spotless - have cleaning supplies on set
- Steam effects - use hot water to ensure visible steam
- Color grade to warm, inviting morning atmosphere
```

### Example 2: Documentary Interview B-Roll

**Request:**
"Storyboard for documentary interview about urban gardening. Need B-roll storyboard to intercut with talking head. 10 shots covering the gardening process."

**Generated Storyboard:**

```
═══════════════════════════════════════════════════════════════
            URBAN ROOTS DOCUMENTARY - B-ROLL
                Interview Subject: Marcus Chen
              10 B-Roll Shots | Various Durations
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ B-ROLL 1: Garden Establishing                DURATION: 6SEC │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │ [BUILDINGS]             │                      │
│            │  ╔════╗  ╔════╗         │                      │
│            │  ║    ║  ║    ║         │                      │
│            │  ╚════╝  ╚════╝         │                      │
│            │  [ROOFTOP GARDEN]       │                      │
│            │   plants  plants        │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: EWS → WS                      CAMERA: 24mm, f/8       │
│ ANGLE: Eye level, rooftop           MOVEMENT: Slow pan R→L │
│ LIGHTING: Natural daylight          TRANSITION: L-cut from │
│           (afternoon)                           interview   │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Wide shot of rooftop garden with city skyline      │
│         in background. Pan reveals scope of garden project. │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: V.O. - Marcus discussing starting the garden        │
│        AMBIENT - Wind, distant city sounds                  │
│ DIALOGUE: (From interview) "I started with just four       │
│           planters on my rooftop..."                        │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Shoot on clear day, golden hour if possible. Need   │
│        drone/roof access for this angle.                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ B-ROLL 2: Hands in Soil                      DURATION: 4SEC │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │      ┌──────┐           │                      │
│            │  ┌───┤HANDS ├───┐       │                      │
│            │  │   └──────┘   │       │                      │
│            │  │   [SOIL]     │       │                      │
│            │  └──────────────┘       │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: ECU                           CAMERA: 100mm, f/2.8    │
│ ANGLE: Slightly overhead            MOVEMENT: Slow push in  │
│ LIGHTING: Natural + reflector       TRANSITION: Cut         │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Marcus's hands working rich, dark soil. Fingers    │
│         press soil around seedling. Dirt under fingernails. │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: V.O. - Marcus on connection to earth                │
│        SFX - Soil sounds, hands working                     │
│ DIALOGUE: "There's something healing about putting your    │
│           hands in the soil..."                             │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Capture authentic dirt, working hands. This shot    │
│        represents connection and labor.                     │
└─────────────────────────────────────────────────────────────┘

[Continue with B-Roll shots 3-10:
- Watering can pouring
- Tomato plants with fruit
- Community members arriving
- Harvest basket filling
- Children touching plants
- Compost system detail
- Marcus teaching volunteer
- Sunset over garden]

═══════════════════════════════════════════════════════════════
B-ROLL PRODUCTION NOTES
═══════════════════════════════════════════════════════════════

SHOT LIST STRATEGY:
- Mix of wide establishing and intimate details
- Capture garden through different times of day
- Include human element (hands, people, community)
- Show process: planting → growing → harvesting

EQUIPMENT:
- Camera: Documentary run-and-gun setup (Sony FX6)
- Lenses: 24-70mm f/2.8, 70-200mm f/2.8, 100mm macro
- Gimbal for smooth movement shots
- Circular polarizer for outdoor shots
- Reflector for close-up detail work

SCHEDULING:
- Multiple shoot days across growing season
- Golden hour shots for establishing (sunrise/sunset)
- Midday for detail work with controlled lighting
- Community events as they occur

EDITORIAL INTENT:
- B-roll illustrates interview points
- Pacing varies (contemplative to energetic)
- Show seasonal progression if possible
- Emphasize transformation (barren → abundant)
```

### Example 3: Music Video Chorus Section

**Request:**
"Storyboard for the chorus of an indie rock music video. Chorus is 30 seconds, repeats twice. Energetic, performance-based with creative angles."

**Generated Storyboard:**

```
═══════════════════════════════════════════════════════════════
          "BREAKING WAVES" - CHORUS STORYBOARD
           Artist: The Coastline | Duration: 30s
             Repeat: 2x (Chorus 1 & 2 variations)
═══════════════════════════════════════════════════════════════

CHORUS 1 (First iteration - 0:45-1:15)

┌─────────────────────────────────────────────────────────────┐
│ CH1-1: Lead Singer                       DURATION: 2.5 SEC  │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │     ╔═══╗               │                      │
│            │     ║ ◉ ║ Singer        │                      │
│            │     ║ │ ║ (dynamic)     │                      │
│            │     ╚═══╝               │                      │
│            │  [BACKLIT HAZE]         │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: MCU                           CAMERA: 50mm, f/1.8     │
│ ANGLE: Low angle, looking up        MOVEMENT: Handheld,    │
│                                              energetic       │
│ LIGHTING: Strong backlight,         TRANSITION: Beat-synced │
│           creating halo effect                cut from verse│
├─────────────────────────────────────────────────────────────┤
│ ACTION: Singer belts chorus opening, head tilted back,     │
│         passionate performance. Backlight creates haze.     │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: MUSIC - Chorus explosion (full band, high energy)   │
│ LYRICS: "Breaking waves crash over me..."                  │
├─────────────────────────────────────────────────────────────┤
│ NOTES: Cut on first drum hit of chorus. Backlight through  │
│        haze machine for ethereal effect.                    │
└─────────────────────────────────────────────────────────────┘

[Shots CH1-2 through CH1-12 showing:
- Drummer hitting snare (ECU, high speed)
- Bassist head bang (WS, Dutch angle)
- Guitar strings vibrating (ECU macro, 60fps)
- Full band (EWS, crane sweeping down)
- Lead vocal close-up (CU, emotional)
- Crowd (MS, jumping, handheld)
- Quick cuts building energy]

CHORUS 2 (Second iteration - 2:30-3:00)

[Similar structure but with variations:
- Different angles on same performances
- More extreme movements (whip pans, crash zooms)
- Additional practical effects (confetti, stage lighting)
- Faster cutting pace (1-1.5 sec per shot vs 2-2.5 sec)]

═══════════════════════════════════════════════════════════════
MUSIC VIDEO PRODUCTION NOTES
═══════════════════════════════════════════════════════════════

CREATIVE CONCEPT:
- High energy, raw performance aesthetic
- Mix of sharp, crisp shots and hazy, backlit atmosphere
- Color grade: Desaturated with teal/orange push
- Practical lighting effects (spotlights, haze, colored gels)

EQUIPMENT:
- 2x Cameras for coverage (primary + roaming handheld)
- 24mm, 35mm, 50mm, 85mm, 100mm macro lenses
- Gimbal + handheld for energy variety
- High-speed capability (60fps minimum, 120fps for inserts)
- Crane/jib for sweeping overhead shots

SHOOTING STRATEGY:
- Record full song multiple times (8-10 takes)
- First takes: scripted storyboard shots
- Later takes: Free-form experimentation
- Capture performance at multiple speeds (normal, 2x, 4x)
- Shoot inserts separately (hands, instruments, details)

LIGHTING DESIGN:
- Backlight: 2x 2K tungsten through haze
- Key: Moving head spotlights (practical, in-frame)
- Fill: Colored gels (teal, magenta) for mood
- Practicals: String lights, floor lamps (visible in shots)

POST-PRODUCTION:
- Beat-synced cutting (every 2 beats chorus 1, every beat chorus 2)
- Speed ramps on select shots
- Film grain overlay for texture
- Color: Desaturate 20%, push contrast, teal shadows/orange highlights
```

### Example 4: Animation Storyboard Sequence

**Request:**
"Storyboard for 20-second 2D animation showing a character discovering a magical book in a library. For pitch presentation."

**Generated Storyboard:**

```
═══════════════════════════════════════════════════════════════
      "THE LAST LIBRARY" - Discovery Scene Storyboard
           2D Animation Proof of Concept | 20 Seconds
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ PANEL 1                                    DURATION: 3 SEC  │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │  ╔═══╗ ╔═══╗ ╔═══╗     │                      │
│            │  ║:::║ ║:::║ ║:::║     │                      │
│            │  ╚═══╝ ╚═══╝ ╚═══╝     │                      │
│            │      [TALL BOOKSHELVES] │                      │
│            │        ┌─┐              │                      │
│            │   GIRL│●│→             │                      │
│            │        └─┘              │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: Wide Shot                     ANIMATION: Camera pan  │
│ ANGLE: Eye level (character POV)    TIMING: 24fps, on 2s   │
│ STYLE: Soft lighting, muted colors  TRANSITION: Fade in    │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Young girl (Mira, age 10) walks between towering   │
│         library shelves. Camera pans right following her    │
│         movement. She looks up in wonder at endless books.  │
├─────────────────────────────────────────────────────────────┤
│ ANIMATION NOTES:                                            │
│ - Walking cycle: 12 frames, on 2s (6 unique drawings)      │
│ - Background: Parallax scrolling (3 layers)                │
│ - Lighting: Dusty sunbeam from above, God rays              │
│ - Timing: Slow, contemplative pace                          │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: MUSIC - Mysterious, magical theme (woodwinds)       │
│        SFX - Soft footsteps on wood floor, ambient dust    │
├─────────────────────────────────────────────────────────────┤
│ COLOR PALETTE: Warm browns, amber light, dusty atmosphere  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PANEL 2                                    DURATION: 2 SEC  │
├─────────────────────────────────────────────────────────────┤
│            ┌─────────────────────────┐                      │
│            │       ╔═══╗             │                      │
│            │      ┌──┐ ║             │                      │
│            │  MIRA│◉ │ ║ One book   │                      │
│            │   CU └──┘ ║ glowing     │                      │
│            │       ╚═══╝ faintly     │                      │
│            └─────────────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│ SHOT: Medium Close-Up               ANIMATION: Hold + slow │
│ ANGLE: Straight on                           zoom in       │
│ STYLE: Focus on character reaction  TRANSITION: Cut        │
├─────────────────────────────────────────────────────────────┤
│ ACTION: Mira stops, noticing faint glow from one book     │
│         on middle shelf. Her eyes widen, curious.           │
├─────────────────────────────────────────────────────────────┤
│ ANIMATION NOTES:                                            │
│ - Expression change: neutral → curious (8 frames)           │
│ - Eye blink on frame 12                                     │
│ - Glow: Pulsing animation (16-frame loop, subtle)          │
│ - Camera: Slow push in (2 drawings, in-betweens)           │
│ - Hair: Gentle secondary motion (swaying)                   │
├─────────────────────────────────────────────────────────────┤
│ AUDIO: MUSIC - Single harp note as she notices             │
│        SFX - Subtle magical shimmer sound                   │
├─────────────────────────────────────────────────────────────┤
│ COLOR NOTE: Introduce cool blue/purple glow from book      │
└─────────────────────────────────────────────────────────────┘

[Panels 3-8 continue showing:
- Close-up of book with magical runes
- Mira's hand reaching (anticipation)
- Hand touches book (contact moment)
- Book bursts with golden light
- Mira's amazed expression illuminated
- Wide shot: magical energy spreading through library]

═══════════════════════════════════════════════════════════════
ANIMATION PRODUCTION SPECS
═══════════════════════════════════════════════════════════════

TECHNICAL SPECIFICATIONS:
- Frame Rate: 24fps
- Timing: Most animation on 2s (12 drawings/sec)
- Key moments: on 1s for smoothness (24 drawings/sec)
- Resolution: 1920x1080 (can scale to 4K)

ANIMATION COMPLEXITY:
- Full Animation: Character expressions, hands
- Limited Animation: Walking, secondary motion
- Held Frames: Background, static elements
- Effects Animation: Glows, magical energy (hand-drawn)

CHARACTER DESIGN NOTES:
- Mira: Simple, appealing design for animation efficiency
- Costume: Minimal folds, easy to draw consistently
- Expression: Large eyes for emotional range
- Style: Influenced by Studio Ghibli (grounded, relatable)

BACKGROUND DESIGN:
- Library: Atmospheric, detailed but not overwhelming
- Shelves: Repeating elements for efficiency
- Lighting: Painterly, mood-driven
- Color: Warm palette transitions to cool (magical reveal)

EFFECTS BREAKDOWN:
- Book glow: 16-frame pulsing loop (hand-drawn)
- Light burst: 32-frame explosion (effects animation)
- Dust particles: 3D rendered elements composited
- God rays: Digital effects in post

PRODUCTION PIPELINE:
1. Thumbnail storyboards (completed)
2. Animatic with temp audio (1 week)
3. Character design finals (1 week)
4. Background paintings (2 weeks)
5. Key animation (3 weeks)
6. In-betweening (2 weeks)
7. Cleanup (1 week)
8. Color (1 week)
9. Effects and compositing (2 weeks)
10. Final render and audio mix (1 week)

ESTIMATED BUDGET:
- Storyboard/Pre-production: $2,000
- Character Animation: $8,000
- Background Art: $3,000
- Effects and Compositing: $4,000
- Audio (music + SFX): $2,000
- Total: $19,000 for 20-second sequence
```

### Example 5: Social Media Story Sequence

**Request:**
"Instagram story sequence (3 stories, 15 seconds each) promoting a fitness app. Vertical format, fast-paced, engaging."

**Generated Storyboard:**

```
═══════════════════════════════════════════════════════════════
              FITLIFE APP - INSTAGRAM STORY ADS
         3-Part Sequence | 15 seconds each | 9:16 Vertical
═══════════════════════════════════════════════════════════════

STORY 1: "The Problem"

┌───────────────────────┐
│ FRAME 1  (0:00-0:03) │
├───────────────────────┤
│      ┌──────────┐    │
│      │  ╔══╗    │    │
│      │  ║  ║ CU │    │
│      │  ║  ║ Face│   │
│      │  ╚══╝    │    │
│      │  Frustrated   │
│      │  expression   │
│      └──────────┘    │
│                       │
│ TEXT: "6am alarm..."  │
│  (top, bold)          │
├───────────────────────┤
│ SHOT: CU vertical     │
│ Movement: Static      │
│ Lighting: Dim bedroom │
├───────────────────────┤
│ Person in bed, alarm  │
│ ringing, clearly not  │
│ motivated to work out │
└───────────────────────┘

┌───────────────────────┐
│ FRAME 2  (0:03-0:05) │
├───────────────────────┤
│      ┌──────────┐    │
│      │   ╔══╗   │    │
│      │   ║  ║   │    │
│      │   ╚══╝   │    │
│      │  [PHONE] │    │
│      │  in hand │    │
│      └──────────┘    │
│                       │
│ TEXT: "Too tired..."  │
│ "Too busy..."         │
│ "Tomorrow..."         │
│  (appearing rapidly)  │
├───────────────────────┤
│ SHOT: ECU phone      │
│ Movement: Shake/tilt  │
│ Effect: Fast cuts     │
├───────────────────────┤
│ Phone screen showing  │
│ generic fitness apps, │
│ person scrolls        │
│ dismissively          │
└───────────────────────┘

[Frames 3-5 continue establishing problem:
- Empty gym membership card
- Unused workout clothes
- Weight scale (avoid showing)
- Calendar with missed workout X's]

┌───────────────────────┐
│ FRAME 6  (0:12-0:15) │
├───────────────────────┤
│      ┌──────────┐    │
│      │ "WHAT IF │    │
│      │ WORKING  │    │
│      │ OUT WAS  │    │
│      │ ACTUALLY │    │
│      │  FUN?"   │    │
│      └──────────┘    │
│                       │
│ Background: Energetic│
│ burst animation       │
├───────────────────────┤
│ SHOT: Full screen    │
│ text animation        │
│ Movement: Zoom/pulse  │
├───────────────────────┤
│ Transition to Story 2 │
│ Swipe up prompt appears│
└───────────────────────┘

═══════════════════════════════════════════════════════════════

STORY 2: "The Solution"

┌───────────────────────┐
│ FRAME 1  (0:00-0:02) │
├───────────────────────┤
│      ┌──────────┐    │
│      │ [FITLIFE │    │
│      │   LOGO]  │    │
│      │          │    │
│      │  ╔════╗  │    │
│      │  ║APP ║  │    │
│      │  ║UI  ║  │    │
│      │  ╚════╝  │    │
│      └──────────┘    │
│                       │
│ TEXT: "Meet FitLife" │
├───────────────────────┤
│ SHOT: Screen record  │
│ Movement: App opening│
│ Style: Sleek, modern  │
├───────────────────────┤
│ Animated app opening  │
│ Smooth UI reveal      │
└───────────────────────┘

[Frames 2-6 show app features:
- 5-minute quick workouts
- Gamification (points, badges)
- Social challenges
- Progress tracking
- AI personalization
Each frame 2-3 seconds, fast-paced, energetic music]

═══════════════════════════════════════════════════════════════

STORY 3: "The Transformation"

[Frames showing user success stories, before/after energy levels,
social proof, ending with strong CTA and "Swipe Up" prompt]

═══════════════════════════════════════════════════════════════
VERTICAL VIDEO PRODUCTION NOTES
═══════════════════════════════════════════════════════════════

FORMAT SPECIFICATIONS:
- Aspect Ratio: 9:16 (1080x1920)
- Safe Areas: Keep critical content in middle 80%
- Text: Large, high contrast, readable on mobile
- Duration: 15 seconds each (max for non-ad stories)

SHOOTING GUIDELINES:
- Shoot vertically (hold phone vertical)
- Close-ups work best in vertical
- Subject centered or upper 2/3
- Avoid wide shots (poor use of frame)
- Embrace negative space top/bottom for text overlays

TEXT OVERLAYS:
- Font: Bold, sans-serif, high readability
- Size: Minimum 60pt
- Placement: Top or bottom third (avoid middle - faces)
- Animation: Quick, snappy (0.3sec in/out)
- Color: High contrast with background

PACING:
- Shot duration: 1-3 seconds max
- Quick cuts maintain attention
- Beat-synced to music
- Text appears on beat
- Transitions: Cuts, whip pans, swipes (native to platform)

CALL-TO-ACTION:
- Story 1: Build curiosity, no CTA
- Story 2: Soft introduction, "Learn More"
- Story 3: Strong CTA, "Swipe Up - Free Trial"
- Always include swipe-up graphic/arrow

MUSIC STRATEGY:
- Use trending Instagram audio library sounds
- Upbeat, high-energy
- Beat-synced cuts
- Volume: Loud enough to notice, quiet enough for dialogue

ENGAGEMENT TACTICS:
- Poll stickers ("Which workout time? Morning/Evening")
- Question stickers ("What's your fitness goal?")
- Countdown stickers ("Free trial ends in...")
- Emoji sliders ("How motivated are you? 😴→🔥")
```

---

## Quality Checklist

Before delivering storyboard:

**Visual Communication:**

- [ ] Each shot is clearly illustrated or described
- [ ] Camera angles and movements are specified
- [ ] Framing and composition notes are included
- [ ] Transitions between shots are marked
- [ ] Visual flow supports narrative

**Technical Specifications:**

- [ ] All camera specs are provided (lens, aperture, etc.)
- [ ] Lighting setups are detailed
- [ ] Equipment requirements are listed
- [ ] Shot durations are calculated
- [ ] Total timing matches script

**Production Readiness:**

- [ ] Locations are identified and feasible
- [ ] Talent requirements are specified
- [ ] Props and wardrobe are detailed
- [ ] Practical considerations addressed
- [ ] Budget implications understood

**Story and Coverage:**

- [ ] Key story moments are emphasized
- [ ] Adequate coverage for editing
- [ ] Continuity is maintained
- [ ] Pacing supports emotional arc
- [ ] Client/stakeholder intent reflected

**Documentation:**

- [ ] Shots are numbered sequentially
- [ ] Production notes are comprehensive
- [ ] Audio/dialogue is synchronized
- [ ] Special effects are detailed
- [ ] Export formats specified (if applicable)

---

## Best Practices

### Visual Clarity

- Use simple, clear illustrations or detailed descriptions
- Annotate key elements with labels
- Include composition guides (rule of thirds, etc.)
- Show camera position relative to subjects
- Indicate focus points and depth of field

### Coverage Planning

- Shoot master, medium, and close-ups for each scene
- Plan for reverses and cutaways
- Include transition shots
- Consider B-roll and inserts
- Build in safety shots (backups)

### Communication

- Use industry-standard terminology
- Be specific with directions
- Provide context for creative choices
- Include references when helpful
- Anticipate questions from crew

### Efficiency

- Group shots by location
- Batch similar setups
- Minimize company moves
- Plan for equipment changes
- Build realistic schedule

### Flexibility

- Include alternative shot options
- Note "nice to have" vs essential shots
- Plan for weather/location contingencies
- Build in buffer time
- Document improvisation opportunities

---

## Integration Points

### Integration with Other Commands

**From Video Script:**

```bash
# Create storyboard from existing video script
/scripts/storyboard --script /path/to/video-script.md
```

**To Shot List:**

```bash
# Export storyboard as production shot list
/scripts/storyboard --export-shotlist storyboard.md
```

**To Call Sheet:**

```bash
# Generate daily call sheet from storyboard
/scripts/storyboard --call-sheet --shoot-day 1
```

### Workflow Integration

**Pre-Production Pipeline:**

1. Script finalized → `/scripts/video`
2. Storyboard created → `/scripts/storyboard`
3. Shot list exported
4. Locations scouted
5. Equipment booked
6. Talent cast
7. Call sheets distributed
8. Production begins

**Client Approval Workflow:**

1. Generate initial storyboard
2. Present to client/stakeholders
3. Collect feedback
4. Revise storyboard
5. Final approval
6. Distribute to crew
7. Production proceeds

---

## Success Criteria

**Storyboard succeeds when:**

1. **Production Runs Smoothly:**
   - Crew understands all shots
   - Shoot stays on schedule
   - Minimal confusion or miscommunication
   - Equipment and locations are appropriate

2. **Client Satisfaction:**
   - Visual direction is clear and approved
   - Revisions are minimal
   - Expectations are aligned
   - Deliverable matches storyboard

3. **Post-Production Efficiency:**
   - Editor has all needed coverage
   - Story flows as planned
   - Minimal pickup shoots required
   - Vision is realized

4. **Budget Adherence:**
   - No cost overruns from poor planning
   - Realistic shot complexity
   - Efficient resource utilization
   - Contingencies accounted for

---

**Next Steps:**

1. Import video script or concept
2. Generate comprehensive storyboard
3. Review with director/cinematographer
4. Revise based on feedback
5. Distribute to production team
6. Use as guide during shoot
7. Reference in post-production

**Pro Tip:** Maintain a "director's notes" section in your storyboard for shot-specific creative intent, emotional goals, and reference inspiration. This context helps crew understand not just what to shoot, but why, leading to more cohesive creative execution.
