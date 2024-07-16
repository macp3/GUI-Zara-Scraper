from selenium import webdriver
from selenium.webdriver.common.by import By
from pushbullet import PushBullet
import tkinter as tk
import time
import os
from dotenv import load_dotenv

##########################################################
load_dotenv()

DRIVER = webdriver.Chrome()
ACCESS_TOKEN = os.getenv('PUSH_BULLET_API_KEY')

##########################################################

products = []

##########################################################
class ProductZara:
    def __init__(self, link: str, size: str):
        DRIVER.get(link)
        self.id = len(products) + 1
        self.name = DRIVER.find_element(By.CLASS_NAME, 'product-detail-info__header-name').text
        self.size = size
        self.link = link

    def check_size(self):
        DRIVER.get(self.link)

        elements = DRIVER.find_elements(By.CLASS_NAME, "product-size-info__size")

        try:
            element = next(el for el in elements if el.find_element(By.CLASS_NAME, "product-size-info__main-label").text == self.size)
        except StopIteration:
            return False

        if not 'PODOBNE' in element.text:
            pb = PushBullet(ACCESS_TOKEN)
            push = pb.push_note('PRODUKT DOSTĘPNY', self.name)
            return True
        else:
            return False

    def __str__(self):
        return self.name + ", " + self.size

# def remove_product_from_list():
#     listBox.delete(listBox.curselection())
#     return 'active'
#
# window = tk.Tk()
#
# products.append(ProductZara('https://www.zara.com/pl/pl/popelinowy-top-z-wiazaniem-p02715200.html', 1))
# products.append(ProductZara('https://www.zara.com/pl/pl/top-typu-gorset-z-koronki-p03067068.html', 0))
# products.append(ProductZara('https://www.zara.com/pl/pl/top-z-odkrytymi-plecami-p02891777.html', 1))
#
# listBox = tk.Listbox(window, width=100)
#
# for i in range(len(products)):
#     listBox.insert(i+1, products[i].__str__())
#
# remove_button = tk.Button(window, command=remove_product_from_list())
#
# listBox.pack()
# remove_button.pack()
#
#
# window.mainloop()

prod = ProductZara('https://www.zara.com/pl/pl/popelinowy-top-z-wiazaniem-p02715200.html', 'S')

while not prod.check_size():
    time.sleep(3)

DRIVER.quit()