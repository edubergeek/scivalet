# Application Blueprint: ScienceValet

## 1. Plan (Task List Generation)
* **Objective:** Build a web application to curate **astro-ph** papers into a ranked recommended reading list that is based on inferring a person's research interests by mining their online research digital footprint comprising publications, code repositorie, social media posts and other public sources of information (conference presentations, Ted talks, press releases, etc.). The web application securely identifies a person using their ORCID, email address, name and institutional affiliation.
* **Architecture:** Use container virtualization with options for Docker Compose and Kubernetes Pod deployment. Use Python, FastApi, React, SQLAlchemy, Mariadb. Follow pythonic conventions, use CamelCase variable names, OOP, inline Python comments and fully unit test coverage.
* **Repo:** Use the shorthand name **scivalet** for git repos and convenient references to this project.
* **Agent Instruction:** Review this blueprint and generate a structured **Task List**. Do not write code until the **Task List** is approved by the user.

## 2. Implement (Implementation Plan)
* **Execution Strategy:** Break down the approved Task List into modular components. Make a clean separation between frontend and backend components. Assume the backend and background tasks run on Linux using either Docker Compose or Kubernetes. The front end should use HTML5 with modern browser compatibility (at least Chrome, Edge, Safari, Firefox).
* **Parallel Work:** Spin up separate subagents for the frontend UI component, the background user preference inference and astro-ph new paper search components and the FastApi/SQLAlchemy/Mariadb backend.
* **Cron Jobs:** Use cron to automatically execute the background tasks that e.g. scan for new publications and that infer the user preferences.
* **Agent Instruction:** For each major component, generate an **Implementation Plan** artifact. Detail the exact files to be modified. Make all changes in the `develop` branch and generate pull requests for user review and manual merge back to main.

## 3. Verify (Testing & Walkthrough)
* **Quality Gates:** * All new endpoints must have unit tests.
  * Run the OWASP Dependency Checker CLI command on all new `package.json` additions.
* **Agent Instruction:** Once code is deployed locally, generate a **Walkthrough** artifact summarizing the changes, how the user can test them, and capturing UI state screenshots if applicable.

## 4. Deploy
* **CI/CD:** Ensure all tests pass.
* **Agent Instruction:** Use the Git/Composio MCP to stage files, generate a descriptive commit message based on the Walkthrough, and push to the `develop` branch.

