# Application Blueprint: ScienceValet

## 1. Plan (Task List Generation)
* **Objective:** An agentic AI application to curate astro-ph papers based on a person's research publications, code repositories and public sources of information. A web application allows a person to sign in using their ORCID and see the latest prioritized reading list.
* **Architecture:** React frontend, Mariadb backend, Docker Compose microservices.
* **Repo:** Use the shorthand name **scivalet** for git repos and convenient references to this project.
* **Agent Instruction:** Review this blueprint and generate a structured **Task List**. Do not write code until the Task List is approved by the user.

## 2. Implement (Implementation Plan)
* **Execution Strategy:** Break down the approved Task List into modular components. 
* **Parallel Work:** Spin up a subagent for the frontend UI components while the main agent handles the SQLAlchemy/Mariadb modeling.
* **Cron Jobs:** Use cron to automatically execute background tasks that e.g. scan for new publications using the ADS service, scraping Google Scholar, etc.
* **Agent Instruction:** For each major feature, generate an **Implementation Plan** artifact. Detail the exact files to be modified. Make all changes in the `develop` branch and generate pull requests for user review and manual merge back to main.

## 3. Verify (Testing & Walkthrough)
* **Quality Gates:** * All new endpoints must have unit tests.
  * Run the OWASP Dependency Checker CLI command on all new `package.json` additions.
* **Agent Instruction:** Once code is deployed locally, generate a **Walkthrough** artifact summarizing the changes, how the user can test them, and capturing UI state screenshots if applicable.

## 4. Deploy
* **CI/CD:** Ensure all tests pass.
* **Agent Instruction:** Use the Git/Composio MCP to stage files, generate a descriptive commit message based on the Walkthrough, and push to the `develop` branch.

