# -*- coding: utf-8 -*-
PERCENT = "%.1f%%"


class Result:
    def __init__(self):
        self.title = ""
        self.columns = []
        self.rows = []

    def add_row(self, dice, values):
        self.rows.append([dice] + values)

    def get_html(self):
        res = "\n<tr><th class=\"title\">%s</th>" % self.title
        for c in self.columns:
            res += "<th>%s</th>" % c
        res += "</tr>"
        for r in self.rows:
            res += "\n<tr><td class=\"dices\">"

            for d in r[0]:
                res += '<span class="die %s" title="%s"></span>' % (d.name, d.name)

            res += "</td>"

            for v in r[1:]:
                html_class = ""
                if v and v[-1] == "%":
                    try:
                        value = float(v[:-1])
                        html_class = "val-%d" % (int(value / 20) * 20)
                    except ValueError:
                        pass

                if html_class:
                    res += '<td class="%s">%s</td>' % (html_class, v)
                else:
                    res += "<td>%s</td>" % v

            res += "</tr>"
        # res += "</table>"
        return res

    def to_file(self, f):
        f.write(self.get_html())


class Side:
    def __init__(self, shields=0, surges=0, miss=False, hearts=0, range=0):
        self.shields = shields
        self.surges = surges
        self.miss = miss
        self.hearts = hearts
        self.range = range

    def __repr__(self):
        if self.miss:
            return "X"
        result = ""

        if self.shields > 0:
            result += " %s" % ("▢" * self.shields)
        if self.range > 0:
            result += " %d" % self.range
        if self.hearts > 0:
            result += " %s" % ("♥" * self.hearts)
        if self.surges > 0:
            result += " %s" % ("☇" * self.surges)

        return "|" + result.strip() + "|"


class Die:
    def __init__(self, name, code, sides, order = 0):
        if len(sides) != 6:
            raise Exception("Invalid number of dice sides, %d" % len(sides))

        self.name = name
        self.code = code
        self.sides = sides
        self.order = order

    def __repr__(self):
        return "{%s: %s}" % (self.name, "-".join(("%s" % s for s in self.sides)))


class DiceSet:
    def __init__(self, dice):
        self.dice = dice

    def __iter__(self):
        return self.dice.__iter__()

    def __getitem__(self, item):
        return self.dice.__getitem__(item)

    def __len__(self):
        return self.dice.__len__()

    def __cmp__(self, other):
        if len(self.dice) > len(other.dice):
            return 1
        elif len(self.dice) < len(other.dice):
            return -1

        for i, d in enumerate(self.dice):
            if d.order != other.dice[i].order:
                return d.order - other.dice[i].order

        return 0

# single roll, eg. one die and one side
class SingleRoll:
    def __init__(self, die, side):
        assert isinstance(side, Side)
        assert isinstance(die, Die)
        self.die = die
        self.side = side

    def __repr__(self):
        return "%s >> %s" % (self.die.name, self.side)


# full roll, eg. one throw of multiple dice
class FullRoll:
    def __init__(self, rolls):
        # list(SingleRoll)
        self.rolls = rolls

    def miss(self):
        for roll in self.rolls:
            assert isinstance(roll, SingleRoll)
            if roll.side.miss:
                return True

        return False

    def range(self):
        return sum(roll.side.range for roll in self.rolls)

    def surges(self):
        return sum(roll.side.surges for roll in self.rolls)

    def hearts(self):
        return sum(roll.side.hearts for roll in self.rolls)

    def shields(self):
        return sum(roll.side.shields for roll in self.rolls)

# defense
black = Die("black", "Bl",
            [Side(shields=0), Side(shields=2), Side(shields=2), Side(shields=2), Side(shields=3), Side(shields=4)], 6)
gray = Die("gray", "Gr",
           [Side(shields=0), Side(shields=1), Side(shields=1), Side(shields=1), Side(shields=2), Side(shields=3)], 5)
brown = Die("brown", "Br",
            [Side(shields=0), Side(shields=0), Side(shields=0), Side(shields=1), Side(shields=1), Side(shields=2)], 4)

