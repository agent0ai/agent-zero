---
description: Rotate JWT signing keys, API keys, and secrets with zero downtime
argument-hint: [--key-type jwt|api|all] [--graceful-transition]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Task, AskUserQuestion
---

Rotate authentication keys: **${ARGUMENTS}**

## Key Rotation Strategies

**JWT Signing Keys** - Rotate public/private key pairs (RS256)
**API Keys** - Rotate API authentication keys
**Database Credentials** - Rotate database passwords
**OAuth Secrets** - Rotate OAuth client secrets
**Graceful Transition** - Dual-key support during rotation

## Integration Points

**Security Workflow**:

- `/auth/audit` → Detects old keys → Recommends rotation
- `/devops/setup` → Stores new keys in Secret Manager
- `/devops/deploy` → Updates services with new keys

**Compliance**:

- PCI DSS: Rotate keys every 90 days
- HIPAA: Rotate keys annually or on security event
- SOC 2: Document key rotation procedures

## Rotate Keys Safely

Routes to **gcp-security-compliance** for safe key rotation:

```javascript
await Task({
  subagent_type: 'gcp-security-compliance',
  description: 'Rotate authentication keys',
  prompt: `Rotate authentication keys: ${KEY_TYPE || 'all'}

Graceful transition: ${GRACEFUL ? 'enabled' : 'disabled'}

Execute zero-downtime key rotation:

1. **Pre-Rotation Validation**:
   - Check current keys are accessible
   - Verify Secret Manager permissions
   - Identify all services using keys
   - Plan rotation strategy (graceful or immediate)

2. **Generate New Keys**:
   ${KEY_TYPE === 'jwt' || KEY_TYPE === 'all' ? `
   **JWT Signing Keys** (RS256):
   - Generate new 4096-bit RSA key pair
   - Store private key in Secret Manager
   - Store public key in application config
   - Tag with rotation timestamp
   ` : ''}

   ${KEY_TYPE === 'api' || KEY_TYPE === 'all' ? `
   **API Keys**:
   - Generate new cryptographically secure key
   - Store in Secret Manager with versioning
   - Tag with expiry date
   ` : ''}

3. **Graceful Transition** (if enabled):
   ${GRACEFUL ? `
   - Deploy new key as secondary key
   - Accept tokens signed with BOTH old and new keys
   - Monitor usage of old vs new keys
   - Wait for all old tokens to expire
   - Remove old key after grace period
   ` : `
   - Replace old key with new key immediately
   - Invalidate all existing tokens
   - Force users to re-authenticate
   `}

4. **Update Services**:
   - Update Secret Manager versions
   - Deploy configuration changes
   - Restart services if needed
   - Verify new keys work

5. **Validation**:
   - Generate test token with new key
   - Validate test token
   - Check service health
   - Monitor error rates

6. **Cleanup**:
   - Mark old keys as "rotated" (keep for audit)
   - Update key rotation log
   - Document rotation timestamp
   - Schedule next rotation (90 days)

Provide rotation report:
- New key IDs
- Services updated
- Old key status
- Next rotation date
  `
})
```

## JWT Key Rotation (RS256)

