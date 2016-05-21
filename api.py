from selenium.webdriver.common.keys import Keys
import webbrowser
import re
import os
import json
import requests
import random
import selenium
from robobrowser import RoboBrowser
import time


class vk_captcha:
	"""Класс для работы с каптчей. Вырезает img со страницы, отправляет 
	в antigate, получает результат, возвращает введенную каптчу в виде строки"""

	def decode(page, root_path):
		"""Объединение функций _send_captcha и _check_captcha"""
		print("Каптча...")

		key = "4517fb23f10056ec2141bba9a7a158e6"
		a_captchaID = vk_captcha._send_captcha(page, root_path, key) #antigate captcha ID [OK, 406704123]
		if a_captchaID[0] != "OK":
			print("Неудалось отправить запрос на antigate\n%s" % a_captchaID)
			return 0
		while True:
			time.sleep(7)
			a_captchaRESULT = vk_captcha._check_captcha(a_captchaID[1], key)  #antigate captcah RESULT [OK, Fgv4Kl]
			if a_captchaRESULT[0] != "OK":
				continue
			print("Готово. %s" % a_captchaRESULT[1])
			return a_captchaRESULT[1]
		

	def _send_captcha(page, root_path, key):
		"""Получает страницу, возвращает массив формата [OK, 406704123]"""
		img_tag = page.find(id="captcha") 
		if not img_tag:
			img_tag = page.find("img", {"class":"captcha_img"})
		if not img_tag:
			print("Тега с id=captcha не найдено")
			return 0
		img = vk_captcha.request_with_retry(root_path + img_tag["src"]).content
		data = {
			"key": key,
			"method": "post",
		}
		response = vk_captcha.request_with_retry('http://antigate.com/in.php', data=data, files={"file": img}) 
		return (response.text.split("|"))

	def _check_captcha(captcha_id, key):
		response = vk_captcha.request_with_retry("http://antigate.com/res.php?key=" + key + "&action=get&id=" + captcha_id)
		return (response.text.split('|'))

	def request_with_retry(url, data="", files=""):
		TIMEOUT = 0.5
		while True:
			try:
				if data or files:
					response = requests.post(url, data=data, files=files, timeout=TIMEOUT)
				else:
					response = requests.get(url, timeout=TIMEOUT)
			except requests.exceptions.ReadTimeout:
				continue
			break
		return response
	

class vk_session:
	def __init__(self, root_path, proxy="", cookies=""):
		self.is_signed = False
		self.proxy = proxy
		self.root_path = root_path
		session = requests.session()
		if proxy:
			session.proxies.update({'http': 'http://' + proxy, 'ssl': proxy ,'https': 'https://' + proxy})
		headers = {
			"ACCEPT": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"ACCEPT_ENCODING": "gzip, deflate, sdch",
			"ACCEPT_LANGUAGE": "ru-RU,ru;",
			"CONNECTION": "keep-alive",
			"REFERER": root_path,
			"UPGRADE_INSECURE_REQUESTS": "1",
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
		}
		session.headers = headers
		if cookies:
			session.cookies = cookies
		self.browser = RoboBrowser(session=session, timeout=4, history=False)

	def connect(self):
		
		self.browser.open(self.root_path) 	
		print("connected")

		
	def sign_in(self, username, password, captcha):
		try:
			form = self.browser.get_forms()[0]

			form["email"] = username
			form["pass"] = password
			if captcha:
				form["captcha_key"] = vk_captcha.decode(page=self.browser.parsed, root_path=self.root_path)
			self.browser.submit_form(form)
		except:
			print(username)
			raise

	def create_new_group(self, name, group_type, public_type):
		self.browser.open("https://m.vk.com/groups?act=new")
		form = self.browser.get_forms()[0]
		form["title"] = name
		form["type"] = group_type
		form["public_type"] = public_type
		self.browser.submit_form(form)
		time.sleep(1)

	def enter_captcha(self):
		form = self.browser.get_forms()[0]
		form["captcha_key"] = vk_captcha.decode(page=self.browser.parsed, root_path=self.root_path)
		self.browser.submit_form(form)

