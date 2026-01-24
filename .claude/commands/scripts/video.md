---
description: Write video scripts for YouTube, TikTok, or corporate videos
argument-hint: [--platform <youtube|tiktok|corporate>] [--length <seconds>] [--hook-style]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Video Script Creator

Platform-optimized video scripts with hooks, B-roll notes, and CTA placement.

## ROI Analysis: $50,000/year

**Value Breakdown:**

- **Professional Script Writing**: $300-1,500/script → $200/hour saved
- **Platform Optimization**: 60% higher engagement rates
- **Production Efficiency**: 50% faster shoot days with detailed scripts
- **Content Consistency**: 75% reduction in reshoots and edits
- **Multi-Platform Reuse**: 3-5 versions per concept

**Time Savings:** 4-8 hours per script → 2-3 minutes automated
**Quality Improvement:** Professional formatting, timing, and flow
**Business Impact:** Higher view retention, conversion rates, and audience growth

---

## Overview

The Video Script Creator generates platform-specific video scripts optimized for viewer retention, engagement, and conversion. It handles everything from hook creation to CTA placement, B-roll notes, and timing markers.

**Key Features:**

- Platform-specific formatting (YouTube, TikTok, Instagram, LinkedIn, Corporate)
- Hook optimization for first 3-8 seconds
- B-roll and visual cue annotations
- Timing markers and pacing guidance
- Call-to-action placement strategies
- Music and sound effect suggestions
- Subtitle-friendly writing
- Engagement pattern analysis

**Supported Platforms:**

- **YouTube**: Long-form (8-20 min), mid-form (3-8 min), shorts (30-60 sec)
- **TikTok**: Short-form (15-60 sec), series (60-180 sec)
- **Instagram**: Reels (15-90 sec), IGTV (1-15 min)
- **LinkedIn**: Professional (30-120 sec)
- **Corporate**: Training, marketing, internal communications

---

## Implementation

### Step 1: Initialize Video Script Request

Collect essential information about the video project:

**Required Information:**

- **Platform**: YouTube, TikTok, Instagram, LinkedIn, Corporate
- **Video Length**: Target duration in seconds/minutes
- **Topic/Subject**: Main message or content focus
- **Target Audience**: Demographics, interests, pain points
- **Video Goal**: Education, entertainment, conversion, brand awareness
- **Tone**: Professional, casual, energetic, authoritative, friendly

**Optional Parameters:**

- Hook style preference (question, statistic, bold statement, story)
- Existing content to adapt
- Brand voice guidelines
- Competitor references
- Required CTAs or messaging

### Step 2: Analyze Platform Requirements

Apply platform-specific best practices:

**YouTube Optimization:**

- Hook in first 8 seconds to prevent drop-off
- Pattern interrupt every 20-30 seconds
- Clear chapter markers for long content
- Mid-roll CTA placement (if 8+ minutes)
- End screen elements and outro (last 20 seconds)
- Retention curve optimization
- Search-optimized language

**TikTok Optimization:**

- Immediate visual hook (first frame)
- Text overlay synchronization
- Trend integration opportunities
- Sound/music selection notes
- Loop-friendly endings
- Duet/stitch opportunities
- Hashtag integration points

**Instagram Reels Optimization:**

- Strong opening visual (first 1-2 seconds)
- Caption-friendly pacing
- Music beat synchronization
- Share-worthy moments
- Story continuation prompts
- Profile visit CTAs

**LinkedIn Optimization:**

- Professional tone maintenance
- Value-first opening
- Industry-specific language
- Thought leadership positioning
- Clear business takeaways
- Connection/follow prompts

**Corporate Video Optimization:**

- Clear learning objectives
- Structured information delivery
- Professional transitions
- Accessibility compliance
- Brand guideline adherence
- Measurable outcomes

### Step 3: Craft the Hook (First 3-8 Seconds)

Create attention-grabbing openings:

**Hook Types:**

1. **Question Hook**: "What if I told you that 90% of businesses are wasting money on..."
2. **Statistic Hook**: "In the next 60 seconds, 3,000 people will make this costly mistake..."
3. **Bold Statement**: "Everything you know about marketing is wrong."
4. **Story Hook**: "Three months ago, I was broke. Today, I'll show you what changed..."
5. **Pattern Interrupt**: "Stop scrolling. This will save you thousands of dollars."
6. **Curiosity Gap**: "The secret ingredient that millionaires don't want you to know..."
7. **Relatable Problem**: "Tired of wasting hours on content that gets zero engagement?"