```bash
#!/bin/bash
# rotate-jwt-keys.sh

GRACEFUL=${1:-true}
PROJECT_ID=$(gcloud config get-value project)

echo "========================================="
echo "JWT KEY ROTATION"
echo "========================================="
echo "Graceful transition: $GRACEFUL"
echo "========================================="

# 1. Generate new RSA key pair
echo "Generating new RSA key pair (4096-bit)..."

openssl genrsa -out private_key_new.pem 4096
openssl rsa -in private_key_new.pem -pubout -out public_key_new.pem

echo "✓ New key pair generated"

# 2. Upload to Secret Manager
echo "Uploading keys to Secret Manager..."

# Private key (never commit to git!)
gcloud secrets create jwt-private-key-v2 \
  --data-file=private_key_new.pem \
  --project=$PROJECT_ID \
  --labels=rotated_at=$(date +%s),type=jwt

# Public key
gcloud secrets create jwt-public-key-v2 \
  --data-file=public_key_new.pem \
  --project=$PROJECT_ID \
  --labels=rotated_at=$(date +%s),type=jwt

echo "✓ Keys uploaded to Secret Manager"

# 3. Graceful transition (dual-key support)
if [ "$GRACEFUL" = "true" ]; then
  echo "Enabling graceful transition (30-day period)..."

  # Update application to accept both old and new keys
  cat > keys.json <<EOF
{
  "keys": [
    {
      "kid": "key-v1",
      "use": "sig",
      "kty": "RSA",
      "alg": "RS256",
      "n": "$(cat public_key_old.pem | base64 -w 0)",
      "status": "rotating",
      "expires": "$(date -d '+30 days' +%s)"
    },
    {
      "kid": "key-v2",
      "use": "sig",
      "kty": "RSA",
      "alg": "RS256",
      "n": "$(cat public_key_new.pem | base64 -w 0)",
      "status": "active",
      "primary": true
    }
  ]
}
EOF

  # Deploy dual-key configuration
  gcloud run services update auth-service \
    --update-env-vars="JWT_KEYS_CONFIG=$(cat keys.json | base64 -w 0)" \
    --region=$REGION

  echo "✓ Dual-key support enabled"
  echo "  - Old key expires in 30 days"
  echo "  - New key is primary for signing"
  echo "  - Both keys accepted for validation"
else
  echo "Immediate rotation (invalidates all tokens)..."

  # Replace old key with new key
  gcloud run services update auth-service \
    --update-env-vars="JWT_PRIVATE_KEY_VERSION=jwt-private-key-v2,JWT_PUBLIC_KEY_VERSION=jwt-public-key-v2" \
    --region=$REGION

  echo "✓ Keys rotated immediately"
  echo "⚠️  All users must re-authenticate"
fi

# 4. Test new keys
echo "Testing new keys..."

# Generate test token with new key
TEST_TOKEN=$(node -e "
const jwt = require('jsonwebtoken');
const fs = require('fs');
const privateKey = fs.readFileSync('private_key_new.pem');

const token = jwt.sign(
  { sub: 'test-user', test: true },
  privateKey,
  { algorithm: 'RS256', expiresIn: '15m', keyid: 'key-v2' }
);

console.log(token);
")

# Validate test token
curl -X POST https://auth-service.example.com/api/validate \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -H "Content-Type: application/json"

if [ $? -eq 0 ]; then
  echo "✓ New keys working correctly"
else
  echo "✗ ERROR: New keys validation failed!"
  exit 1
fi

# 5. Cleanup
echo "Cleaning up local key files..."
rm -f private_key_new.pem
rm -f public_key_new.pem

# Mark old keys as rotated (keep for audit)
gcloud secrets versions destroy latest \
  --secret=jwt-private-key-v1 \
  --project=$PROJECT_ID

# Log rotation
cat >> key_rotation_log.txt <<EOF
$(date +%Y-%m-%d): JWT keys rotated
  - Old key: key-v1 (rotated)
  - New key: key-v2 (active)
  - Graceful: $GRACEFUL
  - Next rotation: $(date -d '+90 days' +%Y-%m-%d)
EOF

echo ""
echo "========================================="
echo "KEY ROTATION COMPLETE"
echo "========================================="
echo "New key ID: key-v2"
echo "Graceful transition: $GRACEFUL"
echo "Next rotation due: $(date -d '+90 days' +%Y-%m-%d)"
echo "========================================="
```

## API Key Rotation

