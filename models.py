#!/usr/bin/python
# -*- coding: utf-8 -*
import re
import json
from api import *
import rawdata_handler as rawdata
from selenium import webdriver
import random
import requests
import time
import sys

class Group:
	def __init__(self, group_id, session, owner):
		self.group_id = group_id
		self.session = session
		self.link = "https://m.vk.com/" + self.group_id
		self.owner = owner

	def post_retry_decorator(post_func):
		def wrapper(self, arg1, arg2):
			RETRY_TIMES = 5
			WAIT_STEP = 5
			for i in range(RETRY_TIMES):
				try:		
					post_func(self, arg1, arg2)
					break
				except IndexError:
					wait_time = (i + 1) * WAIT_STEP
					time.sleep(wait_time)
					print("service_msg_warning | попытка %s/%s | ожидаем %s | owner %s | ошибка %s" % (i + 1, RETRY_TIMES, wait_time, self.owner, sys.exc_info()[0]))
		return wrapper

	@post_retry_decorator
	def post(self, message, img_b=""):
		page = self.session.browser
		time.sleep(1)
		page.open(self.link)
		if img_b:
			public_id = re.match("public(\w+)", self.group_id).group(1)
			upload_url = "https://m.vk.com/attachments?target=wall-" + public_id + "&from=profile"
			page.open(upload_url)
			form = page.get_forms()[0]
			form["file1"] = img_b
			page.submit_form(form)
		form = page.get_forms()[0]
		form["message"] = message
		if "http" in message:
			time.sleep(1) #Для того, чтобы ссылка успела корректно загрузиться 
		page.submit_form(form)
		while page.parsed.find("img", {"class":"captcha_img"}):
			self.session.enter_captcha()
			WAIT_CAPTCHA = 20
			print("ждем %s сек" % WAIT_CAPTCHA)
			time.sleep(WAIT_CAPTCHA)


	def post_status_of_target(self, message):
		bin_img = sup_func.random_img_binary(img_rel_paths=sup_func.img_paths_list(path="data/content/images"))
		post_info = self.post(message, bin_img)
		bin_img.close()
		print("Группа: %s sleep 0.15" % self.link)
		time.sleep(0.15)

	def post_advert(self, adv_message, campain_images):
		"""Постит рекламное сообщение. в campain_images нужно передать название папки с картинками для оффера"""
		campain_images = "data/content/images_advert/%s" % campain_images
		bin_img = sup_func.random_img_binary(img_rel_paths=sup_func.img_paths_list(path=campain_images))
		post_info = self.post(adv_message, bin_img)
		bin_img.close()	
		print("Рекламное Группа: %s" % self.link)


	def __repr__(self):
		return "Group ID: %s" % self.group_id






class User:
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.proxy = rawdata.load_data_to_class("data/proxy.json", username)
		cookie_dict = rawdata.load_data_to_class("data/cookies.json", username)
		if cookie_dict:
			self.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
		else:
			self.cookies = ""

		self.session = vk_session(root_path="http://m.vk.com", proxy=self.proxy, cookies=self.cookies)
		self.session.connect()

	
		self.driver = "" #Поле будет инициализированно, если понадобится

		groups_list = rawdata.load_data_to_class("data/groups.json", username)
		self.groups = [Group(group_id=group, session=self.session, owner=self) for group in groups_list]

	def sign_in(self):
		page = self.session.browser
		captcha_exist = False
		page.open("http://m.vk.com")
		while True:
			if page.parsed.find("div", {"class":"owner_panel"}):
				print("Аккаунт %s уже авторизирован" % self)
				return 1
			if "act=blocked" in self.session.browser.url:
				print("Аккаунт забанен за спам %s" % self)
				return 0 		
			if "act=authcheck" in self.session.browser.url:
				print("Требуется подтверждение %s" % self)
				return 0
			print("Входим в аккаунт %s" % self.username)
		
			self.session.sign_in(username=self.username, password=self.password , captcha=captcha_exist)
			if page.parsed.find(id="captcha"):
				captcha_exist = True
				continue #Нашли поле для ввода каптчи, теперь выполнится ветвь функции session.sign_in с дополнительным полем формы
			if page.parsed.find("div", {"class":"service_msg_warning"}) or page.parsed.find("input", {"name":"email"}) or page.parsed.find("div", {"id":"login_authcheck_wrap"}):
				print("Проблемы с аккаунтом %s" % self)
				return 0
			if self.groups:
				page.open(self.groups[0].link)
				if page.parsed.find("div", {"class":"login_blocked_panel"}):
					print("Временная блокировка аккаунта %s" % self)
					return 0 
			self.cookies = self.session.browser.session.cookies
			cookie_dict = requests.utils.dict_from_cookiejar(self.cookies)
			rawdata.write_obj_to_json(path='data/cookies.json', data=cookie_dict, username=self.username)
			print("Вход выполнен")
			return 1



	def create_new_group(self, name):
		if not self.driver:
			self.driver = AllUsersControll.start_driver(proxy=self.proxy)
			self.driver = AllUsersControll.set_cookies_to_driver(self.driver, self.get_cookies())
		else:
			self.driver = AllUsersControll.set_cookies_to_driver(self.driver, self.get_cookies())
		print("Cоздание новой группы %s" % name) 
		self.session.create_new_group(name, "1", "4") #Тип группы: "1" (паблик), тип паблика: "4" (музыкальный альбом) (выбраны случайно)
		page = self.session.browser 
		while page.parsed.find("img", {"class":"captcha_img"}):
			self.session.enter_captcha()
			time.sleep(0.5)
		page = self.session.browser
		if page.parsed.find("div", {"class":"service_msg_warning"}):
			print("Действие временно невозможно, поскольку Вы совершили слишком много однотипных действий за последнее время.")
			return 0 
		try:
			page.parsed.find("a", {"class":"fi_value"})["href"] #Получаем ID созданной группы из формы
		except TypeError:
			try:
				self.subscribe_unsubscribe() 
			except:
				print(page.parsed)
				raise
		group_id = self.session.browser.url
		group_id = re.match("http[s]?://m.vk.com/(\w+)\?", group_id)
		try:
			group_id = group_id.group(1)
		except:
			print (self.session.browser.url)
		rawdata.add_group(group_id=group_id, username=self.username)
		group = Group(group_id=group_id, session=self.session, owner=self)
		
		while True:
			AllUsersControll.upload_avatar_to_new(group=group, driver=self.driver)

			page = self.session.browser
			page.open(group.link)
			

			page.open(group.link)
			if page.parsed.find("div", {"class":"profile_photo_upload"}) and page.parsed.find("i", {"class":"i_photo"}):
				continue
			break
		self.unsubscribe(page)
		self.groups.append(group)
		return self.driver

	def unsubscribe(self, page):
		"""на вход страница группы"""
		leave_url = page.parsed.find("a", {"class": "cm_item bli"})["href"]
		page.open("http://m.vk.com" + leave_url)

	def subscribe_unsubscribe(self):
		"""Лечит проблему потери прав администратора на группу"""
		page = self.session.browser 
		self.unsubscribe(page)
		enter_url = page.parsed.find("a", {"class": "button wide_button"})["href"]
		page.open("http://m.vk.com" + enter_url)

	def get_cookies(self):
		return self.cookies.get_dict()

	def __repr__(self):
		return "User: '%s:%s' | Proxy: %s | Groups count: %s" % (self.username, self.password, self.proxy, len(self.groups))




if __name__ == "__main__":
	"""Тесты """
	# a = User("79066335971", "KtOjGvRA")
	# a.sign_in()
	# a.create_new_group("qw233eee324")