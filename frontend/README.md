# Movie Reservation Frontend

Modern React frontend for the Movie Reservation System with TypeScript, Tailwind CSS, and Zustand.

## Features

- ✨ Beautiful modern UI with dark theme
- 🎬 Browse and book movie showtimes
- 💺 Interactive seat selection
- 👤 User authentication (signup/login)
- 👨‍💼 Admin dashboard for managing movies, auditoriums, and showtimes
- 📱 Fully responsive design
- ⚡ Fast and optimized with Vite

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Zustand** - State management
- **Axios** - HTTP client
- **Lucide React** - Icons

## Getting Started

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:3000

### Build

```bash
npm run build
```

### Preview

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable components
│   │   └── Navbar.tsx
│   ├── pages/             # Page components
│   │   ├── LoginPage.tsx
│   │   ├── SignupPage.tsx
│   │   ├── MoviesPage.tsx
│   │   └── AdminPage.tsx
│   ├── lib/
│   │   └── api.ts        # API client with Axios
│   ├── store/
│   │   └── index.ts      # Zustand stores
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # React entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html           # HTML template
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## Features in Detail

### Authentication
- User signup with validation
- Email/password login
- JWT token management
- Automatic token refresh
- Persistent login state

### Movie Browsing
- View all available showtimes
- Filter by movie, auditorium, date
- Real-time seat availability

### Booking System
- Interactive seat selection (grid layout)
- Visual seat status (available, booked, selected)
- One-click booking
- Reservation expiry warning

### Admin Panel
- Manage movies (add, edit, delete)
- Manage auditoriums
- Manage showtimes with conflict detection
- Create seats in batches

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`.

### Key API Endpoints
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token
- `GET /admin/movies` - Get all movies
- `POST /admin/movies` - Create movie
- `GET /showtimes/{id}/seats` - Get available seats
- `POST /showtimes/{id}/holds` - Reserve seats

## Styling

Uses **Tailwind CSS** with custom utility classes for buttons and inputs:
- `.btn-primary` - Primary action button
- `.btn-secondary` - Secondary action button
- `.input-field` - Form input styling
- `.card` - Card component styling
- `.glass` - Glassmorphism effect

## State Management

Uses **Zustand** for simple, efficient state management:
- `useAuthStore` - Authentication state
- `useMoviesStore` - Movies state

## Environment Variables

Create a `.env` file if needed (optional):
```
VITE_API_BASE=http://localhost:8000
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
