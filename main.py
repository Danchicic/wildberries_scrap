import time
from selenium import webdriver
import fake_useragent
import chromedriver_autoinstaller
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement

from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException


def start_driver() -> webdriver:
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


def wait_user() -> bool:
    flag = input("Выбирайте категорию и настраивайте фильтры, как будете готовы нажмите enter: ")
    return flag == ''


def get_org(driver: webdriver) -> str | None:
    """
    function working in opened big-card
    1) opening mini-card
    2) scrap web element of mini-card
    :param driver:
    :return: mini card info
    """
    # ожидание для загрузки всей страницы большой карточки
    # time.sleep(1.5)
    try:

        # мы в большой карточке ищем символ с информацией
        clickable_el = driver.find_element(By.CLASS_NAME, "seller-info__title") \
            .find_element(By.TAG_NAME, "span")
    except NoSuchElementException:
        print("Невозможно найти мини карточку с продавцом")
        return None

    # кликаем на него ( driver.click() по неизвестным причинам не работает)
    ActionChains(driver) \
        .click(clickable_el) \
        .perform()
    # wait for testing
    # time.sleep(1)

    # Нужная информация находится в <div class="tooltip__content"> и мы ищем все элементы т.к.
    # нужный элемент с таким классом не один

    info_cards: list[WebElement] = driver.find_elements(By.CLASS_NAME, 'tooltip__content')
    for el in info_cards:
        # Проходимся по найденным классам и ищем нужный по огрн если он вообще есть
        data: str = el.text.strip()
        if 'ОГРН' in data:
            # Перевели карточку в текст и режем ее до огрн
            data_rows: list[str] = data.split('\n')
            for row in data_rows:
                if "ОГРН" in row:
                    # row = ОГРН: number
                    return row.split(':')[-1].strip()
    else:
        print("[INFO] у данного продавца нет огрн")
    return 'Нет огрн'


def get_url(driver: webdriver) -> str:
    return driver.current_url


def main():
    main_wrapper: webelement
    cards: list[webelement]
    ogrn: str = ''
    product_url: str = ''
    offset = 500
    offset_param = 500  # примерное значение для 15 дюймового монитора одна карточка - 431 пиксель

    driver: webdriver = start_driver()
    # открываем главную страницу
    get_page(driver=driver)
    # ожидаем ввод пользователя
    if wait_user():
        with open('result.txt', 'w+') as f:
            # В случае возникновения ошибки перейдем по этому адресу
            url_zero = driver.current_url

            # пагинация всех страниц
            while 1:
                try:
                    # скроллинг всей страницы чтобы не потерять ни один товар
                    for _ in range(20):
                        time.sleep(1)
                        driver.execute_script(f"window.scrollTo(0, {offset});")
                        offset += offset_param
                    offset = 500  # возврат к первому значению чтобы скролить следующие страницы

                except Exception:
                    driver.refresh()
                    driver.implicitly_wait(5)
                    print("[Error] Не удалось проскролить всю страницу")

                try:
                    # переход к элементу с большими карточками
                    main_wrapper: webelement = driver.find_element(By.CLASS_NAME, 'product-card-list')
                    # Все большие карточки находятся в тэгах article
                    cards: list[webelement] = main_wrapper.find_elements(By.TAG_NAME, 'article')
                except Exception:
                    print(
                        f"[ERROR] Невозможно найти карточки, возможно плохое интернет соединение, перезагружаю страничку:")
                    driver.refresh()
                    driver.implicitly_wait(5)

                for i, card in enumerate(cards):
                    try:
                        # Переходим к карточке
                        card.click()
                    except Exception:
                        print("[ERROR] Не удалось кликнуть на карточку")
                        print("[INFO] Выполняю переход к основной странице")
                        driver.get(url=url_zero)
                        continue

                    # Ожидание для прогрузки страницы
                    if i == 0:
                        driver.implicitly_wait(10)
                        time.sleep(2)

                    try:
                        time.sleep(1)
                        # Получаем огрн
                        ogrn: str = get_org(driver=driver)
                    except Exception:
                        print("[ERROR] Не удалось получить огрн, попробуйте увеличить задержку")
                        current_url = driver.current_url
                        if "seller" in current_url:
                            driver.execute_script("window.history.go(-1)")

                    try:
                        # получаем url-адрес товара
                        product_url: str = get_url(driver=driver)
                    except Exception:
                        print("[ERROR] Не удалось получить url")

                    # Записываем значения в наш файл
                    f.write(f"{ogrn}:{product_url}\n")
                    try:
                        # Возвращаемся к главной странице
                        driver.find_element(By.CLASS_NAME, "breadcrumbs__back").click()
                    except Exception:
                        current_url = driver.current_url
                        if "seller" in current_url:
                            driver.execute_script("window.history.go(-1)")
                        print("[ERROR] Невозможно вернутся к главной странице ")

                    # testing print
                    print("iter", i)
                if 'Следующая страница' not in driver.find_element(By.CLASS_NAME, 'pagination').text:
                    break
                try:
                    driver.find_element(By.LINK_TEXT, 'Следующая страница').click()
                except Exception:
                    print("[ERROR] Невозможно перейти к следующей странице")


if __name__ == '__main__':
    main()
