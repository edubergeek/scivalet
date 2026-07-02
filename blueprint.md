# Application Blueprint: scivalet - Science Reading List Recommender

## 1. Plan (Task List Generation)
* **Objective:** Build a web application to generate a recommended reading list of science papers from sources such as [the arxiv](https://arxiv.org/), Nature, Science, etc. based on some method of modeling a person's research interests.Inputs to the interest model should be heterogenous including UI based filter keywords, tags or prompts, upvoting and downvoting, and non-interactive contextual information such as publication authorship, code repositories, social media posts, conference presentations, Ted talks, press releases, colloquia, invited talks, etc. The web application securely identifies a person using their ORCID, email address, name and institutional affiliation and allows a user to enter or select tags or keywords and a natural language prompt, a button to save the user's preferences and a display of recommended reading with titles, links and a short summary when the user hovers over a list item. Use the ADS list of keywords as a starting point. Implement negation of keywords to filter out matches of a keyword. Treat science domains as keywords that can be included or excluded (negated).
* **Architecture:** Use container virtualization with options for Docker Compose and Kubernetes Pod deployment. Use Python, FastApi, React, SQLAlchemy, Mariadb. Follow pythonic conventions, use CamelCase variable names, OOP, and inline Python comments. Use iterative test driven development as the software engineering methodology to ensure high quality code with full unit testing and robust validation and verification.
* **Repo:** Use the shorthand name **scivalet** for git repos and as convenient shorthand reference to this project. Use 'Science Reading List Recommender' as the full name or title of the project.
* **Agent Instruction:** Review this blueprint and generate a structured **Task List**. Do not write code until the **Task List** is approved by the user. After each **Task List** is approved, use a develop branch to check out the code, write the code then generate a pull request for the user to review and merge. Each new development cycle should be accompanied by a release-notes.md document that highlights new features and important refactoring that was performed.

## 2. Implement (Implementation Plan)
* **Execution Strategy:** Break down the approved Task List into modular components. Make a clean separation between frontend and backend components. Assume the backend and all background tasks run on Linux using cron and either Docker Compose or Kubernetes. The front end should use HTML5, JavaScript and React with modern browser compatibility (the latest Chrome, Edge, Safari, Firefox).
* **Parallel Work:** Spin up separate subagents for the frontend UI component, the background user preference inference, the search for papers online, and the FastApi/SQLAlchemy/Mariadb backend.
* **Cron Jobs:** Use cron to automatically execute the background tasks that e.g. scan for new publications and that infer the user preferences.
* **Agent Instruction:** For each major component, generate an **Implementation Plan** artifact. Detail the exact files to be modified. Make all changes in the develop branch and generate pull requests for user review and manual merge back to main.

## 3. Verify (Testing & Walkthrough)
* **Quality Gates:** * All new endpoints (routes) must have unit tests. Run the OWASP Dependency Checker CLI command on all new `package.json` additions.
* **Agent Instruction:** Once code is deployed locally, generate a **Walkthrough** artifact (release-notes.md) summarizing the changes, how the user can test them, and capturing UI state screenshots if applicable.

## 4. Deploy
* **CI/CD:** Ensure all tests pass.
* **Agent Instruction:** Use the Git/Composio MCP to stage files, generate a descriptive commit message based on the Walkthrough, and push to the `develop` branch.

