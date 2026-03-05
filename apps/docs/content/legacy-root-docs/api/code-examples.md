# FairMind API Code Examples

This document provides code examples for using the FairMind API in multiple programming languages.

## Table of Contents

- [Authentication](#authentication)
- [Bias Detection](#bias-detection)
- [Core Endpoints](#core-endpoints)
- [Error Handling](#error-handling)

## Authentication

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "securepassword123"
    }
)

data = response.json()
access_token = data["access_token"]

# Use token in subsequent requests
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
```

### JavaScript (Fetch API)

```javascript
// Login
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123'
  })
});

const data = await response.json();
const accessToken = data.access_token;

// Use token in subsequent requests
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
};
```

### cURL

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'

# Use token in subsequent requests
curl -X GET "http://localhost:8000/api/v1/models" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Bias Detection

### Python

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Detect bias
response = requests.post(
    "http://localhost:8000/api/v1/bias/detect",
    headers=headers,
    json={
        "model_type": "text_generation",
        "test_category": "representational",
        "sensitive_attributes": ["gender", "race"],
        "model_outputs": [
            {
                "prompt": "The doctor was",
                "output": "The doctor was a skilled professional",
                "metadata": {"model_version": "1.0"}
            },
            {
                "prompt": "The nurse was",
                "output": "The nurse was caring and attentive",
                "metadata": {"model_version": "1.0"}
            }
        ]
    }
)

result = response.json()
print(f"Bias Score: {result['overall_bias_score']}")
print(f"Recommendations: {result['recommendations']}")
```

### JavaScript (Fetch API)

```javascript
// Detect bias
const response = await fetch('http://localhost:8000/api/v1/bias/detect', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model_type: 'text_generation',
    test_category: 'representational',
    sensitive_attributes: ['gender', 'race'],
    model_outputs: [
      {
        prompt: 'The doctor was',
        output: 'The doctor was a skilled professional',
        metadata: { model_version: '1.0' }
      },
      {
        prompt: 'The nurse was',
        output: 'The nurse was caring and attentive',
        metadata: { model_version: '1.0' }
      }
    ]
  })
});

const result = await response.json();
console.log(`Bias Score: ${result.overall_bias_score}`);
console.log(`Recommendations: ${result.recommendations}`);
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/bias/detect" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "text_generation",
    "test_category": "representational",
    "sensitive_attributes": ["gender", "race"],
    "model_outputs": [
      {
        "prompt": "The doctor was",
        "output": "The doctor was a skilled professional",
        "metadata": {"model_version": "1.0"}
      },
      {
        "prompt": "The nurse was",
        "output": "The nurse was caring and attentive",
        "metadata": {"model_version": "1.0"}
      }
    ]
  }'
```

## Core Endpoints

### Python

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Get models
response = requests.get(
    "http://localhost:8000/api/v1/models",
    headers=headers,
    params={"limit": 10, "offset": 0}
)

models = response.json()
print(f"Found {models['count']} models")

# Get datasets
response = requests.get(
    "http://localhost:8000/api/v1/datasets",
    headers=headers,
    params={"limit": 10, "offset": 0}
)

datasets = response.json()
print(f"Found {datasets['count']} datasets")
```

### JavaScript (Fetch API)

```javascript
// Get models
const modelsResponse = await fetch(
  'http://localhost:8000/api/v1/models?limit=10&offset=0',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

const models = await modelsResponse.json();
console.log(`Found ${models.count} models`);

// Get datasets
const datasetsResponse = await fetch(
  'http://localhost:8000/api/v1/datasets?limit=10&offset=0',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

const datasets = await datasetsResponse.json();
console.log(`Found ${datasets.count} datasets`);
```

### cURL

```bash
# Get models
curl -X GET "http://localhost:8000/api/v1/models?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get datasets
curl -X GET "http://localhost:8000/api/v1/datasets?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Error Handling

### Python

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/api/v1/bias/detect",
        headers=headers,
        json=request_data,
        timeout=30
    )
    
    # Check for HTTP errors
    response.raise_for_status()
    
    result = response.json()
    
except requests.exceptions.HTTPError as e:
    if response.status_code == 401:
        print("Authentication failed. Please check your credentials.")
    elif response.status_code == 429:
        print("Rate limit exceeded. Please try again later.")
        retry_after = response.headers.get("Retry-After")
        print(f"Retry after: {retry_after} seconds")
    elif response.status_code == 422:
        print("Validation error:")
        error_data = response.json()
        print(error_data.get("details", []))
    else:
        print(f"HTTP Error: {e}")
        
except requests.exceptions.Timeout:
    print("Request timed out. Please try again.")
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### JavaScript (Fetch API)

```javascript
try {
  const response = await fetch('http://localhost:8000/api/v1/bias/detect', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestData)
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Authentication failed. Please check your credentials.');
    } else if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      throw new Error(`Rate limit exceeded. Retry after: ${retryAfter} seconds`);
    } else if (response.status === 422) {
      const errorData = await response.json();
      throw new Error(`Validation error: ${JSON.stringify(errorData.details)}`);
    } else {
      throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
    }
  }

  const result = await response.json();
  console.log('Success:', result);
  
} catch (error) {
  console.error('Error:', error.message);
}
```

### cURL (Error Handling)

```bash
# Check response status
response=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:8000/api/v1/bias/detect" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '...')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 401 ]; then
  echo "Authentication failed"
elif [ "$http_code" -eq 429 ]; then
  echo "Rate limit exceeded"
elif [ "$http_code" -eq 422 ]; then
  echo "Validation error: $body"
else
  echo "Response: $body"
fi
```

## Rate Limiting

The API implements rate limiting. Check the response headers for rate limit information:

- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
- `Retry-After`: Seconds to wait before retrying (when rate limited)

### Python Example

```python
response = requests.get("http://localhost:8000/api/v1/models", headers=headers)

# Check rate limit headers
rate_limit = response.headers.get("X-RateLimit-Limit")
remaining = response.headers.get("X-RateLimit-Remaining")
reset_time = response.headers.get("X-RateLimit-Reset")

print(f"Rate Limit: {rate_limit} requests/minute")
print(f"Remaining: {remaining} requests")
print(f"Reset at: {reset_time}")
```

## Next Steps

- Explore the interactive API documentation at `/docs` (development mode)
- Import the Postman collection from `docs/api/postman-collection.json`
- Check the OpenAPI schema at `/openapi.json` (development mode)

