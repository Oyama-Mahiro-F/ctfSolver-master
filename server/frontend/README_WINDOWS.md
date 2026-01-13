# CTF Solver Frontend - Windows Usage Guide

## Quick Start

### Method 1: Using Development Server (Recommended)

1. **Install Dependencies** (First time only)
   ```cmd
   cd server\frontend
   npm install
   ```

2. **Start Development Server**
   ```cmd
   start_frontend_dev.bat
   ```
   Or run directly:
   ```cmd
   npm run dev
   ```

3. **Access Frontend**
   Open your browser and visit: `http://localhost:5173`

### Method 2: Using Proxy Server (Production)

1. **Build Frontend**
   ```cmd
   npm run build
   ```

2. **Start Proxy Server**
   ```cmd
   start_proxy.bat
   ```
   Or specify a port:
   ```cmd
   start_proxy.bat 8081
   ```

3. **Access Frontend**
   Open your browser and visit: `http://localhost:8081`

## Requirements

- **Node.js**: Version 16.0 or higher
- **npm**: Version 8.0 or higher
- **Python**: 3.8+ (Only needed for proxy server)
- **pip**: requests module (Only needed for proxy server)

## Installing Node.js

If Node.js is not installed, please visit [Node.js Official Website](https://nodejs.org/) to download and install.

After installation, verify in command line:
```cmd
node --version
npm --version
```

## Installing Python Dependencies (Proxy Server)

If using the proxy server, you need to install the requests module:
```cmd
pip install requests
```

## Common Issues

### 1. Port Already in Use

If port 5173 is occupied, Vite will automatically try other ports (e.g., 5174).

If the proxy server port is occupied, you can specify another port:
```cmd
start_proxy.bat 8082
```

### 2. Cannot Connect to Backend

Make sure the backend service is running on `http://localhost:5000`.

### 3. npm install Failed

- Check your network connection
- Try using a mirror:
  ```cmd
  npm config set registry https://registry.npmmirror.com
  ```

### 4. Proxy Server Failed to Start

- Make sure Python is installed and in PATH
- Make sure the requests module is installed: `pip install requests`
- Check if the backend service is running on `http://localhost:5000`

## Development Guide

### Development Mode

Development mode uses Vite's Hot Module Replacement (HMR), which automatically refreshes after code changes.

```cmd
npm run dev
```

### Build for Production

```cmd
npm run build
```

Built files will be in the `dist` directory.

### Preview Production Build

```cmd
npm run preview
```

## Scripts Description

- `start_frontend_dev.bat`: Start frontend development server
- `start_proxy.bat`: Start proxy server (for production environment)
- `start_frontend.bat`: Comprehensive startup script (calls development server)

## API Configuration

The frontend connects to the backend API at `http://localhost:5000` by default.

You can modify this via environment variables:
- Create a `.env` file
- Add: `VITE_API_BASE_URL=http://your-backend-url:5000`

## More Information

See [README.md](README.md) for detailed project information.
