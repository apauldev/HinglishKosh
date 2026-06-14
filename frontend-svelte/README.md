# HinglishKosh Frontend (SvelteKit)

A modern SvelteKit frontend for the HinglishKosh dictionary, deployed on Cloudflare Pages with D1 database.

## Tech Stack

- **Framework**: SvelteKit 2
- **UI**: shadcn-svelte style components + Tailwind CSS v4
- **Database**: Cloudflare D1 (SQLite)
- **Deployment**: Cloudflare Pages
- **Language**: TypeScript (strict mode)

## Development

### Prerequisites

- Node.js 18+
- pnpm
- Wrangler CLI (`pnpm add -D wrangler`)

### Setup

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Copy environment variables:

   ```bash
   cp .env.example .env
   ```

3. Start local development server:
   ```bash
   pnpm dev
   ```

### Local Development with D1

To test against a local D1 database:

1. Build the project:

   ```bash
   pnpm build
   ```

2. Run with Wrangler (emulates Cloudflare environment):
   ```bash
   pnpm dev:local
   ```

This will start a local server at `http://localhost:8788` with D1 emulation.

### Available Scripts

| Script               | Description                             |
| -------------------- | --------------------------------------- |
| `pnpm dev`           | Start Vite dev server (no D1)           |
| `pnpm dev:local`     | Start with Wrangler (with D1 emulation) |
| `pnpm build`         | Build for production                    |
| `pnpm preview`       | Preview production build                |
| `pnpm preview:local` | Preview with Wrangler                   |
| `pnpm check`         | Run TypeScript/Svelte checks            |
| `pnpm lint`          | Run ESLint + Prettier                   |
| `pnpm format`        | Format code with Prettier               |
| `pnpm deploy`        | Deploy to Cloudflare Pages              |
| `pnpm deploy:prod`   | Deploy to production branch             |

## Deployment

### Prerequisites

1. Cloudflare account with D1 database created
2. `CLOUDFLARE_API_TOKEN` environment variable set
3. Database seeded with data

### Deploy to Cloudflare Pages

```bash
# Build
pnpm build

# Deploy
pnpm deploy
```

Or use the CI/CD pipeline (GitHub Actions).

### Database Setup

1. Create D1 database:

   ```bash
   wrangler d1 create hinglishkosh
   ```

2. Update `wrangler.toml` with the new database ID

3. Apply schema:

   ```bash
   wrangler d1 execute hinglishkosh --file=../frontend/src/schema/d1.sql
   ```

4. Import data (from existing frontend):
   ```bash
   # Use the existing seed scripts in ../frontend/src/seed/
   ```

## Project Structure

```
frontend-svelte/
├── src/
│   ├── lib/
│   │   ├── components/      # Svelte components
│   │   │   ├── ui/          # Base UI components
│   │   │   ├── Header.svelte
│   │   │   ├── Footer.svelte
│   │   │   ├── SearchForm.svelte
│   │   │   ├── EntryCard.svelte
│   │   │   └── ...
│   │   ├── server/
│   │   │   ├── db.ts        # D1 query helpers
│   │   │   └── types.ts     # TypeScript types
│   │   └── utils.ts         # Utility functions
│   ├── routes/              # File-based routing
│   │   ├── +layout.svelte   # Root layout
│   │   ├── +page.svelte     # Home page
│   │   ├── search/          # Search results
│   │   ├── word/[slug]/     # Word detail
│   │   ├── about/           # About page
│   │   └── api/             # API endpoints
│   ├── app.html             # HTML shell
│   ├── app.css              # Global styles
│   └── app.d.ts             # TypeScript declarations
├── static/                  # Static assets
├── wrangler.toml            # Cloudflare config
└── package.json
```

## API Endpoints

| Endpoint                   | Description              |
| -------------------------- | ------------------------ |
| `GET /api/search?q=...`    | Full-text search         |
| `GET /api/suggest?q=...`   | Autocomplete suggestions |
| `GET /api/lookup?word=...` | Word lookup              |
| `GET /api/stats`           | Dataset statistics       |

## License

GPL v3.0
