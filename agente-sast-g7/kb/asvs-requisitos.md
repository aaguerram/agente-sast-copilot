# Requisitos por defecto — OWASP ASVS 5.0.0 (subconjunto L1/L2)

Total: 192 controles.

> Generado por `agente-sast-g7/scripts/kb_asvs.py`; no editar a mano.
> Fuente: OWASP Application Security Verification Standard 5.0.0,
> https://github.com/OWASP/ASVS — © OWASP Foundation, licencia
> [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Texto original en inglés.

**Uso (paso 5, `analizador-gaps`):** si el proyecto objetivo no trae `REQUISITOS.md`,
cada control de esta lista es un requisito verificable. El ID del gap es el del control
(`requisito: "ASVS-V8.2.2"`) y `requisitos_fuente` apunta a este archivo. Revisa
primero L1 y luego L2; un control que no aplica al proyecto (p. ej. no hay subida de
archivos) se registra en `cumplidos` con `"evidencia": "no aplica: …"`.

## V8 — Autorización (incluye IDOR) (Authorization)

CWE típicos del gap: CWE-862, CWE-863, CWE-639.

### V8.1 Authorization Documentation

- **ASVS-V8.1.1** (L1) Verify that authorization documentation defines rules for restricting function-level and data-specific access based on consumer permissions and resource attributes.
- **ASVS-V8.1.2** (L2) Verify that authorization documentation defines rules for field-level access restrictions (both read and write) based on consumer permissions and resource attributes. Note that these rules might depend on other attribute values of the relevant data object, such as state or status.

### V8.2 General Authorization Design

- **ASVS-V8.2.1** (L1) Verify that the application ensures that function-level access is restricted to consumers with explicit permissions.
- **ASVS-V8.2.2** (L1) Verify that the application ensures that data-specific access is restricted to consumers with explicit permissions to specific data items to mitigate insecure direct object reference (IDOR) and broken object level authorization (BOLA).
- **ASVS-V8.2.3** (L2) Verify that the application ensures that field-level access is restricted to consumers with explicit permissions to specific fields to mitigate broken object property level authorization (BOPLA).

### V8.3 Operation Level Authorization

- **ASVS-V8.3.1** (L1) Verify that the application enforces authorization rules at a trusted service layer and doesn't rely on controls that an untrusted consumer could manipulate, such as client-side JavaScript.

### V8.4 Other Authorization Considerations

- **ASVS-V8.4.1** (L2) Verify that multi-tenant applications use cross-tenant controls to ensure consumer operations will never affect tenants with which they do not have permissions to interact.

## V6 — Autenticación (Authentication)

CWE típicos del gap: CWE-287, CWE-306, CWE-307, CWE-798.

### V6.1 Authentication Documentation

- **ASVS-V6.1.1** (L1) Verify that application documentation defines how controls such as rate limiting, anti-automation, and adaptive response, are used to defend against attacks such as credential stuffing and password brute force. The documentation must make clear how these controls are configured and prevent malicious account lockout.
- **ASVS-V6.1.2** (L2) Verify that a list of context-specific words is documented in order to prevent their use in passwords. The list could include permutations of organization names, product names, system identifiers, project codenames, department or role names, and similar.
- **ASVS-V6.1.3** (L2) Verify that, if the application includes multiple authentication pathways, these are all documented together with the security controls and authentication strength which must be consistently enforced across them.

### V6.2 Password Security

- **ASVS-V6.2.1** (L1) Verify that user set passwords are at least 8 characters in length although a minimum of 15 characters is strongly recommended.
- **ASVS-V6.2.2** (L1) Verify that users can change their password.
- **ASVS-V6.2.3** (L1) Verify that password change functionality requires the user's current and new password.
- **ASVS-V6.2.4** (L1) Verify that passwords submitted during account registration or password change are checked against an available set of, at least, the top 3000 passwords which match the application's password policy, e.g. minimum length.
- **ASVS-V6.2.5** (L1) Verify that passwords of any composition can be used, without rules limiting the type of characters permitted. There must be no requirement for a minimum number of upper or lower case characters, numbers, or special characters.
- **ASVS-V6.2.6** (L1) Verify that password input fields use type=password to mask the entry. Applications may allow the user to temporarily view the entire masked password, or the last typed character of the password.
- **ASVS-V6.2.7** (L1) Verify that "paste" functionality, browser password helpers, and external password managers are permitted.
- **ASVS-V6.2.8** (L1) Verify that the application verifies the user's password exactly as received from the user, without any modifications such as truncation or case transformation.
- **ASVS-V6.2.9** (L2) Verify that passwords of at least 64 characters are permitted.
- **ASVS-V6.2.10** (L2) Verify that a user's password stays valid until it is discovered to be compromised or the user rotates it. The application must not require periodic credential rotation.
- **ASVS-V6.2.11** (L2) Verify that the documented list of context specific words is used to prevent easy to guess passwords being created.
- **ASVS-V6.2.12** (L2) Verify that passwords submitted during account registration or password changes are checked against a set of breached passwords.

### V6.3 General Authentication Security

- **ASVS-V6.3.1** (L1) Verify that controls to prevent attacks such as credential stuffing and password brute force are implemented according to the application's security documentation.
- **ASVS-V6.3.2** (L1) Verify that default user accounts (e.g., "root", "admin", or "sa") are not present in the application or are disabled.
- **ASVS-V6.3.3** (L2) Verify that either a multi-factor authentication mechanism or a combination of single-factor authentication mechanisms, must be used in order to access the application. For L3, one of the factors must be a hardware-based authentication mechanism which provides compromise and impersonation resistance against phishing attacks while verifying the intent to authenticate by requiring a user-initiated action (such as a button press on a FIDO hardware key or a mobile phone). Relaxing any of the considerations in this requirement requires a fully documented rationale and a comprehensive set of mitigating controls.
- **ASVS-V6.3.4** (L2) Verify that, if the application includes multiple authentication pathways, there are no undocumented pathways and that security controls and authentication strength are enforced consistently.

### V6.4 Authentication Factor Lifecycle and Recovery

- **ASVS-V6.4.1** (L1) Verify that system generated initial passwords or activation codes are securely randomly generated, follow the existing password policy, and expire after a short period of time or after they are initially used. These initial secrets must not be permitted to become the long term password.
- **ASVS-V6.4.2** (L1) Verify that password hints or knowledge-based authentication (so-called "secret questions") are not present.
- **ASVS-V6.4.3** (L2) Verify that a secure process for resetting a forgotten password is implemented, that does not bypass any enabled multi-factor authentication mechanisms.
- **ASVS-V6.4.4** (L2) Verify that if a multi-factor authentication factor is lost, evidence of identity proofing is performed at the same level as during enrollment.

### V6.5 General Multi-factor authentication requirements

- **ASVS-V6.5.1** (L2) Verify that lookup secrets, out-of-band authentication requests or codes, and time-based one-time passwords (TOTPs) are only successfully usable once.
- **ASVS-V6.5.2** (L2) Verify that, when being stored in the application's backend, lookup secrets with less than 112 bits of entropy (19 random alphanumeric characters or 34 random digits) are hashed with an approved password storage hashing algorithm that incorporates a 32-bit random salt. A standard hash function can be used if the secret has 112 bits of entropy or more.
- **ASVS-V6.5.3** (L2) Verify that lookup secrets, out-of-band authentication code, and time-based one-time password seeds, are generated using a Cryptographically Secure Pseudorandom Number Generator (CSPRNG) to avoid predictable values.
- **ASVS-V6.5.4** (L2) Verify that lookup secrets and out-of-band authentication codes have a minimum of 20 bits of entropy (typically 4 random alphanumeric characters or 6 random digits is sufficient).
- **ASVS-V6.5.5** (L2) Verify that out-of-band authentication requests, codes, or tokens, as well as time-based one-time passwords (TOTPs) have a defined lifetime. Out of band requests must have a maximum lifetime of 10 minutes and for TOTP a maximum lifetime of 30 seconds.

### V6.6 Out-of-Band authentication mechanisms

- **ASVS-V6.6.1** (L2) Verify that authentication mechanisms using the Public Switched Telephone Network (PSTN) to deliver One-time Passwords (OTPs) via phone or SMS are offered only when the phone number has previously been validated, alternate stronger methods (such as Time based One-time Passwords) are also offered, and the service provides information on their security risks to users. For L3 applications, phone and SMS must not be available as options.
- **ASVS-V6.6.2** (L2) Verify that out-of-band authentication requests, codes, or tokens are bound to the original authentication request for which they were generated and are not usable for a previous or subsequent one.
- **ASVS-V6.6.3** (L2) Verify that a code based out-of-band authentication mechanism is protected against brute force attacks by using rate limiting. Consider also using a code with at least 64 bits of entropy.

### V6.8 Authentication with an Identity Provider

- **ASVS-V6.8.1** (L2) Verify that, if the application supports multiple identity providers (IdPs), the user's identity cannot be spoofed via another supported identity provider (eg. by using the same user identifier). The standard mitigation would be for the application to register and identify the user using a combination of the IdP ID (serving as a namespace) and the user's ID in the IdP.
- **ASVS-V6.8.2** (L2) Verify that the presence and integrity of digital signatures on authentication assertions (for example on JWTs or SAML assertions) are always validated, rejecting any assertions that are unsigned or have invalid signatures.
- **ASVS-V6.8.3** (L2) Verify that SAML assertions are uniquely processed and used only once within the validity period to prevent replay attacks.
- **ASVS-V6.8.4** (L2) Verify that, if an application uses a separate Identity Provider (IdP) and expects specific authentication strength, methods, or recentness for specific functions, the application verifies this using the information returned by the IdP. For example, if OIDC is used, this might be achieved by validating ID Token claims such as 'acr', 'amr', and 'auth_time' (if present). If the IdP does not provide this information, the application must have a documented fallback approach that assumes that the minimum strength authentication mechanism was used (for example, single-factor authentication using username and password).

## V7 — Gestión de sesión (Session Management)

CWE típicos del gap: CWE-384, CWE-614, CWE-1004.

### V7.1 Session Management Documentation

- **ASVS-V7.1.1** (L2) Verify that the user's session inactivity timeout and absolute maximum session lifetime are documented, are appropriate in combination with other controls, and that the documentation includes justification for any deviations from NIST SP 800-63B re-authentication requirements.
- **ASVS-V7.1.2** (L2) Verify that the documentation defines how many concurrent (parallel) sessions are allowed for one account as well as the intended behaviors and actions to be taken when the maximum number of active sessions is reached.
- **ASVS-V7.1.3** (L2) Verify that all systems that create and manage user sessions as part of a federated identity management ecosystem (such as SSO systems) are documented along with controls to coordinate session lifetimes, termination, and any other conditions that require re-authentication.

### V7.2 Fundamental Session Management Security

- **ASVS-V7.2.1** (L1) Verify that the application performs all session token verification using a trusted, backend service.
- **ASVS-V7.2.2** (L1) Verify that the application uses either self-contained or reference tokens that are dynamically generated for session management, i.e. not using static API secrets and keys.
- **ASVS-V7.2.3** (L1) Verify that if reference tokens are used to represent user sessions, they are unique and generated using a cryptographically secure pseudo-random number generator (CSPRNG) and possess at least 128 bits of entropy.
- **ASVS-V7.2.4** (L1) Verify that the application generates a new session token on user authentication, including re-authentication, and terminates the current session token.

### V7.3 Session Timeout

- **ASVS-V7.3.1** (L2) Verify that there is an inactivity timeout such that re-authentication is enforced according to risk analysis and documented security decisions.
- **ASVS-V7.3.2** (L2) Verify that there is an absolute maximum session lifetime such that re-authentication is enforced according to risk analysis and documented security decisions.

### V7.4 Session Termination

- **ASVS-V7.4.1** (L1) Verify that when session termination is triggered (such as logout or expiration), the application disallows any further use of the session. For reference tokens or stateful sessions, this means invalidating the session data at the application backend. Applications using self-contained tokens will need a solution such as maintaining a list of terminated tokens, disallowing tokens produced before a per-user date and time or rotating a per-user signing key.
- **ASVS-V7.4.2** (L1) Verify that the application terminates all active sessions when a user account is disabled or deleted (such as an employee leaving the company).
- **ASVS-V7.4.3** (L2) Verify that the application gives the option to terminate all other active sessions after a successful change or removal of any authentication factor (including password change via reset or recovery and, if present, an MFA settings update).
- **ASVS-V7.4.4** (L2) Verify that all pages that require authentication have easy and visible access to logout functionality.
- **ASVS-V7.4.5** (L2) Verify that application administrators are able to terminate active sessions for an individual user or for all users.

### V7.5 Defenses Against Session Abuse

- **ASVS-V7.5.1** (L2) Verify that the application requires full re-authentication before allowing modifications to sensitive account attributes which may affect authentication such as email address, phone number, MFA configuration, or other information used in account recovery.
- **ASVS-V7.5.2** (L2) Verify that users are able to view and (having authenticated again with at least one factor) terminate any or all currently active sessions.

### V7.6 Federated Re-authentication

- **ASVS-V7.6.1** (L2) Verify that session lifetime and termination between Relying Parties (RPs) and Identity Providers (IdPs) behave as documented, requiring re-authentication as necessary such as when the maximum time between IdP authentication events is reached.
- **ASVS-V7.6.2** (L2) Verify that creation of a session requires either the user's consent or an explicit action, preventing the creation of new application sessions without user interaction.

## V9 — Tokens autocontenidos (JWT) (Self-contained Tokens)

CWE típicos del gap: CWE-347, CWE-345.

### V9.1 Token source and integrity

- **ASVS-V9.1.1** (L1) Verify that self-contained tokens are validated using their digital signature or MAC to protect against tampering before accepting the token's contents.
- **ASVS-V9.1.2** (L1) Verify that only algorithms on an allowlist can be used to create and verify self-contained tokens, for a given context. The allowlist must include the permitted algorithms, ideally only either symmetric or asymmetric algorithms, and must not include the 'None' algorithm. If both symmetric and asymmetric must be supported, additional controls will be needed to prevent key confusion.
- **ASVS-V9.1.3** (L1) Verify that key material that is used to validate self-contained tokens is from trusted pre-configured sources for the token issuer, preventing attackers from specifying untrusted sources and keys. For JWTs and other JWS structures, headers such as 'jku', 'x5u', and 'jwk' must be validated against an allowlist of trusted sources.

### V9.2 Token content

- **ASVS-V9.2.1** (L1) Verify that, if a validity time span is present in the token data, the token and its content are accepted only if the verification time is within this validity time span. For example, for JWTs, the claims 'nbf' and 'exp' must be verified.
- **ASVS-V9.2.2** (L2) Verify that the service receiving a token validates the token to be the correct type and is meant for the intended purpose before accepting the token's contents. For example, only access tokens can be accepted for authorization decisions and only ID Tokens can be used for proving user authentication.
- **ASVS-V9.2.3** (L2) Verify that the service only accepts tokens which are intended for use with that service (audience). For JWTs, this can be achieved by validating the 'aud' claim against an allowlist defined in the service.
- **ASVS-V9.2.4** (L2) Verify that, if a token issuer uses the same private key for issuing tokens to different audiences, the issued tokens contain an audience restriction that uniquely identifies the intended audiences. This will prevent a token from being reused with an unintended audience. If the audience identifier is dynamically provisioned, the token issuer must validate these audiences in order to make sure that they do not result in audience impersonation.

## V2 — Validación y lógica de negocio (Validation and Business Logic)

CWE típicos del gap: CWE-20, CWE-840, CWE-841.

### V2.1 Validation and Business Logic Documentation

- **ASVS-V2.1.1** (L1) Verify that the application's documentation defines input validation rules for how to check the validity of data items against an expected structure. This could be common data formats such as credit card numbers, email addresses, telephone numbers, or it could be an internal data format.
- **ASVS-V2.1.2** (L2) Verify that the application's documentation defines how to validate the logical and contextual consistency of combined data items, such as checking that suburb and ZIP code match.
- **ASVS-V2.1.3** (L2) Verify that expectations for business logic limits and validations are documented, including both per-user and globally across the application.

### V2.2 Input Validation

- **ASVS-V2.2.1** (L1) Verify that input is validated to enforce business or functional expectations for that input. This should either use positive validation against an allow list of values, patterns, and ranges, or be based on comparing the input to an expected structure and logical limits according to predefined rules. For L1, this can focus on input which is used to make specific business or security decisions. For L2 and up, this should apply to all input.
- **ASVS-V2.2.2** (L1) Verify that the application is designed to enforce input validation at a trusted service layer. While client-side validation improves usability and should be encouraged, it must not be relied upon as a security control.
- **ASVS-V2.2.3** (L2) Verify that the application ensures that combinations of related data items are reasonable according to the pre-defined rules.

### V2.3 Business Logic Security

- **ASVS-V2.3.1** (L1) Verify that the application will only process business logic flows for the same user in the expected sequential step order and without skipping steps.
- **ASVS-V2.3.2** (L2) Verify that business logic limits are implemented per the application's documentation to avoid business logic flaws being exploited.
- **ASVS-V2.3.3** (L2) Verify that transactions are being used at the business logic level such that either a business logic operation succeeds in its entirety or it is rolled back to the previous correct state.
- **ASVS-V2.3.4** (L2) Verify that business logic level locking mechanisms are used to ensure that limited quantity resources (such as theater seats or delivery slots) cannot be double-booked by manipulating the application's logic.

### V2.4 Anti-automation

- **ASVS-V2.4.1** (L2) Verify that anti-automation controls are in place to protect against excessive calls to application functions that could lead to data exfiltration, garbage-data creation, quota exhaustion, rate-limit breaches, denial-of-service, or overuse of costly resources.

## V1 — Codificación y saneamiento (inyección) (Encoding and Sanitization)

CWE típicos del gap: CWE-89, CWE-78, CWE-79, CWE-74.

### V1.1 Encoding and Sanitization Architecture

- **ASVS-V1.1.1** (L2) Verify that input is decoded or unescaped into a canonical form only once, it is only decoded when encoded data in that form is expected, and that this is done before processing the input further, for example it is not performed after input validation or sanitization.
- **ASVS-V1.1.2** (L2) Verify that the application performs output encoding and escaping either as a final step before being used by the interpreter for which it is intended or by the interpreter itself.

### V1.2 Injection Prevention

- **ASVS-V1.2.1** (L1) Verify that output encoding for an HTTP response, HTML document, or XML document is relevant for the context required, such as encoding the relevant characters for HTML elements, HTML attributes, HTML comments, CSS, or HTTP header fields, to avoid changing the message or document structure.
- **ASVS-V1.2.2** (L1) Verify that when dynamically building URLs, untrusted data is encoded according to its context (e.g., URL encoding or base64url encoding for query or path parameters). Ensure that only safe URL protocols are permitted (e.g., disallow javascript: or data:).
- **ASVS-V1.2.3** (L1) Verify that output encoding or escaping is used when dynamically building JavaScript content (including JSON), to avoid changing the message or document structure (to avoid JavaScript and JSON injection).
- **ASVS-V1.2.4** (L1) Verify that data selection or database queries (e.g., SQL, HQL, NoSQL, Cypher) use parameterized queries, ORMs, entity frameworks, or are otherwise protected from SQL Injection and other database injection attacks. This is also relevant when writing stored procedures.
- **ASVS-V1.2.5** (L1) Verify that the application protects against OS command injection and that operating system calls use parameterized OS queries or use contextual command line output encoding.
- **ASVS-V1.2.6** (L2) Verify that the application protects against LDAP injection vulnerabilities, or that specific security controls to prevent LDAP injection have been implemented.
- **ASVS-V1.2.7** (L2) Verify that the application is protected against XPath injection attacks by using query parameterization or precompiled queries.
- **ASVS-V1.2.8** (L2) Verify that LaTeX processors are configured securely (such as not using the "--shell-escape" flag) and an allowlist of commands is used to prevent LaTeX injection attacks.
- **ASVS-V1.2.9** (L2) Verify that the application escapes special characters in regular expressions (typically using a backslash) to prevent them from being misinterpreted as metacharacters.

### V1.3 Sanitization

- **ASVS-V1.3.1** (L1) Verify that all untrusted HTML input from WYSIWYG editors or similar is sanitized using a well-known and secure HTML sanitization library or framework feature.
- **ASVS-V1.3.2** (L1) Verify that the application avoids the use of eval() or other dynamic code execution features such as Spring Expression Language (SpEL). Where there is no alternative, any user input being included must be sanitized before being executed.
- **ASVS-V1.3.3** (L2) Verify that data being passed to a potentially dangerous context is sanitized beforehand to enforce safety measures, such as only allowing characters which are safe for this context and trimming input which is too long.
- **ASVS-V1.3.4** (L2) Verify that user-supplied Scalable Vector Graphics (SVG) scriptable content is validated or sanitized to contain only tags and attributes (such as draw graphics) that are safe for the application, e.g., do not contain scripts and foreignObject.
- **ASVS-V1.3.5** (L2) Verify that the application sanitizes or disables user-supplied scriptable or expression template language content, such as Markdown, CSS or XSL stylesheets, BBCode, or similar.
- **ASVS-V1.3.6** (L2) Verify that the application protects against Server-side Request Forgery (SSRF) attacks, by validating untrusted data against an allowlist of protocols, domains, paths and ports and sanitizing potentially dangerous characters before using the data to call another service.
- **ASVS-V1.3.7** (L2) Verify that the application protects against template injection attacks by not allowing templates to be built based on untrusted input. Where there is no alternative, any untrusted input being included dynamically during template creation must be sanitized or strictly validated.
- **ASVS-V1.3.8** (L2) Verify that the application appropriately sanitizes untrusted input before use in Java Naming and Directory Interface (JNDI) queries and that JNDI is configured securely to prevent JNDI injection attacks.
- **ASVS-V1.3.9** (L2) Verify that the application sanitizes content before it is sent to memcache to prevent injection attacks.
- **ASVS-V1.3.10** (L2) Verify that format strings which might resolve in an unexpected or malicious way when used are sanitized before being processed.
- **ASVS-V1.3.11** (L2) Verify that the application sanitizes user input before passing to mail systems to protect against SMTP or IMAP injection.

### V1.4 Memory, String, and Unmanaged Code

- **ASVS-V1.4.1** (L2) Verify that the application uses memory-safe string, safer memory copy and pointer arithmetic to detect or prevent stack, buffer, or heap overflows.
- **ASVS-V1.4.2** (L2) Verify that sign, range, and input validation techniques are used to prevent integer overflows.
- **ASVS-V1.4.3** (L2) Verify that dynamically allocated memory and resources are released, and that references or pointers to freed memory are removed or set to null to prevent dangling pointers and use-after-free vulnerabilities.

### V1.5 Safe Deserialization

- **ASVS-V1.5.1** (L1) Verify that the application configures XML parsers to use a restrictive configuration and that unsafe features such as resolving external entities are disabled to prevent XML eXternal Entity (XXE) attacks.
- **ASVS-V1.5.2** (L2) Verify that deserialization of untrusted data enforces safe input handling, such as using an allowlist of object types or restricting client-defined object types, to prevent deserialization attacks. Deserialization mechanisms that are explicitly defined as insecure must not be used with untrusted input.

## V4 — API y servicios web (API and Web Service)

CWE típicos del gap: CWE-16, CWE-942.

### V4.1 Generic Web Service Security

- **ASVS-V4.1.1** (L1) Verify that every HTTP response with a message body contains a Content-Type header field that matches the actual content of the response, including the charset parameter to specify safe character encoding (e.g., UTF-8, ISO-8859-1) according to IANA Media Types, such as "text/", "/+xml" and "/xml".
- **ASVS-V4.1.2** (L2) Verify that only user-facing endpoints (intended for manual web-browser access) automatically redirect from HTTP to HTTPS, while other services or endpoints do not implement transparent redirects. This is to avoid a situation where a client is erroneously sending unencrypted HTTP requests, but since the requests are being automatically redirected to HTTPS, the leakage of sensitive data goes undiscovered.
- **ASVS-V4.1.3** (L2) Verify that any HTTP header field used by the application and set by an intermediary layer, such as a load balancer, a web proxy, or a backend-for-frontend service, cannot be overridden by the end-user. Example headers might include X-Real-IP, X-Forwarded-*, or X-User-ID.

### V4.2 HTTP Message Structure Validation

- **ASVS-V4.2.1** (L2) Verify that all application components (including load balancers, firewalls, and application servers) determine boundaries of incoming HTTP messages using the appropriate mechanism for the HTTP version to prevent HTTP request smuggling. In HTTP/1.x, if a Transfer-Encoding header field is present, the Content-Length header must be ignored per RFC 2616. When using HTTP/2 or HTTP/3, if a Content-Length header field is present, the receiver must ensure that it is consistent with the length of the DATA frames.

### V4.3 GraphQL

- **ASVS-V4.3.1** (L2) Verify that a query allowlist, depth limiting, amount limiting, or query cost analysis is used to prevent GraphQL or data layer expression Denial of Service (DoS) as a result of expensive, nested queries.
- **ASVS-V4.3.2** (L2) Verify that GraphQL introspection queries are disabled in the production environment unless the GraphQL API is meant to be used by other parties.

### V4.4 WebSocket

- **ASVS-V4.4.1** (L1) Verify that WebSocket over TLS (WSS) is used for all WebSocket connections.
- **ASVS-V4.4.2** (L2) Verify that, during the initial HTTP WebSocket handshake, the Origin header field is checked against a list of origins allowed for the application.
- **ASVS-V4.4.3** (L2) Verify that, if the application's standard session management cannot be used, dedicated tokens are being used for this, which comply with the relevant Session Management security requirements.
- **ASVS-V4.4.4** (L2) Verify that dedicated WebSocket session management tokens are initially obtained or validated through the previously authenticated HTTPS session when transitioning an existing HTTPS session to a WebSocket channel.

## V5 — Manejo de archivos (File Handling)

CWE típicos del gap: CWE-22, CWE-434.

### V5.1 File Handling Documentation

- **ASVS-V5.1.1** (L2) Verify that the documentation defines the permitted file types, expected file extensions, and maximum size (including unpacked size) for each upload feature. Additionally, ensure that the documentation specifies how files are made safe for end-users to download and process, such as how the application behaves when a malicious file is detected.

### V5.2 File Upload and Content

- **ASVS-V5.2.1** (L1) Verify that the application will only accept files of a size which it can process without causing a loss of performance or a denial of service attack.
- **ASVS-V5.2.2** (L1) Verify that when the application accepts a file, either on its own or within an archive such as a zip file, it checks if the file extension matches an expected file extension and validates that the contents correspond to the type represented by the extension. This includes, but is not limited to, checking the initial 'magic bytes', performing image re-writing, and using specialized libraries for file content validation. For L1, this can focus just on files which are used to make specific business or security decisions. For L2 and up, this must apply to all files being accepted.
- **ASVS-V5.2.3** (L2) Verify that the application checks compressed files (e.g., zip, gz, docx, odt) against maximum allowed uncompressed size and against maximum number of files before uncompressing the file.

### V5.3 File Storage

- **ASVS-V5.3.1** (L1) Verify that files uploaded or generated by untrusted input and stored in a public folder, are not executed as server-side program code when accessed directly with an HTTP request.
- **ASVS-V5.3.2** (L1) Verify that when the application creates file paths for file operations, instead of user-submitted filenames, it uses internally generated or trusted data, or if user-submitted filenames or file metadata must be used, strict validation and sanitization must be applied. This is to protect against path traversal, local or remote file inclusion (LFI, RFI), and server-side request forgery (SSRF) attacks.

### V5.4 File Download

- **ASVS-V5.4.1** (L2) Verify that the application validates or ignores user-submitted filenames, including in a JSON, JSONP, or URL parameter and specifies a filename in the Content-Disposition header field in the response.
- **ASVS-V5.4.2** (L2) Verify that file names served (e.g., in HTTP response header fields or email attachments) are encoded or sanitized (e.g., following RFC 6266) to preserve document structure and prevent injection attacks.
- **ASVS-V5.4.3** (L2) Verify that files obtained from untrusted sources are scanned by antivirus scanners to prevent serving of known malicious content.

## V15 — Código y arquitectura seguros (Secure Coding and Architecture)

CWE típicos del gap: CWE-502, CWE-915, CWE-1104.

### V15.1 Secure Coding and Architecture Documentation

- **ASVS-V15.1.1** (L1) Verify that application documentation defines risk based remediation time frames for 3rd party component versions with vulnerabilities and for updating libraries in general, to minimize the risk from these components.
- **ASVS-V15.1.2** (L2) Verify that an inventory catalog, such as software bill of materials (SBOM), is maintained of all third-party libraries in use, including verifying that components come from pre-defined, trusted, and continually maintained repositories.
- **ASVS-V15.1.3** (L2) Verify that the application documentation identifies functionality which is time-consuming or resource-demanding. This must include how to prevent a loss of availability due to overusing this functionality and how to avoid a situation where building a response takes longer than the consumer's timeout. Potential defenses may include asynchronous processing, using queues, and limiting parallel processes per user and per application.

### V15.2 Security Architecture and Dependencies

- **ASVS-V15.2.1** (L1) Verify that the application only contains components which have not breached the documented update and remediation time frames.
- **ASVS-V15.2.2** (L2) Verify that the application has implemented defenses against loss of availability due to functionality which is time-consuming or resource-demanding, based on the documented security decisions and strategies for this.
- **ASVS-V15.2.3** (L2) Verify that the production environment only includes functionality that is required for the application to function, and does not expose extraneous functionality such as test code, sample snippets, and development functionality.

### V15.3 Defensive Coding

- **ASVS-V15.3.1** (L1) Verify that the application only returns the required subset of fields from a data object. For example, it should not return an entire data object, as some individual fields should not be accessible to users.
- **ASVS-V15.3.2** (L2) Verify that where the application backend makes calls to external URLs, it is configured to not follow redirects unless it is intended functionality.
- **ASVS-V15.3.3** (L2) Verify that the application has countermeasures to protect against mass assignment attacks by limiting allowed fields per controller and action, e.g., it is not possible to insert or update a field value when it was not intended to be part of that action.
- **ASVS-V15.3.4** (L2) Verify that all proxying and middleware components transfer the user's original IP address correctly using trusted data fields that cannot be manipulated by the end user, and the application and web server use this correct value for logging and security decisions such as rate limiting, taking into account that even the original IP address may not be reliable due to dynamic IPs, VPNs, or corporate firewalls.
- **ASVS-V15.3.5** (L2) Verify that the application explicitly ensures that variables are of the correct type and performs strict equality and comparator operations. This is to avoid type juggling or type confusion vulnerabilities caused by the application code making an assumption about a variable type.
- **ASVS-V15.3.6** (L2) Verify that JavaScript code is written in a way that prevents prototype pollution, for example, by using Set() or Map() instead of object literals.
- **ASVS-V15.3.7** (L2) Verify that the application has defenses against HTTP parameter pollution attacks, particularly if the application framework makes no distinction about the source of request parameters (query string, body parameters, cookies, or header fields).

## V11 — Criptografía (Cryptography)

CWE típicos del gap: CWE-327, CWE-328, CWE-330.

### V11.1 Cryptographic Inventory and Documentation

- **ASVS-V11.1.1** (L2) Verify that there is a documented policy for management of cryptographic keys and a cryptographic key lifecycle that follows a key management standard such as NIST SP 800-57. This should include ensuring that keys are not overshared (for example, with more than two entities for shared secrets and more than one entity for private keys).
- **ASVS-V11.1.2** (L2) Verify that a cryptographic inventory is performed, maintained, regularly updated, and includes all cryptographic keys, algorithms, and certificates used by the application. It must also document where keys can and cannot be used in the system, and the types of data that can and cannot be protected using the keys.

### V11.2 Secure Cryptography Implementation

- **ASVS-V11.2.1** (L2) Verify that industry-validated implementations (including libraries and hardware-accelerated implementations) are used for cryptographic operations.
- **ASVS-V11.2.2** (L2) Verify that the application is designed with crypto agility such that random number, authenticated encryption, MAC, or hashing algorithms, key lengths, rounds, ciphers and modes can be reconfigured, upgraded, or swapped at any time, to protect against cryptographic breaks. Similarly, it must also be possible to replace keys and passwords and re-encrypt data. This will allow for seamless upgrades to post-quantum cryptography (PQC), once high-assurance implementations of approved PQC schemes or standards are widely available.
- **ASVS-V11.2.3** (L2) Verify that all cryptographic primitives utilize a minimum of 128-bits of security based on the algorithm, key size, and configuration. For example, a 256-bit ECC key provides roughly 128 bits of security where RSA requires a 3072-bit key to achieve 128 bits of security.

### V11.3 Encryption Algorithms

- **ASVS-V11.3.1** (L1) Verify that insecure block modes (e.g., ECB) and weak padding schemes (e.g., PKCS#1 v1.5) are not used.
- **ASVS-V11.3.2** (L1) Verify that only approved ciphers and modes such as AES with GCM are used.
- **ASVS-V11.3.3** (L2) Verify that encrypted data is protected against unauthorized modification preferably by using an approved authenticated encryption method or by combining an approved encryption method with an approved MAC algorithm.

### V11.4 Hashing and Hash-based Functions

- **ASVS-V11.4.1** (L1) Verify that only approved hash functions are used for general cryptographic use cases, including digital signatures, HMAC, KDF, and random bit generation. Disallowed hash functions, such as MD5, must not be used for any cryptographic purpose.
- **ASVS-V11.4.2** (L2) Verify that passwords are stored using an approved, computationally intensive, key derivation function (also known as a "password hashing function"), with parameter settings configured based on current guidance. The settings should balance security and performance to make brute-force attacks sufficiently challenging for the required level of security.
- **ASVS-V11.4.3** (L2) Verify that hash functions used in digital signatures, as part of data authentication or data integrity are collision resistant and have appropriate bit-lengths. If collision resistance is required, the output length must be at least 256 bits. If only resistance to second pre-image attacks is required, the output length must be at least 128 bits.
- **ASVS-V11.4.4** (L2) Verify that the application uses approved key derivation functions with key stretching parameters when deriving secret keys from passwords. The parameters in use must balance security and performance to prevent brute-force attacks from compromising the resulting cryptographic key.

### V11.5 Random Values

- **ASVS-V11.5.1** (L2) Verify that all random numbers and strings which are intended to be non-guessable must be generated using a cryptographically secure pseudo-random number generator (CSPRNG) and have at least 128 bits of entropy. Note that UUIDs do not respect this condition.

### V11.6 Public Key Cryptography

- **ASVS-V11.6.1** (L2) Verify that only approved cryptographic algorithms and modes of operation are used for key generation and seeding, and digital signature generation and verification. Key generation algorithms must not generate insecure keys vulnerable to known attacks, for example, RSA keys which are vulnerable to Fermat factorization.

## V12 — Comunicación segura (Secure Communication)

CWE típicos del gap: CWE-319, CWE-295.

### V12.1 General TLS Security Guidance

- **ASVS-V12.1.1** (L1) Verify that only the latest recommended versions of the TLS protocol are enabled, such as TLS 1.2 and TLS 1.3. The latest version of the TLS protocol must be the preferred option.

### V12.2 HTTPS Communication with External Facing Services

- **ASVS-V12.2.1** (L1) Verify that TLS is used for all connectivity between a client and external facing, HTTP-based services, and does not fall back to insecure or unencrypted communications.
- **ASVS-V12.2.2** (L1) Verify that external facing services use publicly trusted TLS certificates.

## V13 — Configuración (Configuration)

CWE típicos del gap: CWE-16, CWE-798, CWE-209.

### V13.1 Configuration Documentation

- **ASVS-V13.1.1** (L2) Verify that all communication needs for the application are documented. This must include external services which the application relies upon and cases where an end user might be able to provide an external location to which the application will then connect.

### V13.2 Backend Communication Configuration

- **ASVS-V13.2.1** (L2) Verify that communications between backend application components that don't support the application's standard user session mechanism, including APIs, middleware, and data layers, are authenticated. Authentication must use individual service accounts, short-term tokens, or certificate-based authentication and not unchanging credentials such as passwords, API keys, or shared accounts with privileged access.
- **ASVS-V13.2.2** (L2) Verify that communications between backend application components, including local or operating system services, APIs, middleware, and data layers, are performed with accounts assigned the least necessary privileges.
- **ASVS-V13.2.3** (L2) Verify that if a credential has to be used for service authentication, the credential being used by the consumer is not a default credential (e.g., root/root or admin/admin).
- **ASVS-V13.2.4** (L2) Verify that an allowlist is used to define the external resources or systems with which the application is permitted to communicate (e.g., for outbound requests, data loads, or file access). This allowlist can be implemented at the application layer, web server, firewall, or a combination of different layers.
- **ASVS-V13.2.5** (L2) Verify that the web or application server is configured with an allowlist of resources or systems to which the server can send requests or load data or files from.

### V13.3 Secret Management

- **ASVS-V13.3.1** (L2) Verify that a secrets management solution, such as a key vault, is used to securely create, store, control access to, and destroy backend secrets. These could include passwords, key material, integrations with databases and third-party systems, keys and seeds for time-based tokens, other internal secrets, and API keys. Secrets must not be included in application source code or included in build artifacts. For an L3 application, this must involve a hardware-backed solution such as an HSM.
- **ASVS-V13.3.2** (L2) Verify that access to secret assets adheres to the principle of least privilege.

### V13.4 Unintended Information Leakage

- **ASVS-V13.4.1** (L1) Verify that the application is deployed either without any source control metadata, including the .git or .svn folders, or in a way that these folders are inaccessible both externally and to the application itself.
- **ASVS-V13.4.2** (L2) Verify that debug modes are disabled for all components in production environments to prevent exposure of debugging features and information leakage.
- **ASVS-V13.4.3** (L2) Verify that web servers do not expose directory listings to clients unless explicitly intended.
- **ASVS-V13.4.4** (L2) Verify that using the HTTP TRACE method is not supported in production environments, to avoid potential information leakage.
- **ASVS-V13.4.5** (L2) Verify that documentation (such as for internal APIs) and monitoring endpoints are not exposed unless explicitly intended.

## V14 — Protección de datos (Data Protection)

CWE típicos del gap: CWE-200, CWE-312, CWE-532.

### V14.1 Data Protection Documentation

- **ASVS-V14.1.1** (L2) Verify that all sensitive data created and processed by the application has been identified and classified into protection levels. This includes data that is only encoded and therefore easily decoded, such as Base64 strings or the plaintext payload inside a JWT. Protection levels need to take into account any data protection and privacy regulations and standards which the application is required to comply with.
- **ASVS-V14.1.2** (L2) Verify that all sensitive data protection levels have a documented set of protection requirements. This must include (but not be limited to) requirements related to general encryption, integrity verification, retention, how the data is to be logged, access controls around sensitive data in logs, database-level encryption, privacy and privacy-enhancing technologies to be used, and other confidentiality requirements.

### V14.2 General Data Protection

- **ASVS-V14.2.1** (L1) Verify that sensitive data is only sent to the server in the HTTP message body or header fields, and that the URL and query string do not contain sensitive information, such as an API key or session token.
- **ASVS-V14.2.2** (L2) Verify that the application prevents sensitive data from being cached in server components, such as load balancers and application caches, or ensures that the data is securely purged after use.
- **ASVS-V14.2.3** (L2) Verify that defined sensitive data is not sent to untrusted parties (e.g., user trackers) to prevent unwanted collection of data outside of the application's control.
- **ASVS-V14.2.4** (L2) Verify that controls around sensitive data related to encryption, integrity verification, retention, how the data is to be logged, access controls around sensitive data in logs, privacy and privacy-enhancing technologies, are implemented as defined in the documentation for the specific data's protection level.

### V14.3 Client-side Data Protection

- **ASVS-V14.3.1** (L1) Verify that authenticated data is cleared from client storage, such as the browser DOM, after the client or session is terminated. The 'Clear-Site-Data' HTTP response header field may be able to help with this but the client-side should also be able to clear up if the server connection is not available when the session is terminated.
- **ASVS-V14.3.2** (L2) Verify that the application sets sufficient anti-caching HTTP response header fields (i.e., Cache-Control: no-store) so that sensitive data is not cached in browsers.
- **ASVS-V14.3.3** (L2) Verify that data stored in browser storage (such as localStorage, sessionStorage, IndexedDB, or cookies) does not contain sensitive data, with the exception of session tokens.

## V16 — Registro de seguridad y manejo de errores (Security Logging and Error Handling)

CWE típicos del gap: CWE-778, CWE-117, CWE-209.

### V16.1 Security Logging Documentation

- **ASVS-V16.1.1** (L2) Verify that an inventory exists documenting the logging performed at each layer of the application's technology stack, what events are being logged, log formats, where that logging is stored, how it is used, how access to it is controlled, and for how long logs are kept.

### V16.2 General Logging

- **ASVS-V16.2.1** (L2) Verify that each log entry includes necessary metadata (such as when, where, who, what) that would allow for a detailed investigation of the timeline when an event happens.
- **ASVS-V16.2.2** (L2) Verify that time sources for all logging components are synchronized, and that timestamps in security event metadata use UTC or include an explicit time zone offset. UTC is recommended to ensure consistency across distributed systems and to prevent confusion during daylight saving time transitions.
- **ASVS-V16.2.3** (L2) Verify that the application only stores or broadcasts logs to the files and services that are documented in the log inventory.
- **ASVS-V16.2.4** (L2) Verify that logs can be read and correlated by the log processor that is in use, preferably by using a common logging format.
- **ASVS-V16.2.5** (L2) Verify that when logging sensitive data, the application enforces logging based on the data's protection level. For example, it may not be allowed to log certain data, such as credentials or payment details. Other data, such as session tokens, may only be logged by being hashed or masked, either in full or partially.

### V16.3 Security Events

- **ASVS-V16.3.1** (L2) Verify that all authentication operations are logged, including successful and unsuccessful attempts. Additional metadata, such as the type of authentication or factors used, should also be collected.
- **ASVS-V16.3.2** (L2) Verify that failed authorization attempts are logged. For L3, this must include logging all authorization decisions, including logging when sensitive data is accessed (without logging the sensitive data itself).
- **ASVS-V16.3.3** (L2) Verify that the application logs the security events that are defined in the documentation and also logs attempts to bypass the security controls, such as input validation, business logic, and anti-automation.
- **ASVS-V16.3.4** (L2) Verify that the application logs unexpected errors and security control failures such as backend TLS failures.

### V16.4 Log Protection

- **ASVS-V16.4.1** (L2) Verify that all logging components appropriately encode data to prevent log injection.
- **ASVS-V16.4.2** (L2) Verify that logs are protected from unauthorized access and cannot be modified.
- **ASVS-V16.4.3** (L2) Verify that logs are securely transmitted to a logically separate system for analysis, detection, alerting, and escalation. The aim is to ensure that if the application is breached, the logs are not compromised.

### V16.5 Error Handling

- **ASVS-V16.5.1** (L2) Verify that a generic message is returned to the consumer when an unexpected or security-sensitive error occurs, ensuring no exposure of sensitive internal system data such as stack traces, queries, secret keys, and tokens.
- **ASVS-V16.5.2** (L2) Verify that the application continues to operate securely when external resource access fails, for example, by using patterns such as circuit breakers or graceful degradation.
- **ASVS-V16.5.3** (L2) Verify that the application fails gracefully and securely, including when an exception occurs, preventing fail-open conditions such as processing a transaction despite errors resulting from validation logic.
