from bs4 import BeautifulSoup
import requests
import os 
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
link_web = "https://thienvu.com.vn/"
driver = webdriver.Chrome()
driver.implicitly_wait(0.5)


response = requests.get(link_web)
soup = BeautifulSoup(response.text, 'html.parser')

item_categories = soup.find_all(class_='category__item')
item_brands = soup.find(class_="manufacturer__list").find_all(class_="row_items")
folder_brands = 'static/brands'
for idx, item_row in enumerate(item_brands):
    for item in item_row.find_all('a'):
        name = item['href'].split('/')[-1].replace('-',' ').title()
        slug_brand = item['href'].split('/')[-1]
        img_element = item.find('img')
        image_url = img_element.get('data-src') if img_element else None
        if image_url:
            if not os.path.exists(folder_brands):
                os.makedirs(folder_brands)
            response_img = requests.get(image_url)
            img_path = os.path.join(folder_brands, f'{image_url.split('/')[-1]}').replace('\\','/')
            if response_img.status_code == 200:
                with open(img_path, 'wb') as img_file:
                    img_file.write(response_img.content)
                    
            with open('craw_data/brands.txt', 'a', encoding='utf-8') as file:
                file.write(f"{name} <> {slug_brand} <> brands/{image_url.split('/')[-1]} \n" )

for idx, item in enumerate(item_categories):
    link = item.find(class_='category__item-image').find('a')
    name = item.find('h3').find('a')
    image_url = item.find(class_='category__item-image').find('img')
    folder_path_categories = f'static/data/{link['href'].split('/')[-1]}'
    slug_category = link['href'].split('/')[-1]
    if not os.path.exists(folder_path_categories):
        os.makedirs(folder_path_categories)
    try:
        img_src = image_url.get('data-src', '')
        if img_src and not img_src.startswith(('http:', 'https:')):
            img_src = f"{link_web.rstrip('/')}/{img_src.lstrip('/')}"
        if img_src:
            response_img = requests.get(img_src)
            img_path = os.path.join(folder_path_categories, f'{img_src.split('/')[-1]}').replace('\\','/')
            if response_img.status_code == 200:
                with open(img_path, 'wb') as img_file:
                    img_file.write(response_img.content)
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        continue
    with open('craw_data/categories.txt', 'a', encoding='utf-8') as file:
        file.write(f"{name.text} <> {link['href'].split('/')[-1]} <> {img_path} \n" )
    
    response = requests.get(link['href'])
    soup = BeautifulSoup(response.text, 'html.parser')
    driver.get(link['href'])
    while True:
        try:
            # Chờ tối đa 5 giây để nút xuất hiện
            button_view_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "view-more-button"))
            )
            button_view_more.click()
            time.sleep(0.5)  # Giữ sleep ngắn sau khi bấm
        except:
            break
    
    # Get all product-box elements and print their HTML structure
    product_boxes = driver.find_elements(By.CLASS_NAME, "product-box")
    for product_box in product_boxes:
        # Find the first media tag and get srcset
        try:
            media = product_box.find_element(By.TAG_NAME, "source")
            image_url = media.get_attribute("srcset")
            if not image_url.startswith(('http:', 'https:')):
                image_url = f"{link_web.rstrip('/')}/{image_url.lstrip('/')}"
            
            # Get product title from h3 inside product-box__info
            product_info = product_box.find_element(By.CLASS_NAME, "product-box__info")
            title = product_info.find_element(By.TAG_NAME, "h3").text
            
            # Get and format price
            price_element = product_box.find_element(By.CLASS_NAME, "current-price")
            price_text = price_element.text.replace(',', '').replace('đ', '').replace('Liên hệ','').strip()
            price_number = int(price_text) if price_text else 0
            
            link_product = product_info.find_element(By.TAG_NAME, "h3").find_element(By.TAG_NAME, "a").get_attribute("href")
            response = requests.get(link_product)  # Note: variable name should match (link_product instead of link_web)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            with open(f'craw_data/products.txt', 'a', encoding='utf-8') as file:
                image_url_save = f"data/{link['href'].split('/')[-1]}/{image_url.split('/')[-1]}"
                
                brand_element = soup.find(class_="brand")
                if brand_element:
                    brand_slug = brand_element.find('a')  # Tìm thẻ 'a' bên trong brand_element
                    slug_brand = brand_slug['href'].split('/')[-1] if brand_slug else 'none-brand'
                else:
                    slug_brand = 'none-brand'  # Gán giá trị mặc định nếu không tìm thấy brand_element
                
                file.write(f"{title} <> {price_number} <> {slug_brand} <> {slug_category} <> {image_url_save}\n")

            
            response_img = requests.get(image_url)
            if response_img.status_code == 200:
                img_name = image_url.split('/')[-1]
                directory = os.path.join('static/data', link['href'].split('/')[-1])
                if not os.path.exists(directory):
                    os.makedirs(directory)
                img_path = os.path.join(directory, img_name).replace('\\','/')
                with open(img_path, 'wb') as img_file:
                    img_file.write(response_img.content)
        except Exception as e:
            print(f"Error processing product: {str(e)}")

        