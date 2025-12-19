# FileHub - File Authorization System with OpenFGA

A Django REST API demonstrating fine-grained authorization using OpenFGA (Open Fine-Grained Authorization) for managing file access permissions based on relationships.

## 1. Overview

This project implements a file management system where access control is managed through OpenFGA, providing **relationship-based authorization (ReBAC)** instead of   traditional **role-based access control (RBAC)**.

## 2. Technologies Used

| Technology            | Version | Purpose                              |
| --------------------- | ------- | ------------------------------------ |
| Django                | 5.2+    | Backend web framework                |
| Django REST Framework | -       | RESTful API development              |
| OpenFGA               | latest  | Fine-grained authorization engine    |
| PostgreSQL            | 17      | Relational database for OpenFGA data |
| Docker Compose        | -       | Container orchestration              |
| Python OpenFGA SDK    | latest  | Authorization client library         |
| JWT                   | -       | API authentication                   |

## 3. Architecture

| Service         | Container        | Purpose                                               | Ports                                       |
| --------------- | ---------------- | ----------------------------------------------------- | ------------------------------------------- |
| postgres        | openfga-postgres | Stores OpenFGA authorization data, and django migrations    | 5432                                        |
| openfga-migrate | openfga-migrate  | One-shot migration container for database schema      | -                                           |
| openfga         | openfga          | Authorization server handling permission checks       | 8080 (HTTP), 8081 (gRPC), 3000 (Playground) |
| django-web      | django-docker    | REST API server with file management logic            | 8000                                        |
| openfga-cli     | openfga-cli      | CLI tool for managing stores and authorization models | -                                           |

