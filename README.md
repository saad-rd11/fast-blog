# FastAPI Blog

A hybrid web application that combines a RESTful API with a server-side rendered frontend, built using FastAPI, SQLAlchemy (Async), and Jinja2 templates.

## Features

*   **FastAPI Powered:** High-performance, easy-to-learn web framework.
*   **Async Database:** Uses `SQLAlchemy` with `aiosqlite` for asynchronous database operations.
*   **Hybrid Architecture:**
    *   **REST API:** JSON endpoints for User and Post management (CRUD).
    *   **Frontend:** Server-side rendered HTML pages using `Jinja2` templates.
*   **User Management:** Create, read, update, and delete users.
*   **Post Management:** Create, read, update, and delete posts.
*   **Static & Media Files:** Served directly by FastAPI.

## Tech Stack

*   **Language:** Python 3.12+
*   **Framework:** FastAPI
*   **Database:** SQLite (via `aiosqlite`)
*   **ORM:** SQLAlchemy
*   **Templating:** Jinja2
*   **Dependency Management:** `uv` (recommended) or `pip`

## Project Structure

```
.
├── database.py      # Database connection and session management
├── main.py          # Application entry point and configuration
├── models.py        # SQLAlchemy database models
├── schemas.py       # Pydantic schemas for data validation
├── routers/         # API route handlers
│   ├── posts.py     # Post-related endpoints
│   └── users.py     # User-related endpoints
├── templates/       # HTML templates (Jinja2)
├── static/          # CSS, JavaScript, and static images
└── media/           # User-uploaded content (e.g., profile pics)
```

## Installation

### Prerequisites

*   Python 3.12 or higher
*   [uv](https://github.com/astral-sh/uv) (recommended) or `pip`

### Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd fastapi_blog
    ```

2.  **Install dependencies:**

    Using `uv` (faster, utilizes `uv.lock`):
    ```bash
    uv sync
    ```

    Using `pip`:
    ```bash
    pip install -r requirements.txt
    # Note: If requirements.txt doesn't exist, use:
    # pip install "fastapi[standard]" sqlalchemy aiosqlite greenlet
    ```

## Usage

1.  **Run the development server:**

    Using `uv`:
    ```bash
    uv run fastapi dev main.py
    ```

    Using standard python:
    ```bash
    fastapi dev main.py
    ```

2.  **Access the application:**
    *   Open your browser and navigate to `http://127.0.0.1:8000`.
    *   API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`.
    *   ReDoc: `http://127.0.0.1:8000/redoc`.

## API Endpoints

The application exposes the following API endpoints (prefixed with `/api`):

### Users (`/api/users`)
*   `POST /`: Create a new user.
*   `GET /{user_id}`: Get user details.
*   `GET /{user_id}/posts`: Get all posts for a specific user.
*   `PUT /{user_id}`: Update user details (full update).
*   `PATCH /{user_id}`: Update user details (partial update).
*   `DELETE /{user_id}`: Delete a user.

### Posts (`/api/posts`)
*   *(Check `/docs` for full list of post endpoints)*

## Database

The project uses SQLite (`blog.db`). The database tables are automatically created on application startup if they do not exist (defined in `main.py` lifespan).