```javascript
// rotate-api-keys.js
const crypto = require('crypto');
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');

async function rotateAPIKey(keyName, gracefulDays = 30) {
  const client = new SecretManagerServiceClient();

  // 1. Generate new API key
  const newKey = crypto.randomBytes(32).toString('base64url');

  // 2. Store in Secret Manager
  const [version] = await client.addSecretVersion({
    parent: `projects/${PROJECT_ID}/secrets/${keyName}`,
    payload: {
      data: Buffer.from(newKey, 'utf8')
    }
  });

  console.log(`✓ New API key version created: ${version.name}`);

  // 3. If graceful, keep both keys active
  if (gracefulDays > 0) {
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + gracefulDays);

    await updateKeyRegistry({
      keyName,
      oldKey: await getCurrentKey(keyName),
      newKey,
      oldKeyExpiry: expiryDate
    });

    console.log(`✓ Graceful transition enabled (${gracefulDays} days)`);
    console.log(`  Old key expires: ${expiryDate.toISOString()}`);
  } else {
    // Immediate rotation
    await disableOldKeys(keyName);
    console.log('✓ Old keys disabled immediately');
  }

  // 4. Notify API key holders
  await notifyKeyHolders({
    keyName,
    newKey,
    gracefulDays
  });

  return {
    newKey,
    expiresAt: gracefulDays > 0 ? new Date(Date.now() + gracefulDays * 24 * 60 * 60 * 1000) : null
  };
}

async function validateAPIKey(providedKey) {
  const activeKeys = await getActiveKeys();

  // Check if key matches any active key
  for (const key of activeKeys) {
    if (crypto.timingSafeEqual(Buffer.from(providedKey), Buffer.from(key.value))) {
      // Check if key is expired
      if (key.expiresAt && new Date() > key.expiresAt) {
        return {
          valid: false,
          reason: 'Key expired, please use new key'
        };
      }

      return { valid: true, keyId: key.id };
    }
  }

  return {
    valid: false,
    reason: 'Invalid API key'
  };
}
```

## Database Credential Rotation

```bash
#!/bin/bash
# rotate-db-credentials.sh

INSTANCE_NAME=${1}
NEW_PASSWORD=$(openssl rand -base64 32)

echo "Rotating database credentials for $INSTANCE_NAME..."

# 1. Create new user with new password (graceful)
gcloud sql users create app_user_v2 \
  --instance=$INSTANCE_NAME \
  --password=$NEW_PASSWORD

# 2. Grant same permissions as old user
gcloud sql users set-password app_user_v2 \
  --instance=$INSTANCE_NAME \
  --password=$NEW_PASSWORD

# 3. Update Secret Manager
gcloud secrets versions add db-password \
  --data-file=- <<< "$NEW_PASSWORD"

# 4. Update application to use new credentials
gcloud run services update my-app \
  --update-env-vars="DB_USER=app_user_v2,DB_PASSWORD_VERSION=latest" \
  --region=$REGION

# 5. Wait for services to restart
sleep 60

# 6. Verify new credentials work
psql -h $DB_HOST -U app_user_v2 -d $DB_NAME -c "SELECT 1;" && echo "✓ New credentials working"

# 7. Delete old user (after grace period)
echo "Scheduling old user deletion in 30 days..."
at now + 30 days <<EOF
gcloud sql users delete app_user --instance=$INSTANCE_NAME
EOF
```

## Key Rotation Schedule

```javascript
// Automated key rotation schedule
const rotationSchedule = {
  'jwt-signing-keys': {
    frequency: 'quarterly', // Every 90 days
    graceful: true,
    gracePeriod: 30 // days
  },
  'api-keys': {
    frequency: 'annually', // Every 365 days
    graceful: true,
    gracePeriod: 60 // days
  },
  'database-credentials': {
    frequency: 'biannually', // Every 180 days
    graceful: true,
    gracePeriod: 7 // days
  },
  'oauth-secrets': {
    frequency: 'on-demand', // Only when compromised
    graceful: false
  }
};

// Check if rotation is due
function isRotationDue(keyType) {
  const lastRotation = getLastRotationDate(keyType);
  const config = rotationSchedule[keyType];

  const daysSinceRotation = (Date.now() - lastRotation) / (1000 * 60 * 60 * 24);

  const frequencyDays = {
    daily: 1,
    weekly: 7,
    monthly: 30,
    quarterly: 90,
    biannually: 180,
    annually: 365
  };

  return daysSinceRotation >= frequencyDays[config.frequency];
}
```