### 3.1 Network Architecture
All services run on a shared openfga Docker bridge network, enabling internal DNS resolution (e.g., http://openfga:8080).

Key Connections:
- Django → OpenFGA (HTTP:8080) - Authorization checks via Python SDK
- OpenFGA → Postgres (TCP:5432) - Stores tuples and models
- Host → Django (HTTP:8000) - API access via Postman/Browser
- OpenFGA CLI → OpenFGA (HTTP:8080) - Store/model management

## 4. Setup & Installation

### 4.1 Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### 4.2 Quick Start

```bash
git clone https://github.com/Sweekar07/filehub
git checkout main
cd filehub
```

> [!IMPORTANT] Branch
> > The local development setup is available in `main` branch only.
> 
> **Branch:** main
> 
> Make sure to switch to `main` branch.

### 4.3 Start services

- Build and Start the container:
```bash
docker compose -f docker-compose.local.yml up --build
```

- Stop the container:
```bash
docker compose -f docker-compose.local.yml down
```

### 4.4 OpenFGA CLI code

#### 4.4.1 Basic Command Breakdown

- **`docker compose -f docker-compose.local.yml`**: Specifies the Docker Compose file to use.
- **`run --rm`**: Runs the command in a temporary container that is removed after execution.
- **`openfga-cli`**: The OpenFGA CLI service defined in your Docker Compose file.
- **`--api-token=key1`**: The API token for authenticating with the OpenFGA server.

#### 4.4.2 Create OpenFGA store Manually

- Command:
```bash
docker compose -f docker-compose.local.yml run --rm openfga-cli --api-token=key1 store create --name="FileHub"
```

- Output:
```bash
{
  "store": {
    "created_at":"2025-12-17T15:14:27.312857Z",
    "id":"01KCPE0YBDZH4ATPY1M7270DVC",
    "name":"FileHub",
    "updated_at":"2025-12-17T15:14:27.312857Z"
  }
}
```

> [!IMPORTANT] Store ID
> > Fetch the `store.id` from the output above. This ID is required for configuring the Django environment variables.
> 
> **Store ID:** `01KCPE0YBDZH4ATPY1M7270DVC`
> 
> Make sure to copy this ID and **replace** it to your Django environment variables as `FGA_STORE_ID`.

#### 4.4.3 Write Model for Store

- command:
```bash
docker compose -f docker-compose.local.yml run --rm openfga-cli --api-token=key1 model write --store-id=01KCPE0YBDZH4ATPY1M7270DVC --file=data/filehub/first-model.fga
```

- output::
```bash
{
  "authorization_model_id":"01KCPEZGSQQN3QPP77GST6T129"
}
```

> [!IMPORTANT] Model Authorization ID
> > Fetch the `` from the output above. This ID is required for configuring the Django environment variables.
> 
> **Model Authorization ID:** `01KCPEZGSQQN3QPP77GST6T129`
> 
> Make sure to copy this ID and **replace** it to your Django environment variables as `FGA_AUTHZ_MODEL_ID`.


#### 4.4.4 Replace OpenFGA Env File variables
```
# .envs/.local/.env.django
FGA_STORE_ID=01KCHFZ97681C91WBDPPY303AT      # Replace with the Store ID generated by OpenFGA
FGA_AUTHZ_MODEL_ID=01KCK13Z9V4F5SEBX9J67HJJGF       # Replace with the Authorization Model ID generated by OpenFGA
```

> [!IMPORTANT] Restart the docker Container
> > Need to restart the docker containers since environment variables are changed now.
> 
> Refer above **Docker Command** to stop and start the containers again.

### 4.5 CreateDjango Super User

- command:
```bash
docker exec -it django-docker python manage.py createsuperuser
# Enter your name, email and password.
```

## 5. API Endpoints

### 5.1 Authentication
- Base URL: *localhost:8000*
#### 5.1.1 Obtain JWT Token
```bash
POST /api/token/
Content-Type: application/json

{
  "username": "john",
  "password": "password123"
}

```
Response:
```bash
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 5.1.2 Refresh Token
```bash
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 5.2 File Management
- Note: All endpoints require Authorization: Bearer <access_token> header.

#### 5.2.1 List Files
```bash
GET /api/files/
Authorization: Bearer <token>
```
response:
```bash
[
  {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "project-proposal.pdf",
    "owner": "user:john",
    "created_at": "2025-12-19T10:00:00Z"
  }
]
```

#### 5.2.2 Create File
```bash
POST /api/files/
Authorization: Bearer <token>
Content-Type: application/json

{
  "file": "design-mockup.png",
  "content": "<base64-encoded-content>"
}
```
response:
```bash
{
  "uuid": "660e8400-e29b-41d4-a716-446655440001",
  "file": "design-mockup.png",
}
```

#### 5.2.3 Get File Details
```bash
GET /api/files/{uuid}/
Authorization: Bearer <token>
```
response:
```bash
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "file": "project-proposal.pdf"
}

```


#### 5.2.4 Share File
```bash
POST /api/files/{uuid}/share/
Authorization: Bearer <token>
Content-Type: application/json

{
	"permissions": [
		{"user_id": "3", "relation": "editor"}
	]
}
```
- Supported relations: owner, editor, viewer
response:
```bash
{
	"detail": "File shared successfully."
}
```

#### 5.2.5 Check Permissions
```bash
GET /api/files/{uuid}/permissions/
Authorization: Bearer <token>
```
response:
```bash
{
	"file": "079cd8b8-c2ef-4705-8a24-048d1de70836",
	"permissions": {
		"owners": [
			"user:1"
		],
		"viewers": [
			"user:2"
		],
		"editors": [
			"user:3"
		]
	}
}
```


#### 5.2.6 Get File Relations
```bash
GET /api/files/{uuid}/relations/
Authorization: Bearer <token>
```
response:
```bash
{
	"user": "user:1",
	"object": "file:079cd8b8-c2ef-4705-8a24-048d1de70836",
	"relations": [
		"can_view",
		"can_edit",
		"owner"
	]
}
```

## 6. Authorization Model
OpenFGA uses a relationship-based model inspired by Google Zanzibar. Here's the authorization model for this project:
```bash
model
  schema 1.1

type user

type file
  relations
    define owner: [user]
    define editor: [user] or owner
    define viewer: [user] or editor
    define can_read: viewer
    define can_write: editor
```
How it works:
- owner: Full control over the file
- editor: Can read and write (inherits viewer permissions)
- viewer: Can only read (basic access)
- Computed permissions: can_read, can_write, etc. are derived from relations

## 7. OpenFGA vs Traditional Authorization

Traditional RBAC with Postgres

```bash
-- Traditional approach: permission checks via database queries
SELECT * FROM user_roles WHERE user_id = 1 AND role = 'admin';
SELECT * FROM file_permissions WHERE file_id = 123 AND user_id = 1;
```

Drawbacks:
- Authorization logic scattered across application code
- Hard to audit and update policies
- Role explosion for complex scenarios
- Tight coupling between auth and business logic​

OpenFGA Approach
```bash
# Centralized authorization check
response = await fga_client.check(
    user="user:john",
    relation="can_write",
    object="file:550e8400-..."
)
# Returns: {"allowed": true/false}
```

Key Advantages
| Aspect              | Traditional Auth         | OpenFGA                                               |
| ------------------- | ------------------------ | ----------------------------------------------------- |
| Authorization Logic | Scattered in code        | Centralized in modelsopenfga​                         |
| Performance         | Multiple DB queries      | Optimized graph traversal, <1ms for simple checksdev​ |
| Scalability         | Limited by app logic     | 1M+ RPS capabilitydev​                                |
| Auditability        | Manual logging needed    | Complete audit trail built-inopenfga​                 |
| Policy Updates      | Requires code deployment | No-code model updatesdev​                             |
| Flexibility         | Role explosion issue     | Relationship-based (fine-grained)aserto​              |
| Maintenance         | High (custom code)       | Low (battle-tested patterns)dev​                      |

## 7. Contributing

Contributions are welcome! Please open an issue or submit a pull request.

📄 License
MIT License
