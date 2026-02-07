
print("Checking imports...")
try:
    from app.config import BOT_TOKEN, DB_PATH
    print("✅ config")
    
    from app.db.models import init_db
    print("✅ models")
    
    from app.states import ClientReg
    print("✅ states")
    
    from app.keyboards.reply import client_main_kb
    print("✅ keyboards.reply")

    from app.keyboards.inline import regions_kb
    print("✅ keyboards.inline")

    from app.services.user_service import get_user
    from app.services.region_service import list_regions
    from app.services.butcher_service import create_butcher
    from app.services.price_service import upsert_price
    from app.services.broadcast_service import send_broadcast
    from app.services.geo_service import haversine
    print("✅ services")

    from app.handlers import common, client, butcher, admin
    print("✅ handlers")
    
    print("🎉 All imports successful!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
