# Docker Run Commands

## Basic Commands

### 1. Show Help
```powershell
docker run --rm s3-component-replacer --help
```

### 2. Dry-Run with AWS SSO Profile (Recommended)
```powershell
docker run --rm `
  -v "$env:USERPROFILE\.aws:/home/appuser/.aws:ro" `
  s3-component-replacer `
  --profile xyz `
  --bucket spinomenal-cdn-main `
  --dry-run
```

### 3. Actual Copy Operation (dev → stage)
```powershell
docker run --rm `
  -v "$env:USERPROFILE\.aws:/home/appuser/.aws:ro" `
  s3-component-replacer `
  --profile xyz `
  --bucket spinomenal-cdn-main
```

### 4. Copy from Stage to Production
```powershell
docker run --rm `
  -v "$env:USERPROFILE\.aws:/home/appuser/.aws:ro" `
  s3-component-replacer `
  --profile xyz `
  --bucket spinomenal-cdn-main `
  --source-prefix stage `
  --destination-prefix prd
```

### 5. With Environment Variables (Alternative to SSO)
```powershell
docker run --rm `
  -e AWS_ACCESS_KEY_ID="your-access-key-id" `
  -e AWS_SECRET_ACCESS_KEY="your-secret-access-key" `
  -e AWS_SESSION_TOKEN="your-session-token" `
  s3-component-replacer `
  --bucket spinomenal-cdn-main `
  --dry-run
```

### 6. Debug Mode with Verbose Logging
```powershell
docker run --rm `
  -v "$env:USERPROFILE\.aws:/home/appuser/.aws:ro" `
  s3-component-replacer `
  --profile xyz `
  --bucket spinomenal-cdn-main `
  --log-level DEBUG `
  --dry-run
```

### 7. Custom Configuration Files
```powershell
docker run --rm `
  -v "$env:USERPROFILE\.aws:/home/appuser/.aws:ro" `
  -v "$PWD/config/custom_mapping.json:/app/config/custom_mapping.json:ro" `
  -v "$PWD/config/custom_components.json:/app/config/custom_components.json:ro" `
  s3-component-replacer `
  --profile xyz `
  --bucket spinomenal-cdn-main `
  --mapping-file config/custom_mapping.json `
  --components-file config/custom_components.json `
  --dry-run
```

### 8. Custom Bucket and Region
```powershell
docker run --rm `
  -v "$env:USERPROFILE\.aws:/home/appuser/.aws:ro" `
  s3-component-replacer `
  --profile xyz `
  --bucket my-custom-bucket `
  --region us-west-2 `
  --dry-run
```

## Linux/Mac Commands (for reference)

### Dry-Run with AWS SSO Profile
```bash
docker run --rm \
  -v $HOME/.aws:/home/appuser/.aws:ro \
  s3-component-replacer \
  --profile xyz \
  --bucket spinomenal-cdn-main \
  --dry-run
```

### Actual Copy Operation
```bash
docker run --rm \
  -v $HOME/.aws:/home/appuser/.aws:ro \
  s3-component-replacer \
  --profile xyz \
  --bucket spinomenal-cdn-main
```

## Important Notes

1. **Mount Path**: Use `/home/appuser/.aws` (not `/root/.aws`) because the container runs as non-root user `appuser`

2. **Read-Only Mount**: The `:ro` flag makes the mount read-only for security

3. **Profile Name**: Replace `xyz` with your actual AWS SSO profile name

4. **Session Token**: If using temporary credentials, include `AWS_SESSION_TOKEN` environment variable

5. **Windows Path**: On Windows, use `$env:USERPROFILE\.aws` instead of `$HOME/.aws`

