# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-04-30 19:28:15

from pwn import *
from unit import BaseUnit
import units
import os
from units import NotApplicable

# JOHN: This may be used across mutliple units, so I place them here
#       to prevent duplicate code
potential_username_variables = [
			'username', 'user', 'uname', 'un', 'name', 'user1', 'input1', 'uw1', 'username1', 'uname1', 'tbUsername', 'usern', 'id'
]
potential_password_variables = [
	'password', 'pass', 'pword', 'pw', 'pass1', 'input2', 'password1', 'pw1', 'pword1', 'tbPassword'
]

potential_file_variables = [
	'fileToUpload', 'file', 'upload_file', 'file_to_upload',
]


user_regex = "<\s*input.*name\s*=\s*['\"](%s)['\"]" % "|".join(potential_username_variables)
pass_regex = "<\s*input.*name\s*=\s*['\"](%s)['\"]" % "|".join(potential_password_variables)

potential_cookie_names = [ 'admin', 'is_admin', 'isadmin', 'administrator', 'isAdmin' ]

delim = '@@DELIMETER@@'
special = '@@SPECIAL@@'

potential_flag_names = ['flag', 'flag.txt']


class WebUnit(BaseUnit):
	
	def __init__(self, katana, parent, target):

		super(WebUnit, self).__init__(katana, parent, target)
		
		if not self.target.is_url:
			raise NotApplicable("not a web url")
