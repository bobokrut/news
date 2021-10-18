from typing import List as _List


class KeyboardException(Exception):
    pass


class Keyboard:
    @staticmethod
    def create_keyboard(buttons_map: _List[int], **buttons: str) -> str:
        """
        Creates keyboard for telegram api

        :param buttons_map: array of number of columns for each row eg. (2, 1) -> $button$ $button$ %new row% $button$
        :param buttons: callback = button text
        :return: inline keyboard
        """
        base = '{"inline_keyboard":[%s]}'

        if sum(buttons_map) != len(buttons.keys()):
            raise KeyboardException(f"Buttons map doesn't math given arguments: {sum(buttons_map)} != {len(buttons.keys())}")
        if "orignal" in buttons or "translate" in buttons:
            if "original" in buttons:
                del buttons["original"]
            if "translate" in buttons:
                del buttons["translate"]
            buttons_map[-1] -= 1
            if buttons_map[-1] == 0:
                buttons_map.pop(-1)
        inx_i = 0
        inx_j = 0
        internal_str = ["["]
        for callback, button in buttons.items():
            if inx_i == buttons_map[inx_j] - 1:
                internal_str.append('{"text": "%s", "callback_data": "%s"}' % (button, callback))
                internal_str.append("]" if inx_j == len(buttons_map) - 1 else "],[")
                inx_i = 0
                inx_j += 1
            else:
                inx_i += 1
                internal_str.append('{"text": "%s", "callback_data": "%s"}' % (button, callback))
                internal_str.append(",")

        return base % "".join(internal_str)
