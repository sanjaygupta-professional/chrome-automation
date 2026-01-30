"""
Chrome Browser Automation with Playwright
==========================================
Comprehensive examples for browser automation tasks including:
- Web scraping
- Form filling
- Clicking and navigation
- Waiting strategies
- Data extraction
"""

import json
import csv
import time
from dataclasses import dataclass
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser, ElementHandle


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ScrapedProduct:
    """Represents a scraped product from an e-commerce site."""
    name: str
    price: str
    rating: Optional[str] = None
    url: Optional[str] = None


@dataclass
class FormField:
    """Represents a form field to fill."""
    selector: str
    value: str
    field_type: str = "text"  # text, select, checkbox, radio


# =============================================================================
# WEB SCRAPING EXAMPLES
# =============================================================================

def scrape_table_data(page: Page, table_selector: str) -> list[dict]:
    """
    Scrape data from an HTML table.

    Args:
        page: Playwright page object
        table_selector: CSS selector for the table

    Returns:
        List of dicts, each representing a row with column headers as keys
    """
    # Get header cells
    headers = page.query_selector_all(f"{table_selector} thead th")
    header_names = [h.inner_text().strip() for h in headers]

    # Get data rows
    rows = page.query_selector_all(f"{table_selector} tbody tr")
    data = []

    for row in rows:
        cells = row.query_selector_all("td")
        row_data = {}
        for i, cell in enumerate(cells):
            if i < len(header_names):
                row_data[header_names[i]] = cell.inner_text().strip()
        data.append(row_data)

    return data


def scrape_product_listings(page: Page, container_selector: str) -> list[ScrapedProduct]:
    """
    Scrape product listings from an e-commerce page.

    This works with common patterns like Amazon, eBay, etc.

    Args:
        page: Playwright page object
        container_selector: CSS selector for product containers

    Returns:
        List of ScrapedProduct objects
    """
    products = []
    items = page.query_selector_all(container_selector)

    for item in items:
        # Flexible selectors that work across many sites
        name_el = item.query_selector("h2, h3, .product-title, .item-title, [data-testid='title']")
        price_el = item.query_selector(".price, .product-price, [data-testid='price'], span:has-text('$')")
        rating_el = item.query_selector(".rating, .stars, [aria-label*='rating']")
        link_el = item.query_selector("a[href]")

        if name_el and price_el:
            products.append(ScrapedProduct(
                name=name_el.inner_text().strip(),
                price=price_el.inner_text().strip(),
                rating=rating_el.inner_text().strip() if rating_el else None,
                url=link_el.get_attribute("href") if link_el else None
            ))

    return products


def scrape_with_pagination(page: Page, item_selector: str, next_button_selector: str,
                           max_pages: int = 5) -> list[str]:
    """
    Scrape items across multiple pages.

    Args:
        page: Playwright page object
        item_selector: CSS selector for items to scrape
        next_button_selector: CSS selector for the "next" button
        max_pages: Maximum number of pages to scrape

    Returns:
        List of scraped item texts
    """
    all_items = []

    for page_num in range(max_pages):
        print(f"Scraping page {page_num + 1}...")

        # Wait for items to load
        page.wait_for_selector(item_selector)

        # Scrape current page
        items = page.query_selector_all(item_selector)
        all_items.extend([item.inner_text().strip() for item in items])

        # Try to go to next page
        next_button = page.query_selector(next_button_selector)
        if next_button and next_button.is_visible() and next_button.is_enabled():
            next_button.click()
            page.wait_for_load_state("networkidle")
        else:
            print("No more pages")
            break

    return all_items


def extract_structured_data(page: Page) -> dict:
    """
    Extract JSON-LD structured data from a page (common for SEO).

    Many sites include structured data for products, articles, etc.

    Returns:
        Parsed JSON-LD data or empty dict
    """
    scripts = page.query_selector_all('script[type="application/ld+json"]')

    for script in scripts:
        try:
            content = script.inner_text()
            return json.loads(content)
        except json.JSONDecodeError:
            continue

    return {}


