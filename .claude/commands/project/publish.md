---
description: Generate marketing content from project and publish to GCP buckets for multiple audiences
allowed-tools: ["Bash", "Read", "Write", "Glob", "Grep"]
argument-hint: <project-path> [--audiences b2c,b2b,investor,internal] [--preview-only] [--version major|minor|patch] [--tone professional|casual|technical|enthusiastic] [--skip-approval]
---

# /project:publish - Project Marketing Showcase Publisher

Generate AI-powered marketing content from software projects and publish to GCP storage buckets for multiple audiences (B2C, B2B, Investor, Internal).

## Usage

```bash
/project:publish <project-path> [options]
```

### Options

- `--audiences <list>` - Comma-separated audience types (default: b2c,b2b)
  - `b2c`: Consumer-focused (ease of use, quick value, social proof)
  - `b2b`: Enterprise-focused (ROI, security, scalability, integration)
  - `investor`: Fundraising-focused (market size, traction, competitive advantage)
  - `internal`: Technical documentation (architecture, development, team notes)

- `--preview-only` - Generate content but don't publish to GCP (review mode)

- `--version <type>` - Version increment type (default: minor)
  - `major`: Breaking changes or major release (1.0.0 → 2.0.0)
  - `minor`: New features (1.0.0 → 1.1.0)
  - `patch`: Bug fixes or small updates (1.0.0 → 1.0.1)

- `--tone <style>` - Content tone (default: professional)
  - `professional`: Business-appropriate, formal
  - `casual`: Friendly, conversational
  - `technical`: Detailed, developer-focused
  - `enthusiastic`: Energetic, exciting

- `--skip-approval` - Skip manual review and publish directly (use with caution)

## Examples

```bash
# Basic usage - B2C and B2B audiences
/project:publish ./my-awesome-project

# Preview mode only (no publishing)
/project:publish ./my-project --preview-only

# Publish to all audiences with casual tone
/project:publish ./my-saas-app --audiences b2c,b2b,investor,internal --tone casual

# Major version release for investors
/project:publish ./my-startup --audiences investor --version major

# Quick patch update for B2C
/project:publish ./my-app --audiences b2c --version patch --skip-approval
```

## Workflow

This command orchestrates a 7-step workflow:

1. **Project Analysis** (2-3 min) - Extract metadata from project files
2. **AI Content Generation** (5-8 min) - Generate marketing content with Claude
3. **User Review** (Interactive) - Preview and edit generated content
4. **Approval Confirmation** - Confirm publishing targets
5. **Template Rendering** (2-4 min) - Render HTML with Handlebars
6. **GCP Upload** (3-5 min per bucket) - Publish to selected buckets
7. **Success Output** - Display URLs and next steps

---

## Implementation

### Step 1: Parse Arguments and Validate

```typescript
const args = process.argv.slice(2);
const projectPath = args[0];

if (!projectPath) {
  console.error('❌ Error: Project path is required');
  console.log('Usage: /project:publish <project-path> [options]');
  process.exit(1);
}

// Parse options
const options = {
  audiences: (args.find(a => a.startsWith('--audiences='))?.split('=')[1]?.split(',') || ['b2c', 'b2b']) as AudienceType[],
  previewOnly: args.includes('--preview-only'),
  versionType: (args.find(a => a.startsWith('--version='))?.split('=')[1] || 'minor') as 'major' | 'minor' | 'patch',
  tone: (args.find(a => a.startsWith('--tone='))?.split('=')[1] || 'professional') as 'professional' | 'casual' | 'technical' | 'enthusiastic',
  skipApproval: args.includes('--skip-approval'),
};

console.log('🚀 Starting project marketing showcase generation...');
console.log(`📁 Project: ${projectPath}`);
console.log(`👥 Audiences: ${options.audiences.join(', ')}`);
console.log(`🎨 Tone: ${options.tone}`);
console.log(`📦 Version: ${options.versionType}`);
console.log('');
```

### Step 2: Project Analysis

