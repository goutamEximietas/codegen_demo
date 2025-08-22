Technical Specifications Requirements Document
* Project Name: LeaveBoard
* Module / Feature: Core Leave Management System
* Version: 1.0
* Author: Engineering Team (Collaborative)
* Date: 2023-10-27




Core System Components
For each major component, provide the following:


![System Component Diagram]()Placeholder for a high-level system component diagram showing interaction between Frontend, Backend, Database, and Email Service.


🔹 Component: Backend Service (LeaveBoard API)
* Purpose: Provides RESTful API endpoints for leave management, handles core business logic (leave request submission, approval workflows, leave calculation), and manages data persistence. It acts as the central hub for all application data and logic.[Expert A Contribution: High-level purpose and responsibilities]
* Technical Requirements:-   Runtime: Node.js (LTS version, e.g., 18.x or 20.x)-   Framework: Express.js-   ORM: Prisma-   Database Client: PostgreSQL client (managed by Prisma)-   Testing Framework: Jest-   Key Libraries: express, @prisma/client, jsonwebtoken, bcryptjs (for password hashing), cors middleware.[Expert A/C Contribution: Based on MoM tech stack decisions]
* Interfaces:-   Consumers: Frontend React.js application. Future potential consumers may include internal HR systems.-   Providers: PostgreSQL database (accessed via Prisma), External Email Service (for sending notifications).-   Protocols: RESTful API over HTTPS.[Expert B Contribution: Defining communication points]
* Data Requirements:-   Inputs: JSON payloads from the frontend (e.g., user login credentials, leave request details, manager approval actions).-   Outputs: JSON responses (e.g., authenticated user data, leave request statuses, error messages).-   Storage: Persists User and LeaveRequest data in PostgreSQL database.-   Volume: Anticipated low to medium for MVP, scaling based on typical SME usage.[Expert B Contribution: Defining data flow and scale]




🔹 Component: Frontend Application (LeaveBoard UI)
* Purpose: Provides an intuitive and responsive user interface for employees to submit leave requests and view their leave history, and for managers to review and act upon pending leave requests from their direct reports.[Expert A Contribution: High-level purpose and responsibilities]
* Technical Requirements:-   Runtime: Web Browser (modern evergreen browsers)-   Framework: React.js-   Language: TypeScript-   Build Tool: Vite-   UI Library: Chakra UI-   API Client: Axios-   State Management: React Context API (for global state like authentication), local component state (for form data, UI interactions).-   Testing Frameworks: Vitest, React Testing Library[Expert A/C Contribution: Based on MoM tech stack decisions]
* Interfaces:-   Consumers: End-users via web browsers.-   Providers: Backend LeaveBoard API Service.-   Protocols: REST over HTTPS.[Expert B Contribution: Defining communication points]
* Data Requirements:-   Inputs: User interactions and form submissions (e.g., date selection for leave, text input for reasons, button clicks for actions).-   Outputs: Display of leave information, real-time feedback, validation messages, and potentially non-sensitive local cached data for UX improvements.-   Local Storage: Minimal usage, primarily for non-sensitive UI preferences or caching, no sensitive user data.[Expert B Contribution: Defining data flow and local data handling]




🔹 Component: PostgreSQL Database
* Purpose: Provides reliable, persistent, and structured storage for all application data, including user profiles, organizational hierarchy, and leave request details. It serves as the single source of truth for all leave management data.[Expert A Contribution: High-level purpose]
* Technical Requirements:-   Type: Relational Database (PostgreSQL 14+).-   Access Method: Accessed exclusively by the Backend Service via the Prisma ORM. No direct client access.-   Hosting: Managed service provided by Render.[Expert A/C Contribution: Based on MoM tech stack decisions]
* Interfaces:-   Consumers: Backend Service only.-   Protocols: Standard PostgreSQL client/server wire protocol.[Expert B Contribution: Defining access and protocols]
* Data Requirements:-   Inputs: Data writes from the Backend (e.g., new user registrations, leave request creations, status updates for leave requests).-   Outputs: Data reads for the Backend (e.g., fetching user details, retrieving leave history, querying pending requests for a manager).-   Format: Structured relational tables and schemas. Dates related to leave duration will be stored using the DATE type to avoid time-of-day ambiguity and adhere to the single "Company Timezone" approach.[Expert B Contribution: Defining data flow and specific formatting]




