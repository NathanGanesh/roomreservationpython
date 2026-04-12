# DealRadar Flask Prototype

This project is the Python/Flask ingestion-side prototype for DealRadar. It is the Assignment 1 Flask backend and now stands on its own again.

The service provides:

- JWT-based auth
- profile management
- alert rule CRUD
- listing CRUD
- match CRUD and status updates
- ingestion of external listing batches

The newer Spring backend and mobile app were moved into the sibling project:

- `/mnt/c/Users/Gebruiker/PycharmProjects/dealradar`

## Stack

- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- PostgreSQL in development
- SQLite in tests

Access tokens expire after 8 hours by default. This is controlled by `JWT_ACCESS_TOKEN_EXPIRES_HOURS`.

## Local setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r reqs.txt
```

Copy the environment file if needed:

```bash
cp .env.example .env
```

Start PostgreSQL:

```bash
docker compose up -d python-db
```

Load the environment and apply migrations:

```bash
set -a
source .env
set +a
flask --app app:app db upgrade
```

Run the app:

```bash
flask --app app:app run
```

## Docker workflow

Run the full local container setup with:

```bash
docker compose up --build
```

In the Docker flow, the Python container now:

1. waits for PostgreSQL to become reachable
2. runs `flask --app app:app db upgrade`
3. starts the Flask server

This means `docker compose up` now brings up a usable app without a separate manual migration command. The migration step is still part of the deployment/setup process; it is just automated inside container startup for local development.

The API is then available at:

```text
http://localhost:5000
```

Useful endpoints:

- `GET /`
- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET/POST/PUT/DELETE /alert-rules`
- `GET/POST/PUT/DELETE /listings`
- `POST /ingestion/listings`
- `GET/POST/PUT/DELETE /matches`

Endpoint roles:

- `POST /listings` is the single-item CRUD create endpoint and expects one listing JSON object
- `POST /ingestion/listings` is the batch ingestion endpoint and expects `{ "listings": [...] }`
- the ingestion endpoint stores the submitted listings first, creating new listings when they do not exist yet and reusing/updating existing listings when the same `sourceName + externalId` already exists
- after storing those listings, the ingestion endpoint evaluates alert rules and returns any created matches

Alert rules are unique per user by their full normalized filter combination. Creating or updating a rule to the same effective values returns `400`.
Alert rules also validate their price range. If both `minPrice` and `maxPrice` are set, `maxPrice` must be greater than or equal to `minPrice`.

For auth testing:

- `POST /auth/register` and `POST /auth/login` return an access token
- the access token is valid for 8 hours by default
- after expiry, the user must log in again to get a new token
- updating the profile does not automatically mint a fresh token; the current token remains valid until its normal expiry
- manual API verification was done with Postman by reusing the returned JWT as `Authorization: Bearer <token>` on protected routes

## Manual API examples

The examples below match the current implemented Flask routes and were used in Postman during manual API verification.

Example `PUT /listings/{id}` request:

```http
PUT http://localhost:5000/listings/1
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "externalId": "mk-1",
  "sourceName": "marktplaats",
  "title": "MacBook Pro 14",
  "description": "Laptop in good state",
  "price": 1199,
  "currency": "EUR",
  "city": "Utrecht",
  "url": "https://example.com/listings/mk-1",
  "postedAt": "2026-04-03T09:00:00"
}
```

Expected response:

```json
{
  "id": 1,
  "externalId": "mk-1",
  "sourceName": "marktplaats",
  "title": "MacBook Pro 14",
  "description": "Laptop in good state",
  "price": 1199.0,
  "currency": "EUR",
  "city": "Utrecht",
  "url": "https://example.com/listings/mk-1",
  "postedAt": "2026-04-03T09:00:00+00:00"
}
```

Example `DELETE /listings/{id}` request:

```http
DELETE http://localhost:5000/listings/1
Authorization: Bearer <token>
```

Expected response:

```json
{
  "message": "listing deleted"
}
```

Example `POST /ingestion/listings` request:

```http
POST http://localhost:5000/ingestion/listings
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "listings": [
    {
      "externalId": "mk-iphone-1",
      "sourceName": "marktplaats",
      "title": "iPhone 14 128GB",
      "description": "Used phone with box",
      "price": 450,
      "currency": "EUR",
      "city": "Rotterdam",
      "url": "https://example.com/listings/mk-iphone-1",
      "postedAt": "2026-04-03T10:00:00"
    },
    {
      "externalId": "mk-bike-1",
      "sourceName": "marktplaats",
      "title": "City bike",
      "description": "Daily commuter bike",
      "price": 150,
      "currency": "EUR",
      "city": "Rotterdam",
      "url": "https://example.com/listings/mk-bike-1",
      "postedAt": "2026-04-03T10:30:00"
    }
  ]
}
```

