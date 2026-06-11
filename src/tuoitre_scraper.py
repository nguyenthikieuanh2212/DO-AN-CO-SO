import json
import random
import re
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://tuoitre.vn"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

RAW_DIR = Path(r"D:\Do An Co So\GOM CUM VAN BAN TIENG VIET\data\raw\tuoitre")
PROGRESS_JSON = Path(r"D:\Do An Co So\GOM CUM VAN BAN TIENG VIET\data\meta\tuoitre_progress.json")

USE_HEADLESS = True

DEFAULT_TARGET_LINKS = 900
MAX_NO_NEW_ROUNDS = 10

SLEEP_AFTER_OPEN_CATEGORY = 5
SLEEP_AFTER_SCROLL = 3
SLEEP_AFTER_CLICK_VIEW_MORE = 4
SLEEP_BETWEEN_ARTICLES_MIN = 0.8
SLEEP_BETWEEN_ARTICLES_MAX = 1.8

CATEGORY_CONFIG = {
    "the_thao": {
        "display_name": "Thể thao",
        "url": "https://tuoitre.vn/the-thao.htm",
    },
    "cong_nghe": {
        "display_name": "Công nghệ",
        "url": "https://tuoitre.vn/cong-nghe.htm",
    },
    "giao_duc": {
        "display_name": "Giáo dục",
        "url": "https://tuoitre.vn/giao-duc.htm",
    },
    "suc_khoe": {
        "display_name": "Sức khỏe",
        "url": "https://tuoitre.vn/suc-khoe.htm",
    },
    "du_lich": {
        "display_name": "Du lịch",
        "url": "https://tuoitre.vn/du-lich.htm",
    },
    "xe": {
        "display_name": "Xe",
        "url": "https://tuoitre.vn/xe.htm",
    },
}

# Số lượng bài báo mục tiêu theo từng chuyên mục để kiểm soát quy mô dữ liệu thu thập
CATEGORY_TARGETS = {
    "the_thao": 2000,
    "cong_nghe": 2000,
    "giao_duc": 2000,
    "suc_khoe": 2000,
    "du_lich": 2000,
    "xe": 2000,
}

NOISE_PATTERNS = [
    r"^xem thêm\b",
    r"^xem thêm tại đây\b",
    r"^tin liên quan\b",
    r"^mời bạn đọc\b",
    r"^mời quý độc giả\b",
    r"^độc giả có thể\b",
    r"^tuổi trẻ online\b",
    r"^tto\b",
    r"^ảnh:\b",
    r"^video:\b",
    r"^đồ họa:\b",
    r"^infographic:\b",
    r"^nguồn:\b",
    r"^xem video\b",
    r"^xem trực tiếp\b",
    r"^mọi hình thức sao chép\b",
    r"^bản quyền thuộc về\b",
    r"^vui lòng ghi rõ nguồn\b",
    r"^hotline\b",
    r"^đặt báo\b",
    r"^quảng cáo\b",
]

NOISE_REGEXES = [re.compile(pattern, flags=re.IGNORECASE) for pattern in NOISE_PATTERNS]


def ensure_directories() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_JSON.parent.mkdir(parents=True, exist_ok=True)


def get_csv_path(category_clean: str) -> Path:
    return RAW_DIR / f"{category_clean}.csv"


def get_target_for_category(category_clean: str) -> int:
    return CATEGORY_TARGETS.get(category_clean, DEFAULT_TARGET_LINKS)


def clean_spaces(text: Optional[str]) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_text_for_compare(text: Optional[str]) -> str:
    text = clean_spaces(text).lower()
    text = re.sub(
        r"[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
        " ",
        text,
    )
    return clean_spaces(text)


def build_driver():
    options = webdriver.ChromeOptions()

    if USE_HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=vi-VN")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--blink-settings=imagesEnabled=false")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_page_load_timeout(90)
    return driver


def is_valid_article_url(url: str) -> bool:
    if not url:
        return False

    if not url.startswith(BASE_URL):
        return False

    if not url.endswith(".htm"):
        return False

    blocked_keywords = [
        "/video.htm",
        "/podcast.htm",
        "/tim-kiem.htm",
        "/chu-de.htm",
        "/photo.htm",
        "/multimedia.htm",
        "/magazine.htm",
        "/infographic.htm",
    ]

    if any(keyword in url for keyword in blocked_keywords):
        return False

    return bool(re.search(r"-\d{8,}\.htm$", url))