API Specifications
🔹 Endpoint Requirements
* Endpoint:/api/v1/auth/login-   Method:POST-   Description: Authenticates a user with email and password. On success, issues a JSON Web Token (JWT) and sets it as an httpOnly, secure, SameSite=Lax cookie.-   Parameters:    -   body: { "email": "string", "password": "string" }-   Response Format:JSON (e.g., {"message": "Login successful"}). The JWT is delivered via cookie, not in the response body.-   Notes: No direct JWT return in response body for enhanced security.[Expert B Contribution]
* Endpoint:/api/v1/auth/logout-   Method:POST-   Description: Invalidates the user's session by clearing the httpOnly cookie.-   Parameters: None-   Response Format:JSON (e.g., {"message": "Logout successful"})-   Notes: Requires an active session (cookie present).[Expert B Contribution]
* Endpoint:/api/v1/users/me-   Method:GET-   Description: Retrieves the authenticated user's profile information.-   Parameters: None-   Response Format:JSON (See Data Formats for User object schema)-   Notes: Authentication required via JWT cookie.[Expert B Contribution]
* Endpoint:/api/v1/leaves-   Method:POST-   Description: Allows an authenticated employee to submit a new leave request.-   Parameters:    -   body: { "startDate": "string (YYYY-MM-DD)", "endDate": "string (YYYY-MM-DD)", "reason": "string (max 500 chars)", "type": "string" }-   Response Format:JSON (See Data Formats for Leave Request object schema of the newly created request)-   Notes: Authentication required. All requests must be for full-day increments. startDate and endDate are inclusive, based on simple calendar day calculation.[Expert B / A Cross-check for functional details]
* Endpoint:/api/v1/leaves/my-   Method:GET-   Description: Retrieves all leave requests submitted by the authenticated user.-   Parameters:    -   query: status (optional, string: e.g., 'Pending', 'Approved', 'Rejected')-   Response Format:JSON array of Leave Request objects-   Notes: Authentication required.[Expert B Contribution]
* Endpoint:/api/v1/leaves/pending-   Method:GET-   Description: Retrieves pending leave requests for the authenticated manager's direct reports.-   Parameters: None-   Response Format:JSON array of Leave Request objects-   Notes: Authentication required. User must have a 'Manager' role. Requests follow employee organizational changes.[Expert B / A Cross-check for functional details]
* Endpoint:/api/v1/leaves/:id/approve-   Method:PUT-   Description: Approves a specific leave request.-   Parameters:    -   path: id (UUID of the leave request)    -   body: {} (Optional: approverId and approvalDate derived internally)-   Response Format:JSON (updated Leave Request object)-   Notes: Authentication required. User must be the respective manager of the employee or an authorized administrator. Triggers an email notification to the employee.[Expert B / A Cross-check for functional details]
* Endpoint:/api/v1/leaves/:id/reject-   Method:PUT-   Description: Rejects a specific leave request.-   Parameters:    -   path: id (UUID of the leave request)    -   body: { "rejectionReason": "string (optional, max 500 chars)" }-   Response Format:JSON (updated Leave Request object)-   Notes: Authentication required. User must be the respective manager or an authorized administrator. Triggers an email notification to the employee.[Expert B / A Cross-check for functional details]


🔹 Authentication
* Mechanism: JSON Web Tokens (JWTs) are used to maintain user sessions post-authentication.
* Token Storage: JWTs will be stored in httpOnly and secure cookies on the client side.
* Cookie Attributes:-   httpOnly: Prevents client-side JavaScript from accessing the token, providing robust protection against Cross-Site Scripting (XSS) attacks.-   secure: Ensures the cookie is only sent over encrypted HTTPS connections.-   SameSite=Lax: Offers a good balance of security and usability, mitigating some forms of Cross-Site Request Forgery (CSRF) attacks. Explicit CORS configuration on the backend is crucial to avoid misconfigurations.
* Token Expiration: JWTs will have a defined expiration time (e.g., 1 hour, TBD) to limit the window of compromise. A refresh token mechanism is out of scope for MVP but can be added later.[Expert D / B Cross-check: Security details for the authentication method]


