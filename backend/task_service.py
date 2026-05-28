import datetime
import uuid
from typing import List, Dict, Any, Set
from database import supabase, is_supabase_configured, get_supabase_client
import schemas

# In-Memory storage mock for offline mode
in_memory_tasks: List[Dict[str, Any]] = []
onboarded_users: Set[str] = set()

def generate_demo_tasks(user_id: str) -> List[Dict[str, Any]]:
    now = datetime.datetime.utcnow()
    
    def past_date(days: int):
        return (now - datetime.timedelta(days=days)).date().isoformat()
        
    def future_date(days: int):
        return (now + datetime.timedelta(days=days)).date().isoformat()
        
    def past_datetime(days: int):
        return (now - datetime.timedelta(days=days)).isoformat() + "Z"

    return [
        {
            "id": f"demo-1-{user_id}",
            "title": "Fix Auth Session State Leak",
            "description": "Audit and patch authentication session storage leakage in React client-side lifecycle to secure multi-user environments.",
            "is_completed": False,
            "created_at": past_datetime(5),
            "due_date": past_date(3),
            "priority": "high",
            "user_id": user_id,
            "completed_at": None
        },
        {
            "id": f"demo-2-{user_id}",
            "title": "Migrate Postgres Database Schema",
            "description": "Run the supabase-schema.sql script in the Supabase SQL editor to create columns and enable strict Row-Level Security (RLS) policies.",
            "is_completed": False,
            "created_at": past_datetime(4),
            "due_date": past_date(1),
            "priority": "medium",
            "user_id": user_id,
            "completed_at": None
        },
        {
            "id": f"demo-3-{user_id}",
            "title": "Optimize Donut Chart Performance",
            "description": "Refactor SVGCircle calculations inside User Analysis dashboard to minimize renders during real-time filters.",
            "is_completed": False,
            "created_at": past_datetime(1),
            "due_date": future_date(2),
            "priority": "high",
            "user_id": user_id,
            "completed_at": None
        },
        {
            "id": f"demo-4-{user_id}",
            "title": "Update Developer Onboarding Docs",
            "description": "Write instructions for connecting other devices to local network address IP for testing purposes.",
            "is_completed": False,
            "created_at": past_datetime(0),
            "due_date": future_date(5),
            "priority": "low",
            "user_id": user_id,
            "completed_at": None
        },
        {
            "id": f"demo-5-{user_id}",
            "title": "Implement Tamas Productivity Score",
            "description": "Design math algorithms to normalize backlog weight indices and cap extreme outliers.",
            "is_completed": True,
            "created_at": past_datetime(3),
            "due_date": past_date(1),
            "priority": "high",
            "completed_at": past_datetime(2),
            "user_id": user_id
        },
        {
            "id": f"demo-6-{user_id}",
            "title": "Design Glassmorphic Auth Screen",
            "description": "Stylize a high-fidelity sign-in/register form with interactive borders and custom glows.",
            "is_completed": True,
            "created_at": past_datetime(2),
            "due_date": past_date(1),
            "priority": "medium",
            "completed_at": past_datetime(2),
            "user_id": user_id
        },
        {
            "id": f"demo-7-{user_id}",
            "title": "Setup Tailwind CSS v4.0 Layout",
            "description": "Configure index.css styling tokens, glass backgrounds, and standard animations.",
            "is_completed": True,
            "created_at": past_datetime(6),
            "due_date": past_date(4),
            "priority": "medium",
            "completed_at": past_datetime(1),
            "user_id": user_id
        }
    ]

def get_local_tasks(user_id: str) -> List[Dict[str, Any]]:
    global in_memory_tasks
    user_tasks = [t for t in in_memory_tasks if t.get("user_id") == user_id]
    has_onboarded = user_id in onboarded_users
    
    if len(user_tasks) == 0 and not has_onboarded:
        default_tasks = generate_demo_tasks(user_id)
        in_memory_tasks.extend(default_tasks)
        onboarded_users.add(user_id)
        return default_tasks
        
    return user_tasks

def save_local_tasks(updated_user_tasks: List[Dict[str, Any]], user_id: str):
    global in_memory_tasks
    in_memory_tasks = [t for t in in_memory_tasks if t.get("user_id") != user_id]
    in_memory_tasks.extend(updated_user_tasks)
    onboarded_users.add(user_id)

