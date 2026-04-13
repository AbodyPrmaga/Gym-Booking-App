# Gym Booking Dashboard

A vanilla JavaScript admin dashboard for the FastAPI schema.

## Features

- Login and registration flow
- Token-based authentication stored in `localStorage`
- Dashboard views for users, services, slots, and bookings
- Create service, slot, and booking forms
- API integration with Tailwind UI styling

## Setup

1. Serve the `frontend` folder with a static server.
2. Update `script.js` if your backend runs on a different host or port.

```js
const API_BASE = 'http://localhost:8000';
```

3. Open `index.html` in the browser.
4. Log in using `/auth/login` or register using `/auth/register`.

## Notes

- Protected endpoints require a valid JWT token from `/auth/login`.
- The dashboard assumes the backend exposes the provided OpenAPI paths.
- If CORS is enabled on the backend, the dashboard can be served from any static host.
