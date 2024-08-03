from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import NoSuchElementException, ElementNotInteractableException, InvalidArgumentException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from pushbullet import PushBullet
import tkinter as tk
from tkinter import ttk
import time
import os
from dotenv import load_dotenv
from functools import partial
import threading as th
import sv_ttk
import pywinstyles, sys

##########################################################
load_dotenv()

DRIVER = 0
ACCESS_TOKEN = os.getenv('PUSH_BULLET_API_KEY')

##########################################################

products = []

##########################################################

def apply_theme_to_titlebar(window: tk.Tk | tk.Toplevel):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(window, "#1c1c1c")
    elif version.major == 10:
        pywinstyles.apply_style(window, "dark")

        window.wm_attributes("-alpha", 0.99)
        window.wm_attributes("-alpha", 1)
        

##########################################################
class MainWindow():
    def __init__(self) -> None:
        self.window = tk.Tk()
        self.window.title("Product finder")
        self.window.iconbitmap("./assets/icon.ico")
        self.window.geometry("600x215")
        self.window.protocol("WM_DELETE_WINDOW", self.stop_app)

        apply_theme_to_titlebar(self.window)
        sv_ttk.set_theme('Dark', self.window)

        self.listBox = tk.Listbox(self.window, width=130)

        self.reset_ListBox()

        self.lookup_thread = 0
        self.lookup = False
        self.add_button = ttk.Button(self.window, width=10, text='Add', command=self.add_form_func)
        self.remove_button = ttk.Button(self.window, width=10, text='Remove', command=self.remove_product)
        self.run_button = ttk.Button(self.window, width=10, text='Run', command=self.start_lookup)
        self.stop_button = ttk.Button(self.window, width=10, text='Stop', command=self.stop_lookup)

        self.listBox.pack(padx=2, pady=2)

        self.add_button.pack(side=tk.LEFT, padx=(4, 2), pady=(2, 4))
        self.remove_button.pack(side=tk.LEFT, padx=2, pady=(2, 4))
        self.run_button.pack(side=tk.RIGHT, padx=(2, 4), pady=(2, 4))
        self.stop_button.pack(side=tk.RIGHT, padx=2, pady=(2, 4))

        self.window.mainloop()

    def stop_app(self):
        self.stop_lookup()
        self.stop_driver()
        if not DRIVER == 0: 
            DRIVER.quit()
        self.window.destroy()

    def start_driver(self):
        global DRIVER
        if DRIVER == 0:
            options = Options()
            options.add_argument("--disable-search-engine-choice-screen")
            DRIVER = webdriver.Chrome(options=options)
            DRIVER.minimize_window()
        return DRIVER
    
    def stop_driver(self):
        global DRIVER
        if not DRIVER == 0:
            DRIVER.quit()
            DRIVER = 0

    def reset_ListBox(self):
        self.listBox.delete(0, tk.END)
        for i in range(len(products)):
            products[i].id = i+1
            self.listBox.insert(i+1, str(products[i]))

    def add_form_func(self):
        if not self.lookup:
            form = AddingFormZara(self)
        else:
            pass # alert to add

    def remove_product(self):
        for i in self.listBox.curselection():
            products.pop(int(self.listBox.get(i)[0])-1)
        self.reset_ListBox()

    def start_lookup(self):
        if len(products) > 0 and self.start_driver():
            self.lookup_thread = th.Thread(target=self.lookup_thread_func)
            self.lookup_thread.start()

    def lookup_thread_func(self):
        self.start_driver()
        self.lookup = True
        while self.lookup:
            for prod in products:
                time.sleep(0.5)
                if prod.buy():
                    self.lookup = False
                    break
            time.sleep(1)

    def stop_lookup(self):
        if self.lookup == True:
            self.lookup = False
            self.lookup_thread.join() 
            self.stop_driver()

