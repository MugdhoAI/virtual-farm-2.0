# Contributing to Virtual Farm 2.0

Thank you for considering a contribution to Virtual Farm 2.0. Contributions can include bug fixes, tests, documentation improvements, accessibility fixes, and features that make the project more reliable for people making agricultural decisions.

## Before you start

For a small change, open an issue or discussion describing the problem before doing substantial work. For a larger feature or a change to simulation behavior, discuss the proposed approach first. This helps avoid duplicated effort and changes that do not fit the project's direction.

Check existing issues and pull requests before starting work.

## How to contribute

1. Fork the repository.
2. Create a branch for your change.
3. Make a focused change that addresses one problem.
4. Add or update tests where appropriate.
5. Run the test suite and review the results.
6. Commit your changes with a clear message.
7. Open a pull request against the `main` branch and explain what changed, why it is needed, and how you tested it.

## Development setup

Use Python 3 and follow any additional setup requirements documented in the README.

From the project root, create and activate a virtual environment.

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project requirements and run the tests:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

If a change affects the frontend, test the page at mobile and desktop widths and check browser console errors. Update the README if setup steps, API behavior, or project status changes.

## Simulation data and result integrity

Virtual Farm 2.0 must not present invented values as real agricultural or economic results.

- Do not add fabricated production data, crop yields, prices, fertilizer costs, labor costs, or other inputs to make a simulation appear complete.
- If required data is missing, preserve the existing validation behavior and report the limitation clearly.
- Use traceable sources for real datasets and document their origin, units, assumptions, and relevant limitations.
- Add tests for validation and failure cases when changing simulation logic.
- Keep calculations understandable and avoid presenting estimates as verified facts.

Reliable results are more important than producing an answer when the required evidence is unavailable.

## Pull request expectations

A good pull request should:

- Explain the problem and the proposed solution.
- Stay focused and avoid unrelated refactoring.
- Include tests for bug fixes or changes to behavior.
- Pass the relevant tests, or clearly document any existing failure that prevents them from passing.
- Update documentation when needed.
- Avoid committing secrets, API keys, local databases, virtual environments, generated files, or personal data.
- Respect existing licenses and the terms of any third party code or data.

Be prepared to respond to review feedback. A pull request may be discussed, revised, declined, or merged at the maintainers' discretion. Opening a pull request does not guarantee that it will be accepted.

## Reporting bugs

When reporting a bug, include the steps to reproduce it, the expected behavior, the actual behavior, and relevant error messages. Remove passwords, API keys, personal information, and other sensitive data before sharing logs.

## License

By submitting a contribution, you agree that your contribution is provided under the project's [MIT License](LICENSE). You retain the copyright to your contribution; the license allows others to use, modify, and distribute it under the MIT License terms.

## Questions

If you are unsure whether a change fits the project, open an issue before investing substantial time in implementation.
