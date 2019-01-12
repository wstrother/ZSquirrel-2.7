import constants as con


class Context:
    def __init__(self, game, class_dict=None):
        self.game = game
        self._class_dict = class_dict
        self.model = {}
        self.reset_model()

    def reset_model(self):
        self.model = {
            con.CONTEXT: self,
            con.GAME: self.game
        }

        cd = self._class_dict
        if cd:
            self.model.update(cd)

    def update_model(self, data):
        for item_name in data:
            item = data[item_name]
            for key in item:
                item[key] = self.get_value(item[key])

            self.model[item_name] = item

    def get_value(self, value, sub=None):
        def get(k):
            if k in self.model:
                return self.model[k]

            elif sub and k in sub:
                return sub[k]

            else:
                return k

        if type(value) is list:
            new = []
            for item in value:
                new.append(
                    self.get_value(item, sub=sub)
                )

            return new

        elif type(value) is dict:
            for key in value:
                if value[key] is True:
                    value[key] = self.get_value(
                        key, sub=sub
                    )

                else:
                    value[key] = self.get_value(
                        value[key], sub=sub
                    )

            return value

        else:
            return get(value)
