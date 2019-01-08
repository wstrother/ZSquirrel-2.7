class MemberTable:
    def __init__(self):
        self.table = [[]]
        self.pointer = 0, 0

    @property
    def active_member(self):
        if self.member_list:
            return self.get_member(*self.pointer)

    @property
    def member_list(self):
        l = []
        for row in self.table:
            for item in row:
                if item:
                    l.append(item)

        return l

    def get_member(self, i, j):
        return self.table[i][j]

    def can_select(self, i, j):
        try:
            return self.select_function(self.get_member(i, j))
        except IndexError:
            return False

    @staticmethod
    def select_function(item):
        return item is not None

    def move_pointer(self, x, y):
        i, j = self.pointer
        table = self.table
        start = [i, j]

        cycling = True
        while cycling:
            if x != 0:
                j += x
                cells = len(table[i]) - 1

                if j > cells:
                    j = 0
                elif j < 0:
                    j = cells

            if y != 0:
                i += y
                rows = len(table) - 1

                if i > rows:
                    i = 0
                elif i < 0:
                    i = rows

            self.pointer = [i, j]
            cycling = not self.can_select(*self.pointer)

            if self.pointer == start:
                cycling = False

    def adjust_size(self, size, border_size, buffers):
        w, h = size
        border_w, border_h = border_size
        buff_w, buff_h = buffers

        body_w, body_h = self.get_minimum_body_size(buffers)
        full_w, full_h = (
            body_w + ((border_w + buff_w) * 2),
            body_h + ((border_h + buff_h) * 2))

        if w < full_w:
            w = full_w
        if h < full_h:
            h = full_h

        return w, h

    def get_minimum_body_size(self, buffers):
        members = self.table
        r_widths, r_heights = [], []
        buff_w, buff_h = buffers

        for row in members:
            row_w, row_h = self.get_minimum_row_size(row, buff_w)
            r_widths.append(row_w)
            r_heights.append(row_h)

        try:
            width = sorted(r_widths, key=lambda x: x * -1)[0]
        except IndexError:
            width = 0
        height = sum(r_heights) + ((len(r_heights) - 1) * buff_h)

        return width, height

    @staticmethod
    def get_minimum_row_size(row, buff_w):
        row_w, row_h = 0, 0
        item_widths = []

        for item in row:
            w, h = getattr(item, "size", (0, 0))
            item_widths.append(w)

            if h > row_h:
                row_h = h
        row_w = sum(item_widths) + ((len(row) - 1) * buff_w)

        return row_w, row_h

    def set_member_positions(self, position, size, border_size, buffers, aligns):
        if self.member_list:
            parent_x, parent_y = position
            w, h = size

            if aligns:
                align_h, align_v = aligns
            else:
                align_h, align_v = "c", "c"

            border_w, border_h = border_size
            buff_w, buff_h = buffers

            edge_x, edge_y = border_w + buff_w, border_h + buff_h
            body_w, body_h = w - (edge_x * 2), h - (edge_y * 2)

            def get_cell_size(items):
                ch = body_w / len(items)
                cw = body_h / len(self.table)

                return ch, cw

            i, y_disp = 0, 0
            for row in self.table:
                if row:
                    cell_w, cell_h = get_cell_size(row)

                    row_w, row_h = self.get_minimum_row_size(row, buff_w)

                    j, x_disp = 0, 0
                    for item in row:
                        if item:
                            item_w, item_h = item.size
                            x, y = edge_x, edge_y
                            r_offset = body_w - row_w
                            b_edge = body_h - self.get_minimum_body_size(buffers)[1]

                            x += {
                                "l": x_disp,
                                "c": (j * cell_w) + ((cell_w - item_w) / 2),
                                "r": r_offset + x_disp
                            }[align_h]

                            y += {
                                "t": y_disp,
                                "c": (i * cell_h) + ((cell_h - item_h) / 2),
                                "b": b_edge + y_disp
                            }[align_v]

                            item.set_position(
                                parent_x + x,
                                parent_y + y
                            )

                            x_disp += item_w + buff_w
                        j += 1
                    y_disp += row_h + buff_h
                    i += 1

    @staticmethod
    def get_cell_size(size, num_cells):
        w, h = size

        return w / num_cells, h / num_cells