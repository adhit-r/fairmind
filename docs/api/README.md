# FairMind API Documentation

This directory contains comprehensive API documentation and resources for the FairMind AI Governance Platform.

## Contents

- **`code-examples.md`**: Code examples in Python, JavaScript, and cURL
- **`postman-collection.json`**: Postman collection for API testing
- **Interactive Documentation**: Available at `/docs` (development mode)

## Quick Start

### 1. Interactive API Documentation

Visit `/docs` when running the backend in development mode to access the interactive Swagger UI documentation with try-it-out functionality.

### 2. Postman Collection

Import the Postman collection to test the API:

1. Open Postman
2. Click "Import"
3. Select `postman-collection.json`
4. Configure the `base_url` variable (default: `http://localhost:8000`)
5. Authenticate using the Login endpoint to get an access token
6. The token will be automatically used in subsequent requests

### 3. Code Examples

See `code-examples.md` for:
- Authentication examples
- Bias detection examples
- Core endpoint examples
- Error handling examples
- Rate limiting information

## API Endpoints

### Authentication

- `POST /api/v1/auth/login` - Authenticate and receive JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout and invalidate tokens

### Core

- `GET /api/v1/models` - List all models
- `GET /api/v1/datasets` - List all datasets
- `GET /api/v1/activity/recent` - Get recent activity
- `GET /api/v1/governance/metrics` - Get governance metrics

### Bias Detection

- `POST /api/v1/bias/detect` - Detect bias in model outputs
- `GET /api/v1/bias/templates` - Get available bias test templates
- `POST /api/v1/bias/templates` - Add custom bias test template

### Health Checks

- `GET /health` - Health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

## Authentication

Most endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Rate Limiting

API requests are rate-limited to 100 requests per minute per IP address. Check response headers for rate limit information:

- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
- `Retry-After`: Seconds to wait before retrying (when rate limited)

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error responses include a JSON body with error details:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {}
}
```

## OpenAPI Schema

The OpenAPI schema is available at `/openapi.json` (development mode). This can be used to:
- Generate client libraries
- Import into API testing tools
- Generate documentation

## Support

For questions or issues:
- Open an issue on GitHub
- Check the main README.md
- Review the code examples in `code-examples.md`

