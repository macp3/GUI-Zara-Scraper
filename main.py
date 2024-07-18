from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import NoSuchElementException, ElementNotInteractableException, InvalidArgumentException, NoSuchElementException
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
lookup = False

##########################################################
class ProductZara:
    def __init__(self, link: str, size: str):
        DRIVER.get(link)
        self.id = len(products) + 1
        self.name = DRIVER.find_element(By.CLASS_NAME, 'product-detail-info__header-name').text

        size_buttons = DRIVER.find_elements(By.CLASS_NAME, 'size-selector-list__item')

        for size_button in size_buttons:
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
        return str(self.id) + " " + self.name + ", " + self.size
    
class AddingForm:
    def __init__(self) -> None:
        self.add_window = tk.Toplevel()
        self.add_window.title('Add product')
        self.add_window.geometry("600x220")

        self.add_window.grab_set()

        self.link_label = tk.Label(self.add_window, text='Link do zary: ')
        self.link_label.pack()
        self.link_entry = tk.Entry(self.add_window, width=300)
        self.link_entry.pack()

        self.sizes = []
        size_button = tk.Button(self.add_window, width=10, text='Check sizes', command=self.check_size)
        size_button.pack(pady=10)

        self.size_label = tk.Label(self.add_window, text='Rozmiar: ')
        self.size_label.pack()

        self.size_var = tk.StringVar(self.add_window, "S")
        
        submit_button = tk.Button(self.add_window, width=10, text='Add', command=self.add_product_to_list)
        submit_button.place(x=210, y=140)

        cancel_button = tk.Button(self.add_window, width=10, text='Cancel', command=self.cancel_adding_form)
        cancel_button.place(x=310, y=140)


        self.alert_label_text = tk.StringVar(self.add_window)
        self.alert_label = tk.Label(self.add_window, textvariable=self.alert_label_text)
        self.alert_label.place(x=180, y=190)

        self.radioButtons = []

    def check_size(self):
        try:
            self.sizes = []

            for but in self.radioButtons:
                but.destroy()

            DRIVER.get(self.link_entry.get())
            size_buttons = DRIVER.find_elements(By.CLASS_NAME, "size-selector-list__item")

            for size_button in size_buttons:
                self.sizes.append(size_button.text.split('\n')[0])

            x=70
            for size in self.sizes:
                x+=60
                R = tk.Radiobutton(self.add_window, text=size, variable=self.size_var, value=size)
                R.place(x=x, y=110)
                self.radioButtons.append(R)
        except (InvalidArgumentException, NoSuchElementException):
            self.alert_label_text.set("Niepoprawny link do produktu")

    def add_product_to_list(self):
        try:
            if len(self.sizes) == 0:
                raise Exception
            product = ProductZara(self.link_entry.get(), self.size_var.get())
            products.append(product)
            reset_ListBox()

            self.add_window.destroy()
        except ValueError:
            self.alert_label_text.set("Nie ma takiego rozmiaru dla tego produktu")
        except (InvalidArgumentException, NoSuchElementException):
            self.alert_label_text.set("Niepoprawny link do produktu")
        except Exception:
            self.alert_label_text.set("Załaduj najpierw rozmiary produktu")


    def cancel_adding_form(self):
        self.add_window.destroy()


def reset_ListBox():
    listBox.delete(0, tk.END)
    for i in range(len(products)):
        products[i].id = i+1
        listBox.insert(i+1, str(products[i]))


def add_form_func():
        form = AddingForm()

def remove_product():
    for i in listBox.curselection():
        products.pop(int(listBox.get(i)[0])-1)
    reset_ListBox()

def start_lookup():
    lookup = True
    while lookup:
        for prod in products:
            prod.buy()
            time.sleep(0.5)
        time.sleep(1)

def stop_lookup():
    lookup = False


if __name__ == "__main__":
    window = tk.Tk()
    window.title("Product finder")
    
    products.append(ProductZara('https://www.zara.com/pl/pl/popelinowy-top-z-wiazaniem-p02715200.html', 'S'))
    products.append(ProductZara('https://www.zara.com/pl/pl/top-typu-gorset-z-koronki-p03067068.html', 'XXL'))
    products.append(ProductZara('https://www.zara.com/pl/pl/top-z-odkrytymi-plecami-p02891777.html', 'L'))
    
    listBox = tk.Listbox(window, width=100)
    
    reset_ListBox()
    
    add_button = tk.Button(window, width=10, text='Add', command=add_form_func)
    remove_button = tk.Button(window, width=10, text='Remove', command=remove_product)
    run_button = tk.Button(window, width=10, text='Run', command=start_lookup)
    stop_button = tk.Button(window, width=10, text='Stop', command=stop_lookup)
    
    listBox.pack(padx=2, pady=2)
    
    add_button.pack(side=tk.LEFT, padx=(4, 2), pady=(2, 4))
    remove_button.pack(side=tk.LEFT, padx=2, pady=(2, 4))
    run_button.pack(side=tk.RIGHT, padx=(2, 4), pady=(2, 4))
    stop_button.pack(side=tk.RIGHT, padx=2, pady=(2, 4))
    
    window.mainloop()