# =============================================================================
# FORM FILLING EXAMPLES
# =============================================================================

def fill_text_field(page: Page, selector: str, value: str, clear_first: bool = True):
    """Fill a text input field."""
    if clear_first:
        page.fill(selector, "")  # Clear existing content
    page.fill(selector, value)


def fill_select_dropdown(page: Page, selector: str, value: str):
    """Select an option from a dropdown by value or label."""
    page.select_option(selector, value)


def fill_checkbox(page: Page, selector: str, should_check: bool = True):
    """Check or uncheck a checkbox."""
    checkbox = page.locator(selector)
    is_checked = checkbox.is_checked()

    if should_check and not is_checked:
        checkbox.check()
    elif not should_check and is_checked:
        checkbox.uncheck()


def fill_radio_button(page: Page, selector: str):
    """Select a radio button."""
    page.check(selector)


def fill_complex_form(page: Page, fields: list[FormField]):
    """
    Fill a form with multiple field types.

    Args:
        page: Playwright page object
        fields: List of FormField objects describing each field
    """
    for field in fields:
        if field.field_type == "text":
            fill_text_field(page, field.selector, field.value)
        elif field.field_type == "select":
            fill_select_dropdown(page, field.selector, field.value)
        elif field.field_type == "checkbox":
            fill_checkbox(page, field.selector, field.value.lower() == "true")
        elif field.field_type == "radio":
            fill_radio_button(page, field.selector)


def fill_login_form(page: Page, username: str, password: str,
                    username_selector: str = "#username, #email, input[name='email'], input[type='email']",
                    password_selector: str = "#password, input[name='password'], input[type='password']",
                    submit_selector: str = "button[type='submit'], input[type='submit']"):
    """
    Fill and submit a login form with common selector patterns.

    Args:
        page: Playwright page object
        username: Username or email
        password: Password
        username_selector: CSS selector for username field
        password_selector: CSS selector for password field
        submit_selector: CSS selector for submit button
    """
    page.fill(username_selector, username)
    page.fill(password_selector, password)
    page.click(submit_selector)
    page.wait_for_load_state("networkidle")


# =============================================================================
# CLICKING AND NAVIGATION
# =============================================================================

def click_and_wait(page: Page, selector: str, wait_for: str = "networkidle"):
    """
    Click an element and wait for page to settle.

    Args:
        page: Playwright page object
        selector: CSS selector for element to click
        wait_for: What to wait for - "networkidle", "load", "domcontentloaded"
    """
    page.click(selector)
    page.wait_for_load_state(wait_for)


def click_with_navigation(page: Page, selector: str) -> str:
    """
    Click a link and wait for navigation to complete.

    Returns:
        The new URL after navigation
    """
    with page.expect_navigation():
        page.click(selector)
    return page.url


def hover_and_click(page: Page, hover_selector: str, click_selector: str):
    """
    Hover over one element to reveal another, then click.

    Common for dropdown menus.
    """
    page.hover(hover_selector)
    page.wait_for_selector(click_selector, state="visible")
    page.click(click_selector)


def scroll_and_click(page: Page, selector: str):
    """Scroll element into view before clicking."""
    element = page.locator(selector)
    element.scroll_into_view_if_needed()
    element.click()


def right_click_context_menu(page: Page, selector: str, menu_item_text: str):
    """Right-click to open context menu and select an item."""
    page.click(selector, button="right")
    page.click(f"text={menu_item_text}")


def double_click(page: Page, selector: str):
    """Double-click an element."""
    page.dblclick(selector)


def drag_and_drop(page: Page, source_selector: str, target_selector: str):
    """Drag an element from source to target."""
    page.drag_and_drop(source_selector, target_selector)


