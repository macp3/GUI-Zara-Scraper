from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from pushbullet import PushBullet
import tkinter as tk
import time
import os
from dotenv import load_dotenv
from functools import partial

##########################################################
load_dotenv()

DRIVER = webdriver.Chrome()
ACCESS_TOKEN = os.getenv('PUSH_BULLET_API_KEY')

##########################################################

products = []
add_form = False

##########################################################
class ProductZara:
    def __init__(self, link: str, size: str):
        DRIVER.get(link)
        self.id = len(products) + 1
        self.name = DRIVER.find_element(By.CLASS_NAME, 'product-detail-info__header-name').text

        size_buttons = DRIVER.find_elements(By.CLASS_NAME, 'size-selector-list__item')

        for size_button in size_buttons:
            print(size_button.text.split('\n')[0])
            if size_button.text.split('\n')[0] == size:
                self.size = size
                break
        else:
            raise ValueError("Wrong size for this product")

        self.size = size
        self.link = link

    def buy(self):
        DRIVER.get(self.link)

        elements = DRIVER.find_elements(By.CLASS_NAME, "size-selector-list__item")

        try:
            element = next(el for el in elements if el.find_element(By.CLASS_NAME, "product-size-info__main-label").text == self.size)
        except StopIteration:
            return False

        if not 'size-selector-list__item--out-of-stock' in element.get_attribute("class"):

            errors = [NoSuchElementException, ElementNotInteractableException]
            wait = WebDriverWait(DRIVER, timeout=3, poll_frequency=.2, ignored_exceptions=errors)

            cookie = wait.until(lambda d : DRIVER.find_element(By.ID, 'onetrust-reject-all-handler') or True)

            wait.until(lambda d : cookie.click() or True)
            wait.until(lambda d : element.click() or True)

            cart_adding_button = wait.until(lambda d : DRIVER.find_element(By.CLASS_NAME, 'product-cart-buttons__first-row') or True)
            wait.until(lambda d : cart_adding_button.click() or True)

            cart_button = wait.until(lambda d : DRIVER.find_element(By.CLASS_NAME, 'add-to-cart-notification__cart-button') or True)
            wait.until(lambda d : cart_button.click() or True)

            pb = PushBullet(ACCESS_TOKEN)
            push = pb.push_note('PRODUKT DOSTĘPNY', self.name)

            return True
        else:
            return False

    def __str__(self):
        return self.name + ", " + self.size
    
class AddingForm:
    def __init__(self) -> None:
        self.add_window = tk.Tk()
        self.add_window.title('Add product')
        self.add_window.geometry("600x180")

        self.link_label = tk.Label(self.add_window, text='Link do zary: ')
        self.link_label.pack()
        self.link_entry = tk.Entry(self.add_window, width=300)
        self.link_entry.pack()

        self.size_label = tk.Label(self.add_window, text='Rozmiar: ')
        self.size_label.pack()

        sizes = ["XS","S", "M", "L", "XL","XXL"]

        self.size_var = tk.StringVar(self.add_window, "S")

        x=70
        for size in sizes:
            x+=60
            tk.Radiobutton(self.add_window, text=size, variable=self.size_var, value=size).place(x=x, y=70)
        
        submit_button = tk.Button(self.add_window, width=10, text='Add', command=self.add_product_to_list)
        submit_button.place(x=260, y=110)


        self.alert_label_text = tk.StringVar(self.add_window)
        self.alert_label = tk.Label(self.add_window, textvariable=self.alert_label_text)
        self.alert_label.place(x=180, y=150)

    def add_product_to_list(self):
        try:
            product = ProductZara(self.link_entry.get(), self.size_var.get())
            products.append(product)
            reset_ListBox()
            self.add_window.destroy()
            global add_form
            add_form = False
        except ValueError:
            self.alert_label_text.set("Nie ma takiego rozmiaru dla tego produktu")

def reset_ListBox():
    listBox.delete(0, tk.END)
    for i in range(len(products)):
        listBox.insert(i+1, products[i].__str__())


def add_form_func():
    global add_form

    if not add_form:
        add_form = True
        form = AddingForm()


if __name__ == "__main__":
    window = tk.Tk()
    window.title("Product finder")
    
    products.append(ProductZara('https://www.zara.com/pl/pl/popelinowy-top-z-wiazaniem-p02715200.html', 'S'))
    products.append(ProductZara('https://www.zara.com/pl/pl/top-typu-gorset-z-koronki-p03067068.html', 'XXL'))
    products.append(ProductZara('https://www.zara.com/pl/pl/top-z-odkrytymi-plecami-p02891777.html', 'L'))
    
    listBox = tk.Listbox(window, width=100)
    
    reset_ListBox()
    
    add_button = tk.Button(window, width=10, text='Add', command=add_form_func)
    remove_button = tk.Button(window, width=10, text='Remove')
    run_button = tk.Button(window, width=10, text='Run')
    stop_button = tk.Button(window, width=10, text='Stop')
    
    listBox.pack(padx=2, pady=2)
    
    add_button.pack(side=tk.LEFT, padx=(4, 2), pady=(2, 4))
    remove_button.pack(side=tk.LEFT, padx=2, pady=(2, 4))
    run_button.pack(side=tk.RIGHT, padx=(2, 4), pady=(2, 4))
    stop_button.pack(side=tk.RIGHT, padx=2, pady=(2, 4))
    
    window.mainloop()