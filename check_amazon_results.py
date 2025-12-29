import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['product_checker']
    
    # Check scan results for Amazon URLs
    results = await db.scan_results.find({'url': {'$regex': 'amazon', '$options': 'i'}}).sort('scanned_at', -1).limit(10).to_list(length=10)
    
    print(f"\nFound {len(results)} Amazon scan results:")
    for r in results:
        print(f"  URL: {r['url'][:60]}")
        print(f"    Status: {r['status']}")
        print(f"    Add to Cart: {r['add_to_cart']}")
        print(f"    Scanned at: {r['scanned_at']}")
        if r.get('error_message'):
            print(f"    Error: {r['error_message'][:80]}")
        print()
    
    client.close()

asyncio.run(check())
