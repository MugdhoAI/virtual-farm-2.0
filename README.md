# Virtual Farm 2.0

Virtual Farm 2.0 is an evolving agricultural decision support project. It is being built to help users explore farm management choices through a structured software workflow, with an emphasis on validating inputs and producing results only when the required model data is available.

The project is currently in active development. The focus is on making the application reliable, testable, and grounded in usable agricultural data before public deployment.

## The problem

Farm planning involves connected decisions about land, seed quality, fertilizer, labor, irrigation, and whether to sell or store a harvest. A decision tool can help organize these choices, but its output is only useful when the underlying assumptions and data are credible.

Virtual Farm aims to provide a foundation for exploring these decisions in one application. It is being developed with a clear rule: **missing model data must be reported, not replaced with invented figures.**

## Current project status

The application has a Flask backend, a browser based frontend, input validation for simulation decisions, an early access signup endpoint, and automated tests.

The simulation workflow is deliberately guarded. Some production model data and economic cost inputs are not yet complete, so the API can return a service unavailable response instead of presenting unsupported simulation results. This is an intentional data integrity safeguard while the model is being completed.

The project has not yet been deployed as a production service. Work is focused on auditing the current implementation, completing and validating the model inputs, improving end to end behavior, and strengthening the test suite.

| Area | Current state |
| --- | --- |
| Frontend | Existing HTML interface under active review |
| Backend API | Flask application with health, simulation, and early access routes |
| Input validation | Simulation decisions are checked before execution |
| Simulation model | Core workflow exists; required production data and economic inputs still need completion |
| Early access signup | Validation and SQLite persistence are implemented; deployment storage needs to be verified before hosting |
| Automated tests | Pytest suite is available and used during development |
| Deployment | Not deployed; release is intentionally paused until readiness checks pass |

## Design principles

- **Evidence over invented results.** The application should not generate agricultural or financial outputs from missing inputs.
- **Validate before calculating.** User decisions and request formats are checked before reaching the simulation engine.
- **Make limitations explicit.** When a required model input is missing, the system should explain that the result cannot yet be produced.
- **Improve through verification.** Changes should be supported by tests and end to end checks, not only by a page that appears to work.
- **Release responsibly.** Deployment follows model validation, functional testing, and a review of production requirements.

## Technology

- Python
- Flask
- SQLite for early access signup storage
- Pytest
- HTML, CSS, and JavaScript for the frontend

## Project structure

```text
virtual-farm-2.0/
├── backend/
│   ├── app.py
│   ├── early_access.py
│   └── simulation/
│       ├── engine.py
│       └── validation.py
├── frontend/
│   └── index.html
├── data/
├── requirements.txt
└── README.md
```

This is a high level view of the main application areas. Supporting modules and tests may add more files.

## Run locally

Python 3.10 or newer is recommended. The project has been developed and tested locally with Python 3.14.

### 1. Clone the repository

```bash
git clone https://github.com/MugdhoAI/virtual-farm-2.0.git
cd virtual-farm-2.0
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current terminal session, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the application

Run the Flask application from the backend directory so its simulation modules resolve correctly:

```bash
cd backend
python app.py
```

Open the local address printed by Flask in your browser. Keep the development server local; it is not a production deployment.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Serves the frontend |
| GET | `/health` | Returns the API health status |
| POST | `/simulate` | Validates simulation decisions and attempts to run the model |
| POST | `/early-access` | Validates and stores an early access signup |

The simulation endpoint expects a JSON object containing a `decisions` object and may accept a `seed` value. Invalid decisions are rejected. If required model data is unavailable, the API returns a service unavailable response rather than fabricating a result. Refer to the current source code and tests for the exact request fields and response formats.

## Run tests

From the repository root, with the virtual environment activated:

```bash
python -m pytest
```

Run the test suite after changing validation, simulation logic, API behavior, persistence, or frontend interactions. A passing test suite is one release requirement, not a substitute for checking that model data is complete and correct.

## Development roadmap

1. Audit the current frontend, backend, data files, and API behavior.
2. Resolve functional bugs and improve error handling.
3. complete the required agricultural and economic model inputs using documented, verifiable sources.
4. Add and verify tests for simulation behavior, validation, persistence, and error cases.
5. Test the complete user journey across supported screen sizes.
6. Review configuration, persistent storage, security, and operational requirements.
7. Deploy only after the release checks pass.

## Current limitations

Virtual Farm 2.0 is not yet intended for real farm planning or financial decisions. The production simulation depends on model data and economic inputs that are still being completed and verified. Until that work is finished, simulation results should not be treated as available or authoritative.

The early access feature uses SQLite locally. Its persistence and write access must be verified in any hosting environment before the feature is relied on in production.

These are active engineering milestones. Documenting them makes the project's progress measurable and keeps future improvements tied to correctness, reliability, and user trust.

## Contributing

The project is being stabilized before its first production release. Bug reports, reproducible test cases, and suggestions for improving model validation or data quality are useful. Please describe the expected behavior, actual behavior, and steps to reproduce an issue.

## License

No license has been specified yet. Until a license is added to the repository, permission to reuse, modify, or distribute this project should not be assumed.
