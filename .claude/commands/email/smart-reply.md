---
description: AI-powered context-aware email responses with tone matching and multi-draft generation
argument-hint: "[--email-id <id>] [--tone <professional|friendly|brief>] [--drafts <count>]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Smart Email Reply Command

## Overview

AI-powered email response generation that analyzes email context, thread history, sender relationship, and your communication patterns to draft perfect replies. Saves 1-2 hours/day on email composition.

**Part of Phase 3**: Motion + AI Autopilot integration

## What This Command Does

- ✅ Analyzes email context and full thread history
- ✅ Understands sender relationship (client, colleague, vendor, etc.)
- ✅ Matches your writing style and tone
- ✅ Generates 2-3 draft responses with different approaches
- ✅ Incorporates relevant context (calendar, tasks, previous emails)
- ✅ Suggests optimal response time (immediate vs scheduled)
- ✅ **Saves 1-2 hours/day on email responses**

## Usage

```bash
# Smart reply to current email
/email:smart-reply

# Reply to specific email
/email:smart-reply --email-id "msg_abc123"

# With tone preference
/email:smart-reply --tone professional
/email:smart-reply --tone friendly
/email:smart-reply --tone brief

# Generate multiple drafts
/email:smart-reply --drafts 3

# Schedule reply for optimal time
/email:smart-reply --schedule-optimal
```

## AI Email Intelligence

The AI analyzes:

1. **Email Context**:
   - Subject line and main content
   - Sender and recipients
   - Full thread history
   - Attachments and links
   - Urgency indicators

2. **Relationship Context**:
   - Sender type (client, colleague, manager, vendor)
   - Communication history
   - Typical response patterns
   - Formality level

3. **Your Context**:
   - Calendar (upcoming meetings with sender)
   - Tasks related to email topic
   - Previous similar emails you've sent
   - Your writing style and vocabulary

4. **Business Context**:
   - Current projects with sender
   - Deadlines and commitments
   - Open action items
   - Recent interactions

## Implementation Details

### Step 1: Fetch and Analyze Email

```javascript
// Fetch email via Gmail MCP
const email = await mcp.gmail.getMessage({
  id: emailId || getCurrentEmailId(),
  format: 'full' // Get full content including thread
});

// Fetch thread history
const thread = await mcp.gmail.getThread({
  id: email.threadId,
  format: 'full'
});

// Analyze sender relationship
const senderContext = await analyzeSenderRelationship(email.from);
// Returns: { type: 'client', formality: 'high', history: [...] }
```

### Step 2: Gather Relevant Context

```javascript
// Search for related calendar events
const upcomingMeetings = await mcp.calendar.searchEvents({
  query: email.from.email,
  timeMin: new Date().toISOString(),
  timeMax: addDays(new Date(), 7).toISOString()
});

// Search for related tasks
const relatedTasks = await mcp.notion.search({
  query: extractKeywords(email.subject),
  filter: { property: 'Type', select: { equals: 'Task' } }
});

// Find previous similar emails
const similarEmails = await mcp.gmail.search({
  query: `from:${email.from.email} subject:"${extractKeywords(email.subject)}"`,
  maxResults: 5
});

// Build context package
const contextPackage = {
  currentEmail: email,
  threadHistory: thread.messages,
  senderContext: senderContext,
  upcomingMeetings: upcomingMeetings,
  relatedTasks: relatedTasks,
  similarEmails: similarEmails,
  yourWritingStyle: await loadWritingStyleProfile()
};
```

### Step 3: AI Generates Draft Responses

```javascript
const draftResponses = await claude.generateEmailReplies({
  prompt: `Generate ${options.drafts || 2} email reply drafts based on this context.

  INCOMING EMAIL:
  From: ${email.from.name} <${email.from.email}>
  Subject: ${email.subject}
  Date: ${email.date}

  Body:
  ${email.body}

  THREAD HISTORY (${thread.messages.length} messages):
  ${formatThreadHistory(thread.messages)}

  SENDER CONTEXT:
  Type: ${senderContext.type} (client|colleague|manager|vendor)
  Formality Level: ${senderContext.formality}
  Communication History: ${senderContext.history.length} previous emails
  Last Interaction: ${senderContext.lastInteraction}

  RELEVANT CONTEXT:
  Upcoming Meetings:
  ${upcomingMeetings.map(m => `• ${m.summary} - ${m.start.dateTime}`).join('\n')}

  Related Tasks:
  ${relatedTasks.map(t => `• ${t.properties.Name.title[0].text.content}`).join('\n')}

  YOUR WRITING STYLE:
  Tone: ${writingStyle.tone}
  Average Length: ${writingStyle.avgLength} words
  Common Phrases: ${writingStyle.commonPhrases.join(', ')}
  Signature: ${writingStyle.signature}

  USER PREFERENCES:
  Preferred Tone: ${options.tone || 'match sender'}
  Formality: ${senderContext.formality}

  TASK: Generate ${options.drafts || 2} reply drafts with different approaches:

  Draft 1: ${getDraftStrategy(1, senderContext, options)}
  Draft 2: ${getDraftStrategy(2, senderContext, options)}
  ${options.drafts >= 3 ? `Draft 3: ${getDraftStrategy(3, senderContext, options)}` : ''}

  For each draft, provide:
  {
    "subject": "Re: [subject]" or new subject if needed,
    "body": "Full email body with greeting and signature",
    "tone": "professional|friendly|brief",
    "approach": "Description of this draft's strategy",
    "pros": ["Advantage 1", "Advantage 2"],
    "cons": ["Potential downside 1"],
    "recommendedSendTime": "immediate|in_2_hours|tomorrow_morning",
    "reasoning": "Why this send time"
  }

  REQUIREMENTS:
  • Match the user's writing style (tone, length, vocabulary)
  • Address all points from the incoming email
  • Include relevant context (meetings, tasks, previous discussions)
  • Be concise but complete
  • Use appropriate formality level
  • Include clear next steps if action required
  • Add signature automatically
  `
});

// Example draft strategies:
// Draft 1: Professional and comprehensive (addresses all points)
// Draft 2: Brief and action-oriented (gets to the point)
// Draft 3: Friendly and conversational (builds relationship)
```

