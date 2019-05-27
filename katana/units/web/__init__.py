# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-02-28 22:33:18
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-05-26 11:31:36

from pwn import *
from katana.unit import BaseUnit
from katana import units
import os
from katana.units import NotApplicable
# import target

# JOHN: This may be used across mutliple units, so I place them here
#       to prevent duplicate code
potential_username_variables = [
	b'username', b'user', b'uname', b'un', b'name', b'user1', b'input1', b'uw1', b'username1', b'uname1', b'tbUsername', b'usern', b'id'
]
potential_password_variables = [
	b'password', b'pass', b'pword', b'pw', b'pass1', b'input2', b'password1', b'pw1', b'pword1', b'tbPassword'
]

potential_file_variables = [
	b'fileToUpload', b'file', b'upload_file', b'file_to_upload',
]


user_regex = rb'<\s*input.*name\s*=\s*[\'"](%s)[\'"]' % b"|".join(potential_username_variables)
pass_regex = rb'<\s*input.*name\s*=\s*[\'"](%s)[\'"]' % b"|".join(potential_password_variables)

potential_cookie_names = [ 'admin', 'is_admin', 'isadmin', 'administrator', 'isAdmin' ]

delim = '@@DELIMETER@@'
special = '@@SPECIAL@@'

potential_flag_names = [b'flag', b'flag.txt']


class WebUnit(BaseUnit):
	
	def __init__(self, katana, target):

		super(WebUnit, self).__init__(katana, target)
		
		if not self.target.is_url:
			raise NotApplicable("not a web url")