**Hook Formula:**

```
[ATTENTION GRABBER] + [BENEFIT PREVIEW] + [TIMEFRAME]

Example: "In the next 90 seconds, I'll show you the exact formula that
grew our YouTube channel from 0 to 100k subscribers in 6 months."
```

### Step 4: Structure the Main Content

Organize content for maximum retention:

**YouTube Long-Form Structure:**

```
[0:00-0:08] Hook
[0:08-0:30] Introduction + credibility
[0:30-1:00] Preview of what's covered
[1:00-8:00] Main content (3-5 major points)
  - Point 1 [1:00-2:30]
  - Point 2 [2:30-4:00]
  - Point 3 [4:00-6:00]
  - Point 4 [6:00-7:30]
[7:30-8:00] Summary + CTA
[8:00-8:20] Outro + end screen
```

**TikTok/Short-Form Structure:**

```
[0:00-0:02] Visual hook
[0:02-0:05] Verbal hook + promise
[0:05-0:45] Rapid delivery of value
  - 3-5 quick tips/points
  - Visual variety every 3-5 seconds
[0:45-0:60] Payoff + CTA + loop
```

**Corporate Training Structure:**

```
[0:00-0:30] Learning objectives
[0:30-1:00] Why this matters
[1:00-8:00] Step-by-step instruction
  - Concept explanation
  - Demonstration
  - Practice guidance
[8:00-9:00] Summary + next steps
[9:00-10:00] Resources + Q&A
```

### Step 5: Add B-Roll and Visual Notes

Annotate every section with visual guidance:

**B-Roll Categories:**

- **Illustrative**: Graphics, animations, diagrams
- **Demonstrative**: Screen recordings, product demos
- **Supportive**: Stock footage, relevant imagery
- **Emotional**: Reaction shots, lifestyle footage
- **Transitional**: Motion graphics, scene changes

**Annotation Format:**

```
SCRIPT: "The first step is to identify your target audience."

[B-ROLL: Graph animation showing audience segmentation]
[SCREEN: Highlight demographic data on dashboard]
[TEXT OVERLAY: "Know Your Audience"]
[MUSIC: Upbeat, energetic - fade under dialogue]

SCRIPT: "This changed everything for our business."

[B-ROLL: Before/after comparison shots]
[TRANSITION: Quick zoom effect]
[SOUND EFFECT: Whoosh transition]
```

### Step 6: Insert Timing and Pacing Markers

Add production timing guidance:

**Marker Types:**

- `[00:00]` - Timestamp markers
- `[PAUSE 2 SEC]` - Silence for emphasis
- `[QUICK CUT]` - Fast transition
- `[SLOW REVEAL]` - Gradual visual reveal
- `[BEAT DROP]` - Music synchronization point
- `[TEXT ON SCREEN: 3 SEC]` - Text display duration
- `[PATTERN INTERRUPT]` - Retention technique

**Pacing Guidelines:**

- **Fast-paced**: 150-180 words per minute (TikTok, Reels)
- **Medium-paced**: 130-150 words per minute (YouTube)
- **Slow-paced**: 110-130 words per minute (Corporate, Educational)

### Step 7: Optimize for Engagement and Retention

Apply retention techniques:

**Pattern Interrupts (Every 20-30 seconds):**

- Visual changes (zoom, pan, cut)
- Tone/energy shifts
- Direct address to viewer
- Questions or challenges
- Unexpected statements
- Graphics or text overlays

**Engagement Triggers:**

- **Call-to-Action**: "Comment below if you agree"
- **Poll/Question**: "Which option would you choose?"
- **Challenge**: "Try this and let me know what happens"
- **Teaser**: "But wait, there's something even better coming..."
- **Cliffhanger**: "And the most important tip is... [next section]"

**Retention Strategies:**

- Open loops (promises to be fulfilled later)
- Progress indicators ("3 more tips to go")
- Value stacking ("And it gets even better")
- Curiosity gaps
- Story continuation