### Step 4: Present Drafts to User

```javascript
console.log(`
🤖 AI SMART REPLY: "${email.subject}"

Analyzed:
  • Email content and ${thread.messages.length}-message thread
  • Sender: ${email.from.name} (${senderContext.type})
  • ${upcomingMeetings.length} upcoming meetings
  • ${relatedTasks.length} related tasks
  • Your writing style from ${writingStyle.sampleSize} previous emails

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DRAFT 1: Professional & Comprehensive ⭐ RECOMMENDED

Approach: Addresses all points thoroughly, maintains professional tone

${draftResponses[0].body}

✅ Pros:
   • Addresses all questions raised
   • Professional and thorough
   • Includes relevant meeting reference
   • Sets clear expectations

⚠️  Cons:
   • Slightly longer (~${countWords(draftResponses[0].body)} words)
   • May be too formal for casual relationships

📤 Recommended Send Time: ${draftResponses[0].recommendedSendTime}
   Reasoning: ${draftResponses[0].reasoning}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DRAFT 2: Brief & Action-Oriented

Approach: Gets straight to the point, emphasizes next steps

${draftResponses[1].body}

✅ Pros:
   • Concise and actionable (~${countWords(draftResponses[1].body)} words)
   • Clear next steps
   • Respects recipient's time

⚠️  Cons:
   • May seem too brief for important clients
   • Less relationship-building

📤 Recommended Send Time: ${draftResponses[1].recommendedSendTime}
   Reasoning: ${draftResponses[1].reasoning}