🔹 Data Formats
* Request/Response: All communication with the API will use JSON format.
* Schemas:-   User Object (Example):    `json    {      "id": "string (UUID)",      "name": "string",      "email": "string (unique)",      "role": "string", // Example: "Employee", "Manager"      "managerId": "string (UUID) | null" // Self-referencing to User ID, null if no manager    }    `-   Leave Request Object (Example):    `json    {      "id": "string (UUID)",      "employeeId": "string (UUID)",      "startDate": "string (YYYY-MM-DD)",      "endDate": "string (YYYY-MM-DD)",      "durationDays": "number", // Calculated based on calendar days, inclusive      "type": "string", // TBD: e.g., "Vacation", "Sick", "Unpaid", etc. (or a defined enum for strictness)      "reason": "string",      "status": "string", // "Pending", "Approved", "Rejected"      "requestDate": "string (ISO 8601, YYYY-MM-DDTHH:mm:ssZ)",      "approverId": "string (UUID) | null",      "approvalDate": "string (ISO 8601, YYYY-MM-DDTHH:mm:ssZ) | null",      "rejectionReason": "string | null"    }    `-   Login Request: {"email": "string", "password": "string"}
* Validation Rules: Server-side validation will enforce presence, type, format, and range constraints (e.g., startDate before endDate, non-empty strings, valid email format).[Expert B Contribution: Defining data structures]