class TaskService:
    async def test_connection(self, token: str = None) -> Dict[str, Any]:
        client = get_supabase_client(token)
        if not is_supabase_configured or not client:
            return {"success": False, "error": "Supabase is not configured"}
        try:
            client.table("tasks").select("id, user_id").limit(1).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fetch_tasks(self, user_id: str, token: str = None) -> List[Dict[str, Any]]:
        client = get_supabase_client(token)
        if is_supabase_configured and client:
            try:
                response = client.table("tasks") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .order("created_at", desc=True) \
                    .execute()
                data = response.data or []
                
                if len(data) == 0 and user_id not in onboarded_users:
                    demo_tasks = generate_demo_tasks(user_id)
                    seed_response = client.table("tasks").insert([
                        {
                            "title": t["title"],
                            "description": t["description"],
                            "is_completed": t["is_completed"],
                            "created_at": t["created_at"],
                            "due_date": t["due_date"],
                            "priority": t["priority"],
                            "completed_at": t["completed_at"],
                            "user_id": t["user_id"]
                        } for t in demo_tasks
                    ]).execute()
                    onboarded_users.add(user_id)
                    return seed_response.data or demo_tasks
                return data
            except Exception as e:
                print(f"Supabase fetch failed. Falling back to local: {e}")
                return get_local_tasks(user_id)
        return get_local_tasks(user_id)

    async def add_task(self, input_data: schemas.CreateTaskInput, user_id: str, token: str = None) -> Dict[str, Any]:
        temp_id = str(uuid.uuid4())
        new_task = {
            "id": temp_id,
            "title": input_data.title,
            "description": input_data.description,
            "is_completed": False,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "due_date": input_data.due_date,
            "priority": input_data.priority,
            "user_id": user_id,
            "completed_at": None
        }

        client = get_supabase_client(token)
        if is_supabase_configured and client:
            try:
                response = client.table("tasks").insert({
                    "title": input_data.title,
                    "description": input_data.description,
                    "due_date": input_data.due_date,
                    "priority": input_data.priority,
                    "is_completed": False,
                    "user_id": user_id
                }).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
            except Exception as e:
                print(f"Supabase insert failed. Saving to local. Error: {e}")
                
        # Fallback
        tasks = get_local_tasks(user_id)
        tasks.insert(0, new_task)
        save_local_tasks(tasks, user_id)
        return new_task

    async def update_task(self, task_id: str, updates: schemas.UpdateTaskInput, user_id: str, token: str = None) -> Dict[str, Any]:
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        if "is_completed" in update_dict:
            update_dict["completed_at"] = (datetime.datetime.utcnow().isoformat() + "Z") if update_dict["is_completed"] else None

        client = get_supabase_client(token)
        if is_supabase_configured and client:
            try:
                response = client.table("tasks").update(update_dict).eq("id", task_id).eq("user_id", user_id).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
            except Exception as e:
                print(f"Supabase update failed. Applying to local. Error: {e}")
                
        # Fallback
        tasks = get_local_tasks(user_id)
        for i, t in enumerate(tasks):
            if t["id"] == task_id:
                for k, v in update_dict.items():
                    t[k] = v
                save_local_tasks(tasks, user_id)
                return t
        raise Exception("Task not found")

    async def delete_task(self, task_id: str, user_id: str, token: str = None) -> None:
        client = get_supabase_client(token)
        if is_supabase_configured and client:
            try:
                client.table("tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()
                return
            except Exception as e:
                print(f"Supabase delete failed. Applying to local. Error: {e}")
                
        # Fallback
        tasks = get_local_tasks(user_id)
        filtered = [t for t in tasks if t["id"] != task_id]
        save_local_tasks(filtered, user_id)

    async def delete_all_tasks(self, user_id: str, token: str = None) -> None:
        client = get_supabase_client(token)
        if is_supabase_configured and client:
            try:
                client.table("tasks").delete().eq("user_id", user_id).execute()
                return
            except Exception as e:
                print(f"Supabase delete all failed. Error: {e}")
                
        # Fallback
        save_local_tasks([], user_id)

    async def reset_onboarding(self, user_id: str) -> None:
        if user_id in onboarded_users:
            onboarded_users.remove(user_id)

task_service = TaskService()