Expected response:

- `storedListings` includes the stored listing records
- `createdMatches` includes the new matches generated from alert-rule evaluation
- `matchCount` is the number of created matches

Important:

- a bare JSON array is not valid for `/ingestion/listings`
- `/listings` is for one listing object
- `/ingestion/listings` is for a wrapped batch payload: `{ "listings": [...] }`

## Manual verification checklist

The checklist below was used for live API verification in Postman after starting the app with `docker compose up --build`.

### Postman setup

Create a small Postman environment or collection variables for:

- `baseUrl = http://localhost:5000`
- `tokenUser1`
- `tokenUser2`
- `ruleId1`
- `ruleId2`
- `listingId`
- `matchId`

Use these default headers:

- `Content-Type: application/json`
- `Authorization: Bearer {{tokenUser1}}` for protected routes until the steps explicitly switch to user 2

Importable Postman files are included in:

- `postman/dealradar-flask.postman_collection.json`
- `postman/dealradar-flask.postman_environment.json`

The collection auto-saves returned JWTs and created entity IDs into the environment variables. If a register request fails because the user already exists, run the matching login request instead. The persistence check still requires one manual terminal step:

```bash
docker compose restart python-ingestion
```

### 1. Confirm the app is running

Request:

```http
GET {{baseUrl}}/health
```

Expected:

- `200`
- response body:

```json
{
  "service": "dealradar-ingestion",
  "status": "ok"
}
```

### 2. Register user 1 and save the token

Request:

```http
POST {{baseUrl}}/auth/register
Content-Type: application/json
```

```json
{
  "email": "seller@example.com",
  "firstName": "Deal",
  "lastName": "Hunter",
  "password": "StrongPass123"
}
```

Save from the response:

- `accessToken` -> `tokenUser1`

Expected:

- `201`
- response contains both `user` and `accessToken`

If this user already exists, use `POST {{baseUrl}}/auth/login` with the same credentials and save the returned `accessToken` into `tokenUser1`.

### 3. Create two alert rules for user 1

Request 1:

```http
POST {{baseUrl}}/alert-rules
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "keyword": "iphone",
  "category": "electronics",
  "minPrice": 100,
  "maxPrice": 500,
  "location": "amsterdam",
  "active": true
}
```

Save from the response:

- `id` -> `ruleId1`

Expected:

- `201`
- response contains the created alert rule

Request 2:

```http
POST {{baseUrl}}/alert-rules
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "keyword": "macbook",
  "category": "electronics",
  "minPrice": 500,
  "maxPrice": 1200,
  "location": "utrecht",
  "active": true
}
```

Save from the response:

- `id` -> `ruleId2`

Expected:

- `201`

### 4. Verify the one-to-many relation for user 1

Request:

```http
GET {{baseUrl}}/alert-rules
Authorization: Bearer {{tokenUser1}}
```

Expected:

- `200`
- response has an `items` array
- both `ruleId1` and `ruleId2` appear in that array
- both rules belong to the logged-in user

This is the clearest manual proof of the required `User -> AlertRule` one-to-many relation.

### 5. Create one listing for user 1

Request:

```http
POST {{baseUrl}}/listings
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "externalId": "mk-1",
  "sourceName": "marktplaats",
  "title": "MacBook Pro 14",
  "description": "Laptop in good state",
  "price": 1299,
  "currency": "EUR",
  "city": "Utrecht",
  "url": "https://example.com/listings/mk-1",
  "postedAt": "2026-04-03T09:00:00"
}
```

Save from the response:

- `id` -> `listingId`

Expected:

- `201`
- response contains the created listing

### 6. Verify `Match` CRUD

Create the match:

```http
POST {{baseUrl}}/matches
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "alertRuleId": {{ruleId2}},
  "listingId": {{listingId}}
}
```

Save from the response:

- `id` -> `matchId`

Expected:

- `201`
- response contains a created match object

Read all matches:

```http
GET {{baseUrl}}/matches
Authorization: Bearer {{tokenUser1}}
```

Expected:

- `200`
- `items` contains the `matchId`

Read one match:

```http
GET {{baseUrl}}/matches/{{matchId}}
Authorization: Bearer {{tokenUser1}}
```

Expected:

- `200`
- response `id` equals `matchId`

Update the match status:

```http
PUT {{baseUrl}}/matches/{{matchId}}
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "status": "reviewed"
}
```

Expected:

- `200`
- response contains `"status": "reviewed"`

Negative check:

```http
PUT {{baseUrl}}/matches/{{matchId}}
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "status": "invalid_status"
}
```