# attack
blue = Die("blue", "Uu", [
    Side(miss=True),
    Side(range=2, hearts=2, surges=1),
    Side(range=3, hearts=2),
    Side(range=4, hearts=2),
    Side(range=5, hearts=1),
    Side(range=6, hearts=1, surges=1),
], 0)

# power
yellow = Die("yellow", "Ye", [
    Side(range=1, surges=1),
    Side(range=1, hearts=1),
    Side(hearts=2),
    Side(hearts=2, surges=1),
    Side(hearts=1, surges=1),
    Side(range=2, hearts=1),
], 2)

red = Die("red", "Re", [
    Side(hearts=1),
    Side(hearts=2),
    Side(hearts=2),
    Side(hearts=2),
    Side(hearts=3),
    Side(hearts=3, surges=1),
], 3)
green = Die("green", "Gn", [
    Side(hearts=1),
    Side(range=1, hearts=1, surges=1),
    Side(range=1, hearts=1),
    Side(range=1, surges=1),
    Side(hearts=1, surges=1),
    Side(surges=1)
], 1)


def roll_all_rolls(dice):
    """

    :rtype : list
    """
    die = dice[0]

    if len(dice) == 1:
        return list(
            (
                FullRoll(
                    [SingleRoll(die, side)]
                )
                for side in die.sides
            )
        )

    rest_all = roll_all_rolls(dice[1:])

    result = []

    for side in die.sides:
        for rest_single in rest_all:
            result.append(FullRoll([SingleRoll(die, side)] + rest_single.rolls))

    return result


def experiment_ranges(ranges, combinations):
    combinations.sort()
    res = Result()
    res.title = "Ranges"
    res.columns.append("AVG")
    for r in ranges:
        res.columns.append("%d+" % r)


    for comb in combinations:
        all_rolls = roll_all_rolls(comb)

        row = []

        ranges_sum = 0
        hit_count = 0
        for full_roll in all_rolls:
            assert isinstance(full_roll, FullRoll)

            if full_roll.miss():
                continue

            ranges_sum += full_roll.range()
            hit_count += 1

        row.append('%.2f <span class="icon range"/>' % (ranges_sum * 1.0 / hit_count))

        for r in ranges:
            passes = 0
            for full_roll in all_rolls:
                assert isinstance(full_roll, FullRoll)
                if full_roll.miss():
                    continue

                if full_roll.range() < r:
                    continue

                passes += 1

            row.append(PERCENT % (passes * 100.0 / hit_count))

        res.add_row(comb, row)

    return res


def experiment_surges(surges, combinations):
    combinations.sort()
    res = Result()
    res.title = "Surges"
    res.columns.append("AVG")
    for s in surges:
        res.columns.append("%d+" % s)

    for comb in combinations:
        all_rolls = roll_all_rolls(comb)

        row = []

        surges_sum = 0
        hit_count = 0
        for full_roll in all_rolls:
            assert isinstance(full_roll, FullRoll)

            if full_roll.miss():
                continue

            surges_sum += full_roll.surges()
            hit_count += 1

        row.append('%.2f <span class="icon surge"/>' % (surges_sum * 1.0 / hit_count))

        for s in surges:
            passes = 0
            for full_roll in all_rolls:
                assert isinstance(full_roll, FullRoll)

                total_surges = full_roll.surges()
                if full_roll.miss():
                    total_surges = 0

                if total_surges < s:
                    continue

                passes += 1

            row.append(PERCENT % (passes * 100.0 / hit_count))

        res.add_row(comb, row)

    return res


def experiment_hearts(hearts, combinations):
    combinations.sort()
    res = Result()
    res.title = "Hearts"
    res.columns.append("AVG")
    for h in hearts:
        res.columns.append("%d+" % h)

    for comb in combinations:
        all_rolls = roll_all_rolls(comb)

        row = []

        hearts_sum = 0
        hit_count = 0
        for full_roll in all_rolls:
            assert isinstance(full_roll, FullRoll)

            if full_roll.miss():
                continue

            hearts_sum += full_roll.hearts()
            hit_count += 1

        row.append('%.2f <span class="icon heart"/>' % (hearts_sum * 1.0 / hit_count))

        for h in hearts:
            passes = 0
            for full_roll in all_rolls:
                assert isinstance(full_roll, FullRoll)

                total_hearts = full_roll.hearts()
                if full_roll.miss():
                    total_hearts = 0

                if total_hearts < h:
                    continue

                passes += 1

            row.append(PERCENT % (passes * 100.0 / hit_count))

        res.add_row(comb, row)

    return res


