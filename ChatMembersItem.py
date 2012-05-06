from AbstractListItem import AbstractListItem


class ChatMembersItem(AbstractListItem):
	def __init__(self, parent, jid, show, con):
		AbstractListItem.__init__(self, parent, jid, show, con)
