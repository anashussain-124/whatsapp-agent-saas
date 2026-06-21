#!/usr/bin/env python3
"""
Programmatic SEO Engine for WhatsApp Agent SaaS.
Generates hyper-local landing pages targeting Indian cities + industries.

Usage:
    python seo_engine.py --generate-all
    python seo_engine.py --city Mumbai --industry salon
    python seo_engine.py --list-cities
    python seo_engine.py --list-industries

Output:
    Generates static HTML files in ../landing/public/seo/
    Each file is a complete, self-contained landing page.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────────

CITIES = [
    # Tier 1
    {"name": "Mumbai", "state": "Maharashtra", "slug": "mumbai"},
    {"name": "Delhi", "state": "Delhi NCR", "slug": "delhi"},
    {"name": "Bangalore", "state": "Karnataka", "slug": "bangalore"},
    {"name": "Hyderabad", "state": "Telangana", "slug": "hyderabad"},
    {"name": "Chennai", "state": "Tamil Nadu", "slug": "chennai"},
    {"name": "Kolkata", "state": "West Bengal", "slug": "kolkata"},
    {"name": "Pune", "state": "Maharashtra", "slug": "pune"},
    {"name": "Ahmedabad", "state": "Gujarat", "slug": "ahmedabad"},
    # Tier 2
    {"name": "Jaipur", "state": "Rajasthan", "slug": "jaipur"},
    {"name": "Lucknow", "state": "Uttar Pradesh", "slug": "lucknow"},
    {"name": "Kanpur", "state": "Uttar Pradesh", "slug": "kanpur"},
    {"name": "Nagpur", "state": "Maharashtra", "slug": "nagpur"},
    {"name": "Indore", "state": "Madhya Pradesh", "slug": "indore"},
    {"name": "Bhopal", "state": "Madhya Pradesh", "slug": "bhopal"},
    {"name": "Patna", "state": "Bihar", "slug": "patna"},
    {"name": "Visakhapatnam", "state": "Andhra Pradesh", "slug": "visakhapatnam"},
    {"name": "Vadodara", "state": "Gujarat", "slug": "vadodara"},
    {"name": "Coimbatore", "state": "Tamil Nadu", "slug": "coimbatore"},
    {"name": "Kochi", "state": "Kerala", "slug": "kochi"},
    {"name": "Guwahati", "state": "Assam", "slug": "guwahati"},
]

INDUSTRIES = [
    {
        "name": "Salon",
        "slug": "salon",
        "keywords": ["beauty salon", "hair salon", "beauty parlor", "hair spa"],
        "services": ["Haircut", "Hair Color", "Facial", "Manicure", "Pedicure", "Hair Spa"],
        "price_range": "₹200 - ₹2,000",
    },
    {
        "name": "Clinic",
        "slug": "clinic",
        "keywords": ["medical clinic", "doctor clinic", "health clinic", "dental clinic"],
        "services": ["General Checkup", "Dental Cleaning", "Skin Consultation", "Eye Checkup", "Physiotherapy"],
        "price_range": "₹300 - ₹1,500",
    },
    {
        "name": "Tutor",
        "slug": "tutor",
        "keywords": ["home tutor", "private tutor", "coaching classes", "tuition center"],
        "services": ["Maths Tuition", "Science Tuition", "English Tuition", "Competitive Exam Prep", "Online Classes"],
        "price_range": "₹500 - ₹3,000/month",
    },
    {
        "name": "Repair Service",
        "slug": "repair",
        "keywords": ["repair service", "AC repair", "appliance repair", "mobile repair"],
        "services": ["AC Repair", "Washing Machine Repair", "Mobile Repair", "Laptop Repair", "Refrigerator Repair"],
        "price_range": "₹200 - ₹1,500",
    },
    {
        "name": "Restaurant",
        "slug": "restaurant",
        "keywords": ["restaurant", "cafe", "food court", "dining"],
        "services": ["Table Reservation", "Home Delivery", "Catering", "Private Dining"],
        "price_range": "₹200 - ₹2,000 per person",
    },
    {
        "name": "Retail Store",
        "slug": "retail",
        "keywords": ["retail store", "shop", "boutique", "kirana store"],
        "services": ["Product Inquiry", "Order Placing", "Delivery Scheduling", "Stock Check"],
        "price_range": "Varies",
    },
]

# ─── Page Templates ─────────────────────────────────────────────────

def generate_landing_page(city: dict, industry: dict) -> str:
    """Generate a complete SEO-optimized landing page for a city+industry combo."""
    city_name = city["name"]
    city_state = city["state"]
    industry_name = industry["name"]
    industry_slug = industry["slug"]
    city_slug = city["slug"]

    page_slug = f"{industry_slug}-{city_slug}"
    canonical_url = f"https://whatsapp-agent-saas.com/{page_slug}"

    title = f"WhatsApp Booking for {industry_name}s in {city_name} | AI Assistant"
    description = (
        f"Automate your {industry_name.lower()} in {city_name} with AI-powered WhatsApp booking. "
        f"Let customers book appointments, ask questions, and get support 24/7. "
        f"Perfect for {industry['keywords'][0]}s in {city_name}, {city_state}."
    )

    h1 = f"WhatsApp Booking Assistant for {industry_name}s in {city_name}"
    h2_features = f"Why {industry_name}s in {city_name} Love WhatsApp Agent"
    h2_how = f"How It Works for Your {industry_name} in {city_name}"
    h2_faq = f"FAQs — WhatsApp Automation for {industry_name}s in {city_name}"

    services_list = ", ".join(industry["services"][:4])
    keywords_list = ", ".join(industry["keywords"][:3])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="WhatsApp booking {city_name}, {keywords_list}, AI assistant {city_name}, {industry_name.lower()} automation India">
    <link rel="canonical" href="{canonical_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="en_IN">
    <meta name="robots" content="index, follow">
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "WhatsApp Agent for {industry_name}s",
        "description": "{description}",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "offers": {{
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "INR"
        }},
        "areaServed": {{
            "@type": "City",
            "name": "{city_name}",
            "containedInPlace": {{"@type": "State", "name": "{city_state}"}}
        }}
    }}
    </script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a1a; line-height: 1.6; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 0 20px; }}
        .hero {{ background: linear-gradient(135deg, #25D366 0%, #128C7E 100%); color: white; padding: 80px 0 60px; text-align: center; }}
        .hero h1 {{ font-size: 2.5rem; font-weight: 800; margin-bottom: 16px; }}
        .hero p {{ font-size: 1.2rem; opacity: 0.9; max-width: 600px; margin: 0 auto 32px; }}
        .cta-btn {{ display: inline-block; background: white; color: #128C7E; padding: 16px 40px; border-radius: 50px; font-weight: 700; text-decoration: none; font-size: 1.1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }}
        .section {{ padding: 60px 0; }}
        .section-alt {{ background: #f8f9fa; }}
        h2 {{ font-size: 2rem; font-weight: 700; margin-bottom: 24px; text-align: center; }}
        .features-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; margin-top: 40px; }}
        .feature-card {{ background: white; border-radius: 16px; padding: 32px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e5e7eb; }}
        .feature-card h3 {{ font-size: 1.2rem; margin-bottom: 8px; color: #128C7E; }}
        .feature-card p {{ color: #6b7280; font-size: 0.95rem; }}
        .steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 32px; margin-top: 40px; }}
        .step {{ text-align: center; }}
        .step-num {{ font-size: 3rem; font-weight: 800; color: #25D366; }}
        .step h3 {{ font-size: 1.1rem; margin: 8px 0; }}
        .step p {{ color: #6b7280; font-size: 0.9rem; }}
        .faq-item {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; border: 1px solid #e5e7eb; }}
        .faq-item h3 {{ font-size: 1.05rem; margin-bottom: 8px; }}
        .faq-item p {{ color: #6b7280; font-size: 0.95rem; }}
        .cta-section {{ background: #25D366; color: white; text-align: center; padding: 60px 0; }}
        .cta-section h2 {{ color: white; }}
        .cta-section .cta-btn {{ background: white; color: #128C7E; }}
        .footer {{ background: #1a1a1a; color: #9ca3af; text-align: center; padding: 32px 0; font-size: 0.85rem; }}
        .footer a {{ color: #25D366; text-decoration: none; }}
        .tag {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin: 4px; }}
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 1.8rem; }}
            h2 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <section class="hero">
        <div class="container">
            <div style="margin-bottom: 16px;">
                <span class="tag">{city_name}</span>
                <span class="tag">{industry_name}</span>
                <span class="tag">WhatsApp Automation</span>
            </div>
            <h1>{h1}</h1>
            <p>Let customers book appointments, ask about services, and get instant support — all through WhatsApp. No apps, no calls, no missed opportunities.</p>
            <a href="https://whatsapp-agent-saas.com/#pricing" class="cta-btn">Start Free Trial →</a>
            <p style="margin-top: 16px; font-size: 0.9rem; opacity: 0.8;">50 free conversations • No credit card • Setup in 5 min</p>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <h2>{h2_features}</h2>
            <p style="text-align: center; color: #6b7280; max-width: 600px; margin: 0 auto 0;">
                Whether you run a {industry['keywords'][0]} or a {industry['keywords'][1]} in {city_name},
                WhatsApp Agent helps you automate customer interactions and grow your business.
            </p>
            <div class="features-grid">
                <div class="feature-card">
                    <h3>📅 24/7 Appointment Booking</h3>
                    <p>Customers book appointments anytime — even at 2 AM. AI handles the entire flow: service selection, date, time, and confirmation.</p>
                </div>
                <div class="feature-card">
                    <h3>💬 Instant Query Resolution</h3>
                    <p>Answer questions about services ({services_list}), pricing ({industry['price_range']}), hours, and location — instantly.</p>
                </div>
                <div class="feature-card">
                    <h3>🔔 Smart Reminders</h3>
                    <p>Automatic WhatsApp reminders reduce no-shows by up to 40%. Customers get notified before their appointment.</p>
                </div>
                <div class="feature-card">
                    <h3>📊 Business Insights</h3>
                    <p>Get daily reports on bookings, popular services, and customer trends — delivered right to your WhatsApp.</p>
                </div>
                <div class="feature-card">
                    <h3>🌐 Multi-Language Support</h3>
                    <p>Communicate in Hindi, English, or any language your customers prefer. Perfect for {city_name}'s diverse population.</p>
                </div>
                <div class="feature-card">
                    <h3>💰 Zero App Download</h3>
                    <p>Works entirely within WhatsApp. Your customers already use it. No new app to install, no learning curve.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="section section-alt">
        <div class="container">
            <h2>{h2_how}</h2>
            <div class="steps">
                <div class="step">
                    <div class="step-num">1</div>
                    <h3>Connect WhatsApp</h3>
                    <p>Link your WhatsApp Business number in 2 minutes. No coding needed.</p>
                </div>
                <div class="step">
                    <div class="step-num">2</div>
                    <h3>Add Your Services</h3>
                    <p>List your services — {services_list} — with prices and availability.</p>
                </div>
                <div class="step">
                    <div class="step-num">3</div>
                    <h3>Go Live</h3>
                    <p>Customers start chatting. AI handles bookings and queries 24/7.</p>
                </div>
                <div class="step">
                    <div class="step-num">4</div>
                    <h3>Grow</h3>
                    <p>Track bookings, analyze trends, and make smarter business decisions.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <h2>What {industry_name}s in {city_name} Are Saying</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <p style="font-style: italic; color: #374151;">"My customers love booking on WhatsApp. I used to miss calls all the time. Now the AI handles everything."</p>
                    <p style="margin-top: 12px; font-weight: 600; color: #128C7E;">— {industry_name} Owner, {city_name}</p>
                </div>
                <div class="feature-card">
                    <p style="font-style: italic; color: #374151;">"Setup took 10 minutes. I get bookings at midnight, early morning — anytime. My no-shows dropped by 35%."</p>
                    <p style="margin-top: 12px; font-weight: 600; color: #128C7E;">— {industry_name} Owner, {city_name}</p>
                </div>
                <div class="feature-card">
                    <p style="font-style: italic; color: #374151;">"Parents ask about fees and timings. The bot answers instantly. I get fewer calls and more enrollments."</p>
                    <p style="margin-top: 12px; font-weight: 600; color: #128C7E;">— {industry_name} Owner, {city_name}</p>
                </div>
            </div>
        </div>
    </section>

    <section class="section section-alt">
        <div class="container">
            <h2>{h2_faq}</h2>
            <div class="faq-item">
                <h3>How does WhatsApp booking work for my {industry_name.lower()} in {city_name}?</h3>
                <p>Customers message your WhatsApp number. The AI assistant asks what service they need, shows available slots, and confirms the booking — all in a natural chat flow. No apps to download.</p>
            </div>
            <div class="faq-item">
                <h3>What services can I list? (e.g., {services_list})</h3>
                <p>You can list any services your {industry_name.lower()} offers. Common ones include {services_list}. Each service can have a price, duration, and description.</p>
            </div>
            <div class="faq-item">
                <h3>What's the price range for {industry_name.lower()}s in {city_name}?</h3>
                <p>Typical pricing for {industry_name.lower()}s in {city_name} ranges from {industry['price_range']}. You set your own prices and the AI shares them with customers instantly.</p>
            </div>
            <div class="faq-item">
                <h3>Is there a free plan?</h3>
                <p>Yes! You get 50 free conversations per month. No credit card required. Upgrade to Pro (₹999/mo) for unlimited conversations and advanced features.</p>
            </div>
            <div class="faq-item">
                <h3>Can customers chat in Hindi?</h3>
                <p>Absolutely. The AI supports Hindi, English, and many other languages. Customers can chat in whichever language they're comfortable with.</p>
            </div>
            <div class="faq-item">
                <h3>How is this different from a regular WhatsApp chatbot?</h3>
                <p>Traditional chatbots follow rigid scripts. Our AI agent understands natural language, handles multi-turn conversations, and makes intelligent decisions — just like a human receptionist would.</p>
            </div>
        </div>
    </section>

    <section class="cta-section">
        <div class="container">
            <h2>Ready to Automate Your {industry_name} in {city_name}?</h2>
            <p style="opacity: 0.9; margin-bottom: 24px;">Start with 50 free conversations. No credit card. No commitment.</p>
            <a href="https://whatsapp-agent-saas.com/#pricing" class="cta-btn">Get Started Free →</a>
        </div>
    </section>

    <footer class="footer">
        <div class="container">
            <p>© 2026 WhatsApp Agent SaaS. All rights reserved.</p>
            <p style="margin-top: 8px;">
                <a href="https://whatsapp-agent-saas.com/">Home</a> |
                <a href="https://whatsapp-agent-saas.com/#features">Features</a> |
                <a href="https://whatsapp-agent-saas.com/#pricing">Pricing</a> |
                <a href="https://whatsapp-agent-saas.com/privacy">Privacy</a>
            </p>
            <p style="margin-top: 8px; font-size: 0.75rem;">
                WhatsApp Agent serves {industry_name.lower()}s in {city_name}, {city_state} and across India.
            </p>
        </div>
    </footer>
</body>
</html>"""

    return html


