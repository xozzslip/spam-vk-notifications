from models import *
from api import *
import rawdata_handler as rawdata
import time
import random
import sys
from threading import Thread, current_thread
from queue import *
import sys
import gc
from pympler import muppy, summary, tracker


sys.getsizeof(object)


TARGETS_PATH = 'data/targets.json'
ACCOUNTS_PATH = 'data/accounts.json'
ADV_MESSAGES_PATH = 'data/adv_messages.json'

COUNT_OF_GROUPS = 130
NAME_OF_GROUPS = "Мысли"

def main():
	
	adv_messages = rawdata.load_dict_from_json(ADV_MESSAGES_PATH)

	banned_users = []
	
	while True:
		accounts = rawdata.load_dict_from_json(ACCOUNTS_PATH)
		users = init(accounts)
		accounts.clear()
		try:
			queue = Queue()

			users_signed = []
			for user in users:
				if not user in banned_users:
					queue.put(user)

			for i in range(len(users) - len(banned_users)):
				thread = Thread(target=signing, args=(queue, users_signed, banned_users))
				thread.daemon = True
				thread.start()
			queue.join()
			del users[:]
			users = users_signed.copy()
			del users_signed[:]

			queue = Queue()
			for user in users:
				if not user in banned_users:
					queue.put(user)
			theard_count = 3 if len(users) >= 5 else 1
			for i in range(theard_count):
				thread = Thread(target=group_creating_desire_c, args=(queue, COUNT_OF_GROUPS, NAME_OF_GROUPS))
				thread.daemon = True
				thread.start()
			queue.join()

			arg_list = {"counter":0, "adv_counter":0, "iteration":0}
			
			while True:
				queue = Queue()
				del_targ = []
				targets = rawdata.load_dict_from_json(TARGETS_PATH)
				len_targets = len(targets)
				time_start = time.time()
				for user in users:
					if not user in banned_users:
						queue.put(user)
				print("незабаненных пользователей %s/%s | забаненны %s" % (len(users) - len(banned_users), len(users), banned_users))
				for i in range(len(users) - len(banned_users)):
					thread = Thread(target=posting_for_all_users, args=(queue, targets, adv_messages, arg_list, del_targ, banned_users))
					thread.daemon = True
					thread.start()

				queue.join()

				time_stop = time.time()
				time_dif = time_stop - time_start
				wait_time = 60*(24 + random.uniform(0, 5)) - time_dif

				u_banned_users = [user.username for user in banned_users]
				rawdata.delete_from_json(data=del_targ, path_to_data=TARGETS_PATH)
				rawdata.delete_from_json(data=u_banned_users, path_to_data=ACCOUNTS_PATH)
				del del_targ[:]
				targets.clear()
				del targets
				
				gc.collect()
				summary.print_(summary.summarize(muppy.get_objects()))


				print("Осталось целей %s" % len_targets)
				print("Всего/рекламных %s/%s за %s мин" % (arg_list["counter"], arg_list["adv_counter"], str(time_dif / 60)))
				
				if wait_time > 0:
					print("Пауза %s минут\n" % str(wait_time / 60))
					time.sleep(wait_time)
				else:
					print("Продолжаем без паузы %s мин запаздывания\n" % str(-1 * wait_time / 60))
				arg_list["iteration"] += 1
		except:
			print("Ошибка в posting.py/main %s" % sys.exc_info()[0])
			raise


def signing(queue, users_signed, banned_users):
	while not queue.empty():
		a = queue.get_nowait()
		while True:
			try:
				if a.sign_in():
					users_signed.append(a)
				else:
					banned_users.append(a)
				break
			except:
				time.sleep(1)
				print("____________KEK")
				continue

		queue.task_done()

def init(accounts):
	users = []
	for a in accounts:
		a = User(a, accounts[a])
		users.append(a)
	return users

def group_creating_all(users, gr_count, name):
	for u in users:
		print(u)
		for i in range(gr_count):
			u.create_new_group(name)

def group_creating_desire_c(queue, gr_count_desire, name):
	while not queue.empty():
		u = queue.get_nowait()
		print("групп %s/%s" % (len(u.groups), gr_count_desire))
		driver = None
		while len(u.groups) < gr_count_desire:
			driver = u.create_new_group(name)
			if not driver:
				break
		if driver:
			driver.close()


		queue.task_done()
		


def posting_for_all_users(queue, targets, adv_messages, arg_list, del_targ, banned_users):
	while not queue.empty():
		try:
			u = queue.get_nowait()
			STEP_OF_ADV = 5
			c_adv_posts_every_iter = len(u.groups) // STEP_OF_ADV
			groups_for_adv = [(arg_list["iteration"] - 1 + STEP_OF_ADV * s) % len(u.groups) for s in range(c_adv_posts_every_iter)] #рекламные посты в ... 
			
			while True:
				try:
					for j in range(len(u.groups)):
						group = u.groups[j]
						if j in groups_for_adv and arg_list["iteration"] > 0: 
							number_of_adv = random.randint(0, len(adv_messages) - 1)
							adv_message = adv_messages[number_of_adv]
							group.post_advert(adv_message=adv_message["text"], campain_images=adv_message["path"])
							arg_list["adv_counter"] += 1
							rawdata.add_counter_to_adv_mes(field_name=number_of_adv, path_to_data=ADV_MESSAGES_PATH)
							time.sleep(5) #после рекламного поста 5 секунд
						else:
							number_of_target = random.choice(list(targets.keys()))
							targ = targets[number_of_target]
							message = AllUsersControll.make_message(targ)
							group.post_status_of_target(message=message)
							del targets[number_of_target]
							del_targ.append(number_of_target)
						arg_list["counter"] += 1
					break
				except requests.exceptions.ConnectionError:
					print("ConnectionError, продолжаем") 
					time.sleep(7)
					continue

		except:
			print("Аккаунт, возможно, забанен %s" % u)
			banned_users.append(u)

		queue.task_done()

		


if __name__ == "__main__":
	main()

	