def load_existing_urls(csv_path: Path) -> set[str]:
    if not csv_path.exists():
        return set()

    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        if "url" not in df.columns:
            return set()
        return set(df["url"].dropna().astype(str).tolist())
    except Exception as exc:
        print(f"[CẢNH BÁO] Không đọc được file cũ {csv_path.name}: {exc}")
        return set()


def count_existing_articles(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0

    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        return len(df)
    except Exception:
        return 0


def append_article_to_csv(article_data: dict, csv_path: Path) -> None:
    file_exists = csv_path.exists()
    df = pd.DataFrame([article_data])

    df.to_csv(
        csv_path,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig",
    )


def load_progress(progress_path: Path) -> dict:
    default_progress = {
        "category_indices": {category: 0 for category in CATEGORY_CONFIG.keys()},
        "category_links": {category: [] for category in CATEGORY_CONFIG.keys()},
        "done_categories": [],
    }

    if not progress_path.exists():
        return default_progress

    try:
        with open(progress_path, "r", encoding="utf-8") as file:
            progress = json.load(file)

        if "category_indices" not in progress:
            progress["category_indices"] = default_progress["category_indices"]

        if "category_links" not in progress:
            progress["category_links"] = default_progress["category_links"]

        if "done_categories" not in progress:
            progress["done_categories"] = []

        for category in CATEGORY_CONFIG.keys():
            progress["category_indices"].setdefault(category, 0)
            progress["category_links"].setdefault(category, [])

        return progress

    except Exception:
        return default_progress


def save_progress(progress: dict, progress_path: Path) -> None:
    with open(progress_path, "w", encoding="utf-8") as file:
        json.dump(progress, file, ensure_ascii=False, indent=2)


def deduplicate_links(links: list[str]) -> list[str]:
    seen = set()
    deduped = []

    for link in links:
        if link not in seen:
            seen.add(link)
            deduped.append(link)

    return deduped


def open_category_with_retry(driver, category_url: str, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            driver.get(category_url)
            time.sleep(SLEEP_AFTER_OPEN_CATEGORY)
            return True
        except Exception as exc:
            print(f"Lỗi load trang lần {attempt + 1}: {category_url} -> {exc}")
            time.sleep(5)

    return False


def try_click_view_more(driver) -> bool:
    xpaths = [
        "//a[contains(normalize-space(.), 'Xem thêm')]",
        "//button[contains(normalize-space(.), 'Xem thêm')]",
        "//*[contains(normalize-space(.), 'Xem thêm')]",
    ]

    for xpath in xpaths:
        try:
            buttons = driver.find_elements(By.XPATH, xpath)
            for button in buttons:
                if button.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", button)
                    print("Đã click nút Xem thêm")
                    time.sleep(SLEEP_AFTER_CLICK_VIEW_MORE)
                    return True
        except Exception:
            continue

    return False


def get_links_selenium(
    category_url: str,
    target: int,
    cached_links: Optional[list[str]] = None,
) -> list[str]:
    links = deduplicate_links(cached_links or [])
    seen = set(links)

    if len(links) >= target:
        return links[:target]

    driver = build_driver()

    if not open_category_with_retry(driver, category_url, retries=3):
        print(f"Bỏ qua chuyên mục vì load thất bại: {category_url}")
        driver.quit()
        return links

    old_count = len(links)
    no_new_rounds = 0

    while len(links) < target:
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SLEEP_AFTER_SCROLL)
        except Exception as exc:
            print(f"Lỗi cuộn trang: {category_url} -> {exc}")
            break

        elements = driver.find_elements(By.CSS_SELECTOR, "a[href$='.htm']")

        for element in elements:
            try:
                href = element.get_attribute("href")
                if is_valid_article_url(href) and href not in seen:
                    seen.add(href)
                    links.append(href)

                    if len(links) >= target:
                        break
            except Exception:
                continue

        print(f"Đã lấy: {len(links)}/{target} link")

        if len(links) >= target:
            break

        if len(links) == old_count:
            no_new_rounds += 1
        else:
            no_new_rounds = 0

        print(f"no_new_rounds = {no_new_rounds}")
        old_count = len(links)

        if no_new_rounds >= MAX_NO_NEW_ROUNDS:
            print("Không có link mới sau nhiều lần cuộn/bấm. Dừng chuyên mục này.")
            break

        clicked = try_click_view_more(driver)

        if not clicked:
            try:
                driver.execute_script("window.scrollBy(0, -1000);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SLEEP_AFTER_SCROLL + 1)
            except Exception:
                pass

    driver.quit()
    return deduplicate_links(links)


def extract_title(soup: BeautifulSoup) -> str:
    selectors = [
        "h1.detail-title",
        "h1.article-title",
        "h1",
    ]

    for selector in selectors:
        tag = soup.select_one(selector)
        if tag:
            return clean_spaces(tag.get_text(" ", strip=True))

    return ""


def extract_description(soup: BeautifulSoup) -> str:
    selectors = [
        "h2.detail-sapo",
        "div.detail-sapo",
        "div.sapo",
        "h2.sapo",
        "meta[name='description']",
    ]

    for selector in selectors:
        tag = soup.select_one(selector)
        if not tag:
            continue

        if tag.name == "meta":
            return clean_spaces(tag.get("content", ""))

        return clean_spaces(tag.get_text(" ", strip=True))

    return ""


def extract_published_date(soup: BeautifulSoup) -> str:
    meta_selectors = [
        "meta[property='article:published_time']",
        "meta[name='pubdate']",
        "meta[itemprop='datePublished']",
    ]

    for selector in meta_selectors:
        tag = soup.select_one(selector)
        if tag:
            value = clean_spaces(tag.get("content", ""))
            if value:
                return value

    text_selectors = [
        "div.detail-time",
        "span.detail-time",
        "time",
        "div.date-time",
    ]

    for selector in text_selectors:
        tag = soup.select_one(selector)
        if tag:
            value = clean_spaces(tag.get_text(" ", strip=True))
            if value:
                return value

    return ""


def looks_like_email_signature(text: str) -> bool:
    normalized = clean_spaces(text)
    if not normalized:
        return False

    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", normalized))
    short_line = len(normalized) <= 150

    return has_email and short_line


def is_noise_paragraph(text: str) -> bool:
    cleaned = clean_spaces(text)
    if not cleaned:
        return True

    cleaned_norm = normalize_text_for_compare(cleaned)

    for regex in NOISE_REGEXES:
        if regex.search(cleaned_norm):
            return True

    if looks_like_email_signature(cleaned):
        return True

    return False


def remove_duplicate_description_from_content(description: str, content: str) -> str:
    if not description or not content:
        return content

    description_norm = normalize_text_for_compare(description)
    paragraphs = [clean_spaces(p) for p in content.split("\n") if clean_spaces(p)]

    if not paragraphs:
        return content

    cleaned_paragraphs = []
    removed_first_duplicate = False

    for idx, paragraph in enumerate(paragraphs):
        paragraph_norm = normalize_text_for_compare(paragraph)

        if idx <= 1 and description_norm:
            same_text = paragraph_norm == description_norm
            desc_inside_para = len(description_norm) >= 30 and description_norm in paragraph_norm
            para_inside_desc = len(paragraph_norm) >= 30 and paragraph_norm in description_norm

            if same_text or desc_inside_para or para_inside_desc:
                removed_first_duplicate = True
                continue

        cleaned_paragraphs.append(paragraph)

    if removed_first_duplicate:
        return "\n".join(cleaned_paragraphs).strip()

    return content.strip()


def extract_content(soup: BeautifulSoup, description: str = "") -> str:
    selectors = [
        "div#main-detail-body",
        "div.detail-content",
        "div.fck_detail",
        "div.detail-cmain",
        "article",
    ]

    article = None
    for selector in selectors:
        article = soup.select_one(selector)
        if article:
            break

    if article is None:
        return ""

    for trash in article.select(
        "div.relate-container, div.related-news, table, .banner, .VCSortableInPreviewMode, .box-related-news"
    ):
        trash.decompose()

    paragraphs = []

    for p_tag in article.find_all("p"):
        text = clean_spaces(p_tag.get_text(" ", strip=True))

        if not text:
            continue

        if is_noise_paragraph(text):
            continue

        paragraphs.append(text)

    content = "\n".join(paragraphs).strip()
    content = remove_duplicate_description_from_content(description=description, content=content)

    return content


def extract_article(url: str, category_clean: str) -> Optional[dict]:
    try:
        response = SESSION.get(url, timeout=25)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = extract_title(soup)
        description = extract_description(soup)
        published_date = extract_published_date(soup)
        content = extract_content(soup, description=description)

        if not title or not content:
            return None

        return {
            "source": "tuoitre",
            "category_clean": category_clean,
            "title": title,
            "description": description,
            "content": content,
            "published_date": published_date,
            "url": url,
        }

    except Exception as exc:
        print(f"Lỗi bài báo: {url} -> {exc}")
        return None


def scrape_one_category(
    category_clean: str,
    target_links_per_category: Optional[int] = None,
) -> int:
    """
    Trả về số bài mới thêm của chuyên mục.
    """
    ensure_directories()

    if category_clean not in CATEGORY_CONFIG:
        print(f"[LỖI] Chuyên mục không hợp lệ: {category_clean}")
        return 0

    if target_links_per_category is None:
        target_links_per_category = get_target_for_category(category_clean)

    category_info = CATEGORY_CONFIG[category_clean]
    display_name = category_info["display_name"]
    category_url = category_info["url"]

    csv_path = get_csv_path(category_clean)
    existing_urls = load_existing_urls(csv_path)
    current_total = count_existing_articles(csv_path)
    progress = load_progress(PROGRESS_JSON)

    if current_total < target_links_per_category and category_clean in progress["done_categories"]:
        progress["done_categories"].remove(category_clean)
        save_progress(progress, PROGRESS_JSON)

    print(f"\n===== CHUYÊN MỤC: {display_name} ({category_clean}) =====")
    print(f"File đích: {csv_path}")
    print(f"Đã có sẵn {current_total} bài")
    print(f"Mục tiêu: {target_links_per_category} bài")

    if current_total >= target_links_per_category:
        print("Chuyên mục này đã đạt target, không cần crawl thêm.")
        if category_clean not in progress["done_categories"]:
            progress["done_categories"].append(category_clean)
            save_progress(progress, PROGRESS_JSON)
        return 0

    cached_links = progress["category_links"].get(category_clean, [])
    links = get_links_selenium(
        category_url=category_url,
        target=target_links_per_category,
        cached_links=cached_links,
    )

    if not links:
        print(f"Không lấy được link ở chuyên mục: {display_name}")
        return 0

    progress["category_links"][category_clean] = links
    save_progress(progress, PROGRESS_JSON)

    start_index = progress["category_indices"].get(category_clean, 0)
    print(f"Bắt đầu từ index: {start_index}")
    print(f"Tổng link hiện có trong cache: {len(links)}")

    total_new = 0

    for i, link in enumerate(links[start_index:], start=start_index):
        if link in existing_urls:
            progress["category_indices"][category_clean] = i + 1
            save_progress(progress, PROGRESS_JSON)
            continue

        article_data = extract_article(link, category_clean=category_clean)

        if article_data:
            append_article_to_csv(article_data, csv_path)
            existing_urls.add(link)
            current_total += 1
            total_new += 1
            print(f"[{current_total}/{target_links_per_category}] Đã lưu: {article_data['title'][:100]}")

        progress["category_indices"][category_clean] = i + 1
        save_progress(progress, PROGRESS_JSON)

        if current_total >= target_links_per_category:
            break

        time.sleep(random.uniform(SLEEP_BETWEEN_ARTICLES_MIN, SLEEP_BETWEEN_ARTICLES_MAX))

    if current_total >= target_links_per_category and category_clean not in progress["done_categories"]:
        progress["done_categories"].append(category_clean)
        save_progress(progress, PROGRESS_JSON)

    print(f"\nHoàn tất chuyên mục {display_name}. Đã lưu thêm {total_new} bài mới.")
    return total_new


def scrape_all_categories() -> None:
    """
    Crawl toàn bộ 6 chuyên mục của Tuổi Trẻ theo target riêng từng mục.
    Có in tổng kết ngắn gọn ở cuối.
    """
    ensure_directories()

    overall_new = 0

    print("\nBẮT ĐẦU CÀO TOÀN BỘ BÁO TUỔI TRẺ\n")

    for category_clean in CATEGORY_CONFIG.keys():
        target = get_target_for_category(category_clean)
        new_added = scrape_one_category(
            category_clean=category_clean,
            target_links_per_category=target,
        )
        overall_new += new_added

    print("\n===== TỔNG KẾT TUỔI TRẺ =====")
    for category_clean in CATEGORY_CONFIG.keys():
        csv_path = get_csv_path(category_clean)
        total_now = count_existing_articles(csv_path)
        print(f"{category_clean}: {total_now} bài")

    print(f"Tổng bài mới thêm: {overall_new}")
    print("Đã chạy xong toàn bộ 6 chuyên mục của Tuổi Trẻ.")


if __name__ == "__main__":
    scrape_all_categories()