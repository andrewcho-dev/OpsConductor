# Shared Library Cache Fix

## Problem
Docker was caching shared library installations, causing services to continue using old versions of shared libraries even after changes were made. This led to authentication issues and other bugs where the code appeared correct but containers ran outdated versions.

## Root Cause
Docker's layer caching system was caching both:
1. The `COPY shared-libs /tmp/shared-libs` layer
2. The `RUN pip install -e /tmp/shared-libs` layer

Even with `--no-cache-dir`, Docker would reuse the cached COPY layer, so changes to shared libraries weren't being picked up.

## Solution: Build Args + Cache Bust

### Implementation
Each Dockerfile now includes a cache bust mechanism:

```dockerfile
# Install shared libraries (use build arg to bust cache when shared libs change)
ARG SHARED_LIBS_CACHE_BUST=1
RUN echo "Cache bust: $SHARED_LIBS_CACHE_BUST"
COPY shared-libs /tmp/shared-libs
RUN pip install --no-cache-dir -e /tmp/shared-libs
```

### How It Works
1. **ARG SHARED_LIBS_CACHE_BUST**: Accepts a build argument
2. **RUN echo**: Uses the build arg, forcing Docker to invalidate cache when the arg changes
3. **COPY shared-libs**: Now runs fresh instead of using cached layer
4. **pip --no-cache-dir**: Prevents pip's internal caching

## Usage

### Option 1: Manual Build (Single Service)
```bash
docker compose build --build-arg SHARED_LIBS_CACHE_BUST=$(date +%s) service-name
docker compose up -d service-name
```

### Option 2: Helper Script (Recommended)
```bash
# Rebuild single service
./rebuild-with-shared-libs.sh user-service

# Rebuild all services with shared libraries
./rebuild-with-shared-libs.sh
```

### Option 3: Docker Compose Override (For Development)
Add to `docker-compose.override.yml`:
```yaml
services:
  user-service:
    build:
      args:
        SHARED_LIBS_CACHE_BUST: ${SHARED_LIBS_CACHE_BUST:-1}
```

Then use: `SHARED_LIBS_CACHE_BUST=$(date +%s) docker compose up -d --build`

## Services Using Shared Libraries
- auth-service
- user-service  
- targets-service
- jobs-service
- execution-service
- audit-events-service
- notification-service
- job-management-service
- job-scheduling-service
- target-discovery-service

## When to Use
**Always use cache busting when:**
- Making changes to shared library code
- Fixing authentication issues
- Updating shared utilities or models
- Debugging issues where code looks correct but behavior is wrong

## Verification
After rebuilding, verify the changes are picked up:
```bash
# Check if shared library changes are in the container
docker exec container-name grep -n "your-change" /tmp/shared-libs/path/to/file.py
```

## Performance Impact
- **Minimal**: Only the shared library layers are rebuilt
- **Other layers remain cached**: Dependencies, base image, etc.
- **Build time**: +2-5 seconds per service for shared lib installation

## Alternative Solutions Considered
1. **`--no-cache-dir` only**: ❌ Didn't work (Docker layer caching issue)
2. **`docker build --no-cache`**: ❌ Too slow (rebuilds everything)
3. **Volume mounts**: ❌ Not suitable for production
4. **Build args + cache bust**: ✅ **Chosen solution** (fast + reliable)

## Troubleshooting

### Build Errors
If you get errors like `../shared-libs is not a valid editable requirement`:
1. Check if the service's `requirements.txt` has `-e ../shared-libs` 
2. Remove that line - shared libraries are now installed via Dockerfile
3. Comments like `# Note: Install with: pip install -e ../shared-libs` are fine

### Cache Issues
If shared library changes still aren't picked up:
1. Ensure you're using the cache bust argument
2. Check the build output for "Cache bust: [timestamp]"
3. Verify the COPY and RUN steps are not showing "CACHED"
4. Use `docker compose build --no-cache service-name` as last resort

### Fixed Issues
- ✅ **job-management-service**: Removed `-e ../shared-libs` from requirements.txt
- ✅ **All services**: Now use Dockerfile-based shared library installation