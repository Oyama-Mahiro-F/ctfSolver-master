# CTF Solver Frontend

A modern React frontend for the CTF Solver application, built with:
- React 18 + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui components
- Framer Motion

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 3. Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
src/
  components/
    ui/              # shadcn/ui components
      aurora-background.tsx
    aurora-demo.tsx  # Demo component
  lib/
    utils.ts         # Utility functions (cn helper)
  App.tsx            # Main app component
  main.tsx           # Entry point
  index.css          # Global styles with Tailwind
```

## Component Usage

The `AuroraBackground` component is located in `src/components/ui/aurora-background.tsx` and can be imported and used like:

```tsx
import { AuroraBackground } from "@/components/ui/aurora-background";

<AuroraBackground>
  {/* Your content here */}
</AuroraBackground>
```

## shadcn/ui Setup

This project follows the shadcn/ui structure:
- Components are in `src/components/ui/`
- The `cn` utility function is in `src/lib/utils.ts`
- Tailwind is configured with the required plugins

## Backend Integration

The backend API runs on `http://localhost:5000` (Flask). Make sure to configure API endpoints in your components to connect to the backend.