# =============================================================================
# WAITING STRATEGIES
# =============================================================================

def wait_for_element(page: Page, selector: str, timeout: int = 30000) -> ElementHandle:
    """
    Wait for an element to appear in the DOM.

    Args:
        page: Playwright page object
        selector: CSS selector
        timeout: Maximum wait time in milliseconds

    Returns:
        The element handle
    """
    return page.wait_for_selector(selector, timeout=timeout)


def wait_for_element_visible(page: Page, selector: str, timeout: int = 30000):
    """Wait for element to be visible (not just in DOM)."""
    page.wait_for_selector(selector, state="visible", timeout=timeout)


def wait_for_element_hidden(page: Page, selector: str, timeout: int = 30000):
    """Wait for element to disappear (useful for loading spinners)."""
    page.wait_for_selector(selector, state="hidden", timeout=timeout)


def wait_for_text(page: Page, text: str, timeout: int = 30000):
    """Wait for specific text to appear on the page."""
    page.wait_for_selector(f"text={text}", timeout=timeout)


def wait_for_url_change(page: Page, url_pattern: str, timeout: int = 30000):
    """Wait for URL to match a pattern."""
    page.wait_for_url(url_pattern, timeout=timeout)


def wait_for_network_idle(page: Page, timeout: int = 30000):
    """Wait for all network requests to complete."""
    page.wait_for_load_state("networkidle", timeout=timeout)


def wait_for_api_response(page: Page, url_pattern: str):
    """
    Wait for a specific API call to complete.

    Useful for SPAs that load data via AJAX.
    """
    with page.expect_response(lambda r: url_pattern in r.url) as response_info:
        pass  # The actual action that triggers the API call happens here
    return response_info.value


def custom_wait_condition(page: Page, condition_fn, timeout: int = 30000, poll_interval: int = 100):
    """
    Wait for a custom condition to be true.

    Args:
        page: Playwright page object
        condition_fn: Function that takes page and returns bool
        timeout: Maximum wait time in ms
        poll_interval: How often to check in ms
    """
    start = time.time() * 1000
    while (time.time() * 1000) - start < timeout:
        if condition_fn(page):
            return True
        time.sleep(poll_interval / 1000)
    raise TimeoutError(f"Condition not met within {timeout}ms")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def take_screenshot(page: Page, url: str, filename: str) -> str:
    """Navigate to URL and take a screenshot."""
    page.goto(url)
    page.wait_for_load_state("networkidle")
    screenshot_path = f"{filename}.png"
    page.screenshot(path=screenshot_path, full_page=True)
    return screenshot_path