class sup_func:
	"""Вспомогательные функции"""

	def img_paths_list(path="data/content/images"):
		"""Получет путь к каталогу с папками с картинками, возвращает их относ. пути"""
		img_rel_paths = []
		for directory in os.listdir(path):
			img_dir_path = path + "/"
			img_dir_path += directory
			for f in os.listdir(img_dir_path):
				img_path = img_dir_path + "/" + f
				img_rel_paths.append(os.path.abspath(img_path))

		return img_rel_paths

	def random_img_binary(img_rel_paths=img_paths_list()):
		random_img = random.choice(img_rel_paths)
		binary_img = open(random_img, "rb")
		return binary_img

	def random_img(img_rel_paths=img_paths_list()):
		random_img = random.choice(img_rel_paths)
		return random_img

	def open_page_with_retries(page, upload_url):
		for i in range(5) :
			page.open(upload_url)
			if "service_msg_warning" in page.parsed:
				wait_time = 5 * (i + 1)
				print("service_msg_warning: Одинаковые обращения | ожидаем %s" % wait_time)
				time.sleep(wait_time)
				continue
			return page

	def avatar_retry_decorator(post_func):
		def wrapper(arg1, arg2):
			RETRY_TIMES = 5
			WAIT_STEP = 5
			for i in range(RETRY_TIMES):
				try:		
					post_func(arg1, arg2)
					break
				except IndexError:
					wait_time = (i + 1) * WAIT_STEP
					time.sleep(wait_time)
					print("Не удалось загрузить аватар | попытка %s/%s | ожидаем %s" % (i + 1, RETRY_TIMES, wait_time))
		return wrapper


	

class AllUsersControll:
	"""Методы для управления всеми аккаунтами"""
	def start_driver(proxy=""):
		for i in range(5):
			try:
				if proxy:
					raise #посмотреть serv ad, port num
					proxy = proxy.split(":")
					server_adress = proxy[0] 
					port_number = int(proxy[1])
					profile = selenium.webdriver.FirefoxProfile()
					profile.set_preference("network.proxy.type", 1)
					profile.set_preference("network.proxy.http", server_adress)
					profile.set_preference("network.proxy.http_port", port_number)
					profile.set_preference('network.proxy.ssl_port', port_number)
					profile.set_preference('network.proxy.ssl', server_adress)
					profile.update_preferences()
					driver = selenium.webdriver.Firefox(firefox_profile=profile)
				else:
					driver = selenium.webdriver.Firefox()
				break
			except selenium.common.exceptions.WebDriverException:
				time.sleep(3)
				print("Не удалось открыть selenium firefox в api.py/AllUsersControll.start_driver()")
				continue

		return driver

	def set_cookies_to_driver(driver, cookies):
		driver.delete_all_cookies()
		driver.get("https://m.vk.com/")
		for cookie in cookies:
			driver.add_cookie({'name':cookie, 'value':cookies[cookie]})
		#driver.get("https://m.vk.com/")
		return driver

	@sup_func.avatar_retry_decorator
	def _change_avatar_with_driver(group, driver):
		"""driver должен быть signed in"""
		while True:
			try:
				driver.get("https://m.vk.com/" + group.group_id)
				input_elem = driver.find_element_by_class_name("inline_upload")
				img = sup_func.random_img()
				input_elem.send_keys(img)
				time.sleep(1)
				break
			except selenium.common.exceptions.NoSuchElementException:
				print('слишком много однотипных действий sleep 7s')
				time.sleep(7)
		while True:
			try:
				save_button = driver.find_element_by_id("zpv_save_button")
				save_button.click()
				time.sleep(3)
				continue
			except:
				break
		time.sleep(1)
		return 1

	def upload_avatar_to_new(group, driver):
		AllUsersControll._change_avatar_with_driver(group, driver)


	def upload_avatars_to_all(users, driver=""):
		if not driver:
			driver = AllUsersControll.start_driver()
		for user in users:
			driver = AllUsersControll.set_cookies_to_driver(driver, user.get_cookies())
			for group in user.groups:
				AllUsersControll._change_avatar_with_driver(group, driver)

	def make_message(targ):
		message = "%s\n@id%s(%s %s ©)" % (targ["status"], targ["id"], targ["first_name"], targ["last_name"])
		return message






# 	def get_all_users(path="data/accounts.json"):
# 		with open(path,"r") as f:
# 			accounts = f.read()
# 			if not accounts:
# 				return 0 # Файл accounts.json пуст
# 			accounts = json.loads(accounts)
# 		all_users = []
# 		for account in accounts:
# 			all_users.append(User(account, accounts[account]))
# 		return all_users

# 	def get_all_exists_groups(users=get_all_users()):
# 		all_groups = []
# 		for user in users:
# 			session = user.session
# 			set_session_to_driver(driver, session)
# 			for group in user.groups:
# 				all_groups.append(group)
# 		return all_groups


# 	def upload_avatars_to_new_groups(users=get_all_users()):
# 		"""Использует Selenium для выполнения js скриптов"""
# 		driver = start_driver() # Предварительно инициализируем driver, для каждого пользователя меняем только сессию
# 		for group in get_all_exists_groups():



#<div class="service_msg service_msg_error">Вы попытались загрузить более одной однотипной страницы в секунду. Вернитесь назад и повторите попытку.</div>





if __name__ == "__main__":
	print(sup_func.random_img_to_binary())






	








		