class ProductZara:
    def __init__(self, link: str, size: str, main: MainWindow):
        self.mainFrame = main

        if self.mainFrame.start_driver():
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

            self.mainFrame.stop_driver()
        else:
            raise Exception("Not able to start DRIVER")

    def buy(self):
        DRIVER.get(self.link)

        elements = DRIVER.find_elements(By.CLASS_NAME, "size-selector-list__item")

        try:
            element = next(el for el in elements if el.find_element(By.CLASS_NAME, "product-size-info__main-label").text == self.size)
        except StopIteration:
            return False

        if not 'size-selector-list__item--out-of-stock' in element.get_attribute("class"):
            DRIVER.maximize_window()

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
    def __init__(self, mainFrame: MainWindow) -> None:
        self.add_window = tk.Toplevel()
        self.add_window.title('Add product')
        self.add_window.iconbitmap("./assets/icon.ico")
        self.add_window.geometry("600x250")
        apply_theme_to_titlebar(self.add_window)

        self.main = mainFrame

        self.add_window.grab_set()

        self.link_label = ttk.Label(self.add_window, text='Zara link: ')
        self.link_label.pack(pady=15)
        self.link_entry = ttk.Entry(self.add_window, width=300)
        self.link_entry.pack()

        self.sizes = []
        size_button = ttk.Button(self.add_window, width=10, text='Check sizes', command=self.check_size)
        size_button.pack(pady=10)

        self.size_label = ttk.Label(self.add_window, text='Sizes: ')
        self.size_label.pack()

        self.sizes_frame = ttk.Frame(self.add_window, borderwidth=10)
        self.sizes_frame.pack()

        self.size_var = tk.StringVar(self.add_window, "S")
        
        self.button_frame = ttk.Frame(self.add_window)
        self.button_frame.pack(pady=10)

        self.submit_button = ttk.Button(self.button_frame, width=10, text='Add', command=self.add_product_to_list)
        self.submit_button.pack(side=tk.LEFT, padx=20)

        self.cancel_button = ttk.Button(self.button_frame, width=10, text='Cancel', command=self.cancel_adding_form)
        self.cancel_button.pack(side=tk.LEFT, padx=20)


        self.alert_label_text = tk.StringVar(self.add_window)
        self.alert_label = ttk.Label(self.add_window, textvariable=self.alert_label_text)
        self.alert_label.pack(side=tk.BOTTOM)

        self.radioButtons = []

    def check_size(self):
        pass

    def add_product_to_list(self):
        pass
    
    def cancel_adding_form(self):
        self.add_window.grab_release()
        self.add_window.destroy()
        self.main.stop_driver()

class AddingFormZara(AddingForm):
    def check_size(self):
        try:
            link = str(self.link_entry.get()).strip()
            if link == '':
                raise InvalidArgumentException

            if self.main.start_driver():

                self.sizes = []

                for but in self.radioButtons:
                    but.destroy()

                DRIVER.get(link)
                size_buttons = DRIVER.find_elements(By.CLASS_NAME, "size-selector-list__item")

                for size_button in size_buttons:
                    self.sizes.append(size_button.text.split('\n')[0])

                for size in self.sizes:
                    R = ttk.Radiobutton(self.sizes_frame, text=size, variable=self.size_var, value=size)
                    R.pack(side=tk.LEFT)
                    self.radioButtons.append(R)
        except (InvalidArgumentException, NoSuchElementException):
            self.alert_label_text.set("Niepoprawny link do produktu")
            self.main.stop_driver()

    def add_product_to_list(self):
        try:
            if len(self.sizes) == 0:
                raise Exception
            product = ProductZara(self.link_entry.get(), self.size_var.get(), self.main)
            products.append(product)

            self.main.reset_ListBox()

            self.add_window.grab_release()
            self.add_window.destroy()
            self.main.stop_driver()
        except ValueError:
            self.alert_label_text.set("Nie ma takiego rozmiaru dla tego produktu")
        except (InvalidArgumentException, NoSuchElementException):
            self.alert_label_text.set("Niepoprawny link do produktu")
        except Exception:
            self.alert_label_text.set("Załaduj najpierw rozmiary produktu")

if __name__ == '__main__':
    mainFrame = MainWindow()
    