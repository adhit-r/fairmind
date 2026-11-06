// Where server-side route handlers reach the FastAPI backend.
export const BACKEND_BASE_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.BACKEND_API_URL ||
  'http://fairmind.railway.internal:8000'