def experiment_shields(shields, combinations):
    combinations.sort()
    res = Result()
    res.title = "Shields"
    res.columns.append("AVG")
    for s in shields:
        res.columns.append("%d+" % s)

    for comb in combinations:
        all_rolls = roll_all_rolls(comb)

        row = []

        shields_sum = 0
        for full_roll in all_rolls:
            assert isinstance(full_roll, FullRoll)

            shields_sum += full_roll.shields()

        row.append('%.2f <span class="icon shield"/>' % (shields_sum * 1.0 / len(all_rolls)))

        for s in shields:
            passes = 0
            for full_roll in all_rolls:
                assert isinstance(full_roll, FullRoll)

                if full_roll.shields() < s:
                    continue

                passes += 1

            row.append(PERCENT % (passes * 100.0 / (len(all_rolls))))

        res.add_row(comb, row)

    return res


def experiment_attribute_test(shields, combinations):
    combinations.sort()
    res = Result()
    res.title = "Attribute tests"
    res.columns.append("")
    for s in shields:
        res.columns.append("%8s" % s)

    for comb in combinations:
        all_rolls = roll_all_rolls(comb)

        row = [""]

        for s in shields:
            passes = 0
            for full_roll in all_rolls:
                assert isinstance(full_roll, FullRoll)

                if full_roll.shields() > s:
                    continue

                passes += 1

            row.append(PERCENT % (passes * 100.0 / (len(all_rolls))))

        res.add_row(comb, row)

    return res


with open("head.html", "r") as headfile:
    data = headfile.read()

f = file("dice.html", "w")
f.write(data)

attack_die_standard = [
    DiceSet([blue, green]),
    DiceSet([blue, green]),
    DiceSet([blue, yellow]),
    DiceSet([blue, red]),
    DiceSet([blue, green, green]),
    DiceSet([blue, yellow, green]),
    DiceSet([blue, yellow, yellow]),
    DiceSet([blue, red, green]),
    DiceSet([blue, red, yellow]),
    DiceSet([blue, red, yellow, green]),
    DiceSet([blue, red, green, green]),
    DiceSet([blue, red, red]),
    DiceSet([blue, yellow, yellow, green]),
    DiceSet([blue, yellow, yellow, green, green]),
    # [red, red, green, green],
]

experiment_ranges(range(1, 12), [
    DiceSet([blue, ]),
    DiceSet([green, ]),
    DiceSet([yellow, ]),
    DiceSet([blue, green]),
    DiceSet([blue, yellow]),
    DiceSet([blue, green, green]),
    DiceSet([blue, yellow, green]),
    DiceSet([blue, yellow, yellow]),
]).to_file(f)

experiment_surges(range(1, 6), [
    DiceSet([blue, ]),
    DiceSet([green, ]),
    DiceSet([yellow, ]),
    DiceSet([red, ]),
] + attack_die_standard + [
                      DiceSet([red, green]),  # apothecary heal+
                      DiceSet([red, red])
                  ]).to_file(f)

experiment_hearts(range(1, 10), [
    DiceSet([blue, ]),
    DiceSet([yellow, ]),
    DiceSet([red, ]),
    DiceSet([red, red, ]),
] + attack_die_standard
                  + [
                      DiceSet([red, green]),  # apothecary heal+
                  ]
                  ).to_file(f)
experiment_shields(range(1, 13), [
    DiceSet([brown, ]),
    DiceSet([gray, ]),
    DiceSet([black]),

    DiceSet([gray, brown, ]),
    DiceSet([gray, gray, ]),
    DiceSet([black, brown, ]),
    DiceSet([black, gray, ]),

    DiceSet([gray, brown, brown]),
    DiceSet([gray, gray, brown, ]),
    DiceSet([black, gray, brown, ]),
    DiceSet([black, gray, gray, ]),
    DiceSet([black, black, gray, ]),
]).to_file(f)
experiment_attribute_test(range(6, -1, -1), [
    DiceSet([black, gray])
]).to_file(f)

f.write("</table></body></html>")
