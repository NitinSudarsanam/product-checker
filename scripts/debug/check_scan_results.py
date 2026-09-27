import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb+srv://nitinsudarsanam_db_user:OzUBfGFuqIihVDlf@cluster0.2kgrfct.mongodb.net/?appName=Cluster0')
    db = client['ubique-product-checker']
    
    # Get latest 10 scan results
    results = await db.scan_results.find().sort('scanned_at', -1).limit(10).to_list(length=10)
    
    print(f"\n{'='*80}")
    print(f"Latest 10 Scan Results from Database:")
    print(f"{'='*80}\n")
    
    for i, r in enumerate(results, 1):
        url_short = r['url'][:70] + '...' if len(r['url']) > 70 else r['url']
        print(f"{i}. {url_short}")
        print(f"   Status: {r['status']}")
        print(f"   Add to Cart: {r['add_to_cart']}")
        print(f"   Buy Now: {r['buy_now']}")
        print(f"   Scanned: {r['scanned_at']}")
        if r.get('error_message'):
            print(f"   Error: {r['error_message']}")
        print()
    
    client.close()

asyncio.run(check())
