# FairMind Email Configuration

## Domain: FAIRMIND.XYZ
## Email: support@fairmind.xyz

### IMAP Configuration (Incoming)
- **Server**: imap.zoho.com
- **Port**: 993
- **Security**: SSL/TLS
- **Username**: support@fairmind.xyz
- **Password**: [Your email password]

### POP Configuration (Incoming)
- **Server**: pop.zoho.com
- **Port**: 995
- **Security**: SSL/TLS
- **Username**: support@fairmind.xyz
- **Password**: [Your email password]

### SMTP Configuration (Outgoing)
- **Server**: smtp.zoho.com
- **Port**: 465 (SSL) or 587 (TLS)
- **Security**: SSL/TLS
- **Authentication**: Yes
- **Username**: support@fairmind.xyz
- **Password**: [Your email password]

### Environment Variables
Add these to your `.env` file:

```env
# Email Configuration
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_USER=support@fairmind.xyz
EMAIL_PASSWORD=your_email_password
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false

# IMAP Configuration
IMAP_HOST=imap.zoho.com
IMAP_PORT=993
IMAP_USER=support@fairmind.xyz
IMAP_PASSWORD=your_email_password
IMAP_USE_SSL=true
```

### Next.js Email Integration
For the frontend, you can use libraries like:
- `nodemailer` for sending emails
- `@emailjs/browser` for client-side email sending
- `resend` for modern email API

### Backend Email Integration
For the Python FastAPI backend, you can use:
- `fastapi-mail` for email sending
- `aiosmtplib` for async email operations
- `email-validator` for email validation 