${options.drafts >= 3 ? `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DRAFT 3: Friendly & Conversational

Approach: Warm tone, builds relationship while addressing business

${draftResponses[2].body}

✅ Pros:
   • Friendly and approachable
   • Builds rapport
   • Personal touch

⚠️  Cons:
   • May be too casual for formal clients
   • Slightly longer

📤 Recommended Send Time: ${draftResponses[2].recommendedSendTime}
   Reasoning: ${draftResponses[2].reasoning}
` : ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Which draft would you like to use?
[1] Use Draft 1 (Professional)
[2] Use Draft 2 (Brief)
${options.drafts >= 3 ? '[3] Use Draft 3 (Friendly)\n' : ''}[e] Edit before sending
[r] Regenerate with different tone
[s] Schedule for later
[c] Cancel
`);
```

### Step 5: Send or Schedule Reply

```javascript
// User selects Draft 1
const selectedDraft = draftResponses[0];

// Option 1: Send immediately
if (userChoice === '1' || userChoice === '2' || userChoice === '3') {
  const draftIndex = parseInt(userChoice) - 1;
  const draft = draftResponses[draftIndex];

  // Create draft in Gmail
  const gmailDraft = await mcp.gmail.createDraft({
    to: email.from.email,
    cc: email.cc,
    subject: draft.subject,
    body: draft.body,
    threadId: email.threadId, // Reply in thread
    inReplyTo: email.messageId,
    references: email.references
  });

  console.log(`
✓ Draft created in Gmail

📧 To: ${email.from.name} <${email.from.email}>
📋 Subject: ${draft.subject}
📝 Body: ${countWords(draft.body)} words

Next Actions:
[1] Send now → Send immediately
[2] Review in Gmail → Opens draft in browser
[3] Edit → Make changes
[4] Schedule → Send at optimal time (${draft.recommendedSendTime})
  `);
}

// Option 2: Schedule for optimal time
if (userChoice === 's' || userSelectedSchedule) {
  const sendTime = calculateOptimalSendTime(
    draft.recommendedSendTime,
    senderContext,
    email
  );

  // Schedule via Gmail scheduled send
  await mcp.gmail.scheduleSend({
    draftId: gmailDraft.id,
    scheduledTime: sendTime
  });

  console.log(`
✓ Email scheduled for optimal send time

📧 To: ${email.from.name}
⏰ Scheduled: ${formatDateTime(sendTime)}
   (${draft.recommendedSendTime})

Why this time:
${draft.reasoning}

The email will be sent automatically at this time.
You can edit or cancel the scheduled send in Gmail.
  `);
}
```

### Step 6: Learn from Feedback

```javascript
// Track which drafts user chooses
await logEmailReplyChoice({
  emailId: email.id,
  selectedDraft: draftIndex,
  tone: draft.tone,
  approach: draft.approach,
  senderType: senderContext.type,
  edited: userMadeEdits,
  sent: true
});

// AI learns over time:
// - Which tones you prefer for different sender types
// - Which draft approaches you select most often
// - Common edits you make (learn your preferences)
// - Optimal send times that work best
```

## Email Intelligence Features

### Tone Matching

```javascript
// AI matches your writing style
const writingStyle = {
  tone: 'professional-friendly', // Analyzed from sent emails
  avgLength: 120, // Average words per email
  commonPhrases: [
    'Thanks for reaching out',
    'Let me know if you need anything else',
    'Looking forward to'
  ],
  formalityByRecipient: {
    'client': 0.8, // 0-1 scale
    'colleague': 0.5,
    'manager': 0.7
  },
  signature: '\n\nBest regards,\nYour Name\nTitle'
};

// AI adapts drafts to match this style
```

### Context Integration

```javascript
// AI includes relevant context automatically
const contextInclusion = {
  // If meeting scheduled
  meeting: `I see we have a meeting scheduled for ${meeting.start}. We can discuss this further then.`,

  // If task exists
  task: `I've added this to my task list and will have it completed by ${task.due}.`,

  // If previous commitment
  commitment: `As we discussed in my email on ${previousEmail.date}, I'll...`,

  // If attachment needed
  attachment: `I've attached the ${documentName} we discussed.`
};
```

### Optimal Send Timing

```javascript
// AI suggests when to send
const optimalSendTime = (email, senderContext) => {
  // Urgent client email → Immediate
  if (email.urgent && senderContext.type === 'client') {
    return 'immediate';
  }

  // Late evening email → Tomorrow morning
  if (new Date().getHours() > 18) {
    return 'tomorrow_morning'; // 9 AM next day
  }

  // Weekend email → Monday morning
  if (isWeekend(new Date())) {
    return 'monday_morning';
  }

  // Non-urgent → 2 hours (shows thoughtfulness, not too eager)
  return 'in_2_hours';
};
```

## Integration with Other Commands

### With `/workflow:email-to-task`

```bash
# Email contains action items
# AI: "This email has action items. Should I create tasks?"
# → Creates tasks while drafting reply
# → Reply references the created tasks
```

### With `/schedule:smart`

```bash
# Email: "Can we schedule a call?"
# AI draft includes: "I've found 3 times that work..."
# → One-click to schedule via /schedule:smart
```

### With `/autopilot:predict-tasks`

```bash
# Email: "Lease renewal coming up"
# AI: Creates predicted task for lease renewal
# Reply: "I've scheduled the lease renewal for..."
```

## Business Value

**Time Savings**:

- Manual email composition: 5-10 min per email
- Smart reply: 30-60 seconds (review + send)
- Average professional: 40-60 emails/day
- **Saves 1-2 hours/day = 5-10 hours/week**

**Quality Improvements**:

- Consistent tone and professionalism
- Never forgets to address all points
- Includes relevant context automatically
- Optimal send timing
- Reduces back-and-forth (more complete responses)

**Productivity Gains**:

- Faster email processing
- Better response quality
- Less mental fatigue from email writing
- **Value: $750-1,500/week**

## Success Metrics

✅ Draft generation time <10 seconds
✅ User selects AI draft >80% of time
✅ Edits required <20% of drafts
✅ Response quality score >8/10
✅ Time savings >1 hour/day

## Advanced Features

### Multi-Language Support

```bash
# Incoming email in Spanish
/email:smart-reply --language es

# AI detects language automatically and replies in same language
```

### Template Learning

```bash
# AI learns your templates
# Common email types:
# - Meeting confirmation
# - Project update
# - Status inquiry response
# - Deadline extension request

# AI detects type and applies learned template
```

### Attachment Handling

```bash
# AI suggests attaching relevant files
# "You mentioned the proposal - I found 'Q1-Proposal.pdf' in Drive. Attach?"
```

### Multi-Recipient Intelligence

```bash
# Email with multiple recipients
# AI adjusts tone for group context
# Considers reply-all vs direct reply
```

## Related Commands

- `/google:email` - Basic Gmail operations
- `/email:triage` - Morning email automation
- `/workflow:email-to-task` - Email → Task conversion
- `/schedule:smart` - AI meeting scheduling
- `/capture` - Quick capture email content

## Notes

**Privacy**: Your email content is only used to generate drafts. No data is stored beyond learning your style preferences.

**Learning Period**: AI needs 1-2 weeks to learn your writing style accurately.

**Offline**: Drafts are created in Gmail - you can edit/send from any device.

**API Costs**: ~$0.05-0.10 per email reply (Claude Sonnet API calls).

---

*Never spend 10 minutes crafting an email again. AI drafts it in 10 seconds.*
