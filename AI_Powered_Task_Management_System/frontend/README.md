# AI Task Manager - Frontend

Next.js frontend application for the AI-Powered Task Management System.

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Package Manager**: npm

## Installation

```bash
cd AI_Powered_Task_Management_System/frontend

# Install dependencies
npm install
```

## Development

```bash
# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Building for Production

```bash
# Create optimized production build
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                   # Next.js App Router pages
│   ├── dashboard/        # Dashboard page
│   ├── tasks/           # Task management pages
│   ├── analytics/       # Analytics pages
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   └── globals.css      # Global styles
├── components/           # React components
│   ├── ui/              # Reusable UI components
│   └── features/        # Feature-specific components
├── lib/                  # Utilities and helpers
│   ├── api.ts           # API client
│   └── hooks.ts         # Custom React hooks
└── public/              # Static assets
```

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000/api/v1`.

API proxy configuration is set up in `next.config.js` to avoid CORS issues during development.

## Features (Planned)

- Task Dashboard
- Natural Language Task Creation via AI Chat
- Calendar View
- Analytics and Insights
- Chainlit Integration for Conversational AI

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## License

Proprietary - All rights reserved
