import json

def add_accounts():
	f_read = open('data/rawdata/accounts') 
	f_write = open('data/accounts.json', "w")

	lines = f_read.read().splitlines()
	accs = {}
	for line in lines:
		data = line.split(":")
		accs[data[0]] = data[1]
	f_write.write(json.dumps(accs, indent=4))
	f_write.close()
	f_read.close()


def add_group(group_id, username):
	path = 'data/groups.json'
	f = open(path, "r+")
	prev_dara = f.read()
	if prev_dara:
		grp = json.loads(prev_dara)
	else:
		grp = {}
	if not username in grp:
		grp[username] = []
	grp[username].append(group_id)
	f.seek(0)
	f.write(json.dumps(grp, indent=4))
	f.truncate()
	f.close()


def write_obj_to_json(path, data, username):
	f = open(path, "r+")
	prev_dara = f.read()
	if prev_dara:
		grp = json.loads(prev_dara)
	else:
		grp = {}
	grp[username] = data
	f.seek(0)
	f.write(json.dumps(grp, indent=4))
	f.truncate()
	f.close()

def load_data_to_class(path_to_data, username):
	with open(path_to_data) as f:
		data = f.read()
	if not username in data or not data:
		return "" #Если файл пуст или в нем нет указанного пользователя
	data = json.loads(data)
	return data[username]

def load_dict_from_json(path_to_data, f=None):
	if not f:
		f = open(path_to_data)
	data = f.read()
	if not data:
		return {}
	data = json.loads(data)
	if not f:
		f.close()
	return data

def write_dict_to_json(path_to_data, data, f=None):
	if not f:
		f = open(path_to_data, "w")
	f.write(json.dumps(data, indent=4))
	if not f:
		f.close()

def delete_from_json(data, path_to_data):
	"""удаляет поля data из json"""
	f = open(path_to_data, "r+")
	initial_dict = load_dict_from_json(path_to_data=path_to_data, f=f)
	for field in data:
		if field in initial_dict:
			del initial_dict[field]
	f.seek(0)
	write_dict_to_json(data=initial_dict, path_to_data=path_to_data, f=f)
	f.truncate()
	f.close()

def add_counter_to_adv_mes(field_name, path_to_data, data_int=1):
	f = open(path_to_data, "r+")
	initial_dict = load_dict_from_json(path_to_data=path_to_data, f=f)
	initial_dict[field_name]["counter"] += data_int
	f.seek(0)
	write_dict_to_json(data=initial_dict, path_to_data=path_to_data, f=f)
	f.truncate()
	f.close()

def upload_proxy():
	with open('data/rawdata/proxy', 'r') as f:
		proxy = f.read().splitlines()
	accounts = load_dict_from_json('data/accounts.json')
	accs_with_proxy = {}
	i = 0
	if len(proxy) != 0:
		for acc in accounts:
			accs_with_proxy[acc] = proxy[i % len(proxy)]
			i += 1
	else:
		for acc in accounts:
			accs_with_proxy[acc] = ""
	write_dict_to_json('data/proxy.json', accs_with_proxy)



if __name__ == "__main__":
	upload_proxy()