# Job Evolution Tracker — Coding Standards

## Project Structure

```
job-evolution/
├── app/          # FastAPI backend (Python)
├── ui/           # React frontend (TypeScript + Vite)
│   ├── src/
│   │   ├── components/   # Shared & feature components
│   │   │   └── ui/       # shadcn/ui primitives (auto-generated, do not edit)
│   │   ├── lib/          # Utilities (utils.ts, api.ts, …)
│   │   └── types/        # Shared TypeScript types
│   └── components.json   # shadcn/ui config
└── data/         # Source JSON data
```

## Frontend Rules (ui/)

### Language & Syntax
- **TypeScript only** — no `.jsx` or `.js` files in `src/`
- Strict mode is on (`"strict": true` in tsconfig)
- Use `type` imports: `import type { Foo } from './foo'`

### Components
- **Functional components only** — no class components
- Name components with PascalCase; one component per file
- Use named exports: `export function MyComponent()` (not default exports)
- Use `React.FC` or inline prop types — prefer inline:
  ```tsx
  function JobCard({ job }: { job: Job }) { … }
  ```

### Styling
- **Tailwind CSS v4** utility classes only — no custom CSS files
- **shadcn/ui** for all UI primitives (Button, Card, Badge, Table, Dialog, etc.)
  - Add components: `npx shadcn@latest add <component>`
  - Never manually edit files inside `src/components/ui/`
- **Lucide React** for all icons — import individually:
  ```tsx
  import { Briefcase, TrendingUp, Bot } from 'lucide-react'
  ```

### State & Data Fetching
- Use `useState` / `useEffect` for local state
- Fetch from the FastAPI backend at `http://localhost:8000`
- Define API response types in `src/types/api.ts`

### File Naming
| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase | `JobCard.tsx` |
| Hooks | camelCase with `use` prefix | `useJobs.ts` |
| Utilities | camelCase | `formatScore.ts` |
| Types | PascalCase | `types/api.ts` |

## Backend Rules (app/)

- Python 3.12, FastAPI, Pydantic v2
- Async endpoints throughout
- See existing code for patterns

## Git

- Commit messages: imperative mood, ≤72 chars subject line
- Branch off `master` for features
