# SaaS Integration Guide

This document outlines the changes made to transform the standard Agent Zero application into a multi-user, database-driven SaaS platform.

## 1. High-Level Goal

The objective is to transform the standard Agent Zero application into a multi-user, database-driven SaaS platform. This involves replacing the default UI with a custom frontend and adding a robust backend for user authentication and management, while preserving the original Agent Zero UI for authenticated users.

## 2. Core Architectural Changes & Integration Plan

- **Frontend**: The default Agent Zero UI has been replaced by a custom static frontend located in the `webui` folder. This is the main public-facing website where users register and log in.
- **Backend**: A new relational database (SQLite) has been added to manage users.
- **Authentication**: The application now has registration and login capabilities, with user sessions managed via JSON Web Tokens (JWT).
- **Integration with Agent Zero UI**:
    - The original Agent Zero UI, located in the `old_webui` folder, is now treated as the main application for logged-in users.
    - The server has been modified to protect the `old_webui`. It is only accessible to users who have a valid JWT token, served from a protected route at `/app`.
    - After a user logs in successfully through the main website (`webui`), they are presented with a "Go to App" button to access the protected Agent Zero application.

## 3. Folder Structure Modifications

- The original Agent Zero UI folder, `webui`, has been renamed to `old_webui`.
- The custom static frontend has been placed in a new folder named `webui`.

## 4. Backend Implementation Details

### 4.1. Database Setup

The following files were created to set up the database:

- `database/database.py`: Configures the database connection and session management.
- `database/models.py`: Defines the `User` model for the database.
- `database/schemas.py`: Defines the Pydantic schemas for user data validation.
- `database/crud.py`: Contains the functions for creating, reading, updating, and deleting users.

### 4.2. API Endpoints

The following API endpoints were created for user authentication:

- `python/api/api_register.py`: Handles user registration.
- `python/api/api_login.py`: Handles user login and JWT generation.

## 5. Application Startup Modification

In `run_ui.py`, the database is initialized on startup. A call to `init_db()` was added inside the `run()` function.

## 6. Dependencies

The following Python libraries were added to `requirements.txt`:

- `SQLAlchemy==2.0.31`
- `pydantic==2.10.4` (updated to resolve dependency conflicts)
- `passlib[bcrypt]`
- `PyJWT==2.8.0`

## 7. Frontend Integration Plan

A new file, `webui/auth/integration.js`, was created to connect the forms in the custom `webui` to the backend. This script:

- Adds event listeners to the login and registration forms.
- On submit, gathers the email and password values from the input fields.
- Uses the `fetch` API to send POST requests to `/api_login` and `/api_register`.
- Handles the JSON response: On successful login, it saves the returned JWT token to `localStorage` and displays a "Go to App" button. On error, it displays an error message.

## 8. UI/Theme Enhancements

To create a consistent user experience, the theme of the `old_webui` (the original Agent Zero UI) has been updated to match the new `webui`.

- The color variables in `old_webui/css/custom-theme.css` have been updated to match the color palette of the new `webui` for both light and dark modes.
- This approach ensures that the original Agent Zero CSS files are not modified, allowing for easier updates from the upstream project.