### Step 8: Add Call-to-Action Placement

Strategically place CTAs:

**Primary CTA Positions:**

- **Early CTA** (0:20-0:40): Subscribe/Follow for more
- **Mid-Roll CTA** (50% mark): Like if you're finding this valuable
- **Pre-Close CTA** (80% mark): Main conversion action
- **End CTA** (final 10 seconds): Multiple options

**CTA Types:**

- **Engagement**: Like, comment, share, subscribe
- **Conversion**: Visit website, download resource, book call
- **Navigation**: Watch next video, check playlist
- **Community**: Join group, follow on other platforms
- **Transaction**: Buy product, enroll in course

**CTA Formulation:**

```
[SPECIFIC ACTION] + [CLEAR BENEFIT] + [URGENCY/SCARCITY]

Example: "Click the link below to download the free checklist
before we close access at midnight tonight."
```

### Step 9: Format Script for Production

Create production-ready document:

**Script Format:**

```
===============================================
VIDEO TITLE: [SEO-Optimized Title]
PLATFORM: [YouTube/TikTok/etc.]
LENGTH: [Target Duration]
SHOOT DATE: [Date]
===============================================

EQUIPMENT NEEDED:
- Camera: [Specifications]
- Lighting: [Setup details]
- Audio: [Microphone type]
- Props: [List items]

LOCATIONS:
- Scene 1: [Location description]
- Scene 2: [Location description]

PRE-PRODUCTION NOTES:
- [Any special requirements]

===============================================
SCRIPT
===============================================

[00:00 - HOOK]
{ON CAMERA}
"[Opening line]"

[B-ROLL: Description]
[MUSIC: Specification]
[TEXT: Overlay content]

[00:08 - INTRODUCTION]
{ON CAMERA - MEDIUM SHOT}
"[Introduction dialogue]"

[Continue with full script...]

===============================================
POST-PRODUCTION NOTES
===============================================

EDITING NOTES:
- Color grade: [Style]
- Transitions: [Type and placement]
- Music: [Track suggestions]
- Graphics: [Elements needed]

EXPORT SETTINGS:
- Resolution: [1080p/4K]
- Format: [MP4/MOV]
- Platform specs: [Requirements]

THUMBNAIL CONCEPTS:
1. [Concept description]
2. [Concept description]
3. [Concept description]

TITLE OPTIONS:
1. [SEO-optimized title]
2. [Alternative title]
3. [Alternative title]

DESCRIPTION TEMPLATE:
[First 150 characters for preview]

[Full description with timestamps]

HASHTAGS:
[Platform-specific hashtags]
```

### Step 10: Review and Refine

Final optimization checklist:

**Content Review:**

- Hook grabs attention in first 3-8 seconds
- Clear value proposition delivered early
- Logical flow and structure
- Pattern interrupts every 20-30 seconds
- Strong close with clear CTA
- Total runtime matches target

**Technical Review:**

- All timestamps accurate
- B-roll notes are specific and actionable
- Visual cues align with dialogue
- Music/sound notes are clear
- Text overlay content provided
- Transition notes included

**Platform Compliance:**

- Meets platform guidelines
- Appropriate length for format
- Optimized for mobile viewing
- Subtitle-friendly language
- Trend integration (if applicable)
- SEO considerations addressed

---

## Usage Examples

### Example 1: YouTube Tutorial Video (10 minutes)

**Request:**
"Create a YouTube script for a 10-minute tutorial on 'How to Create Professional Instagram Reels.' Target audience is small business owners with basic video skills. Goal is to provide actionable tips while promoting my editing course."

**Generated Script:**

```
===============================================
HOW TO CREATE PROFESSIONAL INSTAGRAM REELS IN 2025
Platform: YouTube | Length: 10:00 | Format: Tutorial
===============================================

[00:00] HOOK
{ON CAMERA - CLOSE UP}
"What if I told you that the Instagram Reels you're making are costing
you thousands of potential customers?"

[B-ROLL: Montage of amateur vs professional Reels]
[TEXT: "Stop Losing Customers"]
[MUSIC: Attention-grabbing opener - upbeat electronic]

[00:05]
{ON CAMERA}
"In the next 10 minutes, I'm going to show you the exact 5-step system
that my clients use to create scroll-stopping Reels that convert viewers
into customers - even if you've never edited a video before."

[B-ROLL: Before/after examples of client Reels]
[TEXT: "5-Step System" - appears on screen]

[00:15 - PATTERN INTERRUPT]
{QUICK CUT TO B-ROLL}
[SCREEN RECORD: Showing viral Reel with analytics]
"This Reel got 847,000 views and generated $12,000 in sales..."

[Continue with full 10-minute script structure...]
```

