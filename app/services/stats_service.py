from app.services.user_service import get_total_users
from app.services.barber_service import get_barbers_count
from app.services.client_service import get_clients_count


async def get_stats() -> dict:
    total = await get_total_users()
    barbers = await get_barbers_count()
    clients = await get_clients_count()
    return {"total": total, "barbers": barbers, "clients": clients}
