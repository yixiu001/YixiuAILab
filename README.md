# Disposable workflow smoke test

This repository contains synthetic, disposable test fixtures for checking a
branch / pull-request / continuous-integration workflow. These examples are not
business requirements, a production application, or a deployment target.

The baseline contains an import smoke test. Task A adds integer addition and its
tests. Task B independently adds integer subtraction and its tests. Both tasks
start from the same baseline so their integration can be tested separately.

Run the standard-library-only test suite with Python 3.12:

```sh
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs this command for pull requests targeting
`develop` and pushes to `develop`. It has read-only repository permissions,
does not persist checkout credentials, and has no production or deployment step.
No application secrets or third-party Python packages are needed.
