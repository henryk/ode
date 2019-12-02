from ode.model import Group, get_titles

from flask_babel import _

def sort_group_by_title(group_list):
	titles = get_titles()

	sorted_group_list = []
		
	for title in titles:
		for group in group_list:
			if str(group.title) == str(title):
				sorted_group_list.append(group)

			if str(title) == '' and str(group.title) == '':
				group.title = _('(no title)')

			if str(group.description) == '':
				group.description = _('(no description)')
	
	return sorted_group_list

	