## Zero-Downtime Rotation

```
Timeline for Graceful JWT Key Rotation:

Day 0:
  • Generate new key (key-v2)
  • Deploy dual-key support
  • Start signing new tokens with key-v2
  • Accept tokens signed with key-v1 OR key-v2

Day 1-30:
  • Monitor key usage
  • 100% of new tokens use key-v2
  • Old tokens (key-v1) still valid until expiry
  • Track when last key-v1 token expires

Day 15:
  • ~99% of tokens now use key-v2
  • Send notification: key-v1 expiring soon

Day 30:
  • All key-v1 tokens have expired (15min lifetime)
  • Remove key-v1 from validation
  • Only key-v2 accepted
  • Zero users affected (no forced re-auth)

Day 31:
  • Archive key-v1 (keep for audit)
  • Document rotation in compliance log
```

## Key Rotation Monitoring

```javascript
// Monitor key usage during rotation
async function monitorKeyRotation() {
  const metrics = {
    'key-v1': 0,
    'key-v2': 0,
    invalid: 0
  };

  // Track which key was used for each token validation
  app.use((req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];

    if (token) {
      const decoded = jwt.decode(token, { complete: true });
      const keyId = decoded.header.kid;

      metrics[keyId] = (metrics[keyId] || 0) + 1;
    }

    next();
  });

  // Log metrics hourly
  setInterval(() => {
    const total = Object.values(metrics).reduce((a, b) => a + b, 0);
    console.log('Key Usage:');
    console.log(`  key-v1: ${(metrics['key-v1'] / total * 100).toFixed(1)}%`);
    console.log(`  key-v2: ${(metrics['key-v2'] / total * 100).toFixed(1)}%`);
    console.log(`  invalid: ${metrics.invalid}`);

    // Alert if old key usage is still high after 14 days
    const daysSinceRotation = getDaysSinceRotation();
    if (daysSinceRotation > 14 && metrics['key-v1'] / total > 0.01) {
      sendAlert('Old JWT key still used by 1%+ of requests');
    }
  }, 60 * 60 * 1000); // hourly
}
```

## Best Practices

**DO**:

- ✓ Rotate keys quarterly (90 days) for JWT signing keys
- ✓ Use graceful transition with dual-key support
- ✓ Store keys in Secret Manager, never in code
- ✓ Test new keys before removing old ones
- ✓ Monitor key usage during transition
- ✓ Keep audit log of all rotations
- ✓ Automate rotation with scheduled jobs

**DON'T**:

- ✗ Rotate keys without graceful transition (forces re-auth)
- ✗ Hardcode keys in application code
- ✗ Commit private keys to version control
- ✗ Skip testing after rotation
- ✗ Delete old keys immediately (keep for audit)
- ✗ Forget to update Secret Manager versions

## Commands

**`/auth/rotate-keys --key-type jwt`** - Rotate JWT signing keys
**`/auth/rotate-keys --key-type api`** - Rotate API keys
**`/auth/rotate-keys --graceful-transition`** - Enable dual-key support
**`/auth/audit`** - Check if key rotation is due
**`/devops/setup`** - Configure Secret Manager

## Success Criteria

- ✓ New keys generated and stored in Secret Manager
- ✓ Dual-key support deployed (if graceful)
- ✓ Services updated with new key versions
- ✓ Test tokens validated successfully
- ✓ No service downtime during rotation
- ✓ Key rotation logged for audit
- ✓ Next rotation scheduled (90 days)
- ✓ Old keys archived (not deleted)

---
**Uses**: gcp-security-compliance, healthcare-security-compliance, gcp-infrastructure-architect
