import time

from bs4 import BeautifulSoup
from selenium import webdriver
import fake_useragent
import chromedriver_autoinstaller
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def start_driver():
    # generate fake useragent
    user = fake_useragent.UserAgent().random

    # collecting options
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument(f"user-agent={user}")
    options.add_argument("--start-maximized")

    # downloading webdriver
    chromedriver_autoinstaller.install()

    # initializing webdriver via options
    driver: webdriver = webdriver.Chrome(options=options)
    return driver


def get_page(driver: webdriver):
    driver.get(url='https://www.wildberries.ru/')


def wait_user():
    flag = input("Выбирайте категорию и настраивайте фильтры, как будете готовы нажмите enter: ")
    return flag == ''


def soup_plus(driver: webdriver):
    print("doing soup")
    time.sleep(15)
    page = driver.page_source
    soup = BeautifulSoup(page, "lxml")
    data = soup.find_all('div', class_='tooltip__content')
    for el in data:
        print("data: ", el.text.strip())


def get_org(driver: webdriver) -> WebElement:
    # мы в карточке ищем символ с информацией и кликаем на него
    clickable_el = driver.find_element(By.CLASS_NAME, "seller-info__title") \
        .find_element(By.TAG_NAME, "span")
    time.sleep(3)

    ActionChains(driver) \
        .click(clickable_el) \
        .perform()
    time.sleep(3)

    print("finding ogr")
    soup_plus(driver)
    quit()
    info_card = driver.find_element(By.CLASS_NAME, 'tooltip__content')
    return info_card


def main():
    driver = start_driver()
    get_page(driver=driver)
    if wait_user():
        try:
            # переход к элементу с карточками
            main_wrapper = driver.find_element(By.CLASS_NAME, 'product-card-list')
            # Все карточки находятся в тэгах article
            cards = main_wrapper.find_elements(By.TAG_NAME, 'article')
            for i, card in enumerate(cards):
                print("[info] click on card")
                # Переходим к карточке
                card.click()
                if i == 0:
                    driver.implicitly_wait(10)
                time.sleep(1)

                mini_info_card = get_org(driver=driver)
                print("text", mini_info_card.text)
                driver.implicitly_wait(1)
                driver.find_element(By.CLASS_NAME, "breadcrumbs__back").click()
                print("iter", i)

        except Exception as ex:
            print("[INFO] Some wrong: \n", ex)

        # start_scrap()


if __name__ == '__main__':
    main()
