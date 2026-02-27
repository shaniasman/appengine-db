# Fast Simon—Cloud Database App

This is an implementation of the Google App Engine challenge, featuring a simple database with persistent state management and undo/redo capabilities.

## Live Application URL
**URL:** [https://project-d39071f6-530a-45c2-885.uc.r.appspot.com/](https://project-d39071f6-530a-45c2-885.uc.r.appspot.com/)

---

## Tech Stack
- **Language:** Python 3.14
- **Framework:** Flask
- **Cloud Provider:** Google Cloud Platform
- **Database:** Google Cloud Datastore

---

## Features Implemented

### Task I: Hello World
- **Path:** `/`
- Displays a basic "Hello, World!" message to verify environment setup.

### Task II: Database Commands
- **SET** (`/set?name={v}&value={v}`): Stores a variable.
- **GET** (`/get?name={v}`): Retrieves a value or returns "None".
- **UNSET** (`/unset?name={v}`): Removes a variable.
- **NUMEQUALTO** (`/numequalto?value={v}`): Returns the count of variables set to a specific value.
- **UNDO** (`/undo`): Reverts the most recent SET/UNSET command.
- **REDO** (`/redo`): Re-applies the most recent undone command.
- **END** (`/end`): Wipes all Datastore entities to ensure a clean state.

---

## Improved Feature
**Feature: Persistent Transaction Journaling with Audit Metadata**

### Why this improves the app:
In a stateless cloud environment like App Engine, standard in memory stacks (Python lists) would reset every time a new instance is spun up. 

1. **State Persistence:** I implemented a global `History` entity in Datastore. This ensures that the UNDO and REDO stacks are preserved across different HTTP requests and server restarts.
2. **Audit Trail:** Every transaction is tagged with a `tx_id` (UUID) and a UTC timestamp (`updated_at`). This turns a simple key-value store into an auditable database, allowing developers to track exactly when and how data changed.
3. **Performance Optimization:** Following Requirement 3, I used `exclude_from_indexes` for the history stacks to ensure that appending actions remains an $O(1)$ operation regardless of history size.

---

## Local Development
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
3. Authenticate with Google Cloud:
   ```bash
   gcloud auth application-default login
4. Set Project ID:
   ```bash
   gcloud config set project project-d39071f6-530a-45c2-885
5. Run the application:
   ```bash
   python main.py
   
The app will be available at http://127.0.0.1:8080.