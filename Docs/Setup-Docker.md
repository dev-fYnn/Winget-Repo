# 🐳 Docker Setup Guide for Winget-Repo

This guide will help you set up and run Winget-Repo using Docker and Docker Compose.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)

You can verify your installation by running:
```bash
docker --version
docker compose version
```

## 🚀 Quick Start

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd Winget-Repo
   ```

2. **Create a `.env` file (optional)**
   ```bash
   cp env.example .env
   ```
   Edit `.env` to customize your configuration (see [Configuration](#configuration) section below).

3. **Build and start the container**
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   Open your browser and navigate to: `http://localhost:5000`

## ⚙️ Configuration

### Environment Variables

You can configure Winget-Repo using environment variables. Create a `.env` file in the project root, or set them directly in `docker-compose.yaml`.

#### Data Paths
- `PATH_LOGOS` - Directory for package logo images (default: `/data/logos`)
- `PATH_FILES` - Directory for uploaded package files (default: `/data/files`)
- `PATH_DATABASE` - Path to the SQLite database file (default: `/data/database/database.db`)

#### Winget Repository Paths
- `PATH_WINGET_REPOSITORY` - Root directory for Winget repository data (default: `/data/winget-repository/`)
- `PATH_WINGET_REPOSITORY_DB` - Path to the Winget public index.db (default: `/data/winget-repository/Public/index.db`)
- `URL_WINGET_REPOSITORY` - External URL for downloading Winget community repository (default: `https://cdn.winget.microsoft.com/cache/`)

#### SSL Certificate Paths (for development mode)
- `PATH_SSL_CERT` - Path to SSL certificate file (default: `/data/ssl/cert.pem`)
- `PATH_SSL_KEY` - Path to SSL private key file (default: `/data/ssl/key.pem`)

#### Network Settings
- `BIND_ADDRESS` - IP address to bind to (default: `0.0.0.0`)


## 📁 Data Persistence

All data is stored in the `./data` directory on your host machine, which is mounted as a volume in the container. This ensures that:

- **Database** - Your database persists across container restarts
- **Uploaded Files** - Package files and logos are preserved
- **Winget Repository** - Repository data is maintained
- **SSL Certificates** - SSL certificates (if used) are stored

The `data` folder structure:
```
data/
├── database/          # SQLite database files
├── files/             # Uploaded package installer files
├── logos/             # Package logo images
├── winget-repository/ # Winget repository data
└── ssl/               # SSL certificates (for dev mode)
```

## 🔧 Common Commands

### Build and Start the container
```bash
docker compose up --build -d
```

### Stop the container
```bash
docker compose stop
```

### Stop and remove the container
```bash
docker compose down
```

## 🌐 Port Configuration

By default, Winget-Repo runs on port **5000**. To change the port, modify the `ports` section in `docker-compose.yaml`:

```yaml
ports:
  - "8080:5000"  # Maps host port 8080 to container port 5000
```

Then access the application at `http://localhost:8080`.

## 🔒 HTTPS Setup (Production)

For production deployments, it's recommended to use a reverse proxy (like Nginx or Apache) in front of Winget-Repo for HTTPS support. The container runs on HTTP by default.

Winget will refuse to use http for repository, having a trusted https connection is mandatory for winget to function.


## 🐛 Troubleshooting

### Database issues

If you encounter database errors:

1. **Check database permissions:**
   ```bash
   ls -la data/database/
   ```

2. **Verify the database file exists:**
   The database will be created automatically on first run.

3. **Reset the database (⚠️ WARNING: This will delete all data):**
   ```bash
   docker compose down
   rm -rf data/database/*
   docker compose up -d
   ```

### Permission issues

If you encounter permission errors:

1. **Check file ownership:**
   ```bash
   ls -la data/
   ```

2. **Fix permissions (Linux/Mac):**
   ```bash
   sudo chown -R $USER:$USER data/
   ```

### Container health check failing

The container includes a health check. If it's failing:

1. **Check container logs:**
   ```bash
   docker compose logs winget-repo
   ```

2. **Verify the application is responding:**
   ```bash
   curl http://localhost:5000
   ```

3. **Check container health status:**
   ```bash
   docker compose ps
   ```

## 🔄 Updating Winget-Repo

To update to a newer version:

1. **Pull the latest code:**
   ```bash
   git pull
   ```

2. **Rebuild and restart:**
   ```bash
   docker compose up -d --build
   ```

3. **Check logs for any migration messages:**
   ```bash
   docker compose logs -f
   ```

## 📊 Monitoring

### View container resource usage
```bash
docker stats winget-repo
```

### Check container health
```bash
docker inspect --format='{{.State.Health.Status}}' winget-repo
```

## 🗑️ Cleanup

To completely remove the container and all data:

⚠️ **WARNING: This will delete all data including the database!**

```bash
docker compose down -v
rm -rf data/
```