```typescript
import { ProjectAnalyzerService } from '../services/ProjectAnalyzerService';

console.log('🔍 Step 1/7: Analyzing project...');

const analyzer = new ProjectAnalyzerService();
let metadata: ProjectMetadata;

try {
  metadata = await analyzer.analyzeProject(projectPath);

  console.log(`✅ Project detected: ${metadata.name} (${metadata.projectType})`);
  console.log(`   Version: ${metadata.version}`);
  console.log(`   Features: ${metadata.features.length} found`);
  console.log(`   Tech stack: ${metadata.techStack.map(t => t.name).join(', ')}`);
  console.log(`   Screenshots: ${metadata.screenshots.length} found`);
  console.log('');
} catch (error) {
  console.error('❌ Project analysis failed:', error.message);
  process.exit(1);
}
```

### Step 3: AI Content Generation (Per Audience)

```typescript
import { MarketingContentGenerator } from '../services/MarketingContentGenerator';

console.log('🤖 Step 2/7: Generating marketing content with AI...');

const generator = new MarketingContentGenerator();
const generatedContent: Map<AudienceType, ProjectShowcaseData> = new Map();
const qualityScores: Map<AudienceType, ContentQualityScore> = new Map();

for (const audience of options.audiences) {
  console.log(`   Generating ${audience.toUpperCase()} content...`);

  try {
    const content = await generator.generateShowcaseContent(metadata, {
      audience,
      tone: options.tone,
      length: 'standard',
      includeMetrics: true,
      includePricing: audience !== 'internal',
      includeTestimonials: audience !== 'internal',
    });

    generatedContent.set(audience, content);

    // Calculate quality score
    const score = await generator.calculateQualityScore(content);
    qualityScores.set(audience, score);

    console.log(`   ✅ ${audience.toUpperCase()}: Generated (Quality: ${score.overall.toFixed(1)}/10)`);
  } catch (error) {
    console.error(`   ❌ ${audience.toUpperCase()}: Generation failed - ${error.message}`);
  }
}

console.log('');
```

### Step 4: User Review and Editing (Interactive)

```typescript
if (!options.skipApproval) {
  console.log('👀 Step 3/7: Review generated content');
  console.log('');

  for (const [audience, content] of generatedContent.entries()) {
    const score = qualityScores.get(audience)!;

    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`📄 ${audience.toUpperCase()} CONTENT PREVIEW`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log('');
    console.log(`🎯 HERO SECTION`);
    console.log(`   Headline: ${content.hero.headline}`);
    console.log(`   Subheadline: ${content.hero.subheadline}`);
    if (content.hero.badge) console.log(`   Badge: ${content.hero.badge}`);
    console.log('');

    if (content.metrics) {
      console.log(`📊 VALUE METRICS`);
      content.metrics.items.forEach(m => {
        console.log(`   ${m.value} - ${m.label}`);
      });
      console.log('');
    }

    console.log(`✨ FEATURES (${content.features.items.length} total)`);
    content.features.items.slice(0, 3).forEach(f => {
      console.log(`   • ${f.title}: ${f.description.substring(0, 60)}...`);
    });
    console.log('');

    console.log(`📈 QUALITY SCORE: ${score.overall.toFixed(1)}/10`);
    console.log(`   Benefit-focused: ${score.breakdown.benefitFocused.toFixed(1)}/10`);
    console.log(`   Concrete metrics: ${score.breakdown.concreteMetrics.toFixed(1)}/10`);
    console.log(`   SEO optimization: ${score.breakdown.seoOptimization.toFixed(1)}/10`);
    console.log(`   Visual appeal: ${score.breakdown.visualAppeal.toFixed(1)}/10`);
    console.log(`   Call-to-action: ${score.breakdown.callToAction.toFixed(1)}/10`);

    if (score.recommendations.length > 0) {
      console.log('');
      console.log(`💡 RECOMMENDATIONS:`);
      score.recommendations.forEach(rec => console.log(`   • ${rec}`));
    }

    console.log('');
  }

  // Ask for approval
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');

  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const approved = await new Promise<boolean>((resolve) => {
    readline.question('✋ Do you approve this content for publishing? (yes/no): ', (answer: string) => {
      readline.close();
      resolve(answer.toLowerCase() === 'yes' || answer.toLowerCase() === 'y');
    });
  });

  if (!approved) {
    console.log('');
    console.log('❌ Publishing cancelled by user');
    console.log('💡 Tip: Content has been saved as drafts in the database');
    console.log('   You can review and edit via the web UI, then publish later');
    process.exit(0);
  }

  console.log('');
  console.log('✅ Content approved for publishing');
  console.log('');
}
```

### Step 5: Template Rendering

