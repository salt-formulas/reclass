class ParameterList(list):
    def __init__(self, *args, **kwargs):
        self._uri = kwargs.pop('uri', None)
        list.__init__(self, *args, **kwargs)

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = uri

    @property
    def has_inv_query(self):
        for item in self:
            if item.has_inv_query:
                return True
        return False

    @property
    def needs_all_envs(self):
        for item in self:
            if item.has_inv_query and item.needs_all_envs:
                return True
        return False

    @property
    def ignore_failed_render(self):
        for item in self:
            if item.has_inv_query and item.ignore_failed_render is False:
                return False
        return True

    def get_inv_references(self):
        inv_refs = []
        for item in self:
            if item.has_inv_query:
                inv_refs += item.get_inv_references()
        return inv_refs