🔹 Error Handling
* HTTP Status Codes: Backend will utilize standard HTTP status codes to indicate the outcome of API requests (e.g., 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error).
* Error Response Structure: All API errors will conform to a consistent JSON structure:`json{  "statusCode": "number",    // HTTP status code  "error": "string",         // A brief, canonical error identifier (e.g., "BAD_REQUEST", "UNAUTHORIZED")  "message": "string",       // A more descriptive, user-friendly message  "details": "object | null" // Optional: Additional context like validation errors or a simplified stack trace (in development environments only)}
* Logging: All 4xx and 5xx errors originating from the backend will be logged, including request details, timestamp, and potentially a unique correlation ID (TBD) for end-to-end tracing in future versions.[Expert B / D Cross-check: Consistent error reporting for usability and debugging]




Data Management Requirements
🔹 Data Models
Placeholder for Entity-Relationship Diagram if available later: ![Entity-Relationship Diagram]()


* Conceptual Entity-Relationship Overview:   User*: Represents an individual. Can be an Employee or a Manager.    *   Attributes: id (Primary Key, UUID), name (String), email (String, Unique), passwordHash (String), role (Enum: Employee, Manager, Admin - for MVP only Employee and Manager are active), managerId (Foreign Key to User.id, nullable for top-level managers/admins).    *   Relationships: Self-referencing Many-to-One (User.managerId -> User.id) to model hierarchy; One-to-Many (User -> LeaveRequest) for employee-submitted requests; One-to-Many (User -> LeaveRequest) for manager-approved requests.   LeaveRequest*: Represents a single instance of a leave request.    *   Attributes: id (Primary Key, UUID), employeeId (Foreign Key to User.id), startDate (DATE), endDate (DATE), type (String, TBD as Enum), reason (Text), status (Enum: Pending, Approved, Rejected), requestDate (DATETIME), approverId (Foreign Key to User.id, nullable until approved/rejected), approvalDate (DATETIME, nullable), rejectionReason (Text, nullable).    *   Relationships: Many-to-One (LeaveRequest.employeeId -> User.id); Many-to-One (LeaveRequest.approverId -> User.id).
* Versioning Strategies: For MVP, schema changes will be managed using Prisma's migration system. Additive changes are preferred. A formal API versioning strategy (e.g., /v2/) is out of scope for MVP.[Expert B Contribution: Defining core entities and their relationships]


🔹 Storage Requirements
* Database type: PostgreSQL.
* Capacity planning:   Initial Estimates*: User records are small (~1KB), LeaveRequest records are also small (~1KB).   MVP Scale*: Anticipated support for up to 100-200 users and several thousand leave requests within the MVP timeframe. Total initial data size expected to be well under 100MB.   Growth Considerations*: Scalability will rely on Render's managed PostgreSQL capabilities. Indexing strategies will be revisited as query performance demands grow.
* Indexing: Default indexes will be applied by Prisma for primary keys and foreign keys. Additional indexes will be added for frequently queried columns (e.g., LeaveRequest.employeeId, LeaveRequest.status, requestDate) to optimize query performance.
* Partitioning, Archival Rules: Not required for MVP. These will be considered in future phases as data volume and retention policies evolve.[Expert B Contribution: Storage strategy and preliminary sizing]


🔹 Data Processing
* ETL pipelines: Not applicable for MVP. Data flow is direct interaction via the API.
* Validation and Sanitization Rules:*   All incoming API request payloads will undergo rigorous server-side validation to ensure data integrity, correct formats, and adherence to business rules.*   User-provided text inputs (e.g., reason, rejectionReason) will be sanitized to prevent injection attacks (e.g., XSS) before storage, though primary XSS mitigation is at the UI layer.
* Transformation Logic:   Leave Duration Calculation*: Based on input startDate and endDate, the system will calculate the inclusive "total calendar days" (as per FR01), not business days or public holidays. This simplified calculation will be explicitly communicated in the UI.   Manager Hierarchy*: Approval routing will use direct managerId lookup. Complex scenarios like manager delegation or multi-level approvals are out of scope for MVP; manual fallback processes are expected.   Timezone Handling*: All date calculations and interpretations will strictly adhere to a single "Company Timezone" (EST/UTC-5, as discussed in MoM). Database columns for dates will use the DATE type to avoid time-of-day ambiguities, with the backend handling timezone conversions for display where required.[Expert B / A Cross-check: Detailing data transformation and business logic from requirements]


🔹 Backup and Recovery
* Strategy: Rely on Render's automated managed PostgreSQL backup services.
* Details: Render typically provides continuous backups and point-in-time recovery capabilities. The specific retention policy provided by Render (e.g., 7 days of continuous archiving) will be utilized.
* Disaster Recovery (DR) RTO/RPO: Formal RTO (Recovery Time Objective) and RPO (Recovery Point Objective) are not explicitly defined for MVP but implicitly rely on Render's service level agreements for their managed database. Manual recovery from backups would serve as a last resort.[Expert D Contribution, noting reliance on cloud provider for data durability]




Integration Requirements
🔹 External System Interfaces
* System: External Email Service (Specific provider TBD, e.g., SendGrid, Mailgun)-   API/Interface: REST API for sending transactional emails.-   Method: POST (for sending email messages).-   Frequency: Event-driven (triggered upon leave request status change: approval or rejection).-   Auth Method: API Key, securely managed as an environment variable in Render.-   Notes: As per FR05 and NFR02, email delivery failures must be logged aggressively; the primary business action (e.g., leave approval) should not fail if the email notification fails. In-app notifications are explicitly out of scope for MVP.[Expert B / A Cross-check: Detailing external dependency and its behavior from requirements]


🔹 Message Formats
* All communication with external RESTful APIs (e.g., Email Service) will use JSON format for request bodies and parse JSON for responses.
* Email content generated by the backend will be standard HTML or plain text, depending on the template.[Expert B Contribution]


🔹 Communication Protocols
* All external API calls (e.g., to the Email Service) will strictly use REST over HTTPS to ensure data in transit is encrypted and secure.[Expert B Contribution]


🔹 Error Handling
* Retry Logic: For transient failures when calling external services (e.g., network timeout, service busy), a basic retry mechanism with exponential backoff will be implemented (e.g., maximum of 3 retries).
* Alerting: Automated alerts (TBD: specific mechanism and severity thresholds) will be configured if the email notification service consistently fails or encounters persistent errors, indicating a systemic issue.
* Dead Letter Queue (DLQ): Not within MVP scope for async integrations. While critical actions should not be blocked by notification failures, unrecoverable email errors will primarily be logged for investigation, not re-queued.[Expert B / D Cross-check: Defining robustness for external integrations]




Security Technical Requirements
🔹 Authentication Mechanisms
* User Authentication: Utilizes JWTs stored in httpOnly, secure, SameSite=Lax cookies. This mechanism ensures valid user sessions while preventing client-side JavaScript access to tokens (XSS mitigation) and providing CSRF protection.
* Credential Management: User passwords will be hashed using a strong, industry-standard algorithm (e.g., bcrypt) before storage in the database.
* Internal Service Authentication: Communications between backend and database, and backend and external email service, will use secure connection strings and API keys, managed as environment variables within the hosting platform (Render).[Expert D Contribution: Comprehensive authentication strategy]


🔹 Authorization Controls
* Role-Based Access Control (RBAC):-   Employee Role: Authorized to create new leave requests, view their own leave history, and update their profile (TBD for profile update API).-   Manager Role: Inherits Employee permissions and is additionally authorized to view and approve/reject leave requests from their direct reports.-   Admin Role: (TBD for MVP: if dedicated admin functions are developed).
* Fine-grained Permissions: Authorization checks will be enforced at the API endpoint level to ensure only authorized roles can perform specific actions (e.g., only managers can access approval endpoints for their direct reports).[Expert D Contribution: Defining access control based on user roles]


🔹 Data Protection
* Encryption at Rest:-   Database Data: PostgreSQL data at rest will be encrypted transparently by the cloud provider (Render's managed service). This covers the physical storage of the database.-   Sensitive Fields: Passwords in the database will be stored as cryptographically strong hashes, not in plain text. Other PII (e.g., names, emails) will not be encrypted at the field level for MVP, relying on database-level encryption and access controls.
* Encryption in Transit:-   All network communication: Between the Frontend and Backend, Backend and Database, and Backend and external services (e.g., Email Service) will be secured using TLS 1.2+ (HTTPS).-   Hosting platforms (Render, Vercel) provide automatic TLS certificate management.[Expert D Contribution: Detailing data encryption and transmission security]


🔹 Audit and Logging
* Critical Action Logging: Key user actions and system events will be logged, including:-   User login/logout attempts (success/failure).-   Creation, modification, and deletion of LeaveRequest records.-   Any critical system errors (e.g., 500 server errors, external service communication failures).
* Log Content: Logs will include relevant context such as timestamp, affected entity ID, action type, user ID (if applicable), and IP address.
* Notification Failure Logging: Instances where an email notification fails to send will be explicitly logged (as per FR05) to allow for manual follow-up or system diagnostics.
* Log Storage & Retention: For MVP, logs will be collected from standard output/error streams by the hosting providers (Render, Vercel). Retention will be determined by the provider's default policy (likely a few days to weeks), suitable for immediate debugging. A dedicated log aggregation platform is not in MVP scope.[Expert D / A / B Cross-check: Defining logging scope for security and operational insights]




Implementation Specifications
🔹 Development Standards
* Code Style Guides:-   Backend: ESLint configured with a standard Node.js/TypeScript ruleset (e.g., based on Airbnb). Prettier will be used for automatic code formatting.-   Frontend: ESLint configured with React and TypeScript-specific rules. Prettier will ensure consistent formatting.
* Git Branching Strategy: A feature-branch workflow will be used (e.g., main for production releases, develop for staging and integration, and feature/X branches for individual feature development).
* Linting and Static Analysis: ESLint and Prettier will be integrated into the development environment (IDE) and enforced as part of the CI/CD pipeline to maintain code quality.[Expert C Contribution: Defining coding practices for consistency and quality]


🔹 Testing Requirements
* Unit Testing:-   Backend: Jest will be used for unit tests covering individual functions, services, and controllers. Target code coverage is TBD but will focus on critical business logic (e.g., leave calculation, approval logic).-   Frontend: Vitest and React Testing Library will be used for unit and component testing, ensuring individual UI components and utility functions behave as expected.
* Integration Testing: Tests to verify interaction between the Backend API and the database (using in-memory or dedicated test databases via Prisma's testing features) and mocked external services.
* End-to-End (E2E) Testing: Initially, E2E testing will be performed manually by the QA team, leveraging Vercel's preview deployments for efficient review. Automated E2E testing frameworks (e.g., Playwright, Cypress) are out of scope for MVP but are a future consideration.
* Automated Test Suite: All unit and integration tests will be run automatically as part of the GitHub Actions CI pipeline on every push to relevant branches (develop, main, feature branches).[Expert C Contribution: Defining testing strategy for quality assurance]


🔹 Documentation Standards
* API Documentation: A formal OpenAPI/Swagger specification might be generated (TBD). At minimum, backend API endpoints, request/response schemas will be documented using JSDoc/TSDoc comments, and a detailed README in the backend repository.
* Inline Code Comments: Will be used judiciously for complex algorithms, business rules, or non-obvious code sections.
* Repository READMEs: Each repository (backend, frontend) will contain a comprehensive README with project setup instructions, development guidelines, scripts, and deployment information.
* Architecture and Design Documents: This Technical Specifications Requirements Document serves as a primary architecture document. A DECISIONS.md file will track key architectural and technical decisions made throughout the project.[Expert C Contribution: Establishing documentation practices]




Deployment Technical Requirements
🔹 Environment Specifications
* Planned Environments:-   development: Local developer machines for isolated development and testing.-   staging: A pre-production environment for integration testing, QA, and internal stakeholder review. Backend and Database hosted on Render, Frontend on Vercel.-   production: The live, public-facing environment. Backend and Database hosted on Render, Frontend on Vercel.
* Resource Allocation: Rely on Render's and Vercel's managed service capabilities for sizing and auto-scaling. Specific CPU/RAM allocations are abstracted by the platforms but will be monitored.
* Secrets Management: All sensitive configurations (e.g., database connection strings, API keys) will be managed as environment variables directly within Render and Vercel's secure configuration settings for each environment.[Expert C Contribution: Detailing deployment landscape]


🔹 Configuration Management
* Runtime Configuration: Application configurations will be managed primarily through environment variables, which can be easily switched per environment (development, staging, production).
* Infrastructure as Code (IaC): Not implemented for MVP to accelerate development. Initial infrastructure setup on Render and Vercel will be performed manually through their respective user interfaces.
* Config Versioning: .env.example files will define required environment variables for local development. Actual sensitive values will be stored securely within the deployment platforms' configuration dashboards and not committed to source control.[Expert C Contribution: How configurations are handled across environments]


🔹 Monitoring and Alerting
* Application Monitoring:-   Backend: Render's built-in platform metrics (e.g., CPU usage, memory consumption, request latency, error rates) and structured application logs will be utilized for basic system health monitoring.-   Frontend: Basic client-side error monitoring will rely on browser developer console logs. Integration with a dedicated error tracking service (e.g., Sentry) is a future enhancement.
* Logging Aggregation: Logs from both backend and frontend applications will be collected by Render and Vercel respectively. These logs will be accessible through their platform dashboards for debugging and troubleshooting. No centralized log aggregation system for MVP.
* Alerting: Minimal alerting configured via Render/Vercel for critical service health events (e.g., service downtime, high error rates). Application-specific alerts (e.g., for persistent email notification failures) are TBD for MVP but could be implemented via a simple webhook/notification service.[Expert C / D Cross-check: Defining monitoring scope aligned with MVP constraints]




Technical Constraints
* Project Timeline: A strict 1-month deadline for MVP delivery necessitates prioritizing core functionality and rapid development over extended features, deep optimizations, or complex infrastructure.
* Leave Calculation Simplification: For MVP, leave duration calculation must be a simple difference between startDate and endDate (inclusive of both days), based on calendar days. Business day calculations, public holiday considerations, and partial-day leaves are explicitly out of scope.
* Manager Delegation: The MVP will not include functionality for manager delegation of approval authority. The system will rely on manual fallback processes (e.g., contacting the manager's manager or HR) when a manager is on leave.
* Timezone Standardisation: All date-related operations, calculations, and database storage will operate under a single, defined "Company Timezone" (EST/UTC-5) to avoid complexities with global timezones. Dates in the database will be stored as DATE types.
* Deployment Platform Lock-in (for MVP): The backend service and database are constrained to be deployed on Render, and the frontend application on Vercel. This decision was made to leverage ease of deployment for the MVP.
* No Containerization/Orchestration: Docker and Kubernetes will not be used for MVP deployment to reduce operational complexity and speed up initial setup and deployment.[Expert D Contribution: Compiling explicit limitations and assumptions from MoM and Workshop notes]




Acceptance Criteria
For each requirement/component, define:


* ID: AC-001-   Requirement: Employee Leave Request Submission-   Acceptance Criteria: An authenticated employee can successfully submit a new full-day leave request (with valid start/end dates and reason) via the UI, which is then persisted in the database with a 'Pending' status.[Expert A Contribution]
* ID: AC-002-   Requirement: Manager Leave Approval/Rejection Workflow-   Acceptance Criteria: An authenticated manager can view pending leave requests from their direct reports and successfully approve or reject them. Upon action, the leave request status updates in the system, and a corresponding email notification attempt is made to the employee.[Expert A Contribution]
* ID: AC-003-   Requirement: Leave Duration Display Accuracy-   Acceptance Criteria: The UI explicitly states "Leave duration is calculated as total calendar days (inclusive)" where relevant, and the displayed duration for any leave request correctly reflects the total number of calendar days between the startDate and endDate (inclusive).[Expert A / D Cross-check (NFR01)]
* ID: AC-004-   Requirement: Secure API Authentication-   Acceptance Criteria: Users can successfully authenticate via email/password, receiving a secure httpOnly JWT cookie. Subsequent API calls requiring authentication are successfully authorized using this cookie. Unauthorized attempts are blocked with a 401 Unauthorized response.[Expert B / D Cross-check]
* ID: AC-005-   Requirement: Data Persistence and Retrieval-   Acceptance Criteria: All data created or modified through API interactions (e.g., user registrations, leave requests, status changes) is reliably stored in the PostgreSQL database and can be consistently retrieved across application restarts and deployments.[Expert B Contribution]
* ID: AC-006-   Requirement: Email Notification Fallback Reliability-   Acceptance Criteria: In cases where an email notification to the employee (e.g., for approval/rejection) fails, the core business action (leave status update)    is successfully completed and persisted, and the email failure is logged without blocking the core    transaction.[Expert A / B / D Cross-check (FR05, NFR02)]
* ID: AC-007-   Requirement: Continuous Integration & Deployment (CI/CD)-   Acceptance Criteria: Pushing code to the develop branch automatically triggers the GitHub Actions workflow, which successfully builds both backend and frontend applications, runs all defined tests (unit/integration), and deploys to the staging environment without manual intervention.[Expert C Contribution]
* ID: AC-008-   Requirement: XSS and CSRF Mitigation-   Acceptance Criteria: The system effectively mitigates XSS attacks by utilizing httpOnly cookies for JWTs and performing input sanitization. CSRF attacks are mitigated through the use of SameSite=Lax cookies and proper CORS configuration on the backend.[Expert D Contribution]
* ID: AC-009-   Requirement: Environment Separation-   Acceptance Criteria: The staging and production environments are fully isolated, each utilizing its own dedicated database instance and distinct, securely managed environment configurations.[Expert C Contribution]
* ID: AC-010-   Requirement: Timezone Compliance-   Acceptance Criteria: All date calculations, interpretations, and database storage consistently adhere to the designated "Company Timezone" (EST/UTC-5), and dates are stored using the DATE type in the PostgreSQL database.[Expert A / B / D Cross-check]