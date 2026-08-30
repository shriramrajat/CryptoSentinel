# CryptoSentinel Frontend Development Guide

## 1. Purpose

This document defines the rules for frontend development and collaboration for the CryptoSentinel project.

The backend API contract is explicitly **frozen**. Frontend developers must consume the contract exactly as it is rather than modify backend behavior to suit the frontend. If the frontend contract is insufficient, it must be discussed and resolved collaboratively before changing backend logic.

---

## 2. Technology Stack

The frontend is built using the following core technologies:

- **React 18**
- **TypeScript 5**
- **Vite 6**
- **React Router**
- **TanStack React Query**
- **Tailwind CSS v4**

Do not introduce large new frameworks or state management libraries without team consensus.

---

## 3. Project Structure

The current structure of the frontend application is:

```
frontend/
├── src/
│   ├── api/          # API client and backend communication
│   ├── components/   # Reusable UI components
│   ├── hooks/        # Reusable React hooks
│   ├── layouts/      # Application layouts
│   ├── lib/          # Pure utility functions
│   ├── pages/        # Page-level screens
│   ├── routes/       # Route definitions
│   └── types/        # Shared TypeScript types
```

**Rules:**
- All API communication goes in `src/api/`.
- Reusable UI elements go in `src/components/`.
- Page-level screens belong in `src/pages/`.
- Shared, custom React logic goes in `src/hooks/`.
- Application-wide layouts go in `src/layouts/`.
- Routing definitions go in `src/routes/`.
- Shared TypeScript interfaces and types go in `src/types/`.
- Pure functions without side effects go in `src/lib/`.
- **Do not** allow business logic to be scattered randomly across components.

---

## 4. API Usage Rules

**NEVER write raw `fetch()` calls directly inside UI components.**

All API communication must go through `src/api/`. You must reuse the existing API client foundation.

The backend exposes the following endpoints:
- `GET /health`
- `GET /version`
- `POST /api/v1/scan`

**Role of API Utilities:**
- **`fetchClient`**: Use this utility to make network requests. It automatically handles the base URL and standardizes error parsing.
- **`ApiError`**: The standardized error class thrown by the client. Contains `status`, `code`, and `message`.
- **Typed Models**: Request and response interfaces are defined in `src/types/api.ts`. Use them strictly.
- **TanStack Query**: Use React Query for all server state (data fetching, caching, loading states).

**Do not duplicate API types manually inside components.** Always import them from `src/types/api.ts`.

---

## 5. Backend Contract Is Frozen

**Frontend developers must NOT:**
- Modify scanner logic.
- Modify risk classification rules.
- Change API response JSON structures.
- Rename API fields in the backend.
- Silently introduce fallback API formats if the backend changes.
- Modify backend error semantics.

If you discover a problem or gap in the backend contract:
**DO NOT silently change the frontend to compensate.** Document the issue and raise it with the backend team before modifying the contract.

---

## 6. Component Rules

- Components should have one clear responsibility.
- Avoid huge components (break them down).
- Prefer composition over deeply nested conditional logic.
- Shared components belong in `src/components/`.
- Page-specific sub-components may live near their respective page if appropriate.
- **Do not duplicate identical UI patterns** across pages; extract them.
- Component props must have explicit TypeScript types.
- Avoid using `any`.

---

## 7. State Management

State must be explicitly categorized and managed using the following rules:

### Server State
Use **TanStack Query**.
*Examples: Scan results, health status, version information.*

### Local UI State
Use **React State** (`useState`, `useReducer`).
*Examples: Selected filter, modal visibility, expanded finding, form input.*

### URL State
Use **React Router / Search Parameters** where appropriate.
*Examples: Active tabs, search queries, pagination.*

**Do NOT introduce Redux, Zustand, or any other global state library unless explicitly approved.**

---

## 8. Loading / Error / Empty States

Every API-driven screen **must** account for:
1. Loading state
2. Success state
3. Empty state (e.g., zero discoveries)
4. API error state
5. Unexpected runtime error state

**Do not build only the happy path.**

Backend error responses must be rendered safely using the API error contract. **Never display stack traces, internal paths, or backend internals to the user.** Render the `message` string safely.

---

## 9. Security Rules

The frontend must **never**:
- Expose secrets.
- Hardcode API keys.
- Commit `.env` files.
- Expose backend internal paths unnecessarily.
- Render unsanitized arbitrary HTML (beware of `dangerouslySetInnerHTML`).
- Log sensitive scan information to the browser console unnecessarily.

*Note: Scanned secrets are redacted by the backend. Do not create frontend code that attempts to bypass or reconstruct that protection.*

---

## 10. Styling Rules

Use **Tailwind CSS v4** for all styling.
**Avoid introducing another styling system** (like styled-components or CSS modules).