Expected:

- `400`
- response contains an `error` field

Delete the match:

```http
DELETE {{baseUrl}}/matches/{{matchId}}
Authorization: Bearer {{tokenUser1}}
```

Expected:

- `200`
- response body:

```json
{
  "message": "match deleted"
}
```

### 7. Register user 2 and verify ownership boundaries

Register a second user or log in as a second user:

```http
POST {{baseUrl}}/auth/register
Content-Type: application/json
```

```json
{
  "email": "buyer@example.com",
  "firstName": "Second",
  "lastName": "User",
  "password": "StrongPass123"
}
```

Save from the response:

- `accessToken` -> `tokenUser2`

Then request:

```http
GET {{baseUrl}}/alert-rules
Authorization: Bearer {{tokenUser2}}
```

Expected:

- `200`
- the second user does not see the first user’s alert rules
- the list is empty or contains only rules created by user 2

### 8. Verify the ingestion flow

Switch back to user 1 with `Authorization: Bearer {{tokenUser1}}`.

Use `/listings` when you want to create exactly one listing object. Use `/ingestion/listings` only for a wrapped batch payload shaped like `{ "listings": [...] }`.

Create this dedicated ingestion rule first:

```http
POST {{baseUrl}}/alert-rules
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "keyword": "iphone",
  "minPrice": 200,
  "maxPrice": 600,
  "location": "rotterdam"
}
```

Then call:

```http
POST {{baseUrl}}/ingestion/listings
Authorization: Bearer {{tokenUser1}}
Content-Type: application/json
```

```json
{
  "listings": [
    {
      "externalId": "mk-iphone-1",
      "sourceName": "marktplaats",
      "title": "iPhone 14 128GB",
      "description": "Used phone with box",
      "price": 450,
      "currency": "EUR",
      "city": "Rotterdam",
      "url": "https://example.com/listings/mk-iphone-1",
      "postedAt": "2026-04-03T10:00:00"
    },
    {
      "externalId": "mk-bike-1",
      "sourceName": "marktplaats",
      "title": "City bike",
      "description": "Daily commuter bike",
      "price": 150,
      "currency": "EUR",
      "city": "Rotterdam",
      "url": "https://example.com/listings/mk-bike-1",
      "postedAt": "2026-04-03T10:30:00"
    }
  ]
}
```

Expected:

- `201`
- `storedListings` contains both stored listings
- those stored listings may be newly created listings or existing listings that were reused/updated based on `sourceName + externalId`
- `createdMatches` contains exactly one match
- `matchCount` is `1`

Then verify:

```http
GET {{baseUrl}}/matches
Authorization: Bearer {{tokenUser1}}
```

Expected:

- `200`
- the created ingestion match appears in `items`

This is the strongest proof that ingestion, matching logic, and persistence work together.

### 9. Verify persistence after restart

Do not restart the database container for this check. Only restart the Flask app container:

```bash
docker compose restart python-ingestion
```

After the restart finishes, reuse `tokenUser1` and call:

```http
GET {{baseUrl}}/alert-rules
Authorization: Bearer {{tokenUser1}}
```

```http
GET {{baseUrl}}/listings
Authorization: Bearer {{tokenUser1}}
```

Expected:

- `200` on both requests
- previously created alert rules are still present
- previously created listings are still present

Optional extra check:

```http
GET {{baseUrl}}/matches
Authorization: Bearer {{tokenUser1}}
```

Expected:

- previously created matches are still present as well

This confirms that persistence survives Flask container restart and is not only in-memory state.

## Tests

Run the test suite:

```bash
pytest
```

The tests cover:

- auth and profile flows
- alert rule CRUD
- listing CRUD
- ingestion and automatic match creation
- health route

## Example credentials

This Flask app does not seed fixed users on startup. Register a user through the API or UI flow. For local testing, the test suite uses:

- `seller@example.com`
- `StrongPass123`

Example register payload:

```json
{
  "email": "seller@example.com",
  "firstName": "Deal",
  "lastName": "Hunter",
  "password": "StrongPass123"
}
```

## Database

By default the development configuration expects PostgreSQL on:

```text
postgresql+psycopg://dealradar:dealradar@localhost:5432/dealradar
```

Migrations live in `migrations/`.

## Integration with the main backend

This prototype can still push listing payloads into the separate Spring backend by URL:

```bash
python3 scripts/push_listings_to_backend.py payload.json
```

The target defaults to:

```text
http://localhost:8080/internal/ingestion/listings
```

Override it with `MAIN_BACKEND_INGEST_URL` if needed.

If the Spring backend expects a service token, set `APP_INGESTION_SERVICE_TOKEN` in `.env`.
