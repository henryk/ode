from ode.model import Group

def get_titles():
	groupTitles = []
	groups = Group.query.all()
	for group in groups:
		if group.title.value not in groupTitles and group.title.value is not '':
			groupTitles.append(group.title.value)

	groupTitles.append('')
	return groupTitles