def save_to_csv(data: list[dict], filename: str):
    """Save scraped data to CSV file."""
    if not data:
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def save_to_json(data, filename: str):
    """Save data to JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_all_links(page: Page) -> list[dict]:
    """Extract all links from the current page."""
    links = page.query_selector_all("a[href]")
    return [
        {"text": link.inner_text().strip(), "href": link.get_attribute("href")}
        for link in links
        if link.get_attribute("href")
    ]


def get_page_text(page: Page) -> str:
    """Get all visible text from the page."""
    return page.inner_text("body")


def execute_javascript(page: Page, script: str):
    """Execute JavaScript in the browser context."""
    return page.evaluate(script)


def intercept_requests(page: Page, url_pattern: str, handler):
    """
    Intercept and modify network requests.

    Args:
        page: Playwright page object
        url_pattern: URL pattern to match
        handler: Function to handle the route
    """
    page.route(url_pattern, handler)


# =============================================================================
# RETRY LOGIC
# =============================================================================

def should_retry_on_error(error_message: str, attempt: int, max_attempts: int) -> bool:
    """
    Determine whether to retry an operation after an error.

    TODO: Implement your retry logic here!

    Consider:
    - Which errors are transient (network timeouts) vs permanent (404)?
    - Should you use exponential backoff?

    Args:
        error_message: The error message from the failed operation
        attempt: Current attempt number (1-indexed)
        max_attempts: Maximum allowed attempts

    Returns:
        True if should retry, False otherwise
    """
    # YOUR IMPLEMENTATION HERE (5-10 lines)
    # Hint: Check for keywords like "timeout", "network", "connection"
    # vs permanent errors like "404", "not found", "forbidden"
    pass


def run_with_retry(func, *args, max_attempts: int = 3, **kwargs):
    """Execute a function with retry logic."""
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if should_retry_on_error(error_msg, attempt, max_attempts):
                print(f"Attempt {attempt} failed: {error_msg}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise


# =============================================================================
# BROWSER SETUP HELPERS
# =============================================================================

def create_browser_context(browser: Browser,
                           viewport_width: int = 1280,
                           viewport_height: int = 720,
                           user_agent: str = None,
                           locale: str = "en-US"):
    """
    Create a configured browser context.

    Args:
        browser: Playwright browser object
        viewport_width: Browser window width
        viewport_height: Browser window height
        user_agent: Custom user agent string
        locale: Browser locale
    """
    return browser.new_context(
        viewport={"width": viewport_width, "height": viewport_height},
        user_agent=user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        locale=locale
    )


def setup_request_logging(page: Page):
    """Log all network requests (useful for debugging)."""
    page.on("request", lambda req: print(f">> {req.method} {req.url}"))
    page.on("response", lambda res: print(f"<< {res.status} {res.url}"))


# =============================================================================
# MAIN DEMO
# =============================================================================

def demo_scraping(page: Page):
    """Demonstrate scraping capabilities."""
    print("\n" + "="*50)
    print("SCRAPING DEMO: Hacker News")
    print("="*50)

    page.goto("https://news.ycombinator.com")
    page.wait_for_load_state("networkidle")

    # Scrape article titles and links
    items = page.query_selector_all(".titleline > a")
    articles = []
    for item in items[:10]:
        articles.append({
            "title": item.inner_text(),
            "url": item.get_attribute("href")
        })

    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title'][:60]}...")

    return articles


def demo_form_filling(page: Page):
    """Demonstrate form filling capabilities."""
    print("\n" + "="*50)
    print("FORM DEMO: DuckDuckGo Search")
    print("="*50)

    page.goto("https://duckduckgo.com")

    # Fill search box
    fill_text_field(page, 'input[name="q"]', "Playwright Python automation")

    # Submit form
    page.press('input[name="q"]', "Enter")
    page.wait_for_load_state("networkidle")

    print(f"Searched! Current URL: {page.url}")
    return page.url


def demo_navigation(page: Page):
    """Demonstrate navigation capabilities."""
    print("\n" + "="*50)
    print("NAVIGATION DEMO: Wikipedia")
    print("="*50)

    page.goto("https://en.wikipedia.org")

    # Click on a link
    print("Clicking 'About Wikipedia' link...")
    click_and_wait(page, 'a:has-text("About Wikipedia")')

    print(f"Navigated to: {page.title()}")
    return page.url


def main():
    """Main entry point demonstrating browser automation."""

    print("="*50)
    print("Chrome Browser Automation Demo")
    print("="*50)

    with sync_playwright() as p:
        # Launch browser in headless mode for reliability
        browser = p.chromium.launch(headless=True)

        # Create browser context
        context = create_browser_context(browser)
        page = context.new_page()

        # Run demos
        try:
            articles = demo_scraping(page)
            save_to_json(articles, "scraped_articles.json")
            print("\nSaved to: scraped_articles.json")

            demo_form_filling(page)
            demo_navigation(page)

            print("\n" + "="*50)
            print("All demos completed successfully!")
            print("="*50)

        except Exception as e:
            print(f"\nError: {e}")
            page.screenshot(path="error_screenshot.png")
            print("Error screenshot saved to: error_screenshot.png")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
