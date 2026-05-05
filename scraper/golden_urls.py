"""
Golden URL fixtures for regression testing retailer support.

These are intended to be US PDP URLs (no login) and cover:
- in_stock_simple
- in_stock_with_variants
- out_of_stock
"""

from __future__ import annotations

from typing import Dict, List


GoldenURLSet = Dict[str, Dict[str, List[str]]]


GOLDEN_URLS: GoldenURLSet = {
    "amazon.com": {
        "in_stock_simple": [
            "https://www.amazon.com/dp/B0035CA96U",
        ],
        "in_stock_with_variants": [
            "https://www.amazon.com/dp/B0035CA96U",
        ],
        "out_of_stock": [
        ],
    },
    "walmart.com": {
        "in_stock_simple": [
            "https://www.walmart.com/ip/Flash-Furniture-Celestial-Metal-Lounge-Chair-in-Red-Set-of-2/3266991169",
        ],
        "in_stock_with_variants": [
            "https://www.walmart.com/ip/Flash-Furniture-Celestial-Metal-Lounge-Chair-in-Red-Set-of-2/3266991169",
        ],
        "out_of_stock": [
        ],
    },
    "target.com": {
        "in_stock_simple": [
            "https://www.target.com/p/-/A-88920975",
        ],
        "in_stock_with_variants": [
            "https://www.target.com/p/-/A-88920975",
        ],
        "out_of_stock": [
        ],
    },
    "wayfair.com": {
        "in_stock_simple": [
            "https://www.wayfair.com/furniture/pdp/martha-stewart-nyla-curved-nail-trim-headboard-platform-bed-large-storage-drawer-mstt6708.html?piid=125456159",
        ],
        "in_stock_with_variants": [
            "https://www.wayfair.com/furniture/pdp/martha-stewart-nyla-curved-nail-trim-headboard-platform-bed-large-storage-drawer-mstt6708.html?piid=125456159",
        ],
        "out_of_stock": [
        ],
    },
    "homedepot.com": {
        "in_stock_simple": [
            "https://www.homedepot.com/p/Carnegy-Avenue-Red-Steel-Outdoor-Lounge-Chair-Set-of-2-CGA-GM-520793-RE-HD/325539070",
        ],
        "in_stock_with_variants": [
            "https://www.homedepot.com/p/Carnegy-Avenue-Red-Steel-Outdoor-Lounge-Chair-Set-of-2-CGA-GM-520793-RE-HD/325539070",
        ],
        "out_of_stock": [
        ],
    },

    "kohls.com": {
        "in_stock_simple": [
            "https://www.kohls.com/product/prd-7859109/flash-furniture-small-refillable-bean-bag-chair-for-kids-and-teens.jsp?color=Green",
        ],
        "in_stock_with_variants": [
            "https://www.kohls.com/product/prd-7859109/flash-furniture-small-refillable-bean-bag-chair-for-kids-and-teens.jsp?color=Green",
        ],
        "out_of_stock": [],
    },
    "lowes.com": {
        "in_stock_simple": [
            "https://www.lowes.com/pd/Flash-Furniture-Omma-Swivel-Glider-Rocker-Recliner-Chair-Manual-360-Degree-Swivel-Wingback-Recliner-Perfect-for-Living-Room-Bedroom-or-Nursery-in-Cream/7722384",
        ],
        "in_stock_with_variants": [
            "https://www.lowes.com/pd/Flash-Furniture-Omma-Swivel-Glider-Rocker-Recliner-Chair-Manual-360-Degree-Swivel-Wingback-Recliner-Perfect-for-Living-Room-Bedroom-or-Nursery-in-Cream/7722384",
        ],
        "out_of_stock": [],
    },
    "officedepot.com": {
        "in_stock_simple": [
            "https://www.officedepot.com/a/products/638918/Flash-Furniture-Adjustable-Drawing-And-Drafting/",
        ],
        "in_stock_with_variants": [
            "https://www.officedepot.com/a/products/638918/Flash-Furniture-Adjustable-Drawing-And-Drafting/",
        ],
        "out_of_stock": [],
    },
    "overstock.com": {
        "in_stock_simple": [
            "https://www.overstock.com/Home-Garden/Martha-Stewart-Curved-Nail-Trim-Headboard-Platform-Bed-Large-Storage-Drawer/44048853/product.html",
        ],
        "in_stock_with_variants": [
            "https://www.overstock.com/Home-Garden/Martha-Stewart-Curved-Nail-Trim-Headboard-Platform-Bed-Large-Storage-Drawer/44048853/product.html",
        ],
        "out_of_stock": [],
    },
    "staples.com": {
        "in_stock_simple": [
            "https://www.staples.com/flash-furniture-hercules-series-fabric-accent-chair-black-xu60555bk/product_1983504",
        ],
        "in_stock_with_variants": [
            "https://www.staples.com/flash-furniture-hercules-series-fabric-accent-chair-black-xu60555bk/product_1983504",
        ],
        "out_of_stock": [],
    },
}


def iter_all_golden_urls() -> List[str]:
    urls: List[str] = []
    for domain, buckets in GOLDEN_URLS.items():
        _ = domain
        for _, lst in buckets.items():
            urls.extend(lst)
    # de-dupe preserving order
    seen = set()
    out: List[str] = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out