Conventions:
- Maintain consistent spacing and typography via Tailwind utility classes.
- Ensure the UI is responsive.
- Extract highly reusable UI patterns into separate components rather than repeating giant inline class strings everywhere.

---

## 11. Routing Rules

Future pages should be registered through the routing layer (`src/App.tsx` or `src/routes/`).
Do not create ad-hoc navigation or scatter route definitions throughout arbitrary components.

---

## 12. Developer Ownership

To avoid merge conflicts and scattered focus, adhere to the primary ownership model:

### Rajat
- Frontend architecture
- API integration & fetch client
- Shared types
- Routing architecture
- Core scan flow integration
- Backend/frontend contract decisions
- Code review

### Rohan
- Dashboard implementation
- Scan results visualization
- Findings UI
- Risk/severity visualization

### Matin
- Landing page
- Scan initiation UI
- Reusable UI components
- Responsive styling

*Note: Ownership does NOT mean developers cannot help each other. It establishes a primary area of responsibility to avoid simultaneous structural edits.*

---

## 13. Shared Files

The following files and directories are high-conflict shared architecture areas:
- `src/App.tsx`
- `src/main.tsx`
- `src/routes/`
- `src/api/`
- `src/types/`
- `src/layouts/`
- `src/index.css`

**Rule:** Do not casually modify shared architecture files. If a shared file needs a structural change, communicate it with the team first.

---

## 14. Git Branch Strategy

Follow a standard feature branch workflow:

```text
main
  ↓
feature/frontend-[feature-name]
```

Examples:
- `feature/frontend-dashboard`
- `feature/frontend-scan-flow`
- `feature/frontend-landing`
- `feature/frontend-components`

**Never commit directly to `main` for feature work.** Each developer should work on their own feature branch.

---

## 15. Commit Convention

Use clear, descriptive, conventional commits.

**Good Examples:**
- `feat: add scan results dashboard`
- `feat: add scan form`
- `fix: handle scan api errors`
- `refactor: extract finding card`
- `style: improve responsive dashboard`

**Avoid vague commits such as:**
- `"changes"`
- `"final"`
- `"update"`
- `"stuff"`

---

## 16. Pull Request Rules

Every Pull Request must contain:

- **What changed**: A short explanation of the changes.
- **Why**: The reasoning behind the implementation.
- **Screenshots**: Mandatory for any visual UI changes.
- **Validation**: Proof that the build passes (e.g., `npm run build`, `npx tsc --noEmit`).
- **Scope**: Explicitly state whether API/backend code was touched. (Frontend PRs should not modify backend files unless explicitly approved).

---

## 17. Pre-PR Checklist

Before opening a PR, ensure:
- [ ] `npm install` succeeds
- [ ] `npm run build` succeeds
- [ ] TypeScript compilation (`npx tsc --noEmit`) succeeds
- [ ] No browser console errors
- [ ] No accidental backend modifications
- [ ] No `.env` files committed
- [ ] Responsive layout checked
- [ ] Loading state checked
- [ ] Error state checked
- [ ] Empty state checked
- [ ] API calls exclusively use `src/api/`
- [ ] No unnecessary dependencies added
- [ ] Screenshots included for UI changes

---

## 18. Do Not Do This (Anti-Patterns)

- Raw `fetch()` inside components.
- Duplicating API interfaces instead of using `src/types/api.ts`.
- Using `any` types everywhere.
- Giant, monolithic components.
- Unnecessary global state (Redux/Zustand).
- Hardcoding backend URLs (use `.env`).
- Committing secrets in source code.
- Modifying the backend simply to make the frontend easier.
- Adding third-party dependencies without a compelling reason.
- Changing API field names locally.
- Ignoring loading/error UI states.
- Committing directly to `main`.

---

## 19. Local Development

**Installation:**
```bash
npm install
```

**Run Development Server:**
```bash
npm run dev
```

**Build for Production:**
```bash
npm run build
```

**Type Checking:**
```bash
npx tsc --noEmit
```

**Environment Variables:**
The required backend URL is configured via `.env`. Use `.env.example` as your baseline:
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 20. API Contract Reference

The frontend is tightly bound to the documented API contract.
**[View the Frontend API Contract](../Docs/FRONTEND.md)**

This document is the authoritative reference for all API interactions.

---

## 21. Definition of Done

A frontend feature is complete only when:
- The UI works as expected.
- TypeScript compilation passes strictly.
- Production build passes.
- API integration follows the strict contract.
- Loading, error, and empty states exist.
- Responsive behavior is visually acceptable.
- No unnecessary dependencies were introduced.
- Code is placed in the correct architectural directory.
- The PR contains screenshots (when applicable).
