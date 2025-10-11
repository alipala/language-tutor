# Frontend Routing & Backend Integration Fix

## Problem Analysis

The staging server returns 404 for `/institution/signup` because:

1. **Next.js App Router generates static HTML files** in `frontend/out/institution/signup.html`
2. **FastAPI StaticFiles doesn't handle App Router paths** - it expects files at exact paths
3. **Backend needs explicit route handlers** for App Router pages

## Root Cause

FastAPI's `StaticFiles(html=True)` only works for Pages Router (e.g., `/privacy.html` → `/privacy`).
For App Router nested routes like `/institution/signup`, we need explicit handlers.

## Solution

Add explicit route handlers in `backend/main.py` for all App Router pages.

## Implementation

### 1. Add Institution Route Handlers

```python
# Institution routes
@app.get("/institution/signup")
async def serve_institution_signup():
    signup_file = frontend_build_path / "institution" / "signup.html"
    if signup_file.exists():
        return FileResponse(signup_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Institution signup page not found")

@app.get("/institution/login")
async def serve_institution_login():
    login_file = frontend_build_path / "institution" / "login.html"
    if login_file.exists():
        return FileResponse(login_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Institution login page not found")
```

### 2. Add Catch-All for App Router Pages

```python
# Catch-all for App Router nested routes
@app.get("/{path:path}")
async def serve_app_router_pages(path: str):
    """Serve App Router pages with proper fallback"""
    # Try exact path
    file_path = frontend_build_path / f"{path}.html"
    if file_path.exists():
        return FileResponse(file_path, media_type="text/html")
    
    # Try as directory with index.html
    dir_path = frontend_build_path / path / "index.html"
    if dir_path.exists():
        return FileResponse(dir_path, media_type="text/html")
    
    # Fallback to 404
    raise HTTPException(status_code=404, detail="Page not found")
```

## Testing

```bash
# Test locally
curl http://localhost:8000/institution/signup
curl http://localhost:8000/institution/login

# Test on staging
curl https://staging-env.up.railway.app/institution/signup
```

## Deployment Checklist

- [ ] Add institution route handlers
- [ ] Add catch-all route handler
- [ ] Test all institutional routes
- [ ] Verify API endpoints still work
- [ ] Deploy to staging
- [ ] Verify in browser