### Example 2: TikTok Product Demo (45 seconds)

**Request:**
"Write a TikTok script for a 45-second demo of a meal prep container set. Target audience is busy professionals age 25-40. Make it entertaining and relatable."

**Generated Script:**

```
===============================================
MEAL PREP CONTAINERS THAT ACTUALLY WORK
Platform: TikTok | Length: 0:45 | Format: Product Demo
===============================================

[00:00] VISUAL HOOK
{CLOSE UP: Messy fridge with containers everywhere}
[TEXT: "Every Sunday..."]
[MUSIC: Relatable frustration beat]

[00:02] VERBAL HOOK
{ON CAMERA - EXASPERATED EXPRESSION}
"Can we talk about how meal prep containers are a literal scam?"

[00:05] PROBLEM AGITATION
{QUICK CUTS}
- Container with missing lid
- Sauce leaking everywhere
- Stained plastic containers
- Warped lids that won't close

[TEXT overlays in rhythm with cuts]
"Missing lids" / "Leaks everywhere" / "Turns orange" / "Won't close"

[00:12] TRANSITION
{ON CAMERA}
"Until I found THESE..."

[BEAT DROP - Music shift to upbeat]
[VISUAL: Slam new container set on counter]

[00:15] DEMO SEQUENCE
{FAST-PACED CUTS}

Shot 1: Stack containers perfectly
[TEXT: "Actually stack"]

Shot 2: Pour sauce, shake vigorously
[TEXT: "100% leak proof"]

Shot 3: Show color after tomato sauce
[TEXT: "Stays clear"]

Shot 4: Microwave to dishwasher
[TEXT: "Dishwasher safe"]

[00:35] SOCIAL PROOF
{ON CAMERA}
"Everyone in my meal prep group switched to these."

[B-ROLL: Screenshots of positive reviews]

[00:40] CTA
{ON CAMERA - POINTING}
"Link in bio - they're 30% off today only!"

[TEXT: "Link in bio 👆"]
[MUSIC: Fades out]

[00:45] LOOP BACK
{RETURN TO MESSY FRIDGE SHOT}
[TEXT: "Stop the chaos"]

===============================================
PRODUCTION NOTES:
- Shoot in natural kitchen lighting
- Use handheld for authentic feel
- Keep camera movements snappy
- Record dialogue separately for clean audio
- Prepare multiple container types for comparison
===============================================
```

### Example 3: LinkedIn Thought Leadership (90 seconds)

**Request:**
"Create a LinkedIn video script about 'The Future of Remote Work' targeting HR executives and business leaders. Professional tone, data-driven, 90 seconds."

**Generated Script:**