```typescript
import { TemplateRenderingService } from '../services/TemplateRenderingService';

console.log('🎨 Step 4/7: Rendering HTML templates...');

const renderer = new TemplateRenderingService();
const renderedHtml: Map<AudienceType, string> = new Map();

for (const [audience, content] of generatedContent.entries()) {
  console.log(`   Rendering ${audience.toUpperCase()}...`);

  try {
    let html = await renderer.renderProjectShowcase(content);

    // Optimize assets (lazy loading, preconnect)
    html = renderer.optimizeAssets(html);

    // Validate HTML
    const validation = renderer.validateHtml(html);
    if (!validation.valid) {
      console.warn(`   ⚠️  HTML validation warnings for ${audience}:`);
      validation.errors.forEach(err => console.warn(`      - ${err}`));
    }

    renderedHtml.set(audience, html);
    console.log(`   ✅ ${audience.toUpperCase()}: Rendered (${(html.length / 1024).toFixed(1)} KB)`);
  } catch (error) {
    console.error(`   ❌ ${audience.toUpperCase()}: Rendering failed - ${error.message}`);
  }
}

console.log('');
```

### Step 6: Preview Mode Check

```typescript
if (options.previewOnly) {
  console.log('👁️  Preview mode enabled - Saving HTML files locally...');
  console.log('');

  const previewDir = path.join(projectPath, '.claude-preview');
  await fs.mkdir(previewDir, { recursive: true });

  for (const [audience, html] of renderedHtml.entries()) {
    const filename = `${metadata.name}-${audience}.html`;
    const filepath = path.join(previewDir, filename);
    await fs.writeFile(filepath, html, 'utf-8');
    console.log(`   📄 Saved: ${filepath}`);
  }

  console.log('');
  console.log('✅ Preview files saved successfully');
  console.log(`📁 Location: ${previewDir}`);
  console.log('💡 Tip: Open these files in a browser to preview before publishing');
  console.log('');
  console.log('🚀 Ready to publish? Run without --preview-only flag:');
  console.log(`   /project:publish ${projectPath} --audiences ${options.audiences.join(',')}`);
  process.exit(0);
}
```

### Step 7: GCP Upload and Publishing

```typescript
import { PublishingService } from '../services/PublishingService';
import { GCPStorageService } from '../services/GCPStorageService';
import { Pool } from 'pg';

console.log('☁️  Step 5/7: Publishing to GCP buckets...');

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const publishingService = new PublishingService(pool);

const publishingResults: PublishingResult[] = [];

for (const [audience, html] of renderedHtml.entries()) {
  console.log(`   📤 Uploading ${audience.toUpperCase()}...`);

  try {
    // Determine bucket name based on audience
    const bucketName = process.env[`GCP_BUCKET_${audience.toUpperCase()}`] || `content-${audience}`;

    // Generate object path with version
    const objectPath = `projects/${metadata.name}/${audience}/index.html`;

    // Upload HTML to GCP
    const uploadStart = Date.now();
    const publicUrl = await GCPStorageService.uploadFromBuffer(
      bucketName,
      objectPath,
      Buffer.from(html, 'utf-8'),
      {
        contentType: 'text/html; charset=utf-8',
        metadata: {
          projectName: metadata.name,
          projectVersion: metadata.version,
          audience,
          generatedAt: new Date().toISOString(),
        },
        public: audience === 'b2c',  // B2C is public, others require auth
        cacheControl: 'public, max-age=3600',
      }
    );
    const uploadDuration = Date.now() - uploadStart;

    // Generate signed URL for non-public audiences
    let signedUrl: string | undefined;
    if (audience !== 'b2c') {
      const expiresIn = audience === 'b2b' ? 86400 : 3600;  // 24h for B2B, 1h for others
      signedUrl = await GCPStorageService.generateSignedUrl(
        bucketName,
        objectPath,
        { action: 'read', expires: expiresIn }
      );
    }

    // Create database records
    const content = generatedContent.get(audience)!;
    const contentId = await publishingService.createContentRecord(
      metadata.name,
      audience,
      content,
      bucketName,
      objectPath
    );

    const eventId = await publishingService.createPublishingEvent(
      contentId,
      audience,
      bucketName,
      objectPath,
      publicUrl,
      {
        version: metadata.version,
        versionType: options.versionType,
        fileSize: html.length,
        uploadDuration,
      }
    );

    publishingResults.push({
      audience,
      contentId,
      eventId,
      url: publicUrl,
      signedUrls: signedUrl ? { default: signedUrl } : undefined,
      success: true,
    });

    console.log(`   ✅ ${audience.toUpperCase()}: Published (${uploadDuration}ms)`);
    console.log(`      URL: ${publicUrl}`);
    if (signedUrl) {
      console.log(`      Signed URL: ${signedUrl.substring(0, 80)}...`);
    }
  } catch (error) {
    console.error(`   ❌ ${audience.toUpperCase()}: Upload failed - ${error.message}`);
    publishingResults.push({
      audience,
      contentId: '',
      eventId: '',
      url: '',
      success: false,
      error: error.message,
    });
  }
}

await pool.end();
console.log('');
```

