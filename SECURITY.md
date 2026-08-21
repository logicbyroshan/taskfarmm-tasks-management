# 🔒 Security Policy

TaskFlixx takes security seriously. We are committed to ensuring the safety of user data and maintaining a secure task orchestration platform.

---

## 🛡️ Supported Versions

We currently support the latest major release of TaskFlixx:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability within TaskFlixx, please **do not open a public GitHub issue**. Instead, follow responsible disclosure practices:

1. **Email the Maintainer**: Send details directly to **`iamroshandamor@gmail.com`**.
2. **Include Key Information**:
   - Description of the vulnerability.
   - Step-by-step reproduction guide or proof-of-concept.
   - Potential impact on users or data integrity.
   - Recommended remediation if known.

We will acknowledge receipt within **48 hours** and provide regular status updates regarding the fix.

---

## 🔐 Security Best Practices for Production

When running TaskFlixx in production environments:
1. **Never run with `DEBUG=True`** in production.
2. **Generate a random `SECRET_KEY`** with at least 50 high-entropy characters.
3. **Always use HTTPS / TLS** to protect cookies and authentication sessions.
4. **Keep Dependencies Updated** regularly using `pip list --outdated`.