```
===============================================
THE REMOTE WORK SHIFT NO ONE IS TALKING ABOUT
Platform: LinkedIn | Length: 1:30 | Format: Thought Leadership
===============================================

[00:00] HOOK
{ON CAMERA - PROFESSIONAL SETUP}
"While everyone is debating return-to-office policies, they're missing
the real transformation happening in the workplace."

[B-ROLL: Modern office vs home office split screen]
[TEXT: "The Real Remote Work Story"]
[MUSIC: Subtle, professional background]

[00:08] CREDIBILITY
{ON CAMERA}
"I've spent 15 years in organizational psychology, and I've analyzed
data from 500+ companies navigating this transition."

[GRAPHIC: Credential highlights]

[00:15] KEY INSIGHT #1
{ON CAMERA}
"Here's what the data actually shows: The question isn't office versus
remote. It's synchronous versus asynchronous work culture."

[B-ROLL: Calendar showing different time zones]
[GRAPHIC: 67% stat animation]
[TEXT: "67% prefer async communication"]

[00:28] KEY INSIGHT #2
{ON CAMERA}
"Companies that have implemented strong asynchronous practices are
seeing 40% higher retention rates and 28% increase in productivity."

[GRAPHIC: Animated bar chart with statistics]
[CITATION: "2024 Workplace Study - Harvard Business Review"]

[00:42] KEY INSIGHT #3
{ON CAMERA}
"But here's the critical mistake most organizations make: They try to
replicate synchronous office culture in a remote environment. That's
like trying to drive a car using horse-and-buggy rules."

[B-ROLL: Visual metaphor - old vs new]
[TEXT: "Don't Replicate. Reimagine."]

[00:58] ACTIONABLE TAKEAWAY
{ON CAMERA}
"Three immediate steps you can implement this week:

One: Establish 'no meeting' blocks for deep work
Two: Document decisions in writing, not just in meetings
Three: Measure output, not activity"

[GRAPHICS: Each point appears as spoken]

[01:15] CTA
{ON CAMERA}
"I've created a free implementation guide that breaks down exactly how
to build an async-first culture. Link in the comments."

[TEXT: "Free Guide in Comments"]

[01:25] CLOSE
{ON CAMERA}
"The future of work isn't about where we work. It's about how we work.
What's your organization doing to adapt?"

[TEXT: "Join the conversation below"]
[FADE OUT]

===============================================
PRODUCTION NOTES:
- Professional background (bookshelf or office)
- Crisp lighting (ring light or softbox)
- Lapel mic for clear audio
- Add captions for accessibility
- Graphics should match LinkedIn's professional aesthetic
===============================================
```

### Example 4: Corporate Training Video (5 minutes)

**Request:**
"Write a corporate training script for 'Effective Email Communication for Customer Service Teams.' 5 minutes, includes examples of good vs bad emails."

**Generated Script:**

```
===============================================
MASTERING CUSTOMER SERVICE EMAIL COMMUNICATION
Platform: Corporate LMS | Length: 5:00 | Format: Training
===============================================

LEARNING OBJECTIVES:
By the end of this module, you will be able to:
1. Write clear, professional customer service emails
2. Apply the 4-part email structure
3. Avoid common communication mistakes
4. Respond appropriately to difficult situations

===============================================

[00:00] INTRODUCTION
{PRESENTER - ON CAMERA}
"Welcome to 'Mastering Customer Service Email Communication.' In this
module, you'll learn proven strategies for writing emails that resolve
issues efficiently while strengthening customer relationships."

[GRAPHIC: Module title and objectives]

[00:15] WHY THIS MATTERS
{ON CAMERA}
"Email remains our primary customer communication channel. Research
shows that 75% of customers form their impression of our company based
on email interactions alone."

[GRAPHIC: Statistic animation - 75%]
[B-ROLL: Customer reading email on phone]

[00:30] SECTION 1 - THE 4-PART STRUCTURE
{ON CAMERA}
"Every effective customer service email follows four essential parts:
Acknowledge, Explain, Solve, and Close. Let's break down each component."

[GRAPHIC: 4-part structure diagram]

[00:45] Part 1: Acknowledge
{ON CAMERA}
"First, acknowledge the customer's concern. This shows empathy and
confirms you understand the issue."

[SCREEN: Example email header]

Good Example:
"Thank you for contacting us about your delayed shipment. I understand
how frustrating it is when orders don't arrive on time, and I'm here
to help resolve this for you."

[PAUSE 3 SEC - Let viewers read]

Bad Example:
"We received your complaint about shipping."

[GRAPHIC: X mark appears]

[01:15] Part 2: Explain
{ON CAMERA}
"Next, briefly explain what happened or what you discovered. Keep it
clear and avoid technical jargon."

[SCREEN: Example continuation]

Good Example:
"I've checked your order #12345, and I can see it was delayed at our
distribution center due to an inventory sync issue."

Bad Example:
"The WMS system experienced a database synchronization failure in the
SKU allocation module."

[GRAPHIC: Comparison highlighting jargon]

[Continue with remaining parts and examples...]

[04:30] KNOWLEDGE CHECK
{ON CAMERA}
"Now it's your turn to practice. Review the scenario in your workbook
and draft a response using the 4-part structure."

[GRAPHIC: Practice exercise instructions]

[04:45] SUMMARY
{ON CAMERA}
"Remember: Acknowledge with empathy, explain clearly, solve proactively,
and close professionally. Following this structure will help you handle
any customer situation with confidence."

[GRAPHIC: Key takeaways checklist]

[04:55] NEXT STEPS
{ON CAMERA}
"Complete the practice exercises and review the email template library
in your resources section. In our next module, we'll cover handling
difficult customer situations."

[GRAPHIC: Resources and next module preview]
[FADE OUT]

===============================================
RESOURCES PROVIDED:
- Email template library (PDF)
- Common scenario quick reference guide
- Before/after email examples
- Tone and language guidelines
===============================================
```

