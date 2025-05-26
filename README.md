# uni-records-management-sys

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python Version](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org)

A comprehensive record management system for universities, designed to streamline administrative processes and ensure data integrity. This project encompasses key university entities such as students, lecturers, courses, and departments, providing a robust database and API for efficient data management and querying.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Key Technologies / Libraries](#key-technologies--libraries)
- [System Architecture](#system-architecture)
- [Data Management and Seeding](#data-management-and-seeding)
- [API and UI](#api-and-ui)
- [Backup and Security](#backup-and-security)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Introduction

The "*uni-records-management-sys*" project aims to provide a modern, efficient, and secure system for managing university records. By leveraging Python (3.11+), Flask, and SQLAlchemy, the project offers a maintainable architecture and a RESTful API for seamless data access.

## Features

- **Comprehensive Data Models**: Well-defined data models for students, lecturers, courses, departments, programs, and research projects.
- **RESTful API**: Exposes a RESTful API built using Flask-RESTx for easy data retrieval and manipulation.
- **Automated Data Seeding**: Includes a sophisticated seeding script to populate the database with realistic dummy data.
- **Secure Backup and Restore**: Implements a robust backup, encryption, and decryption strategy using PowerShell scripts.
- **Detailed API Documentation**: Automatically generated Swagger UI for API documentation.

## Key Technologies / Libraries

This project utilizes several key Python libraries and technologies:

- **Web Framework**:
  - Flask
  - Flask-RESTx *(for API development)*
- **Database & ORM**:
  - SQLAlchemy
  - Flask-SQLAlchemy
  - SQLAlchemy-Utils
  - Flask-Migrate *(for database schema migrations)*
- **MySQL Connector**:
  - PyMySQL
- **Data Handling**:
  - pandas
  - openpyxl *(for data seeding and Excel file interactions)*
- **Security**:
  - cryptography *(for encryption functionalities)*
- **Environment Management**:
  - python-dotenv
- **Utility**:
  - Requests *(for HTTP requests)*
  - psutil *(for system utilities)*
  - colorama *(for colored terminal output)*
- **Testing**:
  - pytest

*For a complete list of dependencies and their exact versions, please see the [`requirements.txt`](./requirements.txt) file.*

## System Architecture

The system architecture is built around a relational database implemented using SQLAlchemy, a powerful Python-based Object-Relational Mapper (ORM). The core entities of the university are defined as Python classes in the [`app/models`](./app/models/) directory.

- **Department**: Represents academic departments within the university (`department.py`).
- **Lecturer**: Stores information about academic staff (`lecturer.py`).
- **Course**: Defines academic courses (`course.py`).
- **BaseModel**: Serves as a parent class for other models, including common fields such as `created_at` and `updated_at` (`base.py`).
- **CourseOffering**: Manages specific instances of courses taught in particular semesters (`course_offering.py`).
- **Program**: Outlines academic programs offered (`program.py`).
- **Student**: Manages student records (`student.py`).
- **Enrollment**: Manages student course registrations (`enrollment.py`).
- **NonAcademicStaff**: Manages records for non-teaching staff (`non_acad_staff.py`).
- **ResearchProject**: Tracks research activities (`research_project.py`).
- **project_team_members**: Links Lecturers to ResearchProjects as team members (`association_tables.py`).

## Data Management and Seeding

The project includes a seeding script (`seed_database_expanded.py`) located in the [`scripts/`](./scripts/) directory. This script populates the database with a large volume of realistic dummy data, ensuring that the system can be thoroughly tested under conditions that mimic real-world usage.

## API and UI

The system exposes a RESTful API built using Flask-RESTx at `http://localhost:5000/api/docsNdemo`. The API endpoints are defined in `app/routes/api.py` and organized using Flask-RESTx namespaces. Flask-RESTx provides automatic Swagger UI generation through Open API Specification for API documentation.

Key API Features:
*   Filtering capabilities
*   Input validation
*   Error handling

## Backup and Security

This project implements a robust backup, encryption, and decryption strategy using PowerShell scripts located in the [`scripts/backup/`](./scripts/backup/) folder.

- **backup_script.ps1**: Automates the process of creating secure MySQL database backups using OpenSSL to create AES-256-CBC with PBKDF2 encrypted backups.
- **decrypt_script.ps1**: Designed to manually decrypt the backups created by `backup_script.ps1`.
- **restore_script.ps1**: Automates the database restoration process from the most recent backup created by `backup_script.ps1`.

These scripts ensure confidentiality, data availability, and integrity, providing a comprehensive solution for data backup and recovery.

## Installation

1.  **Clone the repository:**
    ```
    git clone https://github.com/codex4732/uni-records-management-sys.git

    cd uni-records-management-sys
    ```
2.  **Create a virtual environment (Python 3.11+ recommended):**
    ```
    python -m venv .venv  # Ensure you are using Python 3.11 or newer
    
    source .venv/bin/activate # On Linux/macOS

    # OR

    .venv\Scripts\activate # On Windows
    ```
3.  **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```
4.  **Set up the environment:**
    - Ensure you have a MySQL server running. The default database name is `urms_dev`. You can create/change this in the `.env` file if needed.
    - This program requires/assumes the use of a venv environment (to be named `.venv`) so as to avoid making direct changes to the main environment.
      - not configured for conda out-of-the-box

## Usage

There are two ways to run the application: automated and manual. Ensure that you have a MySQL server running before proceeding.

### Automated (Recommended)

1.  Run the `cross_platform_launcher.py` script:
    ```
    python cross_platform_launcher.py
    ```
2.  Follow the prompts:
    - Select `1` for the first-time setup.
    - Select `2` for subsequent usage (launches the Flask server and opens the web browser to access the API).
    - *Select `0` to exit.*

### Manual

1.  Run the `run.py` file:
    ```
    python run.py
    ```
2.  In a separate terminal, run the seeding script:
    ```
    python -m scripts.seed_database_expanded
    ```
3.  Manually launch a browser and navigate to `http://localhost:5000/api/docsNdemo` to access the API.

## License

Copyright (c) 2025, codex4732, kn-msccs-uol, JohnnyPeng, and edu-mryo

This project is licensed under the BSD 3-Clause License. Please see the [LICENSE](./LICENSE) file for the full license text.

For important notices regarding the licensing of specific components originally from other projects, please refer to the [NOTICE.md](./NOTICE.md) file. This includes details on components derived from the CollegeDatabaseSystem project and their relicensing.
