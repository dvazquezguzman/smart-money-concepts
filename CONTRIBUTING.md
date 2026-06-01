# Contributing

## Getting Started

1. Fork the repo
2. `pip install -e . pytest` (backend) + `cd frontend && npm ci` (frontend)
3. Create a feature branch: `git checkout -b my-feature`
4. Make changes
5. Run tests: `pytest smartmoneyconcepts/dashboard/tests/ -v` + `cd frontend && npx vitest run`
6. Submit a pull request

## Coding Standards

- **Python**: Follow PEP 8. Use type hints for all function signatures.
- **TypeScript/React**: Use strict TypeScript. Prefer functional components with hooks.
- **CSS**: Use Tailwind utility classes. No separate CSS files for new components.
- **Error handling**: Use `HTTPException` for API errors. Never expose stack traces to clients.
- **Naming**: `snake_case` for Python, `camelCase` for TypeScript. Components are `PascalCase`.

## PR Checklist

Before submitting:

- [ ] Tests pass for both backend and frontend
- [ ] No new `console.log`, `print()`, or `import pdb` left in code
- [ ] API changes are backward compatible (or clearly documented)
- [ ] Frontend changes handle loading, error, and empty states
- [ ] TypeScript types are defined for new API responses
- [ ] New dependencies are justified (check `package.json` / `setup.py`)
- [ ] If adding a new page, add it to the sidebar navigation in `layout.tsx`

## PR Guidelines

Less is more -- each pull request should be minimal, focusing on a single function or small feature. Large, sweeping changes will not be merged, as they are harder to review and maintain.

- One feature per PR
- Keep commits atomic
- Write clear commit messages (see git log for style)
- Add tests for new functionality
- Update docs if adding new API endpoints or strategy conditions
