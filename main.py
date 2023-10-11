import time
import datetime

import fake_useragent

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

import pyautogui


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


def get_page(driver: webdriver) -> None:
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
    try:

        # мы в большой карточке ищем символ с информацией
        clickable_el = driver.find_element(By.CLASS_NAME, "seller-info__title") \
            .find_element(By.TAG_NAME, "span")
    except NoSuchElementException:
        print("Невозможно найти мини карточку с продавцом")
        return "Нет огрн"

    # кликаем на него ( driver.click() по неизвестным причинам не работает)
    ActionChains(driver) \
        .click(clickable_el) \
        .perform()

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
    return "Нет огрн"


def get_url(driver: webdriver) -> str:
    return driver.current_url


def get_info_and_write(driver: webdriver, cards: list[webelement], url_zero: str,
                       writing_file) -> webdriver:
    """

    :param driver:
    :param cards: карточки товаров
    :param url_zero: адрес главной страницы
    :param writing_file: наш открытый файл на запись
    :return:
    """
    ogrn: str
    try:
        for i, card in enumerate(cards):
            try:
                # Переходим к карточке
                card.click()
            except Exception:
                print("[ERROR] Не удалось кликнуть на карточку")
                print("[INFO] Выполняю переход к основной странице")

                now = datetime.datetime.now()
                print(f"time ={now}\n[ERROR] Some wrong check log file")
                with open(f"{now}.txt", 'w+') as f:
                    f.write(current_url)

                driver.get(url=url_zero)
                return driver

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

            try:
                # Возвращаемся к главной странице
                driver.find_element(By.CLASS_NAME, "breadcrumbs__back").click()
            except Exception:
                current_url = driver.current_url
                # if "seller" in current_url:
                #     driver.execute_script("window.history.go(-1)")
                driver.get(url=url_zero)
                print("[ERROR] Невозможно вернутся к главной странице ")
            if ogrn == 'Нет огрн':
                continue
            writing_file.write(f"{ogrn}:{product_url}\n")
            # testing print
            print("card", i + 1)

        # Записываем значения в наш файл
    except Exception:
        now = datetime.datetime.now()
        print(f"time ={now}\n[ERROR] Some wrong check log file")
        with open(f"{now}.txt", 'w+') as f:
            f.write(current_url)
    finally:
        return driver


def main():
    main_wrapper: webelement
    cards: list[webelement]
    offset = 500
    offset_param = 400  # примерное значение для 15 дюймового монитора одна карточка - 431 пиксель

    driver: webdriver = start_driver()
    # открываем главную страницу
    get_page(driver=driver)
    # ожидаем ввод пользователя
    if wait_user():
        url_zero = driver.current_url
        print(url_zero)
        try:
            # сразу открываем файл на запись
            with open(f'{url_zero.split("/")[-1]}-{datetime.datetime.now().time()}.txt', 'w+') as in_file:
                # В случае возникновения ошибки перейдем по этому адресу
                pages_count = 0
                # пагинация всех страниц
                while 1:
                    pages_count += 1
                    print(f'New page num: {pages_count}')
                    try:
                        # скроллинг всей страницы чтобы не потерять ни один товар
                        for _ in range(22):
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
                            f"[ERROR] Невозможно найти карточки, возможно плохое интернет соединение, \
                            перезагружаю страничку:")

                        driver.refresh()
                        driver.implicitly_wait(5)

                    driver: webdriver = get_info_and_write(driver=driver, cards=cards,
                                                           url_zero=url_zero, writing_file=in_file
                                                           )
                    pyautogui.moveTo(100, 100, duration=0.25)
                    pyautogui.moveTo(300, 300, duration=0.25)

                    if 'Следующая страница' not in driver.find_element(By.CLASS_NAME, 'pagination').text:
                        break
                    try:
                        url_zero = driver.current_url
                        # переход на следующую страницу
                        a = driver.find_element(By.LINK_TEXT, 'Следующая страница').get_attribute('href')
                        driver.get(a)
                    except Exception as ex:
                        print(f"[ERROR] Невозможно перейти к следующей странице\n{ex}")
        except Exception as ex:
            print(f'[ERROR] Some wrong\n{ex}')
            now = datetime.datetime.now()
            with open(f'{now}.txt', 'w+') as f:
                f.write(url_zero)
    print(f"Последняя страница была: {url_zero}")


if __name__ == '__main__':
    main()