### Step 8: Success Output and Next Steps

```typescript
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('✅ PUBLISHING COMPLETE');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('');

const successCount = publishingResults.filter(r => r.success).length;
const failureCount = publishingResults.filter(r => !r.success).length;

console.log(`📊 Results: ${successCount} successful, ${failureCount} failed`);
console.log('');

if (successCount > 0) {
  console.log('🌐 Published URLs:');
  console.log('');

  for (const result of publishingResults.filter(r => r.success)) {
    console.log(`   ${result.audience.toUpperCase()}:`);
    console.log(`   • Public URL: ${result.url}`);
    if (result.signedUrls?.default) {
      console.log(`   • Signed URL: ${result.signedUrls.default.substring(0, 70)}...`);
      const expiresIn = result.audience === 'b2b' ? '24 hours' : '1 hour';
      console.log(`     (Expires in ${expiresIn})`);
    }
    console.log('');
  }
}

if (failureCount > 0) {
  console.log('❌ Failed:');
  for (const result of publishingResults.filter(r => !r.success)) {
    console.log(`   ${result.audience.toUpperCase()}: ${result.error}`);
  }
  console.log('');
}

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('📚 Next Steps:');
console.log('');
console.log('   1. 📊 View analytics (coming soon)');
console.log(`      /project:analytics ${metadata.name}`);
console.log('');
console.log('   2. 🔄 Update content');
console.log(`      /project:publish ${projectPath} --version patch`);
console.log('');
console.log('   3. ⏪ Rollback if needed');
console.log(`      /project:rollback ${metadata.name} --audience b2c`);
console.log('');
console.log('   4. 🌐 Share with your audience!');
console.log('');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

process.exit(successCount === publishingResults.length ? 0 : 1);
```

---

## Requirements

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:pass@host:5432/db
GCP_PROJECT_ID=your-project-id
GCP_KEY_FILE=/path/to/service-account-key.json

# GCP Bucket Configuration
GCP_BUCKET_B2C=content-b2c
GCP_BUCKET_B2B=content-b2b
GCP_BUCKET_INVESTOR=content-investor
GCP_BUCKET_INTERNAL=content-internal
```

### Database Migration

Run migration `016-marketing-showcase.sql` before using this command.

### Dependencies

```json
{
  "@anthropic-ai/sdk": "^0.28.0",
  "@google-cloud/storage": "^7.7.0",
  "handlebars": "^4.7.8",
  "pg": "^8.11.3"
}
```

---

## Error Handling

- **Project not found**: Clear error with path validation
- **GCP auth failure**: Setup instructions with gcloud commands
- **Bucket access error**: Verify bucket exists and permissions
- **Upload failure**: Automatic retry (3 attempts, exponential backoff)
- **Partial failure**: Rollback successful uploads
- **Database errors**: Transaction ROLLBACK, clear error messages

---

## Performance

- **Project analysis**: 2-3 minutes
- **AI generation**: 5-8 minutes per audience (parallel processing)
- **Template rendering**: 2-4 minutes
- **GCP upload**: 3-5 minutes per bucket
- **Total workflow**: 15-25 minutes for 2 audiences

---

## Security

- API keys never logged or exposed
- Signed URLs for authenticated audiences (B2B: 24h, Investor: 1h, Internal: 1h)
- Approval workflow prevents accidental publishing
- Complete audit trail in database
- Rate limiting per tenant

---

## Related Commands

- `/project:analytics` - View content performance metrics
- `/project:rollback` - Rollback to previous version
- `/project:update` - Update existing content
- `/devops:monitor` - Monitor GCP infrastructure

---

**Generated with Claude Code**