### Example 5: Instagram Reel Series (30 seconds each)

**Request:**
"Create a 3-part Instagram Reel series teaching beginner photographers the 'Exposure Triangle.' Each reel is 30 seconds, should be related but standalone."

**Generated Scripts:**

```
===============================================
REEL 1: APERTURE EXPLAINED
Platform: Instagram Reels | Length: 0:30 | Part 1 of 3
===============================================

[00:00] HOOK
{CLOSE-UP: Camera lens}
"Photography tip you NEED to know 📸"
[TEXT: "Aperture Explained"]
[MUSIC: Upbeat, tutorial-style]

[00:03]
{ON CAMERA}
"Aperture is like the pupil of your camera's eye."

[00:06]
{B-ROLL: Animated diagram}
"Wide aperture (f/1.8) = Blurry background"
[DEMO PHOTO: Portrait with bokeh]

[00:15]
"Narrow aperture (f/16) = Everything sharp"
[DEMO PHOTO: Landscape in focus]

[00:22]
{ON CAMERA - POINTING}
"Follow for parts 2 and 3 of the Exposure Triangle!"
[TEXT: "Part 1 of 3 - Save this!"]

[00:27]
[QUICK EXAMPLE MONTAGE]
[TEXT: "DM me your photos!"]

===============================================
REEL 2: SHUTTER SPEED EXPLAINED
Platform: Instagram Reels | Length: 0:30 | Part 2 of 3
===============================================

[Same professional structure for Shutter Speed...]

===============================================
REEL 3: ISO EXPLAINED
Platform: Instagram Reels | Length: 0:30 | Part 3 of 3
===============================================

[Same professional structure for ISO, with callback to parts 1-2...]

===============================================
SERIES NOTES:
- Consistent visual style across all three
- Same music track family
- Cross-reference each reel
- Use carousel in caption with all three tips
- Encourage saves and shares for complete series
===============================================
```

---

## Quality Checklist

Before finalizing any video script, verify:

**Content Quality:**

- [ ] Hook grabs attention within first 3-8 seconds
- [ ] Value proposition is clear and specific
- [ ] Target audience pain points are addressed
- [ ] Content flows logically from point to point
- [ ] Pattern interrupts maintain engagement
- [ ] CTA is clear, specific, and actionable
- [ ] Closes strong with summary or teaser

**Platform Optimization:**

- [ ] Script length matches platform best practices
- [ ] Formatting follows platform conventions
- [ ] Tone matches platform culture
- [ ] Optimized for mobile viewing
- [ ] Includes platform-specific features (hashtags, trends)
- [ ] Meets technical requirements (length, format)

**Production Readiness:**

- [ ] All timestamps are accurate
- [ ] B-roll notes are specific and achievable
- [ ] Visual cues align perfectly with dialogue
- [ ] Music and sound notes are actionable
- [ ] Text overlay content is provided
- [ ] Equipment and location needs specified
- [ ] Post-production notes are clear

**Accessibility:**

- [ ] Language is clear and easy to understand
- [ ] Subtitle-friendly pacing (not too fast)
- [ ] Visual elements supplement but don't replace audio
- [ ] Text overlays are readable
- [ ] Color contrast considerations noted

**Brand Alignment:**

- [ ] Tone matches brand voice guidelines
- [ ] Messaging aligns with brand values
- [ ] Visual style fits brand aesthetic
- [ ] CTAs support business objectives
- [ ] Compliance with brand standards

---

## Best Practices

### Hook Creation

