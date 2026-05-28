from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import schemas
from task_service import task_service
from database import supabase, is_supabase_configured

app = FastAPI(title="EpexTASK API", description="Python FastAPI Backend for EpexTASK")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
        
    token = authorization.split(" ")[1]
    
    # Check for mock auth session
    if token.startswith("mock-session-"):
        email = token.replace("mock-session-", "")
        return {
            "id": f"local-user-{email}",
            "email": email
        }
        
    # Verify with real Supabase instance if configured
    if is_supabase_configured and supabase:
        try:
            # We call get_user directly with the jwt token
            user_response = supabase.auth.get_user(token)
            user = user_response.user
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired auth session"
                )
            return {
                "id": str(user.id),
                "email": user.email or ""
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Verification failed: {str(e)}"
            )
            
    # Local fallback
    return {
        "id": "local-user",
        "email": "guest@epextask.local"
    }

@app.get("/api/health")
async def health_check():
    db_status = await task_service.test_connection()
    return {
        "status": "ok",
        "database": "connected" if db_status["success"] else "offline_fallback",
        "error": db_status.get("error")
    }

@app.get("/api/tasks", response_model=List[schemas.Task])
async def get_tasks(current_user: Dict[str, str] = Depends(get_current_user)):
    user_id = current_user["id"]
    return await task_service.fetch_tasks(user_id)

@app.post("/api/tasks", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
async def create_task(task_input: schemas.CreateTaskInput, current_user: Dict[str, str] = Depends(get_current_user)):
    user_id = current_user["id"]
    return await task_service.add_task(task_input, user_id)

@app.put("/api/tasks/{task_id}", response_model=schemas.Task)
async def update_task(task_id: str, updates: schemas.UpdateTaskInput, current_user: Dict[str, str] = Depends(get_current_user)):
    user_id = current_user["id"]
    try:
        return await task_service.update_task(task_id, updates, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, current_user: Dict[str, str] = Depends(get_current_user)):
    user_id = current_user["id"]
    await task_service.delete_task(task_id, user_id)
    return {"success": True, "message": "Task deleted successfully"}

@app.delete("/api/tasks")
async def clear_all_tasks(current_user: Dict[str, str] = Depends(get_current_user)):
    user_id = current_user["id"]
    await task_service.delete_all_tasks(user_id)
    return {"success": True, "message": "All tasks cleared successfully"}

@app.post("/api/profile/reset")
async def reset_profile(current_user: Dict[str, str] = Depends(get_current_user)):
    user_id = current_user["id"]
    await task_service.delete_all_tasks(user_id)
    await task_service.reset_onboarding(user_id)
    
    # Re-fetch seeds
    tasks = await task_service.fetch_tasks(user_id)
    return {
        "success": True,
        "message": "Profile reset and re-seeded successfully",
        "tasks": tasks
    }
