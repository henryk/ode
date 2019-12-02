
from flask import session
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, HiddenField, SelectMultipleField, BooleanField, widgets, FieldList, TextField, SelectField
from wtforms.validators import DataRequired, Email

from flask_babel import _
from ode.model import get_titles
from group_titles import sort_group_by_title

from wtforms.utils import unset_value

class MultiCheckboxField(SelectMultipleField):
	widget = widgets.ListWidget(prefix_label=False)
	option_widget = widgets.CheckboxInput()

class EditSelfForm(Form):
	givenname = StringField(_("Given Name"), validators=[DataRequired()])
	surname = StringField(_('Last Name'), validators=[DataRequired()])
	mail = StringField(_('Private E-Mail address'), validators=[DataRequired(),Email()])
	send_password = BooleanField(_('Generate and send new password to user'))

	password = StringField('New Password')
	name = StringField(_('Full Name'), validators=[DataRequired()])

	update = SubmitField(_('Update!'))


def get_EditUserForm(group_list):
	class EditUserForm(Form):
		givenname = StringField(_('Given Name'), validators=[DataRequired()])
		surname = StringField(_('Last Name'), validators=[DataRequired()])
		mail = StringField(_('Private E-Mail address'), validators=[DataRequired(),Email()])
		send_password = BooleanField(_('Generate and send new password to user'))

		password = StringField(_('New Password'))
		userid = HiddenField(_('Username'), validators=[DataRequired()])
		name = StringField(_('Full Name'), validators=[DataRequired()])

		aliases = StringField(_('Additional E-Mail addresses'))

		groups = MultiCheckboxField(_('Groups'), choices = [ (_G.dn,"{},   {} in {}".format(_G.name, _G.description, _G.title)) for _G in sort_group_by_title(group_list) ] )

		update = SubmitField(_('Update!'))

		delete_confirm = BooleanField(_('Confirm deletion'))
		delete = SubmitField(_('Delete!'))
	
	return EditUserForm

def get_NewUserForm(group_list):
	class NewUserForm(Form):
		givenname = StringField(_('Given Name'), validators=[DataRequired()])
		surname = StringField(_('Last Name'), validators=[DataRequired()])
		mail = StringField(_('Private E-Mail address'), validators=[DataRequired(),Email()])
		send_password = BooleanField(_('Generate password and send to user'), default=True)

		password = StringField(_('Password'), validators=[DataRequired()])
		userid = StringField(_('Username'), validators=[DataRequired()])
		name = StringField(_('Full Name'), validators=[DataRequired()])

		aliases = StringField(_('Additional E-Mail addresses'))

		groups = MultiCheckboxField(_('Groups'), choices = [ (_G.dn,"{} - {}".format(_G.name, _G.description)) for _G in group_list ] )

		submit = SubmitField(_('Create!'))

	return NewUserForm

def get_EditGroupForm(user_list):
	class EditGroupForm(Form):
		title = StringField(_('Supercategory'))

		description = StringField(_('Group Description'))
		
		members = MultiCheckboxField(_('Members'), choices = [ (_M.dn,_M.name) for _M in user_list ] )

		update = SubmitField(_('Update!'))

		delete_confirm = BooleanField(_('Confirm deletion'))
		delete = SubmitField(_('Delete!'))
	return EditGroupForm

def get_NewGroupForm(user_list):
	class NewGroupForm(Form):
		title = StringField(_('Supercategory'))

		name = StringField(_('Group Name'), validators=[DataRequired()])

		description = StringField(_('Group Description'))

		members = MultiCheckboxField(_('Members'), choices = [ (_M.dn,_M.name) for _M in user_list ] )

		submit = SubmitField(_('Create!'))

	return NewGroupForm

def get_EditMailingListForm(user_list, group_list):
	class EditMailingListForm(Form):
		list_members = FieldList(StringField(''))
		import_file = FileField(_('Import'), validators=[FileAllowed(['txt'], _('Text files'))])

		update = SubmitField(_('Update!'))

		delete_confirm = BooleanField(_('Confirm deletion'))
		delete = SubmitField(_('Delete!'))
	return EditMailingListForm

def get_NewMailingListForm(user_list, group_list):
	class EditMailingListForm(Form):
		name = StringField(_('Mailing List Name'), validators=[DataRequired()])

		list_members = FieldList(StringField(''))
		import_file = FileField(_('Import'), validators=[FileAllowed(['txt'], _('Text files'))])

		submit = SubmitField(_('Create!'))
	
	return EditMailingListForm

def get_EditAliasForm(user_list, group_list, alias_list):
	class EditAliasForm(Form):
		members = FieldList(StringField(''))

		update = SubmitField(_('Update!'))

		delete_confirm = BooleanField(_('Confirm deletion'))
		delete = SubmitField(_('Delete!'))
	return EditAliasForm

def get_NewAliasForm(user_list, group_list, alias_list):
	class EditAliasForm(Form):
		name = StringField(_('Alias Name'), validators=[DataRequired()])

		members = FieldList(StringField(''))

		submit = SubmitField(_('Create!'))
	
	return EditAliasForm