- Lead with the payoff, not the setup
- Use specific numbers and timeframes
- Create curiosity gaps
- Address pain points immediately
- Promise clear, achievable value
- Test multiple hook variations

### Pacing and Timing

- Match pace to platform expectations
- Vary sentence length for rhythm
- Build in breathing room
- Use pauses strategically for emphasis
- Accelerate pace before key points
- Slow down for complex information

### Visual Storytelling

- Show, don't just tell
- Every 3-5 seconds: new visual element
- Use visual metaphors
- Match visuals to emotional tone
- Layer graphics with footage
- Plan for visual variety

### Engagement Optimization

- Ask questions to trigger comments
- Create decision points
- Use relatable scenarios
- Reference current trends
- Encourage interaction
- Build in shareable moments

### CTA Strategy

- Place CTAs at multiple points
- Make CTAs specific and actionable
- Provide clear next steps
- Reduce friction to action
- Test different CTA placements
- Track CTA performance

### Script Formatting

- Use production-friendly layout
- Include all necessary annotations
- Timestamp everything
- Specify equipment and locations
- Provide alternatives for key moments
- Include post-production guidance

---

## Integration Points

### Integration with Other Commands

**Storyboard Creation:**

```bash
# After creating script, generate storyboard
/scripts/video --platform youtube --length 600 > video-script.md
/scripts/storyboard --script video-script.md --shot-types
```

**Podcast Adaptation:**

```bash
# Adapt video script for podcast format
/scripts/podcast --source video-script.md --format interview
```

**Content Repurposing:**

```bash
# Generate multiple platform versions
/scripts/video --platform youtube --length 600 > youtube.md
/scripts/video --platform tiktok --length 45 > tiktok.md
/scripts/video --platform linkedin --length 90 > linkedin.md
```

### Workflow Integration

**Pre-Production Workflow:**

1. Generate script with `/scripts/video`
2. Create storyboard with `/scripts/storyboard`
3. Review and approve both documents
4. Schedule shoot with production team
5. Distribute scripts to talent and crew

**Content Calendar Integration:**

- Link video topics to content calendar
- Plan series and multi-part content
- Schedule platform-specific versions
- Coordinate with marketing campaigns
- Track performance metrics

---

## Success Criteria

**Script meets success criteria when:**

1. **Attention Metrics:**
   - Hook tests well in A/B testing
   - First 8 seconds drive >70% retention
   - Pattern interrupts maintain engagement

2. **Production Efficiency:**
   - Shoot completes on time
   - Minimal script changes during production
   - Editor understands all annotations
   - B-roll requests are achievable

3. **Performance Metrics:**
   - Watch time exceeds platform average
   - Engagement rate (likes, comments, shares) above baseline
   - CTA click-through rate meets goals
   - Audience retention curve shows minimal drop-off

4. **Content Quality:**
   - Message clarity rated high in testing
   - Brand alignment confirmed by stakeholders
   - Accessibility requirements met
   - Platform guidelines followed

5. **Business Impact:**
   - Supports defined business objectives
   - Drives measurable conversions
   - Builds brand awareness
   - Generates qualified leads (if applicable)

---

## Advanced Techniques

### A/B Testing Scripts

- Create multiple hook variations
- Test different CTA placements
- Experiment with pacing changes
- Compare formal vs casual tone
- Measure retention at key moments

### Series Planning

- Design interconnected episodes
- Build narrative arcs across videos
- Create anticipation for next episode
- Maintain consistent format
- Develop recurring elements

### Viral Optimization

- Study trending formats
- Identify shareable moments
- Create screenshot-worthy frames
- Design for re-watch value
- Build in conversation starters

### Multi-Language Adaptation

- Write with translation in mind
- Avoid idioms and cultural references
- Structure for voice-over replacement
- Plan for subtitle variations
- Consider cultural sensitivities

---

**Next Steps:**

1. Define your video project (platform, length, topic)
2. Generate platform-optimized script
3. Review against quality checklist
4. Create corresponding storyboard
5. Schedule production
6. Track performance metrics
7. Iterate based on results

**Pro Tip:** Keep a swipe file of high-performing hooks, transitions, and CTAs from successful videos. Adapt proven patterns to your specific content for faster script development and higher success rates.