def generate_sitemap(pages: list[dict]) -> str:
    """Generate XML sitemap for all SEO pages."""
    urls = []
    for page in pages:
        urls.append(
            f"  <url>\n"
            f"    <loc>https://whatsapp-agent-saas.com/{page['slug']}</loc>\n"
            f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.8</priority>\n"
            f"  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )


def generate_internal_linking_index(pages: list[dict]) -> str:
    """Generate an HTML index page with internal links to all SEO pages."""
    links = []
    # Group by industry
    by_industry = {}
    for page in pages:
        ind = page["industry"]
        by_industry.setdefault(ind, []).append(page)

    for industry, industry_pages in sorted(by_industry.items()):
        links.append(f'<h2>WhatsApp Automation for {industry}s</h2>\n<ul>')
        for page in industry_pages:
            links.append(
                f'<li><a href="/{page["slug"]}">'
                f'WhatsApp Booking for {industry}s in {page["city"]}</a></li>'
            )
        links.append("</ul>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>WhatsApp Business Automation Directory | All Cities & Industries</title>
    <meta name="robots" content="index, follow">
    <style>
        body {{ font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
        h1 {{ color: #128C7E; }}
        h2 {{ color: #25D366; margin-top: 32px; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        a {{ color: #128C7E; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>WhatsApp Business Automation Directory</h1>
    <p>AI-powered WhatsApp booking and customer support for local businesses across India.</p>
    {chr(10).join(links)}
</body>
</html>"""


# ─── Main Generator ─────────────────────────────────────────────────

def generate_all(output_dir: str = None):
    """Generate all SEO pages.
    
    TASK 7: This is behind a feature flag. Call explicitly with --generate-all.
    Do NOT run by default during deployment — deferred until post-3-paying-customers.
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "landing", "public", "seo")

    os.makedirs(output_dir, exist_ok=True)

    pages = []
    total = len(CITIES) * len(INDUSTRIES)
    count = 0

    print(f"Generating {total} SEO pages ({len(CITIES)} cities × {len(INDUSTRIES)} industries)...")

    for city in CITIES:
        for industry in INDUSTRIES:
            slug = f"{industry['slug']}-{city['slug']}"
            html = generate_landing_page(city, industry)

            filepath = os.path.join(output_dir, f"{slug}.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            pages.append({
                "slug": slug,
                "city": city["name"],
                "industry": industry["name"],
            })
            count += 1
            if count % 10 == 0:
                print(f"  Generated {count}/{total} pages...")

    # Generate sitemap
    sitemap = generate_sitemap(pages)
    with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # Generate internal linking index
    index = generate_internal_linking_index(pages)
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index)

    print(f"\n✅ Done! Generated {count} pages + sitemap + index in {output_dir}")
    print(f"   Total files: {count + 2}")
    return pages


# ─── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Programmatic SEO Engine")
    parser.add_argument("--generate-all", action="store_true", help="Generate all city+industry pages")
    parser.add_argument("--city", type=str, help="Generate for specific city slug (e.g., mumbai)")
    parser.add_argument("--industry", type=str, help="Generate for specific industry slug (e.g., salon)")
    parser.add_argument("--list-cities", action="store_true", help="List all cities")
    parser.add_argument("--list-industries", action="store_true", help="List all industries")
    parser.add_argument("--output-dir", type=str, help="Output directory")

    args = parser.parse_args()

    if args.list_cities:
        for c in CITIES:
            print(f"  {c['name']} ({c['state']}) — slug: {c['slug']}")

    elif args.list_industries:
        for i in INDUSTRIES:
            print(f"  {i['name']} — slug: {i['slug']} — keywords: {', '.join(i['keywords'][:2])}")

    elif args.generate_all:
        generate_all(args.output_dir)

    elif args.city and args.industry:
        city = next((c for c in CITIES if c["slug"] == args.city), None)
        industry = next((i for i in INDUSTRIES if i["slug"] == args.industry), None)
        if city and industry:
            html = generate_landing_page(city, industry)
            out = args.output_dir or "."
            os.makedirs(out, exist_ok=True)
            filepath = os.path.join(out, f"{args.industry}-{args.city}.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Generated: {filepath}")
        else:
            print("City or industry not found. Use --list-cities / --list-industries to see options.")

    else:
        parser.print_help()
