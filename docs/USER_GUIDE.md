# 📖 User Guide - Ubique Product Checker

## Table of Contents
1. [Getting Started](#getting-started)
2. [Adding URLs](#adding-urls)
3. [Running Scans](#running-scans)
4. [Understanding Results](#understanding-results)
5. [Managing URLs](#managing-urls)
6. [Tips and Best Practices](#tips-and-best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Application

Once the system is running, open your web browser and navigate to:
```
http://localhost:3000
```

You'll see the main dashboard with four sections:
- **Statistics** - Overview of your URLs and scan results
- **Add URLs** - Input interface for new product URLs
- **Stored URLs** - List of all saved URLs
- **Scan Results** - Latest detection results

---

## Adding URLs

### Single URL Input

1. Click the **"Single URL"** tab
2. Enter a product page URL (e.g., `https://www.amazon.com/product-example`)
3. (Optional) Enter a **Group Name** to organize related products
4. Click **"Add URLs"**

**Example:**
```
URL: https://www.amazon.com/dp/B08N5WRWNW
Group: Electronics
```

### Bulk URL Import

For adding multiple URLs at once:

1. Click the **"Bulk Import"** tab
2. Paste URLs, **one per line**
3. (Optional) Enter a **Group Name** for all URLs
4. Click **"Add URLs"**

**Example:**
```
https://www.amazon.com/product1
https://www.walmart.com/product2
https://www.ebay.com/product3
https://www.target.com/product4
```

### Supported URL Formats

✅ **Valid URLs:**
- `https://www.amazon.com/product`
- `http://shop.example.com/item/123`
- `https://www.ebay.com/itm/12345`

❌ **Invalid URLs:**
- `www.amazon.com/product` (missing http://)
- `amazon.com/product` (missing protocol)
- Just text without URL format

---

## Running Scans

### Manual Scan

1. Add URLs to the system
2. Click the **"Run Scan"** button in the top-right corner
3. Wait for the scan to complete (typically 2-10 seconds per URL)
4. Results will appear in the **Scan Results** table

### What Happens During a Scan?

The system:
1. Fetches each product page
2. Analyzes the HTML content
3. Searches for "Add to Cart" and "Buy Now" buttons
4. Records the results
5. Displays findings in the results table

### Scan Status Indicators

While scanning:
- Button shows **"Scanning..."**
- A loading spinner appears
- Results update automatically when complete

---

## Understanding Results

### Results Table Columns

| Column | Description |
|--------|-------------|
| **URL** | The product page URL (clickable) |
| **Add to Cart** | ✅ Found / ❌ Not found |
| **Buy Now** | ✅ Found / ❌ Not found |
| **Status** | Overall availability status |
| **Response Time** | Time taken to scan (seconds) |
| **Scanned At** | Date and time of scan |

### Status Types

🟢 **Available**
- At least one buy button was detected
- Product is likely purchasable

🔴 **Unavailable**
- No buy buttons found
- Product may be out of stock or page structure changed

🟡 **Error**
- Scan failed due to timeout, network issue, or invalid page
- Check error message for details

### Button Detection

**Add to Cart Found (✅)**
- Green checkmark indicates button detected
- Product can likely be added to shopping cart

**Add to Cart Not Found (❌)**
- Gray X indicates button not detected
- May indicate out of stock or page issue

**Buy Now Found (✅)**
- Green checkmark indicates instant purchase option available

---

## Managing URLs

### Viewing Stored URLs

The **Stored URLs** section shows:
- All saved product URLs
- Group assignments
- Date added
- Quick actions

### Deleting URLs

To remove a single URL:
1. Find the URL in the **Stored URLs** table
2. Click the **trash icon** (🗑️) on the right
3. Confirm deletion

**Note:** Deleting a URL also removes its associated scan results.

### Organizing with Groups

Group names help organize related products:

**Examples:**
- `Electronics` - Tech products
- `Clothing` - Fashion items
- `Books` - Literature
- `Black Friday Deals` - Seasonal items
- `Competitor Analysis` - Business intel

---

## Tips and Best Practices

### For Best Results

✅ **Use Direct Product Pages**
- Link directly to product detail pages
- Avoid category or search result pages

✅ **Test with Known Products**
- Start with products you know are in stock
- Verify detection is working correctly

✅ **Run Regular Scans**
- Product availability changes frequently
- Scan daily or multiple times per day

✅ **Group Related URLs**
- Makes it easier to manage large numbers of URLs
- Helps with reporting and analysis

### Performance Tips

⚡ **Batch Your URLs**
- Add multiple URLs at once via bulk import
- More efficient than one-by-one

⚡ **Scan During Off-Peak Hours**
- Less likely to hit rate limits
- Websites may respond faster

⚡ **Monitor Response Times**
- Slow response times may indicate:
  - Website issues
  - Network problems
  - Need for timeout adjustment

### Detection Accuracy

The system works best with:
- Major e-commerce platforms (Amazon, Walmart, eBay, etc.)
- Standard shopping cart implementations
- English-language product pages

May have challenges with:
- Heavily customized shopping carts
- Non-standard button implementations
- JavaScript-heavy dynamic sites
- Region-specific sites

---

## Troubleshooting

### Common Issues

**Problem: URL Won't Add**
- ✅ Ensure URL starts with `http://` or `https://`
- ✅ Check for typos in URL
- ✅ Try pasting URL in browser first to verify it works

**Problem: All Scans Show "Error"**
- ✅ Check internet connection
- ✅ Verify websites are accessible
- ✅ Check backend logs for details
- ✅ Try increasing timeout in settings

**Problem: Buttons Not Detected**
- ✅ Verify product is actually in stock
- ✅ Check if website structure has changed
- ✅ Review detection rules configuration
- ✅ Try the URL in a regular browser

**Problem: Scan Takes Too Long**
- ✅ Some websites are naturally slow
- ✅ Check your internet speed
- ✅ Consider disabling Playwright for static sites
- ✅ Reduce concurrent scan limit

**Problem: Duplicate URLs**
- ✅ System automatically prevents duplicates
- ✅ You'll see "duplicate_count" in response
- ✅ Existing URLs won't be re-added

### Getting Help

If you encounter issues:

1. **Check the Statistics**
   - High error counts may indicate systematic issues

2. **Review Recent Scans**
   - Look for patterns in failures

3. **Check Backend Logs**
   ```cmd
   docker-compose logs backend
   ```

4. **Verify Configuration**
   - Review detection rules
   - Check timeout settings

5. **Test with Simple URL**
   - Try a well-known product page
   - Helps isolate the issue

---

## Advanced Features (Future)

🔜 **Scheduled Scans**
- Automatic daily/hourly scanning
- Set it and forget it

🔜 **Notifications**
- Email alerts when products become available
- Slack integration

🔜 **Historical Tracking**
- View availability trends over time
- Charts and graphs

🔜 **Export Results**
- Download as CSV or JSON
- Share with team

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + R` | Refresh data |
| `Enter` | Submit URL form |
| `Esc` | Clear notifications |

---

## FAQs

**Q: How many URLs can I add?**
A: No hard limit, but recommend staying under 1,000 for optimal performance.

**Q: How long does a scan take?**
A: Typically 2-10 seconds per URL, depending on website speed.

**Q: Can I scan international sites?**
A: Yes, but detection rules are optimized for English-language sites.

**Q: Does this work with all shopping websites?**
A: Works best with major e-commerce platforms. Custom sites may need rule adjustments.

**Q: Is my data stored securely?**
A: All data is stored in your local MongoDB instance. Nothing is sent to external servers.

**Q: Can I run this on a server?**
A: Yes! Follow the production deployment guide in SETUP.md.

---

## Support

Need help? 

📧 Contact development team
📚 Review technical documentation
🐛 Report bugs on GitHub
💡 Request features

---

**Happy Monitoring! 🛒✨**
