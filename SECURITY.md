# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously at Mnemosyne. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT Disclose Publicly

Please do **not** open a public GitHub issue for security vulnerabilities. This could put users at risk before a fix is available.

### 2. Contact Us Privately

Send a detailed report to: **security@mnemosyne.dev** (or create a private security advisory on GitHub)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Resolution Timeline**: Depends on severity
  - Critical: 24-72 hours
  - High: 1-2 weeks
  - Medium: 2-4 weeks
  - Low: Next release cycle

### 4. Disclosure Policy

- We follow responsible disclosure practices
- Credit will be given to reporters (unless anonymity is requested)
- We aim to release fixes before public disclosure

## Security Best Practices for Users

### API Key Security

1. **Never commit API keys** to version control
2. Use environment variables or `.env` files
3. Rotate keys regularly
4. Use separate keys for development/production

```bash
# Good: Environment variable
export ANTHROPIC_API_KEY=sk-ant-xxx

# Good: .env file (add to .gitignore)
echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> .env

# Bad: Hardcoded in config
api_key = "sk-ant-xxx"  # DON'T DO THIS
```

### Data Privacy

Mnemosyne records sensitive data including:
- **Keystrokes**: May contain passwords, personal info
- **Screenshots**: May capture sensitive content
- **Window titles**: May reveal browsing history

Recommendations:
1. Use the `blocked_apps` config for sensitive applications
2. Enable `require_confirmation` for the execution agent
3. Regularly review and prune stored data
4. Use disk encryption for the data directory

### Network Security

When running the web interface:
1. **Don't expose to public internet** without authentication
2. Use HTTPS in production (reverse proxy recommended)
3. Restrict CORS origins to trusted domains
4. Use a strong `MNEMOSYNE_SECRET_KEY`

### Docker Security

If using Docker:
1. Run as non-root user (default in our Dockerfile)
2. Use read-only filesystem where possible
3. Limit container capabilities
4. Keep base images updated

## Known Security Considerations

### Local Data Storage

- SQLite database is not encrypted at rest
- Consider using encrypted filesystem (FileVault, LUKS)
- Vector embeddings may leak semantic information

### LLM Interactions

- Data sent to LLM providers is subject to their privacy policies
- Consider using local models (Ollama) for sensitive data
- Review what data is included in LLM prompts

### Input Capture

- Keyboard capture may record sensitive input
- Screen capture may capture sensitive content
- Consider disabling during sensitive activities

## Security Hardening Checklist

- [ ] API keys stored in environment variables
- [ ] `.env` file added to `.gitignore`
- [ ] Sensitive apps added to `blocked_apps`
- [ ] `require_confirmation` enabled for execution
- [ ] Web interface not exposed to public internet
- [ ] Disk encryption enabled
- [ ] Regular data backups (encrypted)
- [ ] Log files reviewed for sensitive data

## Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2024-02-10 | 0.1.0 | Initial security policy |
